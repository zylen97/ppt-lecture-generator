"""
文件模型
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base


class File(Base):
    """文件表"""
    __tablename__ = "files"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)  # 存储的文件名
    original_name = Column(String(255), nullable=False)  # 原始文件名
    file_path = Column(String(500), nullable=False)  # 文件路径
    file_size = Column(BigInteger, nullable=False)  # 文件大小（字节）
    file_hash = Column(String(64), nullable=True)  # 文件哈希值
    slide_count = Column(Integer, nullable=True, default=0)  # 幻灯片数量
    upload_time = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # 允许匿名上传
    
    # 关系
    user = relationship("User", back_populates="files")
    tasks = relationship("Task", back_populates="file", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<File(id={self.id}, original_name='{self.original_name}')>"
    
    @property
    def file_size_mb(self):
        """返回文件大小（MB）"""
        return round(self.file_size / 1024 / 1024, 2) if self.file_size else 0