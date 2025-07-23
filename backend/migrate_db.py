#!/usr/bin/env python3
"""
数据库迁移脚本
为现有数据库添加音视频支持字段
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import text
from app.database import engine, SessionLocal
from app.models import Base


def migrate_database():
    """执行数据库迁移"""
    
    print("🚀 开始数据库迁移...")
    
    # 创建数据库会话
    db = SessionLocal()
    
    try:
        # 1. 为files表添加新字段
        print("📄 更新files表结构...")
        
        migrations = [
            # 添加文件类型字段
            "ALTER TABLE files ADD COLUMN file_type VARCHAR(10) DEFAULT 'ppt' NOT NULL",
            
            # 添加音视频相关字段
            "ALTER TABLE files ADD COLUMN duration FLOAT NULL",
            "ALTER TABLE files ADD COLUMN sample_rate INTEGER NULL", 
            "ALTER TABLE files ADD COLUMN channels INTEGER NULL",
            "ALTER TABLE files ADD COLUMN bitrate INTEGER NULL",
            "ALTER TABLE files ADD COLUMN codec VARCHAR(50) NULL",
            "ALTER TABLE files ADD COLUMN resolution VARCHAR(20) NULL",
            "ALTER TABLE files ADD COLUMN fps FLOAT NULL",
        ]
        
        for migration in migrations:
            try:
                print(f"  执行: {migration}")
                db.execute(text(migration))
                db.commit()
            except Exception as e:
                if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                    print(f"  ⚠️  字段已存在，跳过: {migration}")
                else:
                    print(f"  ❌ 执行失败: {e}")
                    raise
        
        # 2. 更新现有数据的file_type字段
        print("🔄 更新现有数据...")
        update_query = """
        UPDATE files 
        SET file_type = CASE 
            WHEN LOWER(original_name) LIKE '%.ppt' OR LOWER(original_name) LIKE '%.pptx' THEN 'ppt'
            WHEN LOWER(original_name) LIKE '%.mp3' OR LOWER(original_name) LIKE '%.wav' OR 
                 LOWER(original_name) LIKE '%.m4a' OR LOWER(original_name) LIKE '%.flac' OR
                 LOWER(original_name) LIKE '%.ogg' OR LOWER(original_name) LIKE '%.wma' OR
                 LOWER(original_name) LIKE '%.aac' THEN 'audio'
            WHEN LOWER(original_name) LIKE '%.mp4' OR LOWER(original_name) LIKE '%.avi' OR
                 LOWER(original_name) LIKE '%.mkv' OR LOWER(original_name) LIKE '%.mov' OR
                 LOWER(original_name) LIKE '%.wmv' OR LOWER(original_name) LIKE '%.flv' OR
                 LOWER(original_name) LIKE '%.webm' OR LOWER(original_name) LIKE '%.m4v' THEN 'video'
            ELSE 'ppt'
        END
        WHERE file_type = 'ppt'
        """
        
        result = db.execute(text(update_query))
        db.commit()
        print(f"  ✅ 更新了 {result.rowcount} 条记录的文件类型")
        
        print("✅ 数据库迁移完成！")
        
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        db.rollback()
        raise
        
    finally:
        db.close()


def backup_database():
    """备份数据库（开发环境）"""
    import shutil
    from datetime import datetime
    
    db_file = Path("data/app.db")
    if db_file.exists():
        backup_name = f"data/app_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        shutil.copy2(db_file, backup_name)
        print(f"💾 数据库已备份至: {backup_name}")


def main():
    """主函数"""
    print("🔧 PPT讲稿生成器 - 数据库迁移工具")
    print("=" * 50)
    
    # 检查是否在正确的目录
    if not Path("app").exists():
        print("❌ 请在项目根目录运行此脚本")
        sys.exit(1)
    
    # 创建数据目录
    os.makedirs("data", exist_ok=True)
    
    try:
        # 备份现有数据库
        backup_database()
        
        # 执行迁移
        migrate_database()
        
        print("\n🎉 迁移成功完成！")
        print("✨ 系统现在支持音频和视频文件上传和处理。")
        
    except Exception as e:
        print(f"\n💥 迁移过程中出现错误: {e}")
        print("请检查错误信息并重试。")
        sys.exit(1)


if __name__ == "__main__":
    main()