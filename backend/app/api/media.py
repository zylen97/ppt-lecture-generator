"""
音视频处理API
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File as FastAPIFile, status, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pathlib import Path
import hashlib
import uuid
import os
import asyncio
import json
from typing import List, Optional, Dict, Any, Tuple

from ..database import get_db
from ..models import File, Task, TaskType, TaskStatus, FileType
from pydantic import BaseModel
from ..schemas import FileResponse, FileUpload, TaskResponse, TaskCreate
from ..services.media_service import MediaService, MediaProcessingError
from ..services.whisper_service import get_whisper_service, WhisperTranscriptionError
import logging

router = APIRouter()


class TranscriptionRequest(BaseModel):
    model_config = {"protected_namespaces": ()}
    language: str = "auto"
    model_size: str = "base"


@router.post("/upload", response_model=FileUpload)
async def upload_media_file(
    file: UploadFile = FastAPIFile(...),
    db: Session = Depends(get_db)
):
    """
    上传音视频文件
    """
    # 验证文件类型
    file_type = MediaService.detect_media_type(file.filename)
    if not file_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件类型。支持的格式: {MediaService.get_supported_formats()}"
        )
    
    # 验证文件大小 (500MB限制，音视频文件通常较大)
    max_size = 500 * 1024 * 1024  # 500MB
    if file.size and file.size > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="文件大小超过限制（最大500MB）"
        )
    
    try:
        # 创建上传目录
        upload_dir = Path("uploads") / "media"
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成唯一文件名
        file_id = str(uuid.uuid4())
        file_ext = Path(file.filename).suffix.lower()
        filename = f"{file_id}{file_ext}"
        file_path = upload_dir / filename
        
        # 保存文件
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        # 计算文件哈希
        file_hash = hashlib.sha256(content).hexdigest()
        
        # 检查是否已存在相同文件
        existing_file = db.query(File).filter(File.file_hash == file_hash).first()
        if existing_file:
            # 删除刚上传的文件
            os.remove(file_path)
            return FileUpload(
                success=True,
                message="文件已存在",
                file_id=existing_file.id
            )
        
        # 获取媒体文件信息
        try:
            media_info = MediaService.get_media_info(str(file_path))
            if not media_info:
                raise MediaProcessingError("无法解析媒体文件信息")
                
        except Exception as e:
            # 清理文件
            os.remove(file_path)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"媒体文件解析失败: {str(e)}"
            )
        
        # 创建数据库记录
        db_file = File(
            filename=filename,
            original_name=file.filename,
            file_path=str(file_path),
            file_size=file.size or len(content),
            file_hash=file_hash,
            file_type=file_type,
            
            # 媒体信息
            duration=media_info.get('duration'),
            sample_rate=media_info.get('sample_rate'),
            channels=media_info.get('channels'),
            bitrate=media_info.get('bitrate'),
            codec=media_info.get('audio_codec') or media_info.get('video_codec'),
            resolution=media_info.get('resolution'),
            fps=media_info.get('fps'),
        )
        
        db.add(db_file)
        db.commit()
        db.refresh(db_file)
        
        return FileUpload(
            success=True,
            message="媒体文件上传成功",
            file_id=db_file.id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        # 清理文件
        if 'file_path' in locals() and Path(file_path).exists():
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件上传失败: {str(e)}"
        )


@router.get("/{file_id}", response_model=FileResponse)
def get_media_file(file_id: int, db: Session = Depends(get_db)):
    """
    获取媒体文件信息
    """
    file = db.query(File).filter(
        File.id == file_id,
        File.file_type.in_([FileType.AUDIO, FileType.VIDEO])
    ).first()
    
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="媒体文件不存在"
        )
    
    return file


@router.get("/", response_model=List[FileResponse])
def list_media_files(
    file_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    获取媒体文件列表
    """
    query = db.query(File).filter(
        File.file_type.in_([FileType.AUDIO, FileType.VIDEO])
    )
    
    if file_type:
        if file_type.lower() == "audio":
            query = query.filter(File.file_type == FileType.AUDIO)
        elif file_type.lower() == "video":
            query = query.filter(File.file_type == FileType.VIDEO)
    
    files = query.offset(skip).limit(limit).all()
    return files


