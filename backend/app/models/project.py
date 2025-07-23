"""
项目模型
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base


class Project(Base):
    """项目表 - 用于管理课程项目"""
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)  # 项目名称（课程名称）
    description = Column(Text, nullable=True)  # 项目描述
    course_code = Column(String(50), nullable=True, index=True)  # 课程代码
    semester = Column(String(50), nullable=True)  # 学期
    instructor = Column(String(100), nullable=True)  # 授课教师
    target_audience = Column(String(100), nullable=True)  # 目标学员
    cover_image = Column(String(500), nullable=True)  # 封面图片路径
    
    # 统计字段（可以通过关联关系计算，也可以缓存在这里）
    total_files = Column(Integer, default=0)  # 总文件数
    total_tasks = Column(Integer, default=0)  # 总任务数
    total_scripts = Column(Integer, default=0)  # 总讲稿数
    total_duration = Column(Float, nullable=True)  # 总预计时长（分钟）
    
    # 系统字段
    is_active = Column(Boolean, default=True, index=True)  # 是否活跃
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # 创建者
    
    # 关系
    user = relationship("User", back_populates="projects")
    files = relationship("File", back_populates="project", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    scripts = relationship("Script", back_populates="project", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Project(id={self.id}, name='{self.name}', active={self.is_active})>"
    
    @property
    def file_count(self):
        """返回实际文件数量"""
        return len(self.files) if self.files else 0
    
    @property
    def task_count(self):
        """返回实际任务数量"""
        return len(self.tasks) if self.tasks else 0
    
    @property
    def script_count(self):
        """返回实际讲稿数量"""
        return len(self.scripts) if self.scripts else 0
    
    @property
    def completion_rate(self):
        """计算完成率（已完成任务/总任务）"""
        if not self.tasks or len(self.tasks) == 0:
            return 0.0
        
        completed_count = sum(1 for task in self.tasks if task.status.value == 'completed')
        return round(completed_count / len(self.tasks) * 100, 2)
    
    @property
    def estimated_total_duration(self):
        """计算预计总时长（基于所有活跃讲稿）"""
        if not self.scripts:
            return 0
        
        total_minutes = sum(
            script.estimated_duration or 0 
            for script in self.scripts 
            if script.is_active
        )
        return total_minutes
    
    @property
    def total_word_count(self):
        """计算总字数（基于所有活跃讲稿）"""
        if not self.scripts:
            return 0
        
        return sum(
            script.word_count or 0 
            for script in self.scripts 
            if script.is_active
        )
    
    def update_statistics(self):
        """更新统计字段"""
        self.total_files = self.file_count
        self.total_tasks = self.task_count
        self.total_scripts = self.script_count
        self.total_duration = self.estimated_total_duration
        self.updated_at = datetime.utcnow()
    
    @classmethod
    def create_default_project(cls, db_session, user_id=None):
        """创建默认项目"""
        default_project = cls(
            name="默认项目",
            description="系统自动创建的默认项目，用于存放未分类的内容",
            course_code="DEFAULT",
            is_active=True,
            user_id=user_id
        )
        db_session.add(default_project)
        db_session.commit()
        db_session.refresh(default_project)
        return default_project
    
    @property
    def status_summary(self):
        """返回项目状态摘要"""
        if not self.tasks:
            return {
                "total": 0,
                "pending": 0,
                "processing": 0,
                "completed": 0,
                "failed": 0
            }
        
        summary = {
            "total": len(self.tasks),
            "pending": 0,
            "processing": 0,
            "completed": 0,
            "failed": 0
        }
        
        for task in self.tasks:
            status = task.status.value if hasattr(task.status, 'value') else str(task.status)
            if status in summary:
                summary[status] += 1
        
        return summary