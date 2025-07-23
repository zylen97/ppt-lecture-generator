"""
项目相关的数据验证模型
"""

from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class ProjectStatus(str, Enum):
    """项目状态枚举"""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DRAFT = "draft"


class ProjectBase(BaseModel):
    """项目基础信息"""
    name: str = Field(..., min_length=1, max_length=255, description="项目名称")
    description: Optional[str] = Field(None, max_length=2000, description="项目描述")
    course_code: Optional[str] = Field(None, max_length=50, description="课程代码")
    semester: Optional[str] = Field(None, max_length=50, description="学期")
    instructor: Optional[str] = Field(None, max_length=100, description="授课教师")
    target_audience: Optional[str] = Field(None, max_length=100, description="目标学员")
    cover_image: Optional[str] = Field(None, max_length=500, description="封面图片路径")
    
    @validator('name')
    def validate_name(cls, v):
        """验证项目名称"""
        if not v or not v.strip():
            raise ValueError('项目名称不能为空')
        return v.strip()


class ProjectCreate(ProjectBase):
    """创建项目"""
    is_active: bool = Field(True, description="是否活跃")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "计算机网络原理",
                "description": "计算机网络原理课程，包括网络协议、网络架构等内容",
                "course_code": "CS301",
                "semester": "2024春季",
                "instructor": "张教授",
                "target_audience": "计算机科学专业本科生",
                "is_active": True
            }
        }


class ProjectUpdate(BaseModel):
    """更新项目"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="项目名称")
    description: Optional[str] = Field(None, max_length=2000, description="项目描述")
    course_code: Optional[str] = Field(None, max_length=50, description="课程代码")
    semester: Optional[str] = Field(None, max_length=50, description="学期")
    instructor: Optional[str] = Field(None, max_length=100, description="授课教师")
    target_audience: Optional[str] = Field(None, max_length=100, description="目标学员")
    cover_image: Optional[str] = Field(None, max_length=500, description="封面图片路径")
    is_active: Optional[bool] = Field(None, description="是否活跃")
    
    @validator('name')
    def validate_name(cls, v):
        """验证项目名称"""
        if v is not None and (not v or not v.strip()):
            raise ValueError('项目名称不能为空')
        return v.strip() if v else v


class ProjectStatistics(BaseModel):
    """项目统计信息"""
    total_files: int = Field(0, description="总文件数")
    total_tasks: int = Field(0, description="总任务数")  
    total_scripts: int = Field(0, description="总讲稿数")
    total_duration: Optional[float] = Field(0, description="总预计时长（分钟）")
    total_word_count: int = Field(0, description="总字数")
    completion_rate: float = Field(0.0, description="完成率（百分比）")
    
    # 任务状态统计
    status_summary: Dict[str, int] = Field(
        default_factory=lambda: {
            "total": 0,
            "pending": 0,
            "processing": 0,
            "completed": 0,
            "failed": 0
        },
        description="任务状态统计"
    )


class ProjectResponse(ProjectBase):
    """项目响应"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    user_id: Optional[int] = None
    
    # 统计信息
    statistics: ProjectStatistics
    
    class Config:
        from_attributes = True


class ProjectSummary(BaseModel):
    """项目摘要信息（用于列表显示）"""
    id: int
    name: str
    description: Optional[str] = None
    course_code: Optional[str] = None
    semester: Optional[str] = None
    instructor: Optional[str] = None
    cover_image: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    # 简化统计信息
    file_count: int = Field(0, description="文件数量")
    task_count: int = Field(0, description="任务数量")
    script_count: int = Field(0, description="讲稿数量")
    completion_rate: float = Field(0.0, description="完成率")
    
    class Config:
        from_attributes = True


class ProjectDetail(ProjectResponse):
    """项目详细信息（包含关联数据）"""
    # 可以选择是否包含关联的文件、任务、讲稿列表
    include_files: bool = Field(False, description="是否包含文件列表")
    include_tasks: bool = Field(False, description="是否包含任务列表")
    include_scripts: bool = Field(False, description="是否包含讲稿列表")
    
    # 关联数据（根据include参数决定是否包含）
    files: Optional[List[Dict[str, Any]]] = Field(None, description="关联文件列表")
    tasks: Optional[List[Dict[str, Any]]] = Field(None, description="关联任务列表")
    scripts: Optional[List[Dict[str, Any]]] = Field(None, description="关联讲稿列表")


class ProjectListRequest(BaseModel):
    """项目列表查询参数"""
    skip: int = Field(0, ge=0, description="跳过的记录数")
    limit: int = Field(50, ge=1, le=1000, description="返回的记录数")
    active_only: bool = Field(True, description="是否只返回活跃项目")
    search: Optional[str] = Field(None, max_length=100, description="搜索关键词")
    semester: Optional[str] = Field(None, max_length=50, description="按学期筛选")
    instructor: Optional[str] = Field(None, max_length=100, description="按教师筛选")
    order_by: str = Field("updated_at", description="排序字段")
    order_direction: str = Field("desc", pattern="^(asc|desc)$", description="排序方向")


class ProjectListResponse(BaseModel):
    """项目列表响应"""
    items: List[ProjectSummary]
    total: int
    skip: int
    limit: int
    has_more: bool = Field(False, description="是否还有更多数据")


class ProjectActionRequest(BaseModel):
    """项目操作请求"""
    action: str = Field(..., description="操作类型")
    data: Optional[Dict[str, Any]] = Field(None, description="操作数据")


class ProjectActionResponse(BaseModel):
    """项目操作响应"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


class ProjectImportRequest(BaseModel):
    """项目导入请求"""
    name: str = Field(..., description="项目名称")
    file_ids: List[int] = Field(..., description="要导入的文件ID列表")
    task_ids: Optional[List[int]] = Field(None, description="要导入的任务ID列表")
    script_ids: Optional[List[int]] = Field(None, description="要导入的讲稿ID列表")


class ProjectExportRequest(BaseModel):
    """项目导出请求"""
    project_id: int = Field(..., description="项目ID")
    include_files: bool = Field(True, description="是否包含文件")
    include_tasks: bool = Field(True, description="是否包含任务")
    include_scripts: bool = Field(True, description="是否包含讲稿")
    export_format: str = Field("json", pattern="^(json|xlsx|zip)$", description="导出格式")


class ProjectTemplateResponse(BaseModel):
    """项目模板响应"""
    templates: List[Dict[str, Any]] = Field([], description="可用模板列表")
    
    class Config:
        schema_extra = {
            "example": {
                "templates": [
                    {
                        "id": "basic",
                        "name": "基础课程模板",
                        "description": "适用于一般理论课程",
                        "fields": ["name", "description", "course_code", "semester", "instructor"]
                    },
                    {
                        "id": "practical",
                        "name": "实践课程模板", 
                        "description": "适用于实验实践类课程",
                        "fields": ["name", "description", "course_code", "semester", "instructor", "target_audience"]
                    }
                ]
            }
        }