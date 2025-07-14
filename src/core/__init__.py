"""
核心业务逻辑模块

包含PPT处理、AI调用、讲稿生成等核心功能。
"""

from .ppt_processor import PPTProcessor
from .ai_client import AIClient
from .script_generator import ScriptGenerator
from .context_manager import ContextManager

__all__ = ['PPTProcessor', 'AIClient', 'ScriptGenerator', 'ContextManager']