"""
讲稿模型
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base


class Script(Base):
    """讲稿表"""
    __tablename__ = "scripts"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    format = Column(String(20), default="markdown")  # markdown, html, docx等
    version = Column(Integer, default=1)
    word_count = Column(Integer, nullable=True)
    estimated_duration = Column(Integer, nullable=True)  # 预估讲解时长（分钟）
    is_active = Column(Boolean, default=True)  # 是否为当前版本
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)  # 所属项目
    
    # 关系
    task = relationship("Task", back_populates="scripts")
    project = relationship("Project", back_populates="scripts")
    
    def __repr__(self):
        return f"<Script(id={self.id}, title='{self.title}', version={self.version})>"
    
    @property
    def file_size(self):
        """返回内容大小（字符数）"""
        return len(self.content) if self.content else 0
    
    @property
    def reading_time(self):
        """估算阅读时间（分钟），按每分钟200字计算"""
        if self.word_count:
            return max(1, round(self.word_count / 200))
        return None
    
    def update_word_count(self):
        """更新字数统计"""
        if self.content:
            # 简单的中英文字数统计
            chinese_chars = sum(1 for c in self.content if '\u4e00' <= c <= '\u9fff')
            english_words = len([w for w in self.content.split() if w.isalpha()])
            self.word_count = chinese_chars + english_words