def _validate_media_file(db: Session, file_id: int) -> File:
    """
    验证媒体文件是否存在且可访问
    
    Args:
        db: 数据库会话
        file_id: 文件ID
        
    Returns:
        File: 验证通过的文件对象
        
    Raises:
        HTTPException: 文件不存在或不可访问时抛出
    """
    logger = logging.getLogger(__name__)
    
    # 验证数据库记录存在
    file = db.query(File).filter(
        File.id == file_id,
        File.file_type.in_([FileType.AUDIO, FileType.VIDEO])
    ).first()
    
    if not file:
        logger.error(f"Media file not found in database: file_id={file_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="媒体文件不存在"
        )
    
    # 验证物理文件存在
    if not Path(file.file_path).exists():
        logger.error(f"Physical file not found: {file.file_path}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="媒体文件在服务器上不存在"
        )
    
    logger.info(f"Media file validated: {file.original_name} at {file.file_path}")
    return file


def _validate_transcription_params(request: TranscriptionRequest) -> None:
    """
    验证转录参数的有效性
    
    Args:
        request: 转录请求参数
        
    Raises:
        HTTPException: 参数无效时抛出
    """
    logger = logging.getLogger(__name__)
    
    # 获取Whisper服务进行验证
    whisper_service = get_whisper_service(request.model_size)
    
    # 验证模型大小
    if request.model_size not in whisper_service.AVAILABLE_MODELS:
        logger.error(f"Invalid model size: {request.model_size}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的模型大小。可用模型: {whisper_service.AVAILABLE_MODELS}"
        )
    
    # 验证语言设置
    if request.language not in whisper_service.SUPPORTED_LANGUAGES:
        logger.error(f"Invalid language: {request.language}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的语言。支持的语言: {list(whisper_service.SUPPORTED_LANGUAGES.keys())}"
        )
    
    logger.info(f"Transcription params validated: model={request.model_size}, language={request.language}")


def _create_transcription_config(request: TranscriptionRequest) -> Dict[str, Any]:
    """
    创建转录配置字典
    
    Args:
        request: 转录请求参数
        
    Returns:
        Dict[str, Any]: 转录配置字典
    """
    return {
        "language": request.language,
        "model_size": request.model_size,
        "whisper_params": {
            "beam_size": 5,
            "best_of": 5,
            "temperature": 0.0,
            "word_timestamps": True,
            "vad_filter": True,
        }
    }


def _create_task_record(db: Session, file_id: int, config_data: Dict[str, Any]) -> Task:
    """
    创建转录任务数据库记录
    
    Args:
        db: 数据库会话
        file_id: 文件ID
        config_data: 转录配置数据
        
    Returns:
        Task: 创建的任务对象
        
    Raises:
        HTTPException: 任务创建失败时抛出
    """
    logger = logging.getLogger(__name__)
    
    try:
        task = Task(
            file_id=file_id,
            task_type=TaskType.AUDIO_VIDEO_TO_SCRIPT,
            status=TaskStatus.PENDING,
            config_snapshot=json.dumps(config_data)
        )
        
        db.add(task)
        db.commit()
        db.refresh(task)
        
        logger.info(f"Transcription task created successfully: ID={task.id}")
        return task
        
    except Exception as e:
        logger.error(f"Failed to create task record: {e}", exc_info=True)
        db.rollback()
        raise TaskExecutionError(
            task_id=0,
            message=f"数据库记录创建失败: {str(e)}",
            details={"file_id": file_id, "config_data": config_data}
        )


def _schedule_background_transcription(background_tasks: BackgroundTasks, task_id: int) -> None:
    """
    调度后台转录任务
    
    Args:
        background_tasks: FastAPI后台任务管理器
        task_id: 任务ID
    """
    logger = logging.getLogger(__name__)
    
    try:
        background_tasks.add_task(run_transcription_task, task_id)
        logger.info(f"Background transcription task scheduled: task_id={task_id}")
    except Exception as e:
        logger.warning(f"Failed to schedule background task {task_id}: {e}")
        # 调度失败不应该阻断任务创建，用户可以手动启动


