"""
PPT讲稿生成器 - 项目管理系统 FastAPI Backend

这是一个基于FastAPI的现代化教学内容管理平台后端服务，支持：
- 项目级别的数据隔离和管理（每门课程建立一个项目）
- PPT文件处理和讲稿生成（基于GPT-4 Vision）
- 音视频转录服务（基于Whisper）
- WebSocket实时任务状态推送
- RESTful API接口设计
- 完整的错误处理和中间件支持

技术栈：
- FastAPI 0.104.1 + Uvicorn
- SQLAlchemy 2.0.23 ORM
- SQLite数据库
- WebSocket实时通信
- Pydantic数据验证

架构特点：
- 项目级别数据隔离
- 模块化API设计
- 统一错误处理
- 中间件链式处理
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import uvicorn
import os
import logging
from pathlib import Path

from .database import engine, get_db
from .models import Base
from .api import files, tasks, scripts, configs, websockets, media, projects
from .core.error_handler import setup_error_handlers, ErrorResponse
from .core.middleware import setup_middleware

# 配置应用日志系统
# 使用统一的日志格式便于调试和监控
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 初始化数据库模式
# 自动创建所有模型对应的数据表，支持项目管理系统的7个核心模型
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="PPT Lecture Generator API",
    description="PPT讲稿生成器后端API - 现代化架构版本",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 设置错误处理
setup_error_handlers(app)

# 设置中间件
setup_middleware(app)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:9527",  # 前端端口
        "http://127.0.0.1:9527"   # 支持127.0.0.1访问
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件服务（用于文件下载）
upload_dir = Path("uploads")
upload_dir.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# 注册RESTful API路由
# 项目管理系统的7个核心模块，每个模块提供完整的CRUD操作
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])   # 项目管理：创建、查询、更新、删除项目
app.include_router(files.router, prefix="/api/files", tags=["files"])           # 文件管理：上传、存储、查询项目文件
app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])           # 任务管理：创建处理任务、监控状态
app.include_router(scripts.router, prefix="/api/scripts", tags=["scripts"])     # 讲稿管理：生成、编辑、导出讲稿
app.include_router(configs.router, prefix="/api/configs", tags=["configs"])     # 配置管理：API密钥、系统参数
app.include_router(media.router, prefix="/api/media", tags=["media"])           # 媒体处理：音视频转录服务

# 注册WebSocket路由
# 提供实时任务状态推送，支持项目级别隔离
app.include_router(websockets.router, prefix="/ws/tasks", tags=["websockets"])

@app.get("/")
async def root():
    """API根路径"""
    return ErrorResponse.build_success_response(
        data={
            "name": "PPT Lecture Generator API",
            "version": "2.0.0",
            "description": "现代化PPT讲稿生成器后端服务",
            "features": [
                "PPT文件处理",
                "音视频转录",
                "AI讲稿生成",
                "实时任务状态",
                "WebSocket支持"
            ]
        },
        message="API服务运行正常"
    )

@app.get("/health")
async def health_check():
    """
    系统健康检查接口
    
    检查核心系统组件的运行状态，包括：
    - 数据库连接状态
    - 文件上传目录可用性
    - API版本信息
    
    Returns:
        dict: 包含详细健康状态的响应对象
    """
    try:
        # 检查SQLite数据库连接
        # 执行简单查询验证数据库可访问性
        db = next(get_db())
        db.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "unhealthy"
    
    # 检查文件上传目录
    # 确保项目文件存储路径存在且可写
    upload_dir_exists = Path("uploads").exists()
    
    # 构建健康状态报告
    health_data = {
        "status": "healthy" if db_status == "healthy" and upload_dir_exists else "degraded",
        "checks": {
            "database": db_status,
            "upload_directory": "healthy" if upload_dir_exists else "missing",
            "api_version": "2.0.0"
        }
    }
    
    return ErrorResponse.build_success_response(
        data=health_data,
        message="健康检查完成"
    )

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app", 
        host="0.0.0.0", 
        port=7788, 
        reload=True
    )