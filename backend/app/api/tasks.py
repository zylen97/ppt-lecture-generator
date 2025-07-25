"""
任务管理API
"""

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status, BackgroundTasks
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session
import asyncio
import json
from typing import List

from ..database import get_db
from ..models import Task, File, TaskType, TaskStatus
from ..schemas import TaskCreate, TaskResponse, TaskUpdate, TaskProgress
from ..services.task_service import TaskService

router = APIRouter()

@router.post("/", response_model=TaskResponse)
def create_task(
    task_data: TaskCreate,
    db: Session = Depends(get_db)
):
    """
    创建新任务
    """
    # 验证文件存在
    file = db.query(File).filter(File.id == task_data.file_id).first()
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="指定的文件不存在"
        )
    
    # 创建任务
    task = Task(
        file_id=task_data.file_id,
        task_type=task_data.task_type,
        config_snapshot=json.dumps(task_data.config_snapshot) if task_data.config_snapshot else None,
        project_id=task_data.project_id
    )
    
    db.add(task)
    db.commit()
    db.refresh(task)
    
    return task

@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    """
    获取任务详情
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    # 准备响应数据，将config_snapshot转换为字典格式
    response_data = {
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
    
    return response_data

@router.get("/", response_model=List[TaskResponse])  
def list_tasks(
    skip: int = 0,
    limit: int = 50,
    status_filter: str = None,
    project_id: int = None,
    db: Session = Depends(get_db)
):
    """
    获取任务列表
    """
    query = db.query(Task)
    
    if status_filter:
        query = query.filter(Task.status == status_filter)
    
    # 可选的项目过滤
    if project_id is not None:
        query = query.filter(Task.project_id == project_id)
    
    tasks = query.offset(skip).limit(limit).all()
    
    # 转换每个任务的config_snapshot为字典格式
    response_tasks = []
    for task in tasks:
        response_data = {
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
        response_tasks.append(response_data)
    
    return response_tasks

@router.put("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    task_update: TaskUpdate,
    db: Session = Depends(get_db)
):
    """
    更新任务状态
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    # 更新字段
    if task_update.status is not None:
        task.status = task_update.status
    if task_update.progress is not None:
        task.progress = task_update.progress
    if task_update.error_message is not None:
        task.error_message = task_update.error_message
    
    db.commit()
    db.refresh(task)
    
    return task

@router.post("/{task_id}/start")
async def start_task(
    task_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    启动任务处理
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    if task.status != TaskStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只有待处理状态的任务可以启动"
        )
    
    # 根据任务类型启动不同的处理函数
    if task.task_type == TaskType.AUDIO_VIDEO_TO_SCRIPT:
        # 音视频转录任务
        from ..api.media import run_transcription_task
        background_tasks.add_task(run_transcription_task, task_id)
    else:
        # 其他类型任务
        asyncio.create_task(run_task_background(task_id))
    
    return {"message": "任务已启动", "task_id": task_id}

@router.post("/{task_id}/cancel")
def cancel_task(
    task_id: int,
    db: Session = Depends(get_db)
):
    """
    取消任务
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    if task.status not in ["pending", "processing"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只有待处理或处理中的任务可以取消"
        )
    
    # 取消任务
    from ..models.task import TaskStatus
    task.status = TaskStatus.CANCELLED
    db.commit()
    
    return {"message": "任务已取消"}

async def run_task_background(task_id: int):
    """
    在后台运行任务
    """
    try:
        await run_in_threadpool(TaskService.process_task, task_id)
    except Exception as e:
        print(f"任务 {task_id} 处理失败: {e}")
        # 更新任务状态为失败
        # 这里需要获取数据库会话来更新状态

@router.websocket("/{task_id}/progress")
async def task_progress_websocket(websocket: WebSocket, task_id: int):
    """
    WebSocket连接，实时推送任务进度
    """
    await websocket.accept()
    
    try:
        while True:
            # 获取任务状态
            from ..database import SessionLocal
            db = SessionLocal()
            try:
                task = db.query(Task).filter(Task.id == task_id).first()
                if not task:
                    await websocket.send_text(json.dumps({
                        "error": "任务不存在"
                    }))
                    break
                
                progress_data = {
                    "task_id": task_id,
                    "status": task.status.value if hasattr(task.status, 'value') else str(task.status),
                    "progress": task.progress,
                    "message": "处理中..." if task.status == "processing" else str(task.status)
                }
                
                await websocket.send_text(json.dumps(progress_data))
                
                # 如果任务已完成或失败，断开连接
                if task.status in ["completed", "failed", "cancelled"]:
                    break
                    
            finally:
                db.close()
            
            # 等待一段时间后再次检查
            await asyncio.sleep(1)
            
    except WebSocketDisconnect:
        print(f"WebSocket连接断开: task_id={task_id}")
    except Exception as e:
        print(f"WebSocket错误: {e}")
        await websocket.close()