"""
日志模型
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum as PyEnum
from ..database import Base


class LogLevel(PyEnum):
    """日志级别枚举"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ProcessingLog(Base):
    """处理日志表"""
    __tablename__ = "processing_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    level = Column(Enum(LogLevel), nullable=False, default=LogLevel.INFO)
    message = Column(Text, nullable=False)
    details = Column(Text, nullable=True)  # JSON格式的详细信息
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    task = relationship("Task", back_populates="logs")
    
    def __repr__(self):
        return f"<ProcessingLog(id={self.id}, level='{self.level.value}', task_id={self.task_id})>"