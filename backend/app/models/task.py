"""
任务模型
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum as PyEnum
from ..database import Base


class TaskType(PyEnum):
    """任务类型枚举"""
    PPT_TO_SCRIPT = "ppt_to_script"
    SCRIPT_EDIT = "script_edit"
    BATCH_PROCESS = "batch_process"


class TaskStatus(PyEnum):
    """任务状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Task(Base):
    """任务表"""
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=False)
    task_type = Column(Enum(TaskType), nullable=False, default=TaskType.PPT_TO_SCRIPT)
    status = Column(Enum(TaskStatus), nullable=False, default=TaskStatus.PENDING)
    progress = Column(Integer, default=0)  # 进度百分比 0-100
    config_snapshot = Column(Text)  # JSON格式的配置快照
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # 关系
    user = relationship("User", back_populates="tasks")
    file = relationship("File", back_populates="tasks")
    scripts = relationship("Script", back_populates="task", cascade="all, delete-orphan")
    logs = relationship("ProcessingLog", back_populates="task", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Task(id={self.id}, status='{self.status.value}', progress={self.progress})>"
    
    @property
    def duration(self):
        """返回任务执行时长（秒）"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    def start(self):
        """开始任务"""
        self.status = TaskStatus.PROCESSING
        self.started_at = datetime.utcnow()
    
    def complete(self):
        """完成任务"""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.progress = 100
    
    def fail(self, error_message: str):
        """任务失败"""
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.error_message = error_message