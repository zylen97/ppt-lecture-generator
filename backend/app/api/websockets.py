"""
WebSocket API - 实时推送服务
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
import asyncio
import json
import logging
from typing import Dict, List, Set
from datetime import datetime

from ..database import SessionLocal
from ..models import Task
from ..models.task import TaskStatus

logger = logging.getLogger(__name__)

router = APIRouter()

# 连接管理器
class ConnectionManager:
    def __init__(self):
        # 单个任务监听连接
        self.task_connections: Dict[int, List[WebSocket]] = {}
        # 全局任务监听连接
        self.global_connections: Set[WebSocket] = set()
        # 项目级别任务监听连接
        self.project_connections: Dict[int, Set[WebSocket]] = {}
        
    async def connect_task(self, task_id: int, websocket: WebSocket):
        """连接到特定任务的进度监听"""
        await websocket.accept()
        if task_id not in self.task_connections:
            self.task_connections[task_id] = []
        self.task_connections[task_id].append(websocket)
        logger.info(f"WebSocket connected for task {task_id}")
        
    async def connect_global(self, websocket: WebSocket):
        """连接到全局任务状态监听"""
        await websocket.accept()
        self.global_connections.add(websocket)
        logger.info("Global task monitoring WebSocket connected")
        
    def disconnect_task(self, task_id: int, websocket: WebSocket):
        """断开特定任务的连接"""
        if task_id in self.task_connections:
            if websocket in self.task_connections[task_id]:
                self.task_connections[task_id].remove(websocket)
                if not self.task_connections[task_id]:
                    del self.task_connections[task_id]
        logger.info(f"WebSocket disconnected for task {task_id}")
        
    def disconnect_global(self, websocket: WebSocket):
        """断开全局连接"""
        self.global_connections.discard(websocket)
        logger.info("Global task monitoring WebSocket disconnected")
        
    async def connect_project(self, project_id: int, websocket: WebSocket):
        """连接到特定项目的任务监听"""
        await websocket.accept()
        if project_id not in self.project_connections:
            self.project_connections[project_id] = set()
        self.project_connections[project_id].add(websocket)
        logger.info(f"WebSocket connected for project {project_id}")
        
    def disconnect_project(self, project_id: int, websocket: WebSocket):
        """断开特定项目的连接"""
        if project_id in self.project_connections:
            self.project_connections[project_id].discard(websocket)
            if not self.project_connections[project_id]:
                del self.project_connections[project_id]
        logger.info(f"WebSocket disconnected for project {project_id}")
        
    async def send_task_progress(self, task_id: int, message: dict):
        """发送任务进度到特定任务的所有连接"""
        if task_id in self.task_connections:
            disconnected = []
            for websocket in self.task_connections[task_id]:
                try:
                    await websocket.send_text(json.dumps(message))
                except:
                    disconnected.append(websocket)
            
            # 清理断开的连接
            for websocket in disconnected:
                self.disconnect_task(task_id, websocket)
                
    async def broadcast_task_update(self, message: dict):
        """广播任务更新到所有全局连接"""
        disconnected = []
        for websocket in self.global_connections:
            try:
                await websocket.send_text(json.dumps(message))
            except:
                disconnected.append(websocket)
        
        # 清理断开的连接
        for websocket in disconnected:
            self.disconnect_global(websocket)
            
    async def broadcast_project_update(self, project_id: int, message: dict):
        """广播任务更新到特定项目的所有连接"""
        if project_id not in self.project_connections:
            return
            
        disconnected = []
        for websocket in self.project_connections[project_id]:
            try:
                await websocket.send_text(json.dumps(message))
            except:
                disconnected.append(websocket)
        
        # 清理断开的连接
        for websocket in disconnected:
            self.disconnect_project(project_id, websocket)

# 全局连接管理器实例
manager = ConnectionManager()

@router.websocket("/{task_id}/progress")
async def task_progress_websocket(websocket: WebSocket, task_id: int):
    """
    单个任务进度监听WebSocket
    """
    await manager.connect_task(task_id, websocket)
    
    try:
        while True:
            # 获取任务状态
            db = SessionLocal()
            try:
                task = db.query(Task).filter(Task.id == task_id).first()
                if not task:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "task_id": task_id,
                        "message": "任务不存在"
                    }))
                    break
                
                # 发送进度数据
                progress_data = {
                    "type": "progress",
                    "task_id": task_id,
                    "status": task.status.value if hasattr(task.status, 'value') else str(task.status),
                    "progress": task.progress,
                    "message": get_status_message(task.status),
                    "timestamp": datetime.now().isoformat()
                }
                
                await websocket.send_text(json.dumps(progress_data))
                
                # 如果任务已完成或失败，发送完成消息后断开连接
                if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                    await websocket.send_text(json.dumps({
                        "type": "complete",
                        "task_id": task_id,
                        "final_status": task.status.value if hasattr(task.status, 'value') else str(task.status),
                        "timestamp": datetime.now().isoformat()
                    }))
                    break
                    
            finally:
                db.close()
            
            # 等待一段时间后再次检查
            await asyncio.sleep(1)
            
    except WebSocketDisconnect:
        manager.disconnect_task(task_id, websocket)
    except Exception as e:
        logger.error(f"WebSocket error for task {task_id}: {e}")
        manager.disconnect_task(task_id, websocket)
        
@router.websocket("/monitor")
async def global_task_monitor_websocket(websocket: WebSocket):
    """
    全局任务状态监听WebSocket
    用于Tasks页面实时更新所有任务状态
    """
    await manager.connect_global(websocket)
    
    last_task_states = {}
    
    try:
        while True:
            # 获取所有任务状态
            db = SessionLocal()
            try:
                tasks = db.query(Task).all()
                current_states = {}
                changed_tasks = []
                
                for task in tasks:
                    current_state = {
                        "id": task.id,
                        "status": task.status.value if hasattr(task.status, 'value') else str(task.status),
                        "progress": task.progress,
                        "started_at": task.started_at.isoformat() if task.started_at else None,
                        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                        "error_message": task.error_message
                    }
                    
                    current_states[task.id] = current_state
                    
                    # 检查是否有变化
                    if task.id not in last_task_states or last_task_states[task.id] != current_state:
                        changed_tasks.append(current_state)
                
                # 如果有任务状态变化，发送更新
                if changed_tasks:
                    update_message = {
                        "type": "tasks_update",
                        "changed_tasks": changed_tasks,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    await websocket.send_text(json.dumps(update_message))
                
                last_task_states = current_states
                
            finally:
                db.close()
            
            # 等待2秒后再次检查
            await asyncio.sleep(2)
            
    except WebSocketDisconnect:
        manager.disconnect_global(websocket)
    except Exception as e:
        logger.error(f"Global monitor WebSocket error: {e}")
        manager.disconnect_global(websocket)

@router.websocket("/projects/{project_id}/monitor")
async def project_task_monitor_websocket(websocket: WebSocket, project_id: int):
    """
    项目级别任务状态监听WebSocket
    用于监听特定项目下的所有任务状态变化
    """
    await manager.connect_project(project_id, websocket)
    
    last_task_states = {}
    
    try:
        while True:
            # 获取指定项目的所有任务状态
            db = SessionLocal()
            try:
                tasks = db.query(Task).filter(Task.project_id == project_id).all()
                current_states = {}
                changed_tasks = []
                
                for task in tasks:
                    current_state = {
                        "id": task.id,
                        "project_id": task.project_id,
                        "status": task.status.value if hasattr(task.status, 'value') else str(task.status),
                        "progress": task.progress,
                        "started_at": task.started_at.isoformat() if task.started_at else None,
                        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                        "error_message": task.error_message
                    }
                    
                    current_states[task.id] = current_state
                    
                    # 检查是否有变化
                    if task.id not in last_task_states or last_task_states[task.id] != current_state:
                        changed_tasks.append(current_state)
                
                # 如果有任务状态变化，发送更新
                if changed_tasks:
                    update_message = {
                        "type": "project_tasks_update",
                        "project_id": project_id,
                        "changed_tasks": changed_tasks,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    await websocket.send_text(json.dumps(update_message))
                
                last_task_states = current_states
                
            finally:
                db.close()
            
            # 等待2秒后再次检查
            await asyncio.sleep(2)
            
    except WebSocketDisconnect:
        manager.disconnect_project(project_id, websocket)
    except Exception as e:
        logger.error(f"Project {project_id} monitor WebSocket error: {e}")
        manager.disconnect_project(project_id, websocket)

def get_status_message(status: TaskStatus) -> str:
    """获取状态消息"""
    status_messages = {
        TaskStatus.PENDING: "等待处理",
        TaskStatus.PROCESSING: "正在处理...",
        TaskStatus.COMPLETED: "处理完成",
        TaskStatus.FAILED: "处理失败",
        TaskStatus.CANCELLED: "已取消"
    }
    return status_messages.get(status, "未知状态")

# 提供给其他模块使用的函数
async def notify_task_progress(task_id: int, progress: int, message: str = ""):
    """通知任务进度更新"""
    progress_data = {
        "type": "progress",
        "task_id": task_id,
        "progress": progress,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }
    
    # 发送给特定任务监听者
    await manager.send_task_progress(task_id, progress_data)
    
    # 广播给全局监听者
    await manager.broadcast_task_update(progress_data)
    
    # 广播给项目级监听者
    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if task and task.project_id:
            await manager.broadcast_project_update(task.project_id, progress_data)
    finally:
        db.close()

async def notify_task_status_change(task_id: int, status: TaskStatus, error_message: str = None):
    """通知任务状态变化"""
    status_data = {
        "type": "status_change",
        "task_id": task_id,
        "status": status.value if hasattr(status, 'value') else str(status),
        "error_message": error_message,
        "timestamp": datetime.now().isoformat()
    }
    
    # 发送给特定任务监听者
    await manager.send_task_progress(task_id, status_data)
    
    # 广播给全局监听者
    await manager.broadcast_task_update(status_data)
    
    # 广播给项目级监听者
    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if task and task.project_id:
            await manager.broadcast_project_update(task.project_id, status_data)
    finally:
        db.close()