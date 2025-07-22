"""
讲稿相关的数据验证模型
"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ScriptBase(BaseModel):
    """讲稿基础信息"""
    title: str
    content: str
    format: str = "markdown"
    estimated_duration: Optional[int] = None


class ScriptCreate(ScriptBase):
    """创建讲稿"""
    task_id: int


class ScriptUpdate(BaseModel):
    """更新讲稿"""
    title: Optional[str] = None
    content: Optional[str] = None
    estimated_duration: Optional[int] = None


class ScriptResponse(ScriptBase):
    """讲稿响应"""
    id: int
    task_id: int
    version: int
    word_count: Optional[int] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    file_size: int
    reading_time: Optional[int] = None
    
    class Config:
        from_attributes = True


class ScriptSummary(BaseModel):
    """讲稿摘要（用于列表显示）"""
    id: int
    title: str
    version: int
    word_count: Optional[int] = None
    estimated_duration: Optional[int] = None
    created_at: datetime
    is_active: bool