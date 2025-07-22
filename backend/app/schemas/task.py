"""
任务相关的数据验证模型
"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any
from ..models.task import TaskType, TaskStatus


class TaskBase(BaseModel):
    """任务基础信息"""
    task_type: TaskType = TaskType.PPT_TO_SCRIPT
    config_snapshot: Optional[Dict[str, Any]] = None


class TaskCreate(TaskBase):
    """创建任务"""
    file_id: int


class TaskUpdate(BaseModel):
    """更新任务"""
    status: Optional[TaskStatus] = None
    progress: Optional[int] = None
    error_message: Optional[str] = None


class TaskResponse(TaskBase):
    """任务响应"""
    id: int
    file_id: int
    status: TaskStatus
    progress: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    user_id: Optional[int] = None
    duration: Optional[float] = None
    
    class Config:
        from_attributes = True


class TaskProgress(BaseModel):
    """任务进度更新"""
    task_id: int
    progress: int
    message: str
    current_step: Optional[str] = None