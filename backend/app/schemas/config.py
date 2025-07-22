"""
配置相关的数据验证模型
"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class APIConfigBase(BaseModel):
    """API配置基础信息"""
    name: str
    endpoint: str
    model: str
    is_default: bool = False


class APIConfigCreate(APIConfigBase):
    """创建API配置"""
    api_key: str  # 明文API密钥，后端会加密存储


class APIConfigUpdate(BaseModel):
    """更新API配置"""
    name: Optional[str] = None
    endpoint: Optional[str] = None
    model: Optional[str] = None
    api_key: Optional[str] = None
    is_default: Optional[bool] = None


class APIConfigResponse(APIConfigBase):
    """API配置响应"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    user_id: Optional[int] = None
    api_key_masked: str  # 掩码显示的API密钥
    
    class Config:
        from_attributes = True


class APITestRequest(BaseModel):
    """API测试请求"""
    endpoint: str
    api_key: str
    model: str


class APITestResponse(BaseModel):
    """API测试响应"""
    success: bool
    message: str
    latency_ms: Optional[float] = None