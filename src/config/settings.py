"""
设置管理模块

提供配置文件的读写、验证和管理功能。
"""

import json
import configparser
import os
from pathlib import Path
from typing import Dict, Any, Optional, Union
from .constants import DEFAULT_CONFIG, CONFIG_FILE, DEFAULT_CONFIG_FILE, PROJECT_ROOT


class Settings:
    """配置管理类"""
    
    def __init__(self, config_file: Optional[Path] = None):
        """
        初始化设置管理器
        
        Args:
            config_file: 配置文件路径，默认使用常量定义的路径
        """
        self.config_file = config_file or CONFIG_FILE
        self.config = DEFAULT_CONFIG.copy()
        self._ensure_directories()
        self.load_config()
    
    def _ensure_directories(self):
        """确保必要的目录存在"""
        directories = [
            self.config_file.parent,
            PROJECT_ROOT / "temp",
            PROJECT_ROOT / "logs",
            PROJECT_ROOT / "config"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def load_config(self) -> bool:
        """
        加载配置文件
        
        Returns:
            bool: 加载是否成功
        """
        try:
            if self.config_file.exists():
                config_parser = configparser.ConfigParser()
                config_parser.read(self.config_file, encoding='utf-8')
                
                # 将ConfigParser转换为字典
                for section_name in config_parser.sections():
                    if section_name not in self.config:
                        self.config[section_name] = {}
                    
                    for key, value in config_parser.items(section_name):
                        # 尝试转换数据类型
                        self.config[section_name][key] = self._convert_value(value)
                
                return True
            else:
                # 如果配置文件不存在，创建默认配置
                self.save_config()
                return True
                
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            return False
    
    def save_config(self) -> bool:
        """
        保存配置到文件
        
        Returns:
            bool: 保存是否成功
        """
        try:
            config_parser = configparser.ConfigParser()
            
            # 将字典转换为ConfigParser格式
            for section_name, section_data in self.config.items():
                config_parser.add_section(section_name)
                for key, value in section_data.items():
                    config_parser.set(section_name, key, str(value))
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                config_parser.write(f)
            
            return True
            
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            return False
    
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            section: 配置段名
            key: 配置键名
            default: 默认值
            
        Returns:
            Any: 配置值
        """
        try:
            return self.config.get(section, {}).get(key, default)
        except Exception:
            return default
    
    def set(self, section: str, key: str, value: Any) -> bool:
        """
        设置配置值
        
        Args:
            section: 配置段名
            key: 配置键名
            value: 配置值
            
        Returns:
            bool: 设置是否成功
        """
        try:
            if section not in self.config:
                self.config[section] = {}
            
            self.config[section][key] = value
            return True
            
        except Exception as e:
            print(f"设置配置值失败: {e}")
            return False
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        获取整个配置段
        
        Args:
            section: 配置段名
            
        Returns:
            Dict[str, Any]: 配置段内容
        """
        return self.config.get(section, {}).copy()
    
    def set_section(self, section: str, data: Dict[str, Any]) -> bool:
        """
        设置整个配置段
        
        Args:
            section: 配置段名
            data: 配置段数据
            
        Returns:
            bool: 设置是否成功
        """
        try:
            self.config[section] = data.copy()
            return True
        except Exception as e:
            print(f"设置配置段失败: {e}")
            return False
    
    def validate_api_config(self) -> tuple[bool, str]:
        """
        验证API配置
        
        Returns:
            tuple[bool, str]: (是否有效, 错误信息)
        """
        api_config = self.get_section('api')
        
        # 检查必需字段
        required_fields = ['endpoint', 'api_key', 'model']
        for field in required_fields:
            if not api_config.get(field):
                return False, f"API配置缺少必需字段: {field}"
        
        # 检查API密钥格式
        api_key = api_config.get('api_key', '')
        if not api_key.startswith(('sk-', 'sk_')):
            return False, "API密钥格式不正确"
        
        # 检查超时设置
        timeout = api_config.get('timeout', 30)
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            return False, "超时设置必须是正数"
        
        return True, ""
    
    def validate_ppt_config(self) -> tuple[bool, str]:
        """
        验证PPT配置
        
        Returns:
            tuple[bool, str]: (是否有效, 错误信息)
        """
        ppt_config = self.get_section('ppt')
        
        # 检查输出格式
        output_format = ppt_config.get('output_format', 'png').lower()
        if output_format not in ['png', 'jpg', 'jpeg', 'bmp']:
            return False, f"不支持的输出格式: {output_format}"
        
        # 检查DPI设置
        dpi = ppt_config.get('dpi', 300)
        if not isinstance(dpi, int) or dpi < 72 or dpi > 600:
            return False, "DPI设置必须在72-600之间"
        
        # 检查质量设置
        quality = ppt_config.get('quality', 95)
        if not isinstance(quality, int) or quality < 1 or quality > 100:
            return False, "质量设置必须在1-100之间"
        
        # 检查临时目录
        temp_dir = ppt_config.get('temp_dir', './temp')
        try:
            Path(temp_dir).mkdir(parents=True, exist_ok=True)
        except Exception:
            return False, f"无法创建临时目录: {temp_dir}"
        
        return True, ""
    
    def validate_lecture_config(self) -> tuple[bool, str]:
        """
        验证讲稿配置
        
        Returns:
            tuple[bool, str]: (是否有效, 错误信息)
        """
        lecture_config = self.get_section('lecture')
        
        # 检查课程时长
        duration = lecture_config.get('default_duration', 90)
        if not isinstance(duration, int) or duration < 30 or duration > 240:
            return False, "课程时长必须在30-240分钟之间"
        
        # 检查语言设置
        language = lecture_config.get('language', 'zh-CN')
        if language not in ['zh-CN', 'zh-TW', 'en-US']:
            return False, f"不支持的语言: {language}"
        
        # 检查风格设置
        style = lecture_config.get('style', 'academic')
        if style not in ['academic', 'casual', 'formal']:
            return False, f"不支持的风格: {style}"
        
        # 检查目标受众设置
        target_audience = lecture_config.get('target_audience', 'undergraduate')
        if target_audience not in ['undergraduate', 'graduate', 'professional']:
            return False, f"不支持的目标受众: {target_audience}"
        
        return True, ""
    
    def validate_all(self) -> tuple[bool, list[str]]:
        """
        验证所有配置
        
        Returns:
            tuple[bool, list[str]]: (是否全部有效, 错误信息列表)
        """
        errors = []
        
        # 验证各个配置段
        validators = [
            self.validate_api_config,
            self.validate_ppt_config,
            self.validate_lecture_config
        ]
        
        for validator in validators:
            is_valid, error = validator()
            if not is_valid:
                errors.append(error)
        
        return len(errors) == 0, errors
    
    def reset_to_default(self) -> bool:
        """
        重置为默认配置
        
        Returns:
            bool: 重置是否成功
        """
        try:
            self.config = DEFAULT_CONFIG.copy()
            return self.save_config()
        except Exception as e:
            print(f"重置配置失败: {e}")
            return False
    
    def backup_config(self, backup_path: Optional[Path] = None) -> bool:
        """
        备份配置文件
        
        Args:
            backup_path: 备份文件路径
            
        Returns:
            bool: 备份是否成功
        """
        try:
            if backup_path is None:
                backup_path = self.config_file.with_suffix('.backup')
            
            import shutil
            shutil.copy2(self.config_file, backup_path)
            return True
            
        except Exception as e:
            print(f"备份配置文件失败: {e}")
            return False
    
    def restore_config(self, backup_path: Path) -> bool:
        """
        从备份恢复配置
        
        Args:
            backup_path: 备份文件路径
            
        Returns:
            bool: 恢复是否成功
        """
        try:
            if not backup_path.exists():
                return False
            
            import shutil
            shutil.copy2(backup_path, self.config_file)
            return self.load_config()
            
        except Exception as e:
            print(f"恢复配置文件失败: {e}")
            return False
    
    def _convert_value(self, value: str) -> Union[str, int, float, bool]:
        """
        转换配置值的数据类型
        
        Args:
            value: 字符串值
            
        Returns:
            Union[str, int, float, bool]: 转换后的值
        """
        # 尝试转换为布尔值
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        # 尝试转换为整数
        try:
            return int(value)
        except ValueError:
            pass
        
        # 尝试转换为浮点数
        try:
            return float(value)
        except ValueError:
            pass
        
        # 返回原始字符串
        return value
    
    def __getitem__(self, key: str) -> Dict[str, Any]:
        """支持字典式访问"""
        return self.config[key]
    
    def __setitem__(self, key: str, value: Dict[str, Any]):
        """支持字典式设置"""
        self.config[key] = value
    
    def __contains__(self, key: str) -> bool:
        """支持in操作符"""
        return key in self.config


# 全局设置实例
settings = Settings()