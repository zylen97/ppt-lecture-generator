"""
项目管理API
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, asc
from typing import List, Optional, Dict, Any
import logging

from ..database import get_db
from ..models import Project, User, File, Task, Script
from ..schemas import (
    ProjectCreate, ProjectUpdate, ProjectResponse, ProjectSummary, 
    ProjectListRequest, ProjectListResponse, ProjectStatistics,
    ProjectActionRequest, ProjectActionResponse,
    ProjectImportRequest, ProjectExportRequest,
    ProjectTemplateResponse
)

router = APIRouter()
logger = logging.getLogger(__name__)


def _build_project_statistics(project: Project) -> ProjectStatistics:
    """构建项目统计信息"""
    try:
        # 计算任务状态统计
        status_summary = {"total": 0, "pending": 0, "processing": 0, "completed": 0, "failed": 0}
        
        if project.tasks:
            status_summary["total"] = len(project.tasks)
            for task in project.tasks:
                task_status = task.status.value if hasattr(task.status, 'value') else str(task.status)
                if task_status in status_summary:
                    status_summary[task_status] += 1

        return ProjectStatistics(
            total_files=len(project.files) if project.files else 0,
            total_tasks=len(project.tasks) if project.tasks else 0,
            total_scripts=len(project.scripts) if project.scripts else 0,
            total_duration=project.estimated_total_duration,
            total_word_count=project.total_word_count,
            completion_rate=project.completion_rate,
            status_summary=status_summary
        )
    except Exception as e:
        logger.error(f"构建项目统计信息失败: {e}")
        return ProjectStatistics()


@router.post("/", response_model=ProjectResponse)
def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db)
):
    """
    创建新项目
    """
    try:
        # 检查项目名称是否已存在
        existing_project = db.query(Project).filter(
            and_(
                Project.name == project_data.name,
                Project.is_active == True
            )
        ).first()
        
        if existing_project:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"项目名称 '{project_data.name}' 已存在"
            )
        
        # 创建项目
        project = Project(
            name=project_data.name,
            description=project_data.description,
            course_code=project_data.course_code,
            semester=project_data.semester,
            instructor=project_data.instructor,
            target_audience=project_data.target_audience,
            cover_image=project_data.cover_image,
            is_active=project_data.is_active
        )
        
        db.add(project)
        db.commit()
        db.refresh(project)
        
        # 构建响应
        statistics = _build_project_statistics(project)
        response_data = ProjectResponse(
            **project.__dict__,
            statistics=statistics
        )
        
        logger.info(f"项目创建成功: {project.id} - {project.name}")
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建项目失败: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建项目失败: {str(e)}"
        )


@router.get("/", response_model=ProjectListResponse)
def list_projects(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(50, ge=1, le=1000, description="返回的记录数"),
    active_only: bool = Query(True, description="是否只返回活跃项目"),
    search: Optional[str] = Query(None, max_length=100, description="搜索关键词"),
    semester: Optional[str] = Query(None, max_length=50, description="按学期筛选"),
    instructor: Optional[str] = Query(None, max_length=100, description="按教师筛选"),
    order_by: str = Query("updated_at", description="排序字段"),
    order_direction: str = Query("desc", pattern="^(asc|desc)$", description="排序方向"),
    db: Session = Depends(get_db)
):
    """
    获取项目列表
    """
    try:
        # 构建查询
        query = db.query(Project)
        
        # 活跃状态筛选
        if active_only:
            query = query.filter(Project.is_active == True)
            
        # 搜索关键词
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    Project.name.ilike(search_pattern),
                    Project.description.ilike(search_pattern),
                    Project.course_code.ilike(search_pattern)
                )
            )
        
        # 学期筛选
        if semester:
            query = query.filter(Project.semester == semester)
            
        # 教师筛选
        if instructor:
            query = query.filter(Project.instructor.ilike(f"%{instructor}%"))
        
        # 获取总数
        total = query.count()
        
        # 排序
        order_field = getattr(Project, order_by, Project.updated_at)
        if order_direction == "desc":
            query = query.order_by(desc(order_field))
        else:
            query = query.order_by(asc(order_field))
            
        # 预加载关联数据以计算统计信息
        query = query.options(
            joinedload(Project.files),
            joinedload(Project.tasks),
            joinedload(Project.scripts)
        )
        
        # 分页
        projects = query.offset(skip).limit(limit).all()
        
        # 构建摘要信息
        project_summaries = []
        for project in projects:
            summary = ProjectSummary(
                id=project.id,
                name=project.name,
                description=project.description,
                course_code=project.course_code,
                semester=project.semester,
                instructor=project.instructor,
                cover_image=project.cover_image,
                is_active=project.is_active,
                created_at=project.created_at,
                updated_at=project.updated_at,
                file_count=project.file_count,
                task_count=project.task_count,
                script_count=project.script_count,
                completion_rate=project.completion_rate
            )
            project_summaries.append(summary)
        
        return ProjectListResponse(
            items=project_summaries,
            total=total,
            skip=skip,
            limit=limit,
            has_more=skip + limit < total
        )
        
    except Exception as e:
        logger.error(f"获取项目列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取项目列表失败: {str(e)}"
        )


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: int,
    include_stats: bool = Query(True, description="是否包含统计信息"),
    db: Session = Depends(get_db)
):
    """
    获取项目详情
    """
    try:
        # 查询项目（预加载关联数据）
        project = db.query(Project).options(
            joinedload(Project.files),
            joinedload(Project.tasks),
            joinedload(Project.scripts)
        ).filter(Project.id == project_id).first()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"项目 {project_id} 不存在"
            )
        
        # 构建统计信息
        statistics = _build_project_statistics(project) if include_stats else ProjectStatistics()
        
        response_data = ProjectResponse(
            **project.__dict__,
            statistics=statistics
        )
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取项目详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取项目详情失败: {str(e)}"
        )


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    db: Session = Depends(get_db)
):
    """
    更新项目信息
    """
    try:
        # 查询项目
        project = db.query(Project).filter(Project.id == project_id).first()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"项目 {project_id} 不存在"
            )
        
        # 检查名称冲突（如果更新了名称）
        if project_update.name and project_update.name != project.name:
            existing_project = db.query(Project).filter(
                and_(
                    Project.name == project_update.name,
                    Project.id != project_id,
                    Project.is_active == True
                )
            ).first()
            
            if existing_project:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"项目名称 '{project_update.name}' 已存在"
                )
        
        # 更新字段
        update_data = project_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(project, field, value)
        
        db.commit()
        db.refresh(project)
        
        # 重新加载关联数据
        project = db.query(Project).options(
            joinedload(Project.files),
            joinedload(Project.tasks),
            joinedload(Project.scripts)
        ).filter(Project.id == project_id).first()
        
        # 构建响应
        statistics = _build_project_statistics(project)
        response_data = ProjectResponse(
            **project.__dict__,
            statistics=statistics
        )
        
        logger.info(f"项目更新成功: {project.id} - {project.name}")
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新项目失败: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新项目失败: {str(e)}"
        )


@router.delete("/{project_id}")
def delete_project(
    project_id: int,
    force: bool = Query(False, description="是否强制删除（包含数据的项目）"),
    db: Session = Depends(get_db)
):
    """
    删除项目
    """
    try:
        # 查询项目
        project = db.query(Project).options(
            joinedload(Project.files),
            joinedload(Project.tasks),
            joinedload(Project.scripts)
        ).filter(Project.id == project_id).first()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"项目 {project_id} 不存在"
            )
        
        # 检查是否有关联数据
        has_data = (
            (project.files and len(project.files) > 0) or
            (project.tasks and len(project.tasks) > 0) or
            (project.scripts and len(project.scripts) > 0)
        )
        
        if has_data and not force:
            return {
                "success": False,
                "message": "项目包含数据，请使用 force=true 参数强制删除",
                "data": {
                    "file_count": len(project.files) if project.files else 0,
                    "task_count": len(project.tasks) if project.tasks else 0,
                    "script_count": len(project.scripts) if project.scripts else 0
                }
            }
        
        # 删除项目（级联删除关联数据）
        db.delete(project)
        db.commit()
        
        logger.info(f"项目删除成功: {project_id} - {project.name}")
        return {
            "success": True,
            "message": f"项目 '{project.name}' 删除成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除项目失败: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除项目失败: {str(e)}"
        )


@router.post("/{project_id}/archive")
def archive_project(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    归档项目（设置为非活跃状态）
    """
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"项目 {project_id} 不存在"
            )
        
        project.is_active = False
        db.commit()
        
        logger.info(f"项目归档成功: {project_id} - {project.name}")
        return {
            "success": True,
            "message": f"项目 '{project.name}' 已归档"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"归档项目失败: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"归档项目失败: {str(e)}"
        )