def _build_task_response(task: Task) -> Dict[str, Any]:
    """
    构建任务响应数据
    
    Args:
        task: 任务对象
        
    Returns:
        Dict[str, Any]: 格式化的响应数据
    """
    return {
        "id": task.id,
        "file_id": task.file_id,
        "task_type": task.task_type,
        "status": task.status,
        "progress": task.progress,
        "config_snapshot": task.config_snapshot_dict,
        "started_at": task.started_at,
        "completed_at": task.completed_at,
        "error_message": task.error_message,
        "user_id": task.user_id,
        "duration": task.duration,
    }


@router.post("/{file_id}/transcribe", response_model=TaskResponse)
async def create_transcription_task(
    file_id: int,
    request: TranscriptionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    创建音视频转录任务
    
    Args:
        file_id: 媒体文件ID
        request: 转录请求参数
        background_tasks: 后台任务管理器
        db: 数据库会话
        
    Returns:
        Dict[str, Any]: 创建的任务信息
        
    Raises:
        HTTPException: 各种业务异常
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Creating transcription task: file_id={file_id}, language={request.language}, model_size={request.model_size}")
    
    try:
        # 第一步：验证媒体文件
        file = _validate_media_file(db, file_id)
        
        # 第二步：验证转录参数
        _validate_transcription_params(request)
        
        # 第三步：创建配置数据
        config_data = _create_transcription_config(request)
        
        # 第四步：创建任务记录
        task = _create_task_record(db, file_id, config_data)
        
        # 第五步：调度后台任务
        _schedule_background_transcription(background_tasks, task.id)
        
        # 第六步：构建响应
        response_data = _build_task_response(task)
        
        logger.info(f"Transcription task created and scheduled: task_id={task.id}")
        return ErrorResponse.build_success_response(
            data=response_data,
            message="转录任务创建成功"
        )
        
    except (ResourceNotFoundError, ValidationError, TaskExecutionError):
        # 这些错误会被错误处理器自动处理
        raise
    except Exception as e:
        logger.error(f"Unexpected error creating transcription task: {e}", exc_info=True)
        raise TaskExecutionError(
            task_id=0,
            message=f"意外错误: {str(e)}",
            details={"file_id": file_id}
        )




async def _get_task_and_file(db: Session, task_id: int) -> Tuple[Task, File]:
    """
    获取任务和关联文件
    
    Args:
        db: 数据库会话
        task_id: 任务ID
        
    Returns:
        Tuple[Task, File]: 任务和文件对象
        
    Raises:
        ValueError: 任务或文件不存在时抛出
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise ValueError(f"Task not found: {task_id}")
    
    file = db.query(File).filter(File.id == task.file_id).first()
    if not file:
        raise ValueError(f"Associated file not found for task: {task_id}")
    
    return task, file


async def _prepare_audio_file(file: File, task_id: int) -> str:
    """
    准备音频文件用于转录
    
    Args:
        file: 文件对象
        task_id: 任务ID
        
    Returns:
        str: 准备好的音频文件路径
        
    Raises:
        MediaProcessingError: 音频处理失败
    """
    from ..api.websockets import notify_task_progress
    
    await notify_task_progress(task_id, 5, "准备音频文件...")
    
    try:
        prepared_audio = MediaService.prepare_audio_for_transcription(
            file.file_path, file.file_type
        )
        await notify_task_progress(task_id, 15, "音频文件准备完成")
        return prepared_audio
        
    except MediaProcessingError as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Audio preparation failed for task {task_id}: {e}")
        raise


async def _execute_transcription(
    prepared_audio: str, 
    language: str, 
    model_size: str, 
    task_id: int,
    db: Session
) -> Dict[str, Any]:
    """
    执行音频转录
    
    Args:
        prepared_audio: 准备好的音频文件路径
        language: 转录语言
        model_size: 模型大小
        task_id: 任务ID
        db: 数据库会话
        
    Returns:
        Dict[str, Any]: 转录结果
        
    Raises:
        WhisperTranscriptionError: 转录失败
    """
    from ..api.websockets import notify_task_progress
    
    whisper_service = get_whisper_service(model_size)
    
    # 定义进度回调
    async def progress_callback(progress: int, message: str):
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.progress = progress
            db.commit()
        await notify_task_progress(task_id, progress, message)
    
    result = await whisper_service.transcribe_file(
        prepared_audio,
        language=language,
        task_id=task_id,
        progress_callback=progress_callback
    )
    
    return result


async def _save_transcription_result(
    db: Session,
    task_id: int, 
    file: File,
    result: Dict[str, Any],
    model_size: str
) -> None:
    """
    保存转录结果
    
    Args:
        db: 数据库会话
        task_id: 任务ID
        file: 文件对象
        result: 转录结果
        model_size: 模型大小
    """
    from ..models import Script
    from ..api.websockets import notify_task_status_change, notify_task_progress
    
    # 创建转录文本记录
    script = Script(
        task_id=task_id,
        title=f"{file.original_name} - 转录文本",
        content=result["text"],
        format="markdown",
        word_count=len(result["text"].split()),
        metadata={
            "transcription_result": result,
            "source_file": file.original_name,
            "language": result["language"],
            "model_size": model_size,
        }
    )
    
    # 更新任务状态
    task = db.query(Task).filter(Task.id == task_id).first()
    if task:
        db.add(script)
        task.complete()
        db.commit()
        
        await notify_task_status_change(task_id, TaskStatus.COMPLETED)
        await notify_task_progress(task_id, 100, "转录完成")


async def _handle_task_failure(
    db: Session, 
    task_id: int, 
    error_message: str
) -> None:
    """
    处理任务失败
    
    Args:
        db: 数据库会话
        task_id: 任务ID
        error_message: 错误消息
    """
    from ..api.websockets import notify_task_status_change
    
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.fail(error_message)
            db.commit()
            await notify_task_status_change(task_id, TaskStatus.FAILED, error_message)
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to handle task failure for task {task_id}: {e}")


async def run_transcription_task(task_id: int) -> None:
    """
    运行转录任务（后台任务）
    
    Args:
        task_id: 任务ID
    """
    from ..database import SessionLocal
    from ..api.websockets import notify_task_status_change
    
    logger = logging.getLogger(__name__)
    db = SessionLocal()
    prepared_audio = None
    
    try:
        # 第一步：获取任务和文件
        task, file = await _get_task_and_file(db, task_id)
        
        # 第二步：启动任务
        task.start()
        db.commit()
        await notify_task_status_change(task_id, TaskStatus.PROCESSING)
        
        # 第三步：解析配置
        config = {}
        if task.config_snapshot:
            try:
                config = json.loads(task.config_snapshot)
            except json.JSONDecodeError:
                logger.warning(f"Invalid config snapshot for task {task_id}")
                config = {}
        
        language = config.get("language", "auto")
        model_size = config.get("model_size", "base")
        
        # 第四步：准备音频文件
        prepared_audio = await _prepare_audio_file(file, task_id)
        
        # 第五步：执行转录
        result = await _execute_transcription(
            prepared_audio, language, model_size, task_id, db
        )
        
        # 第六步：保存结果
        await _save_transcription_result(db, task_id, file, result, model_size)
        
        logger.info(f"Transcription task completed successfully: task_id={task_id}")
        
    except ValueError as e:
        logger.error(f"Task validation error: {e}")
        return
        
    except MediaProcessingError as e:
        error_msg = f"音频预处理失败: {str(e)}"
        logger.error(f"Media processing failed for task {task_id}: {e}")
        await _handle_task_failure(db, task_id, error_msg)
        
    except WhisperTranscriptionError as e:
        error_msg = f"语音转录失败: {str(e)}"
        logger.error(f"Whisper transcription failed for task {task_id}: {e}")
        await _handle_task_failure(db, task_id, error_msg)
        
    except Exception as e:
        error_msg = f"转录过程异常: {str(e)}"
        logger.error(f"Unexpected error in transcription task {task_id}: {e}", exc_info=True)
        await _handle_task_failure(db, task_id, error_msg)
        
    finally:
        # 清理资源
        if prepared_audio and prepared_audio != file.file_path:
            MediaService.cleanup_temp_file(prepared_audio)
        db.close()


@router.get("/models/info")
def get_whisper_models():
    """
    获取可用的Whisper模型信息
    """
    try:
        whisper_service = get_whisper_service()
        return whisper_service.get_model_info()
    except Exception as e:
        return {
            "error": str(e),
            "whisper_available": False,
        }


@router.get("/formats/supported")
def get_supported_formats():
    """
    获取支持的媒体格式
    """
    return MediaService.get_supported_formats()