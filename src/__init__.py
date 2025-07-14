"""PPT讲稿生成器

一个基于AI的PPT讲稿自动生成工具，支持图片内容分析和连贯讲稿生成。
"""

__version__ = "1.0.0"
__author__ = "PPT Lecture Generator Team"
__email__ = "zylenw97@gmail.com"

# 包导入
from .config import settings
from .utils import logger

# 版本检查
import sys
if sys.version_info < (3, 8):
    raise RuntimeError("PPT讲稿生成器需要Python 3.8或更高版本")

# 初始化日志
logger.init_logger()

__all__ = ['settings', 'logger']