@router.post("/{project_id}/restore")
def restore_project(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    恢复已归档的项目
    """
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"项目 {project_id} 不存在"
            )
        
        project.is_active = True
        db.commit()
        
        logger.info(f"项目恢复成功: {project_id} - {project.name}")
        return {
            "success": True,
            "message": f"项目 '{project.name}' 已恢复"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"恢复项目失败: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"恢复项目失败: {str(e)}"
        )


@router.get("/{project_id}/statistics", response_model=ProjectStatistics)
def get_project_statistics(
    project_id: int,
    refresh: bool = Query(False, description="是否刷新缓存统计"),
    db: Session = Depends(get_db)
):
    """
    获取项目统计信息
    """
    try:
        project = db.query(Project).options(
            joinedload(Project.files),
            joinedload(Project.tasks),
            joinedload(Project.scripts)
        ).filter(Project.id == project_id).first()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"项目 {project_id} 不存在"
            )
        
        # 如果需要刷新统计，更新数据库中的统计字段
        if refresh:
            project.update_statistics()
            db.commit()
        
        return _build_project_statistics(project)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取项目统计失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取项目统计失败: {str(e)}"
        )


@router.get("/templates/", response_model=ProjectTemplateResponse)
def get_project_templates():
    """
    获取项目模板
    """
    templates = [
        {
            "id": "basic",
            "name": "基础课程模板",
            "description": "适用于一般理论课程",
            "fields": ["name", "description", "course_code", "semester", "instructor"],
            "example": {
                "name": "{{课程名称}}",
                "description": "{{课程描述}}",
                "course_code": "{{课程代码}}",
                "semester": "{{学期}}",
                "instructor": "{{教师姓名}}"
            }
        },
        {
            "id": "practical",
            "name": "实践课程模板",
            "description": "适用于实验实践类课程",
            "fields": ["name", "description", "course_code", "semester", "instructor", "target_audience"],
            "example": {
                "name": "{{课程名称}}实践",
                "description": "{{课程名称}}实践课程，包含实验和项目实践",
                "course_code": "{{课程代码}}-LAB",
                "semester": "{{学期}}",
                "instructor": "{{教师姓名}}",
                "target_audience": "{{专业}}学生"
            }
        },
        {
            "id": "seminar",
            "name": "研讨课模板",
            "description": "适用于研讨类课程",
            "fields": ["name", "description", "semester", "instructor", "target_audience"],
            "example": {
                "name": "{{主题}}研讨课",
                "description": "围绕{{主题}}展开的深入研讨课程",
                "semester": "{{学期}}",
                "instructor": "{{教师姓名}}",
                "target_audience": "研究生"
            }
        }
    ]
    
    return ProjectTemplateResponse(templates=templates)