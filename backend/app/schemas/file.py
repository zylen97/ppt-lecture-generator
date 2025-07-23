"""
文件相关的数据验证模型
"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from ..models.file import FileType


class FileBase(BaseModel):
    """文件基础信息"""
    original_name: str
    file_size: int
    file_type: FileType
    
    # PPT相关字段
    slide_count: Optional[int] = 0
    
    # 音视频相关字段
    duration: Optional[float] = None
    sample_rate: Optional[int] = None
    channels: Optional[int] = None
    bitrate: Optional[int] = None
    codec: Optional[str] = None
    resolution: Optional[str] = None
    fps: Optional[float] = None


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
    project_id: Optional[int] = None
    file_size_mb: float
    
    # 计算属性
    is_media_file: bool = False
    is_ppt_file: bool = False
    duration_formatted: Optional[str] = None
    
    class Config:
        from_attributes = True