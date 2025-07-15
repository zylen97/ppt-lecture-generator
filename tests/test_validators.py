"""
验证器模块测试
"""

import unittest
import tempfile
import os
from pathlib import Path
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.validators import Validators


class TestValidators(unittest.TestCase):
    """验证器测试类"""
    
    def setUp(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_files = []
    
    def tearDown(self):
        """清理测试环境"""
        for file_path in self.temp_files:
            try:
                os.remove(file_path)
            except:
                pass
        
        try:
            os.rmdir(self.temp_dir)
        except:
            pass
    
    def create_temp_file(self, filename: str, content: str = "test") -> str:
        """创建临时文件"""
        file_path = os.path.join(self.temp_dir, filename)
        with open(file_path, 'w') as f:
            f.write(content)
        self.temp_files.append(file_path)
        return file_path
    
    def test_validate_file_path(self):
        """测试文件路径验证"""
        # 测试有效文件
        valid_file = self.create_temp_file("test.txt")
        is_valid, error = Validators.validate_file_path(valid_file)
        self.assertTrue(is_valid)
        self.assertEqual(error, "")
        
        # 测试无效文件
        invalid_file = "/nonexistent/file.txt"
        is_valid, error = Validators.validate_file_path(invalid_file)
        self.assertFalse(is_valid)
        self.assertIn("不存在", error)
        
        # 测试空路径
        is_valid, error = Validators.validate_file_path("")
        self.assertFalse(is_valid)
        self.assertIn("不能为空", error)
    
    def test_validate_ppt_file(self):
        """测试PPT文件验证"""
        # 测试有效PPT文件
        valid_ppt = self.create_temp_file("test.pptx")
        is_valid, error = Validators.validate_ppt_file(valid_ppt)
        self.assertTrue(is_valid)
        
        # 测试无效格式
        invalid_format = self.create_temp_file("test.txt")
        is_valid, error = Validators.validate_ppt_file(invalid_format)
        self.assertFalse(is_valid)
        self.assertIn("不支持的PPT格式", error)
    
    def test_validate_api_key(self):
        """测试API密钥验证"""
        # 测试有效密钥
        valid_keys = [
            "sk-1234567890abcdefghijklmnopqrstuvwxyz",
            "sk_1234567890abcdefghijklmnopqrstuvwxyz"
        ]
        
        for key in valid_keys:
            is_valid, error = Validators.validate_api_key(key)
            self.assertTrue(is_valid, f"密钥 {key} 应该有效")
        
        # 测试无效密钥
        invalid_keys = [
            "",
            "invalid_key",
            "sk-",
            "sk_short"
        ]
        
        for key in invalid_keys:
            is_valid, error = Validators.validate_api_key(key)
            self.assertFalse(is_valid, f"密钥 {key} 应该无效")
    
    def test_validate_api_endpoint(self):
        """测试API端点验证"""
        # 测试有效端点
        valid_endpoints = [
            "https://api.openai.com/v1",
            "http://localhost:8080",
            "https://api.example.com"
        ]
        
        for endpoint in valid_endpoints:
            is_valid, error = Validators.validate_api_endpoint(endpoint)
            self.assertTrue(is_valid, f"端点 {endpoint} 应该有效")
        
        # 测试无效端点
        invalid_endpoints = [
            "",
            "invalid_url",
            "ftp://example.com",
            "https://"
        ]
        
        for endpoint in invalid_endpoints:
            is_valid, error = Validators.validate_api_endpoint(endpoint)
            self.assertFalse(is_valid, f"端点 {endpoint} 应该无效")
    
    def test_validate_duration(self):
        """测试时长验证"""
        # 测试有效时长
        valid_durations = [30, 60, 90, 120, 180, 240]
        
        for duration in valid_durations:
            is_valid, error = Validators.validate_duration(duration)
            self.assertTrue(is_valid, f"时长 {duration} 应该有效")
        
        # 测试无效时长
        invalid_durations = [0, 29, 241, 300, -10]
        
        for duration in invalid_durations:
            is_valid, error = Validators.validate_duration(duration)
            self.assertFalse(is_valid, f"时长 {duration} 应该无效")
    
    def test_validate_positive_integer(self):
        """测试正整数验证"""
        # 测试有效整数
        is_valid, error = Validators.validate_positive_integer(10, 1, 100)
        self.assertTrue(is_valid)
        
        # 测试边界值
        is_valid, error = Validators.validate_positive_integer(1, 1, 100)
        self.assertTrue(is_valid)
        
        is_valid, error = Validators.validate_positive_integer(100, 1, 100)
        self.assertTrue(is_valid)
        
        # 测试无效值
        is_valid, error = Validators.validate_positive_integer(0, 1, 100)
        self.assertFalse(is_valid)
        
        is_valid, error = Validators.validate_positive_integer(101, 1, 100)
        self.assertFalse(is_valid)
    
    def test_validate_filename(self):
        """测试文件名验证"""
        # 测试有效文件名
        valid_names = [
            "test.txt",
            "presentation.pptx",
            "lecture-script.md",
            "文档.docx"
        ]
        
        for name in valid_names:
            is_valid, error = Validators.validate_filename(name)
            self.assertTrue(is_valid, f"文件名 {name} 应该有效")
        
        # 测试无效文件名
        invalid_names = [
            "",
            "file<name>.txt",
            "file|name.txt",
            "CON.txt",
            "file:name.txt"
        ]
        
        for name in invalid_names:
            is_valid, error = Validators.validate_filename(name)
            self.assertFalse(is_valid, f"文件名 {name} 应该无效")


if __name__ == '__main__':
    unittest.main()