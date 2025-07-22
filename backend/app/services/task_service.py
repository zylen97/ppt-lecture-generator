"""
任务服务
"""

import json
from pathlib import Path
from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..models import Task, File, Script, ProcessingLog
from ..models.task import TaskStatus
from ..models.log import LogLevel


class TaskService:
    """任务处理服务"""
    
    @staticmethod
    def process_task(task_id: int):
        """
        处理任务的主要逻辑
        """
        db = SessionLocal()
        
        try:
            # 获取任务
            task = db.query(Task).filter(Task.id == task_id).first()
            if not task:
                raise Exception(f"任务 {task_id} 不存在")
            
            # 获取关联的文件
            file = db.query(File).filter(File.id == task.file_id).first()
            if not file:
                raise Exception("关联的文件不存在")
            
            # 记录开始处理
            TaskService._log_task(db, task_id, LogLevel.INFO, "开始处理任务")
            
            # 更新任务进度
            TaskService._update_task_progress(db, task_id, 10, "准备处理文件")
            
            # 这里应该调用实际的处理逻辑
            # 1. 转换PPT到图片
            TaskService._update_task_progress(db, task_id, 30, "转换PPT到图片")
            TaskService._convert_ppt_to_images(db, task, file)
            
            # 2. AI分析图片
            TaskService._update_task_progress(db, task_id, 60, "AI分析图片内容")
            analysis_result = TaskService._analyze_images_with_ai(db, task, file)
            
            # 3. 生成讲稿
            TaskService._update_task_progress(db, task_id, 80, "生成讲稿")
            script_content = TaskService._generate_script(db, task, analysis_result)
            
            # 4. 保存讲稿
            TaskService._update_task_progress(db, task_id, 90, "保存讲稿")
            TaskService._save_script(db, task, script_content)
            
            # 完成任务
            task.complete()
            db.commit()
            
            TaskService._update_task_progress(db, task_id, 100, "任务完成")
            TaskService._log_task(db, task_id, LogLevel.INFO, "任务处理完成")
            
        except Exception as e:
            # 任务失败
            task.fail(str(e))
            db.commit()
            
            TaskService._log_task(db, task_id, LogLevel.ERROR, f"任务处理失败: {str(e)}")
            
        finally:
            db.close()
    
    @staticmethod
    def _update_task_progress(db: Session, task_id: int, progress: int, message: str):
        """更新任务进度"""
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.progress = progress
            db.commit()
    
    @staticmethod
    def _log_task(db: Session, task_id: int, level: LogLevel, message: str, details: dict = None):
        """记录任务日志"""
        log = ProcessingLog(
            task_id=task_id,
            level=level,
            message=message,
            details=json.dumps(details) if details else None
        )
        db.add(log)
        db.commit()
    
    @staticmethod
    def _convert_ppt_to_images(db: Session, task: Task, file: File):
        """转换PPT到图片"""
        try:
            # 这里应该调用现有的PPT处理逻辑
            # 暂时返回模拟结果
            TaskService._log_task(db, task.id, LogLevel.INFO, f"转换PPT文件: {file.original_name}")
            # 实际实现会调用现有的ppt_processor模块
            
        except Exception as e:
            raise Exception(f"PPT转换失败: {str(e)}")
    
    @staticmethod
    def _analyze_images_with_ai(db: Session, task: Task, file: File):
        """使用AI分析图片"""
        try:
            # 这里应该调用现有的AI分析逻辑
            # 暂时返回模拟结果
            TaskService._log_task(db, task.id, LogLevel.INFO, "开始AI分析")
            
            # 获取配置
            config = {}
            if task.config_snapshot:
                config = json.loads(task.config_snapshot)
            
            # 模拟分析结果
            analysis_result = {
                "slides": [
                    {"slide_number": 1, "content": "模拟内容1"},
                    {"slide_number": 2, "content": "模拟内容2"}
                ]
            }
            
            return analysis_result
            
        except Exception as e:
            raise Exception(f"AI分析失败: {str(e)}")
    
    @staticmethod
    def _generate_script(db: Session, task: Task, analysis_result: dict):
        """生成讲稿"""
        try:
            TaskService._log_task(db, task.id, LogLevel.INFO, "开始生成讲稿")
            
            # 这里应该调用现有的讲稿生成逻辑
            # 暂时返回模拟内容
            script_content = """# 课程讲稿
            
## 第1张幻灯片
模拟讲稿内容1...

## 第2张幻灯片
模拟讲稿内容2...
"""
            
            return script_content
            
        except Exception as e:
            raise Exception(f"讲稿生成失败: {str(e)}")
    
    @staticmethod
    def _save_script(db: Session, task: Task, script_content: str):
        """保存讲稿到数据库"""
        try:
            # 获取文件名作为标题
            file = db.query(File).filter(File.id == task.file_id).first()
            title = Path(file.original_name).stem if file else f"讲稿_{task.id}"
            
            # 创建讲稿记录
            script = Script(
                task_id=task.id,
                title=title,
                content=script_content,
                format="markdown"
            )
            
            # 计算字数
            script.update_word_count()
            
            db.add(script)
            db.commit()
            
            TaskService._log_task(db, task.id, LogLevel.INFO, f"讲稿已保存: {script.id}")
            
        except Exception as e:
            raise Exception(f"保存讲稿失败: {str(e)}")