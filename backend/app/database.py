"""
数据库配置和连接管理
"""

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from pathlib import Path

# 数据库配置
DATABASE_DIR = Path("data")
DATABASE_DIR.mkdir(exist_ok=True)
DATABASE_URL = f"sqlite:///{DATABASE_DIR}/ppt_generator.db"

# 创建数据库引擎
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite需要
    echo=False  # 设为True可以看到SQL语句
)

# 会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 声明基类
Base = declarative_base()

def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """创建所有表"""
    Base.metadata.create_all(bind=engine)

def drop_tables():
    """删除所有表（仅用于开发/测试）"""
    Base.metadata.drop_all(bind=engine)