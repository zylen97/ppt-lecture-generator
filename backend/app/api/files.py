"""
文件管理API
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File as FastAPIFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pathlib import Path
import hashlib
import uuid
import os
from typing import List

from ..database import get_db
from ..models import File
from ..schemas import FileResponse, FileUpload
from ..services.file_service import FileService

router = APIRouter()

@router.post("/upload", response_model=FileUpload)
async def upload_file(
    file: UploadFile = FastAPIFile(...),
    db: Session = Depends(get_db)
):
    """
    上传PPT文件
    """
    # 验证文件类型
    allowed_types = ['.ppt', '.pptx']
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件类型。支持的类型: {', '.join(allowed_types)}"
        )
    
    # 验证文件大小 (100MB限制)
    max_size = 100 * 1024 * 1024  # 100MB
    if file.size > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="文件大小超过限制（最大100MB）"
        )
    
    try:
        # 创建上传目录
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        
        # 生成唯一文件名
        file_id = str(uuid.uuid4())
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
        
        # 创建数据库记录
        db_file = File(
            filename=filename,
            original_name=file.filename,
            file_path=str(file_path),
            file_size=file.size,
            file_hash=file_hash
        )
        
        db.add(db_file)
        db.commit()
        db.refresh(db_file)
        
        # 异步获取幻灯片数量
        try:
            slide_count = FileService.get_slide_count(file_path)
            db_file.slide_count = slide_count
            db.commit()
        except Exception as e:
            print(f"获取幻灯片数量失败: {e}")
        
        return FileUpload(
            success=True,
            message="文件上传成功",
            file_id=db_file.id
        )
        
    except Exception as e:
        # 清理文件
        if file_path.exists():
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件上传失败: {str(e)}"
        )

@router.get("/{file_id}", response_model=FileResponse)
def get_file(file_id: int, db: Session = Depends(get_db)):
    """
    获取文件信息
    """
    file = db.query(File).filter(File.id == file_id).first()
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文件不存在"
        )
    return file

@router.get("/", response_model=List[FileResponse])
def list_files(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    获取文件列表
    """
    files = db.query(File).offset(skip).limit(limit).all()
    return files

@router.delete("/{file_id}")
def delete_file(file_id: int, db: Session = Depends(get_db)):
    """
    删除文件
    """
    file = db.query(File).filter(File.id == file_id).first()
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文件不存在"
        )
    
    # 删除物理文件
    try:
        if Path(file.file_path).exists():
            os.remove(file.file_path)
    except Exception as e:
        print(f"删除物理文件失败: {e}")
    
    # 删除数据库记录
    db.delete(file)
    db.commit()
    
    return {"message": "文件删除成功"}

@router.get("/{file_id}/download")
def download_file(file_id: int, db: Session = Depends(get_db)):
    """
    下载文件
    """
    file = db.query(File).filter(File.id == file_id).first()
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文件不存在"
        )
    
    if not Path(file.file_path).exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文件不存在于服务器"
        )
    
    return FileResponse(
        path=file.file_path,
        filename=file.original_name,
        media_type='application/octet-stream'
    )