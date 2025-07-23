#!/usr/bin/env python3
"""
数据库迁移脚本：引入项目管理系统
将现有数据迁移到项目架构中

使用方法:
python migrate_to_projects.py

注意：运行前请备份数据库！
"""

import sys
import os
from pathlib import Path

# 添加app路径以便导入模块
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine, text, Column, Integer
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import logging
from datetime import datetime

# 导入模型
from app.database import DATABASE_URL, Base
from app.models import Project, File, Task, Script, User

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ProjectMigration:
    """项目迁移管理器"""
    
    def __init__(self):
        self.engine = create_engine(DATABASE_URL, echo=True)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
    def backup_database(self):
        """备份数据库"""
        try:
            backup_path = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            if DATABASE_URL.startswith("sqlite:///"):
                db_path = DATABASE_URL.replace("sqlite:///", "")
                import shutil
                shutil.copy2(db_path, backup_path)
                logger.info(f"数据库已备份到: {backup_path}")
                return backup_path
            else:
                logger.warning("当前数据库类型不支持自动备份，请手动备份")
                return None
        except Exception as e:
            logger.error(f"备份数据库失败: {e}")
            return None
            
    def check_existing_tables(self):
        """检查现有表结构"""
        with self.engine.connect() as conn:
            # 检查projects表是否存在
            result = conn.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='projects'"
            ))
            projects_exists = result.fetchone() is not None
            
            # 检查现有表的project_id字段
            tables_to_check = ['files', 'tasks', 'scripts']
            project_id_exists = {}
            
            for table in tables_to_check:
                try:
                    result = conn.execute(text(f"PRAGMA table_info({table})"))
                    columns = [row[1] for row in result.fetchall()]
                    project_id_exists[table] = 'project_id' in columns
                except Exception as e:
                    logger.warning(f"无法检查表 {table}: {e}")
                    project_id_exists[table] = False
                    
        return projects_exists, project_id_exists
        
    def create_tables(self):
        """创建新表结构"""
        try:
            logger.info("开始创建表结构...")
            Base.metadata.create_all(bind=self.engine)
            logger.info("表结构创建完成")
            return True
        except Exception as e:
            logger.error(f"创建表结构失败: {e}")
            return False
            
    def add_project_id_columns(self):
        """为现有表添加project_id字段"""
        tables_to_update = ['files', 'tasks', 'scripts']
        
        with self.engine.connect() as conn:
            for table in tables_to_update:
                try:
                    # 检查字段是否已存在
                    result = conn.execute(text(f"PRAGMA table_info({table})"))
                    columns = [row[1] for row in result.fetchall()]
                    
                    if 'project_id' not in columns:
                        logger.info(f"为表 {table} 添加 project_id 字段...")
                        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN project_id INTEGER"))
                        conn.commit()
                    else:
                        logger.info(f"表 {table} 的 project_id 字段已存在")
                        
                except Exception as e:
                    logger.error(f"为表 {table} 添加 project_id 字段失败: {e}")
                    return False
                    
        return True
        
    def create_default_project(self, db_session):
        """创建默认项目"""
        try:
            # 检查是否已存在默认项目
            existing_project = db_session.query(Project).filter(
                Project.name == "默认项目"
            ).first()
            
            if existing_project:
                logger.info(f"默认项目已存在: {existing_project.id}")
                return existing_project
                
            # 创建默认项目
            default_project = Project(
                name="默认项目",
                description="系统迁移时自动创建的默认项目，用于存放未分类的内容",
                course_code="DEFAULT",
                semester="N/A",
                instructor="系统",
                target_audience="通用",
                is_active=True
            )
            
            db_session.add(default_project)
            db_session.commit()
            db_session.refresh(default_project)
            
            logger.info(f"默认项目创建成功: {default_project.id}")
            return default_project
            
        except Exception as e:
            logger.error(f"创建默认项目失败: {e}")
            db_session.rollback()
            return None
            
    def migrate_existing_data(self, default_project_id):
        """迁移现有数据到默认项目"""
        db = self.SessionLocal()
        try:
            # 统计需要迁移的数据
            files_count = db.query(File).filter(File.project_id.is_(None)).count()
            tasks_count = db.query(Task).filter(Task.project_id.is_(None)).count()
            scripts_count = db.query(Script).filter(Script.project_id.is_(None)).count()
            
            logger.info(f"需要迁移的数据: 文件 {files_count}, 任务 {tasks_count}, 讲稿 {scripts_count}")
            
            # 迁移文件
            if files_count > 0:
                updated_files = db.query(File).filter(File.project_id.is_(None)).update({
                    File.project_id: default_project_id
                })
                logger.info(f"已迁移 {updated_files} 个文件到默认项目")
            
            # 迁移任务
            if tasks_count > 0:
                updated_tasks = db.query(Task).filter(Task.project_id.is_(None)).update({
                    Task.project_id: default_project_id
                })
                logger.info(f"已迁移 {updated_tasks} 个任务到默认项目")
            
            # 迁移讲稿
            if scripts_count > 0:
                updated_scripts = db.query(Script).filter(Script.project_id.is_(None)).update({
                    Script.project_id: default_project_id
                })
                logger.info(f"已迁移 {updated_scripts} 个讲稿到默认项目")
            
            db.commit()
            return True
            
        except Exception as e:
            logger.error(f"迁移现有数据失败: {e}")
            db.rollback()
            return False
        finally:
            db.close()
            
    def create_indexes(self):
        """创建性能优化索引"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_files_project_id ON files(project_id, upload_time)",
            "CREATE INDEX IF NOT EXISTS idx_tasks_project_id ON tasks(project_id, started_at)",
            "CREATE INDEX IF NOT EXISTS idx_scripts_project_id ON scripts(project_id, created_at)",
            "CREATE INDEX IF NOT EXISTS idx_projects_active ON projects(is_active, created_at)",
            "CREATE INDEX IF NOT EXISTS idx_projects_user ON projects(user_id, is_active)"
        ]
        
        with self.engine.connect() as conn:
            for index_sql in indexes:
                try:
                    conn.execute(text(index_sql))
                    logger.info(f"索引创建成功: {index_sql.split()[5]}")
                except Exception as e:
                    logger.warning(f"索引创建跳过: {e}")
            conn.commit()
            
    def update_project_statistics(self, project_id):
        """更新项目统计信息"""
        db = self.SessionLocal()
        try:
            project = db.query(Project).filter(Project.id == project_id).first()
            if project:
                project.update_statistics()
                db.commit()
                logger.info(f"项目 {project_id} 统计信息已更新")
        except Exception as e:
            logger.error(f"更新项目统计失败: {e}")
        finally:
            db.close()
            
    def verify_migration(self):
        """验证迁移结果"""
        db = self.SessionLocal()
        try:
            # 检查项目数量
            project_count = db.query(Project).count()
            logger.info(f"项目总数: {project_count}")
            
            # 检查未分配的数据
            unassigned_files = db.query(File).filter(File.project_id.is_(None)).count()
            unassigned_tasks = db.query(Task).filter(Task.project_id.is_(None)).count()
            unassigned_scripts = db.query(Script).filter(Script.project_id.is_(None)).count()
            
            logger.info(f"未分配项目的数据: 文件 {unassigned_files}, 任务 {unassigned_tasks}, 讲稿 {unassigned_scripts}")
            
            if unassigned_files == 0 and unassigned_tasks == 0 and unassigned_scripts == 0:
                logger.info("✅ 迁移验证成功：所有数据都已分配到项目")
                return True
            else:
                logger.warning("⚠️  存在未分配项目的数据")
                return False
                
        except Exception as e:
            logger.error(f"验证迁移失败: {e}")
            return False
        finally:
            db.close()
            
    def run_migration(self):
        """执行完整迁移流程"""
        logger.info("开始项目系统迁移...")
        
        # 1. 备份数据库
        backup_path = self.backup_database()
        if not backup_path:
            response = input("无法自动备份数据库，是否继续？(y/N): ")
            if response.lower() != 'y':
                logger.info("迁移已取消")
                return False
                
        try:
            # 2. 检查现有表结构
            projects_exists, project_id_exists = self.check_existing_tables()
            logger.info(f"Projects表存在: {projects_exists}")
            logger.info(f"Project_id字段存在情况: {project_id_exists}")
            
            # 3. 创建表结构
            if not self.create_tables():
                return False
                
            # 4. 添加project_id字段
            if not self.add_project_id_columns():
                return False
                
            # 5. 创建默认项目
            db = self.SessionLocal()
            try:
                default_project = self.create_default_project(db)
                if not default_project:
                    return False
                default_project_id = default_project.id
            finally:
                db.close()
                
            # 6. 迁移现有数据
            if not self.migrate_existing_data(default_project_id):
                return False
                
            # 7. 创建索引
            self.create_indexes()
            
            # 8. 更新统计信息
            self.update_project_statistics(default_project_id)
            
            # 9. 验证迁移
            if self.verify_migration():
                logger.info("🎉 项目系统迁移完成！")
                return True
            else:
                logger.error("❌ 迁移验证失败")
                return False
                
        except Exception as e:
            logger.error(f"迁移过程中发生错误: {e}")
            if backup_path:
                logger.info(f"请使用备份文件恢复: {backup_path}")
            return False


def main():
    """主函数"""
    print("🚀 PPT讲稿生成器项目系统迁移工具")
    print("=" * 50)
    
    migration = ProjectMigration()
    
    # 提示用户确认
    print("此脚本将为系统添加项目管理功能，包括：")
    print("1. 创建projects表")
    print("2. 为现有表添加project_id字段")
    print("3. 创建默认项目并迁移现有数据")
    print("4. 创建性能优化索引")
    print()
    
    response = input("确定要继续迁移吗？(y/N): ")
    if response.lower() != 'y':
        print("迁移已取消")
        return
        
    # 执行迁移
    success = migration.run_migration()
    
    if success:
        print("\n✅ 迁移成功完成！")
        print("现在可以启动应用程序使用新的项目管理功能。")
    else:
        print("\n❌ 迁移失败！")
        print("请检查日志文件 migration.log 获取详细错误信息。")
        sys.exit(1)


if __name__ == "__main__":
    main()