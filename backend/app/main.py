"""
PPT讲稿生成器 - FastAPI Backend
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import uvicorn
import os
from pathlib import Path

from .database import engine, get_db
from .models import Base
from .api import files, tasks, scripts, configs, websockets

# 创建数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="PPT Lecture Generator API",
    description="PPT讲稿生成器后端API",
    version="1.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React开发服务器
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件服务（用于文件下载）
upload_dir = Path("uploads")
upload_dir.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# API路由
app.include_router(files.router, prefix="/api/files", tags=["files"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
app.include_router(scripts.router, prefix="/api/scripts", tags=["scripts"])
app.include_router(configs.router, prefix="/api/configs", tags=["configs"])

# WebSocket路由
app.include_router(websockets.router, prefix="/ws/tasks", tags=["websockets"])

@app.get("/")
async def root():
    """API根路径"""
    return {
        "message": "PPT Lecture Generator API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True
    )