"""
讲稿管理API
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session
from pathlib import Path
import tempfile
from typing import List

from ..database import get_db
from ..models import Script, Task
from ..schemas import ScriptCreate, ScriptResponse, ScriptUpdate, ScriptSummary

router = APIRouter()

@router.post("/", response_model=ScriptResponse)
def create_script(
    script_data: ScriptCreate,
    db: Session = Depends(get_db)
):
    """
    创建新讲稿
    """
    # 验证任务存在
    task = db.query(Task).filter(Task.id == script_data.task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="指定的任务不存在"
        )
    
    # 创建讲稿
    script = Script(
        task_id=script_data.task_id,
        title=script_data.title,
        content=script_data.content,
        format=script_data.format,
        estimated_duration=script_data.estimated_duration
    )
    
    # 计算字数
    script.update_word_count()
    
    db.add(script)
    db.commit()
    db.refresh(script)
    
    return script

@router.get("/{script_id}", response_model=ScriptResponse)
def get_script(script_id: int, db: Session = Depends(get_db)):
    """
    获取讲稿详情
    """
    script = db.query(Script).filter(Script.id == script_id).first()
    if not script:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="讲稿不存在"
        )
    return script

@router.get("/", response_model=List[ScriptSummary])
def list_scripts(
    skip: int = 0,
    limit: int = 50,
    task_id: int = None,
    db: Session = Depends(get_db)
):
    """
    获取讲稿列表
    """
    query = db.query(Script)
    
    if task_id:
        query = query.filter(Script.task_id == task_id)
    
    scripts = query.offset(skip).limit(limit).all()
    
    # 转换为摘要格式
    summaries = []
    for script in scripts:
        summaries.append(ScriptSummary(
            id=script.id,
            title=script.title,
            version=script.version,
            word_count=script.word_count,
            estimated_duration=script.estimated_duration,
            created_at=script.created_at,
            is_active=script.is_active
        ))
    
    return summaries

@router.put("/{script_id}", response_model=ScriptResponse)
def update_script(
    script_id: int,
    script_update: ScriptUpdate,
    db: Session = Depends(get_db)
):
    """
    更新讲稿内容
    """
    script = db.query(Script).filter(Script.id == script_id).first()
    if not script:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="讲稿不存在"
        )
    
    # 更新字段
    if script_update.title is not None:
        script.title = script_update.title
    if script_update.content is not None:
        script.content = script_update.content
        script.update_word_count()  # 重新计算字数
    if script_update.estimated_duration is not None:
        script.estimated_duration = script_update.estimated_duration
    
    db.commit()
    db.refresh(script)
    
    return script

@router.delete("/{script_id}")
def delete_script(script_id: int, db: Session = Depends(get_db)):
    """
    删除讲稿
    """
    script = db.query(Script).filter(Script.id == script_id).first()
    if not script:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="讲稿不存在"
        )
    
    db.delete(script)
    db.commit()
    
    return {"message": "讲稿删除成功"}

@router.get("/{script_id}/export/{format}")
def export_script(
    script_id: int,
    format: str,
    db: Session = Depends(get_db)
):
    """
    导出讲稿为指定格式
    支持格式: markdown, html, txt
    """
    script = db.query(Script).filter(Script.id == script_id).first()
    if not script:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="讲稿不存在"
        )
    
    supported_formats = ["markdown", "html", "txt"]
    if format.lower() not in supported_formats:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的导出格式。支持的格式: {', '.join(supported_formats)}"
        )
    
    try:
        # 根据格式处理内容
        if format.lower() == "markdown":
            content = script.content
            media_type = "text/markdown"
            extension = "md"
        elif format.lower() == "html":
            # 这里可以添加markdown到HTML的转换逻辑
            content = f"<html><body><pre>{script.content}</pre></body></html>"
            media_type = "text/html"
            extension = "html"
        elif format.lower() == "txt":
            content = script.content
            media_type = "text/plain"
            extension = "txt"
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix=f'.{extension}', delete=False, encoding='utf-8') as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        
        # 生成文件名
        filename = f"{script.title}_v{script.version}.{extension}"
        
        return FileResponse(
            path=tmp_path,
            filename=filename,
            media_type=media_type
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导出失败: {str(e)}"
        )

@router.get("/{script_id}/preview")
def preview_script(script_id: int, db: Session = Depends(get_db)):
    """
    预览讲稿内容（返回HTML格式）
    """
    script = db.query(Script).filter(Script.id == script_id).first()
    if not script:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="讲稿不存在"
        )
    
    # 简单的markdown到HTML转换
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>{script.title}</title>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 40px; }}
            h1, h2, h3 {{ color: #333; }}
            pre {{ background: #f4f4f4; padding: 10px; border-radius: 5px; }}
        </style>
    </head>
    <body>
        <h1>{script.title}</h1>
        <p><strong>版本:</strong> {script.version}</p>
        <p><strong>字数:</strong> {script.word_count or 'N/A'}</p>
        <p><strong>预估时长:</strong> {script.estimated_duration or 'N/A'}分钟</p>
        <hr>
        <pre>{script.content}</pre>
    </body>
    </html>
    """
    
    return Response(content=html_content, media_type="text/html")