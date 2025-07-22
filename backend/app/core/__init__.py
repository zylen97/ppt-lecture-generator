"""
核心业务逻辑模块
"""

from .ai_client import AIClient, APIResponse
from .ppt_processor import PPTProcessor, SlideInfo
from .script_generator import ScriptGenerator

__all__ = ["AIClient", "APIResponse", "PPTProcessor", "SlideInfo", "ScriptGenerator"]