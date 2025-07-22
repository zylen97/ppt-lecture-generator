"""
文件相关的数据验证模型
"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class FileBase(BaseModel):
    """文件基础信息"""
    original_name: str
    file_size: int
    slide_count: Optional[int] = 0


class FileCreate(FileBase):
    """创建文件记录"""
    filename: str
    file_path: str
    file_hash: Optional[str] = None


class FileUpload(BaseModel):
    """文件上传响应"""
    success: bool
    message: str
    file_id: Optional[int] = None


class FileResponse(FileBase):
    """文件响应"""
    id: int
    filename: str
    file_path: str
    file_hash: Optional[str] = None
    upload_time: datetime
    user_id: Optional[int] = None
    file_size_mb: float
    
    class Config:
        from_attributes = True