"""
日志管理模块

提供统一的日志记录功能，支持文件和控制台输出。
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..config.constants import LOGS_DIR, LOG_LEVELS


class Logger:
    """日志管理器类"""
    
    def __init__(self, name: str = "ppt_lecture_generator"):
        """
        初始化日志管理器
        
        Args:
            name: 日志器名称
        """
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # 避免重复添加处理器
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """设置日志处理器"""
        # 确保日志目录存在
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        
        # 创建格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
        )
        
        # 文件处理器（带轮转）
        file_handler = logging.handlers.RotatingFileHandler(
            LOGS_DIR / 'app.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # 控制台简化格式
        console_formatter = logging.Formatter(
            '%(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # 错误文件处理器
        error_handler = logging.handlers.RotatingFileHandler(
            LOGS_DIR / 'error.log',
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        self.logger.addHandler(error_handler)
    
    def debug(self, message: str, *args, **kwargs):
        """记录调试信息"""
        self.logger.debug(message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs):
        """记录信息"""
        self.logger.info(message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        """记录警告"""
        self.logger.warning(message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        """记录错误"""
        self.logger.error(message, *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs):
        """记录严重错误"""
        self.logger.critical(message, *args, **kwargs)
    
    def exception(self, message: str, *args, **kwargs):
        """记录异常（包含堆栈跟踪）"""
        self.logger.exception(message, *args, **kwargs)
    
    def set_level(self, level: str):
        """
        设置日志级别
        
        Args:
            level: 日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）
        """
        if level.upper() in LOG_LEVELS:
            self.logger.setLevel(LOG_LEVELS[level.upper()])
        else:
            self.warning(f"未知的日志级别: {level}")
    
    def add_file_handler(self, filename: str, level: str = 'INFO'):
        """
        添加文件处理器
        
        Args:
            filename: 文件名
            level: 日志级别
        """
        try:
            file_path = LOGS_DIR / filename
            handler = logging.FileHandler(file_path, encoding='utf-8')
            handler.setLevel(LOG_LEVELS.get(level.upper(), logging.INFO))
            
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            
        except Exception as e:
            self.error(f"添加文件处理器失败: {e}")
    
    def create_session_log(self, session_id: str) -> str:
        """
        创建会话日志文件
        
        Args:
            session_id: 会话ID
            
        Returns:
            str: 日志文件路径
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"session_{session_id}_{timestamp}.log"
            
            self.add_file_handler(filename, 'DEBUG')
            self.info(f"创建会话日志: {filename}")
            
            return str(LOGS_DIR / filename)
            
        except Exception as e:
            self.error(f"创建会话日志失败: {e}")
            return ""
    
    def log_function_call(self, func_name: str, args: tuple = (), kwargs: dict = None):
        """
        记录函数调用
        
        Args:
            func_name: 函数名
            args: 位置参数
            kwargs: 关键字参数
        """
        kwargs = kwargs or {}
        self.debug(f"调用函数: {func_name}, 参数: args={args}, kwargs={kwargs}")
    
    def log_performance(self, operation: str, duration: float, details: str = ""):
        """
        记录性能信息
        
        Args:
            operation: 操作名称
            duration: 耗时（秒）
            details: 详细信息
        """
        message = f"性能统计: {operation} 耗时 {duration:.2f}s"
        if details:
            message += f", 详情: {details}"
        self.info(message)
    
    def log_api_call(self, endpoint: str, method: str, status_code: int, duration: float):
        """
        记录API调用
        
        Args:
            endpoint: API端点
            method: HTTP方法
            status_code: 状态码
            duration: 耗时（秒）
        """
        self.info(f"API调用: {method} {endpoint} -> {status_code} ({duration:.2f}s)")
    
    def log_error_with_context(self, error: Exception, context: dict = None):
        """
        记录错误及上下文
        
        Args:
            error: 异常对象
            context: 上下文信息
        """
        context = context or {}
        self.error(f"错误: {type(error).__name__}: {error}")
        if context:
            self.error(f"上下文: {context}")
        self.exception("异常详情:")


# 全局日志器实例
_global_logger: Optional[Logger] = None


def init_logger(name: str = "ppt_lecture_generator", level: str = "INFO") -> Logger:
    """
    初始化全局日志器
    
    Args:
        name: 日志器名称
        level: 日志级别
        
    Returns:
        Logger: 日志器实例
    """
    global _global_logger
    
    if _global_logger is None:
        _global_logger = Logger(name)
        _global_logger.set_level(level)
        _global_logger.info("日志系统初始化完成")
    
    return _global_logger


def get_logger() -> Logger:
    """
    获取全局日志器
    
    Returns:
        Logger: 日志器实例
    """
    global _global_logger
    
    if _global_logger is None:
        _global_logger = init_logger()
    
    return _global_logger


# 便捷函数
def debug(message: str, *args, **kwargs):
    """记录调试信息"""
    get_logger().debug(message, *args, **kwargs)


def info(message: str, *args, **kwargs):
    """记录信息"""
    get_logger().info(message, *args, **kwargs)


def warning(message: str, *args, **kwargs):
    """记录警告"""
    get_logger().warning(message, *args, **kwargs)


def error(message: str, *args, **kwargs):
    """记录错误"""
    get_logger().error(message, *args, **kwargs)


def critical(message: str, *args, **kwargs):
    """记录严重错误"""
    get_logger().critical(message, *args, **kwargs)


def exception(message: str, *args, **kwargs):
    """记录异常"""
    get_logger().exception(message, *args, **kwargs)