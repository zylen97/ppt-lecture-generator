"""
常量定义模块

定义应用程序中使用的所有常量，包括默认配置、API端点、支持的模型等。
"""

import os
from pathlib import Path

# 应用程序基本信息
APP_NAME = "PPT讲稿生成器"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "基于AI的PPT讲稿自动生成工具"

# 文件路径
PROJECT_ROOT = Path(__file__).parent.parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
RESOURCES_DIR = PROJECT_ROOT / "resources"
TEMP_DIR = PROJECT_ROOT / "temp"
LOGS_DIR = PROJECT_ROOT / "logs"

# 配置文件
CONFIG_FILE = CONFIG_DIR / "config.ini"
DEFAULT_CONFIG_FILE = Path(__file__).parent / "default_config.json"

# 支持的文件格式
SUPPORTED_PPT_FORMATS = ['.ppt', '.pptx']
SUPPORTED_IMAGE_FORMATS = ['.png', '.jpg', '.jpeg', '.bmp', '.gif']
SUPPORTED_OUTPUT_FORMATS = ['.md', '.txt', '.docx', '.pdf']

# API相关常量
DEFAULT_API_ENDPOINTS = {
    'openai': 'https://api.openai.com/v1',
    'chatanywhere': 'https://api.chatanywhere.tech',
    'azure': 'https://your-resource.openai.azure.com',
    'custom': 'https://your-custom-endpoint.com'
}

# 支持的AI模型
SUPPORTED_MODELS = {
    'gpt-4-vision-preview': {
        'name': 'GPT-4 Vision Preview',
        'supports_vision': True,
        'max_tokens': 4096,
        'context_window': 128000
    },
    'gpt-4o': {
        'name': 'GPT-4o',
        'supports_vision': True,
        'max_tokens': 4096,
        'context_window': 128000
    },
    'gpt-4o-mini': {
        'name': 'GPT-4o Mini',
        'supports_vision': True,
        'max_tokens': 16384,
        'context_window': 128000
    },
    'claude-3-opus': {
        'name': 'Claude 3 Opus',
        'supports_vision': True,
        'max_tokens': 4096,
        'context_window': 200000
    },
    'claude-3-sonnet': {
        'name': 'Claude 3 Sonnet',
        'supports_vision': True,
        'max_tokens': 4096,
        'context_window': 200000
    }
}

# 默认配置
DEFAULT_CONFIG = {
    'api': {
        'endpoint': DEFAULT_API_ENDPOINTS['openai'],
        'api_key': '',
        'model': 'gpt-4-vision-preview',
        'timeout': 30,
        'max_retries': 3
    },
    'ppt': {
        'output_format': 'png',
        'dpi': 300,
        'quality': 95,
        'temp_dir': str(TEMP_DIR)
    },
    'lecture': {
        'default_duration': 90,
        'language': 'zh-CN',
        'style': 'academic',
        'include_interaction': True,
        'include_examples': True
    },
    'gui': {
        'theme': 'default',
        'window_size': '1200x800',
        'font_size': 12,
        'auto_save': True
    },
    'logging': {
        'level': 'INFO',
        'file': str(LOGS_DIR / 'app.log'),
        'max_size': '10MB',
        'backup_count': 5
    }
}

# PPT处理相关常量
PPT_PROCESSING = {
    'max_slides': 200,
    'max_file_size': 100 * 1024 * 1024,  # 100MB
    'supported_formats': SUPPORTED_PPT_FORMATS,
    'image_format': 'PNG',
    'image_quality': 95
}

# AI分析相关常量
AI_ANALYSIS = {
    'max_context_length': 100000,
    'batch_size': 5,
    'retry_delay': 1.0,
    'timeout': 30.0,
    'temperature': 0.7,
    'top_p': 0.9
}

# 讲稿生成相关常量
LECTURE_GENERATION = {
    'min_duration': 30,
    'max_duration': 240,
    'default_duration': 90,
    'time_per_slide': 2.0,
    'interaction_frequency': 10,  # 每10分钟一次互动
    'example_frequency': 5       # 每5张幻灯片一个例子
}

# GUI相关常量
GUI_SETTINGS = {
    'window_title': APP_NAME,
    'min_window_size': (800, 600),
    'default_window_size': (1200, 800),
    'icon_size': (32, 32),
    'button_padding': 10,
    'panel_padding': 15
}

# 错误代码
ERROR_CODES = {
    'FILE_NOT_FOUND': 1001,
    'INVALID_FORMAT': 1002,
    'API_ERROR': 2001,
    'NETWORK_ERROR': 2002,
    'PROCESSING_ERROR': 3001,
    'GENERATION_ERROR': 3002,
    'CONFIG_ERROR': 4001,
    'PERMISSION_ERROR': 4002
}

# 状态码
STATUS_CODES = {
    'IDLE': 0,
    'PROCESSING': 1,
    'COMPLETED': 2,
    'ERROR': 3,
    'CANCELLED': 4
}

# 日志级别
LOG_LEVELS = {
    'DEBUG': 10,
    'INFO': 20,
    'WARNING': 30,
    'ERROR': 40,
    'CRITICAL': 50
}

# 提示词模板
PROMPT_TEMPLATES = {
    'slide_analysis': """
请分析这张PPT幻灯片的内容，提供以下信息：
1. 幻灯片标题
2. 主要内容要点
3. 图表或图像的描述
4. 关键概念和术语
5. 教学重点和难点

请用中文回答，格式要求：
- 标题：[提取的标题]
- 要点：[列出主要要点]
- 图表：[描述图表内容]
- 概念：[列出关键概念]
- 重点：[标注教学重点]
""",
    
    'script_generation': """
基于以下幻灯片内容，生成一段{duration}分钟的大学课程讲稿：

幻灯片内容：
{slide_content}

前文摘要：
{context}

要求：
1. 语言自然流畅，符合大学教学风格
2. 包含适当的过渡语和互动环节
3. 解释专业术语，提供实例说明
4. 控制讲话时长约{duration}分钟
5. 保持与前文的逻辑连贯性

请生成结构化的讲稿内容。
"""
}