"""
配置模型
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base


class APIConfig(Base):
    """API配置表"""
    __tablename__ = "api_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    endpoint = Column(String(500), nullable=False)
    api_key_encrypted = Column(Text, nullable=False)  # 加密存储的API密钥
    model = Column(String(100), nullable=False)
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # 关系
    user = relationship("User", back_populates="api_configs")
    
    def __repr__(self):
        return f"<APIConfig(id={self.id}, name='{self.name}', model='{self.model}')>"


class ScriptTemplate(Base):
    """讲稿模板表"""
    __tablename__ = "script_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    template_content = Column(Text, nullable=False)  # JSON格式的模板配置
    is_system = Column(Boolean, default=False)  # 是否为系统预置模板
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # 关系
    user = relationship("User", back_populates="script_templates")
    
    def __repr__(self):
        return f"<ScriptTemplate(id={self.id}, name='{self.name}', is_system={self.is_system})>"