"""
配置服务
"""

import base64
import aiohttp
import asyncio
from cryptography.fernet import Fernet
import os
from typing import Tuple


class ConfigService:
    """配置管理服务"""
    
    # 用于加密API密钥的密钥（在生产环境中应该从环境变量获取）
    _encryption_key = None
    
    @classmethod
    def _get_encryption_key(cls):
        """获取或生成加密密钥"""
        if cls._encryption_key is None:
            # 在生产环境中，这个密钥应该从环境变量或密钥管理服务获取
            key_env = os.getenv('ENCRYPTION_KEY')
            if key_env:
                cls._encryption_key = key_env.encode()
            else:
                # 开发环境生成固定密钥（不安全，仅用于开发）
                cls._encryption_key = Fernet.generate_key()
        return cls._encryption_key
    
    @classmethod
    def encrypt_api_key(cls, api_key: str) -> str:
        """加密API密钥"""
        try:
            key = cls._get_encryption_key()
            fernet = Fernet(key)
            encrypted = fernet.encrypt(api_key.encode())
            return base64.b64encode(encrypted).decode()
        except Exception as e:
            raise Exception(f"API密钥加密失败: {str(e)}")
    
    @classmethod
    def decrypt_api_key(cls, encrypted_key: str) -> str:
        """解密API密钥"""
        try:
            key = cls._get_encryption_key()
            fernet = Fernet(key)
            encrypted_bytes = base64.b64decode(encrypted_key.encode())
            decrypted = fernet.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            raise Exception(f"API密钥解密失败: {str(e)}")
    
    @staticmethod
    def mask_api_key(api_key: str) -> str:
        """掩码显示API密钥"""
        if len(api_key) <= 8:
            return "*" * len(api_key)
        
        # 显示前4位和后4位，中间用*代替
        return api_key[:4] + "*" * (len(api_key) - 8) + api_key[-4:]
    
    @staticmethod
    async def test_api_connection(endpoint: str, api_key: str, model: str) -> Tuple[bool, str]:
        """
        测试API连接
        """
        try:
            # 构造测试请求
            url = f"{endpoint.rstrip('/')}/models" if endpoint.endswith('/v1') else f"{endpoint.rstrip('/')}/v1/models"
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            # 发送测试请求
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # 检查指定的模型是否存在
                        if 'data' in data:
                            models = [m.get('id', '') for m in data['data']]
                            if model in models:
                                return True, f"连接成功，模型 {model} 可用"
                            else:
                                return False, f"模型 {model} 不可用。可用模型: {', '.join(models[:5])}..."
                        else:
                            return True, "连接成功"
                    else:
                        error_text = await response.text()
                        return False, f"连接失败 (HTTP {response.status}): {error_text}"
                        
        except asyncio.TimeoutError:
            return False, "连接超时"
        except aiohttp.ClientError as e:
            return False, f"网络错误: {str(e)}"
        except Exception as e:
            return False, f"测试失败: {str(e)}"
    
    @staticmethod
    def validate_endpoint(endpoint: str) -> Tuple[bool, str]:
        """验证API端点格式"""
        if not endpoint:
            return False, "端点不能为空"
        
        if not endpoint.startswith(('http://', 'https://')):
            return False, "端点必须以 http:// 或 https:// 开头"
        
        if not endpoint.endswith('/v1'):
            return False, "端点应该以 /v1 结尾"
        
        return True, "端点格式正确"
    
    @staticmethod
    def validate_api_key(api_key: str) -> Tuple[bool, str]:
        """验证API密钥格式"""
        if not api_key:
            return False, "API密钥不能为空"
        
        if len(api_key) < 20:
            return False, "API密钥长度不足"
        
        # 可以添加更多的验证逻辑
        
        return True, "API密钥格式正确"