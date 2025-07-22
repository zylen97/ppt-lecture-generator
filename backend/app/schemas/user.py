"""
用户相关的数据验证模型
"""

from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class UserBase(BaseModel):
    """用户基础信息"""
    username: str
    email: Optional[EmailStr] = None


class UserCreate(UserBase):
    """创建用户"""
    pass


class UserResponse(UserBase):
    """用户响应"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True