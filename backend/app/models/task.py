"""
任务模型
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum as PyEnum
import json
from typing import Dict, Any, Optional
from ..database import Base


class TaskType(PyEnum):
    """任务类型枚举"""
    PPT_TO_SCRIPT = "ppt_to_script"              # PPT转讲稿
    AUDIO_VIDEO_TO_SCRIPT = "audio_video_to_script"  # 音视频转讲稿
    SCRIPT_EDIT = "script_edit"                  # 讲稿编辑
    BATCH_PROCESS = "batch_process"              # 批量处理


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
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)  # 所属项目
    
    # 关系
    user = relationship("User", back_populates="tasks")
    project = relationship("Project", back_populates="tasks")
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
    
    @property
    def is_ppt_task(self):
        """判断是否为PPT处理任务"""
        return self.task_type == TaskType.PPT_TO_SCRIPT
    
    @property
    def is_media_task(self):
        """判断是否为音视频处理任务"""
        return self.task_type == TaskType.AUDIO_VIDEO_TO_SCRIPT
    
    @property
    def requires_ai_processing(self):
        """判断是否需要AI处理"""
        return self.task_type in (TaskType.PPT_TO_SCRIPT, TaskType.AUDIO_VIDEO_TO_SCRIPT)
    
    def get_estimated_duration(self):
        """获取预估处理时长（分钟）"""
        if not self.file:
            return None
        
        # PPT任务：基于幻灯片数量估算
        if self.is_ppt_task and self.file.slide_count:
            return max(1, self.file.slide_count * 0.5)  # 每张幻灯片约0.5分钟
        
        # 音视频任务：基于文件时长估算
        if self.is_media_task and self.file.duration:
            # 转录速度通常为实际播放时间的1/10到1/5
            return max(1, self.file.duration / 60 * 0.2)  # 约为播放时间的20%
        
        return 5  # 默认估算5分钟
    
    @property 
    def config_snapshot_dict(self) -> Optional[Dict[str, Any]]:
        """返回config_snapshot的字典格式（用于API响应）"""
        if self.config_snapshot:
            try:
                return json.loads(self.config_snapshot)
            except json.JSONDecodeError:
                return None
        return None