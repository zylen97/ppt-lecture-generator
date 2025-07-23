"""
文件模型
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, BigInteger, Float, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum as PyEnum
from ..database import Base


class FileType(PyEnum):
    """文件类型枚举"""
    PPT = "ppt"           # PPT文档
    AUDIO = "audio"       # 音频文件
    VIDEO = "video"       # 视频文件


class File(Base):
    """文件表"""
    __tablename__ = "files"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)  # 存储的文件名
    original_name = Column(String(255), nullable=False)  # 原始文件名
    file_path = Column(String(500), nullable=False)  # 文件路径
    file_size = Column(BigInteger, nullable=False)  # 文件大小（字节）
    file_hash = Column(String(64), nullable=True)  # 文件哈希值
    file_type = Column(Enum(FileType), nullable=False, default=FileType.PPT)  # 文件类型
    
    # PPT相关字段
    slide_count = Column(Integer, nullable=True, default=0)  # 幻灯片数量
    
    # 音视频相关字段
    duration = Column(Float, nullable=True)  # 时长（秒）
    sample_rate = Column(Integer, nullable=True)  # 采样率（Hz）
    channels = Column(Integer, nullable=True)  # 声道数
    bitrate = Column(Integer, nullable=True)  # 比特率（bps）
    codec = Column(String(50), nullable=True)  # 编码格式
    resolution = Column(String(20), nullable=True)  # 视频分辨率 (例如: "1920x1080")
    fps = Column(Float, nullable=True)  # 视频帧率
    
    upload_time = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # 允许匿名上传
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)  # 所属项目
    
    # 关系
    user = relationship("User", back_populates="files")
    project = relationship("Project", back_populates="files")
    tasks = relationship("Task", back_populates="file", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<File(id={self.id}, original_name='{self.original_name}', type='{self.file_type.value}')>"
    
    @property
    def file_size_mb(self):
        """返回文件大小（MB）"""
        return round(self.file_size / 1024 / 1024, 2) if self.file_size else 0
    
    @property
    def is_media_file(self):
        """判断是否为音视频文件"""
        return self.file_type in (FileType.AUDIO, FileType.VIDEO)
    
    @property
    def is_ppt_file(self):
        """判断是否为PPT文件"""
        return self.file_type == FileType.PPT
    
    @property
    def duration_formatted(self):
        """格式化时长显示 (HH:MM:SS)"""
        if not self.duration:
            return None
        
        hours = int(self.duration // 3600)
        minutes = int((self.duration % 3600) // 60)
        seconds = int(self.duration % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
    
    @classmethod
    def get_supported_extensions(cls):
        """获取支持的文件扩展名"""
        return {
            FileType.PPT: ['.ppt', '.pptx'],
            FileType.AUDIO: ['.mp3', '.wav', '.m4a', '.flac', '.ogg', '.wma', '.aac'],
            FileType.VIDEO: ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v']
        }
    
    @classmethod
    def detect_file_type(cls, filename: str):
        """根据文件扩展名检测文件类型"""
        import os
        ext = os.path.splitext(filename.lower())[1]
        
        for file_type, extensions in cls.get_supported_extensions().items():
            if ext in extensions:
                return file_type
        
        return None  # 不支持的文件类型