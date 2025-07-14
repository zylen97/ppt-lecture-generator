"""
验证器模块

提供各种输入验证和格式检查功能。
"""

import re
import os
import json
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
from urllib.parse import urlparse

from ..config.constants import SUPPORTED_PPT_FORMATS, SUPPORTED_MODELS, DEFAULT_API_ENDPOINTS
from .logger import get_logger


class Validators:
    """验证器工具类"""
    
    @staticmethod
    def validate_file_path(file_path: str) -> Tuple[bool, str]:
        """
        验证文件路径
        
        Args:
            file_path: 文件路径
            
        Returns:
            Tuple[bool, str]: (是否有效, 错误信息)
        """
        try:
            if not file_path:
                return False, "文件路径不能为空"
            
            path = Path(file_path)
            
            if not path.exists():
                return False, f"文件不存在: {file_path}"
            
            if not path.is_file():
                return False, f"路径不是文件: {file_path}"
            
            return True, ""
            
        except Exception as e:
            return False, f"路径验证失败: {str(e)}"
    
    @staticmethod
    def validate_ppt_file(file_path: str) -> Tuple[bool, str]:
        """
        验证PPT文件
        
        Args:
            file_path: PPT文件路径
            
        Returns:
            Tuple[bool, str]: (是否有效, 错误信息)
        """
        # 先验证基本文件路径
        is_valid, error_msg = Validators.validate_file_path(file_path)
        if not is_valid:
            return False, error_msg
        
        try:
            path = Path(file_path)
            
            # 检查文件扩展名
            if path.suffix.lower() not in SUPPORTED_PPT_FORMATS:
                return False, f"不支持的PPT格式: {path.suffix}，支持的格式: {', '.join(SUPPORTED_PPT_FORMATS)}"
            
            # 检查文件大小
            file_size = path.stat().st_size
            max_size = 100 * 1024 * 1024  # 100MB
            if file_size > max_size:
                return False, f"文件过大: {file_size / (1024*1024):.1f}MB，最大支持{max_size / (1024*1024):.0f}MB"
            
            # 检查文件是否可读
            try:
                with open(file_path, 'rb') as f:
                    f.read(1024)  # 尝试读取前1KB
            except Exception:
                return False, "文件无法读取，可能已损坏"
            
            return True, ""
            
        except Exception as e:
            return False, f"PPT文件验证失败: {str(e)}"
    
    @staticmethod
    def validate_api_key(api_key: str) -> Tuple[bool, str]:
        """
        验证API密钥
        
        Args:
            api_key: API密钥
            
        Returns:
            Tuple[bool, str]: (是否有效, 错误信息)
        """
        if not api_key:
            return False, "API密钥不能为空"
        
        # 检查基本格式
        if not api_key.startswith(('sk-', 'sk_')):
            return False, "API密钥格式不正确，应以'sk-'或'sk_'开头"
        
        # 检查长度
        if len(api_key) < 20:
            return False, "API密钥长度不足"
        
        # 检查字符组成
        if not re.match(r'^sk[-_][A-Za-z0-9\-_]+$', api_key):
            return False, "API密钥包含无效字符"
        
        return True, ""
    
    @staticmethod
    def validate_api_endpoint(endpoint: str) -> Tuple[bool, str]:
        """
        验证API端点
        
        Args:
            endpoint: API端点URL
            
        Returns:
            Tuple[bool, str]: (是否有效, 错误信息)
        """
        if not endpoint:
            return False, "API端点不能为空"
        
        try:
            parsed = urlparse(endpoint)
            
            # 检查协议
            if parsed.scheme not in ['http', 'https']:
                return False, "API端点必须使用HTTP或HTTPS协议"
            
            # 检查域名
            if not parsed.netloc:
                return False, "API端点缺少域名"
            
            # 检查格式
            if not re.match(r'^https?://.+', endpoint):
                return False, "API端点格式不正确"
            
            return True, ""
            
        except Exception as e:
            return False, f"API端点验证失败: {str(e)}"
    
    @staticmethod
    def validate_model(model: str) -> Tuple[bool, str]:
        """
        验证模型名称
        
        Args:
            model: 模型名称
            
        Returns:
            Tuple[bool, str]: (是否有效, 错误信息)
        """
        if not model:
            return False, "模型名称不能为空"
        
        # 检查是否在支持的模型列表中
        if model not in SUPPORTED_MODELS:
            return False, f"不支持的模型: {model}，支持的模型: {', '.join(SUPPORTED_MODELS.keys())}"
        
        return True, ""
    
    @staticmethod
    def validate_duration(duration: int) -> Tuple[bool, str]:
        """
        验证课程时长
        
        Args:
            duration: 课程时长（分钟）
            
        Returns:
            Tuple[bool, str]: (是否有效, 错误信息)
        """
        if not isinstance(duration, int):
            return False, "课程时长必须是整数"
        
        if duration < 30:
            return False, "课程时长不能少于30分钟"
        
        if duration > 240:
            return False, "课程时长不能超过240分钟"
        
        return True, ""
    
    @staticmethod
    def validate_language(language: str) -> Tuple[bool, str]:
        """
        验证语言设置
        
        Args:
            language: 语言代码
            
        Returns:
            Tuple[bool, str]: (是否有效, 错误信息)
        """
        supported_languages = ['zh-CN', 'zh-TW', 'en-US']
        
        if language not in supported_languages:
            return False, f"不支持的语言: {language}，支持的语言: {', '.join(supported_languages)}"
        
        return True, ""
    
    @staticmethod
    def validate_output_format(output_format: str) -> Tuple[bool, str]:
        """
        验证输出格式
        
        Args:
            output_format: 输出格式
            
        Returns:
            Tuple[bool, str]: (是否有效, 错误信息)
        """
        supported_formats = ['md', 'txt', 'docx', 'pdf']
        
        if output_format.lower() not in supported_formats:
            return False, f"不支持的输出格式: {output_format}，支持的格式: {', '.join(supported_formats)}"
        
        return True, ""
    
    @staticmethod
    def validate_json_config(config_str: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        验证JSON配置
        
        Args:
            config_str: JSON配置字符串
            
        Returns:
            Tuple[bool, str, Dict[str, Any]]: (是否有效, 错误信息, 配置数据)
        """
        try:
            if not config_str.strip():
                return False, "配置内容不能为空", {}
            
            config_data = json.loads(config_str)
            
            if not isinstance(config_data, dict):
                return False, "配置必须是JSON对象", {}
            
            return True, "", config_data
            
        except json.JSONDecodeError as e:
            return False, f"JSON格式错误: {str(e)}", {}
        except Exception as e:
            return False, f"配置验证失败: {str(e)}", {}
    
    @staticmethod
    def validate_directory(directory: str) -> Tuple[bool, str]:
        """
        验证目录路径
        
        Args:
            directory: 目录路径
            
        Returns:
            Tuple[bool, str]: (是否有效, 错误信息)
        """
        try:
            if not directory:
                return False, "目录路径不能为空"
            
            path = Path(directory)
            
            # 检查是否存在
            if not path.exists():
                # 尝试创建目录
                try:
                    path.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    return False, f"无法创建目录: {str(e)}"
            
            # 检查是否是目录
            if not path.is_dir():
                return False, f"路径不是目录: {directory}"
            
            # 检查是否可写
            if not os.access(path, os.W_OK):
                return False, f"目录不可写: {directory}"
            
            return True, ""
            
        except Exception as e:
            return False, f"目录验证失败: {str(e)}"
    
    @staticmethod
    def validate_filename(filename: str) -> Tuple[bool, str]:
        """
        验证文件名
        
        Args:
            filename: 文件名
            
        Returns:
            Tuple[bool, str]: (是否有效, 错误信息)
        """
        if not filename:
            return False, "文件名不能为空"
        
        # 检查长度
        if len(filename) > 255:
            return False, "文件名过长"
        
        # 检查非法字符
        illegal_chars = r'[<>:"/\\|?*]'
        if re.search(illegal_chars, filename):
            return False, "文件名包含非法字符: < > : \" / \\ | ? *"
        
        # 检查保留名称
        reserved_names = [
            'CON', 'PRN', 'AUX', 'NUL',
            'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
            'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
        ]
        
        if filename.upper().split('.')[0] in reserved_names:
            return False, f"文件名不能使用保留名称: {filename}"
        
        return True, ""
    
    @staticmethod
    def validate_positive_integer(value: Any, min_value: int = 1, 
                                max_value: int = None) -> Tuple[bool, str]:
        """
        验证正整数
        
        Args:
            value: 要验证的值
            min_value: 最小值
            max_value: 最大值
            
        Returns:
            Tuple[bool, str]: (是否有效, 错误信息)
        """
        try:
            if not isinstance(value, int):
                # 尝试转换
                if isinstance(value, str):
                    value = int(value)
                else:
                    return False, "必须是整数"
            
            if value < min_value:
                return False, f"值不能小于{min_value}"
            
            if max_value is not None and value > max_value:
                return False, f"值不能大于{max_value}"
            
            return True, ""
            
        except ValueError:
            return False, "不是有效的整数"
        except Exception as e:
            return False, f"验证失败: {str(e)}"
    
    @staticmethod
    def validate_positive_float(value: Any, min_value: float = 0.0, 
                              max_value: float = None) -> Tuple[bool, str]:
        """
        验证正浮点数
        
        Args:
            value: 要验证的值
            min_value: 最小值
            max_value: 最大值
            
        Returns:
            Tuple[bool, str]: (是否有效, 错误信息)
        """
        try:
            if not isinstance(value, (int, float)):
                # 尝试转换
                if isinstance(value, str):
                    value = float(value)
                else:
                    return False, "必须是数字"
            
            if value < min_value:
                return False, f"值不能小于{min_value}"
            
            if max_value is not None and value > max_value:
                return False, f"值不能大于{max_value}"
            
            return True, ""
            
        except ValueError:
            return False, "不是有效的数字"
        except Exception as e:
            return False, f"验证失败: {str(e)}"
    
    @staticmethod
    def validate_email(email: str) -> Tuple[bool, str]:
        """
        验证邮箱地址
        
        Args:
            email: 邮箱地址
            
        Returns:
            Tuple[bool, str]: (是否有效, 错误信息)
        """
        if not email:
            return False, "邮箱地址不能为空"
        
        # 简单的邮箱格式验证
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return False, "邮箱地址格式不正确"
        
        return True, ""
    
    @staticmethod
    def validate_config_section(section_name: str, config_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        验证配置段
        
        Args:
            section_name: 配置段名称
            config_data: 配置数据
            
        Returns:
            Tuple[bool, List[str]]: (是否有效, 错误信息列表)
        """
        errors = []
        
        if section_name == 'api':
            # 验证API配置
            if 'endpoint' in config_data:
                is_valid, error = Validators.validate_api_endpoint(config_data['endpoint'])
                if not is_valid:
                    errors.append(f"API端点: {error}")
            
            if 'api_key' in config_data:
                is_valid, error = Validators.validate_api_key(config_data['api_key'])
                if not is_valid:
                    errors.append(f"API密钥: {error}")
            
            if 'model' in config_data:
                is_valid, error = Validators.validate_model(config_data['model'])
                if not is_valid:
                    errors.append(f"模型: {error}")
            
            if 'timeout' in config_data:
                is_valid, error = Validators.validate_positive_integer(config_data['timeout'], 5, 120)
                if not is_valid:
                    errors.append(f"超时: {error}")
        
        elif section_name == 'lecture':
            # 验证讲稿配置
            if 'default_duration' in config_data:
                is_valid, error = Validators.validate_duration(config_data['default_duration'])
                if not is_valid:
                    errors.append(f"默认时长: {error}")
            
            if 'language' in config_data:
                is_valid, error = Validators.validate_language(config_data['language'])
                if not is_valid:
                    errors.append(f"语言: {error}")
        
        elif section_name == 'ppt':
            # 验证PPT配置
            if 'temp_dir' in config_data:
                is_valid, error = Validators.validate_directory(config_data['temp_dir'])
                if not is_valid:
                    errors.append(f"临时目录: {error}")
            
            if 'dpi' in config_data:
                is_valid, error = Validators.validate_positive_integer(config_data['dpi'], 72, 600)
                if not is_valid:
                    errors.append(f"DPI: {error}")
            
            if 'quality' in config_data:
                is_valid, error = Validators.validate_positive_integer(config_data['quality'], 1, 100)
                if not is_valid:
                    errors.append(f"质量: {error}")
        
        return len(errors) == 0, errors