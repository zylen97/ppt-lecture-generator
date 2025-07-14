"""
AI API调用模块

负责与AI模型进行交互，支持多种API端点和模型。
"""

import json
import time
import base64
import requests
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from pathlib import Path
import asyncio
import aiohttp

from ..utils.logger import get_logger
from ..config.constants import SUPPORTED_MODELS, AI_ANALYSIS, PROMPT_TEMPLATES


@dataclass
class APIResponse:
    """API响应数据结构"""
    success: bool
    content: str
    error_message: str = ""
    usage: Dict[str, Any] = None
    response_time: float = 0.0
    status_code: int = 200


class AIClient:
    """AI API客户端"""
    
    def __init__(self, api_key: str, api_base: str = "https://api.openai.com/v1", 
                 model: str = "gpt-4-vision-preview"):
        """
        初始化AI客户端
        
        Args:
            api_key: API密钥
            api_base: API基础URL
            model: 使用的模型
        """
        self.api_key = api_key
        self.api_base = api_base.rstrip('/')
        self.model = model
        self.logger = get_logger()
        
        # 会话配置
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'User-Agent': 'PPT-Lecture-Generator/1.0'
        })
        
        # 重试配置
        self.max_retries = AI_ANALYSIS['retry_delay']
        self.retry_delay = AI_ANALYSIS['retry_delay']
        self.timeout = AI_ANALYSIS['timeout']
        
        self.logger.info(f"初始化AI客户端: {api_base}, 模型: {model}")
    
    def test_connection(self) -> Tuple[bool, str]:
        """
        测试API连接
        
        Returns:
            Tuple[bool, str]: (是否成功, 错误信息)
        """
        try:
            url = f"{self.api_base}/models"
            response = self.session.get(url, timeout=self.timeout)
            
            if response.status_code == 200:
                self.logger.info("API连接测试成功")
                return True, "连接成功"
            else:
                error_msg = f"API连接失败: {response.status_code}"
                self.logger.error(error_msg)
                return False, error_msg
                
        except Exception as e:
            error_msg = f"连接测试异常: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def get_available_models(self) -> List[str]:
        """
        获取可用模型列表
        
        Returns:
            List[str]: 模型列表
        """
        try:
            url = f"{self.api_base}/models"
            response = self.session.get(url, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                models = [model['id'] for model in data.get('data', [])]
                self.logger.debug(f"获取到{len(models)}个可用模型")
                return models
            else:
                self.logger.error(f"获取模型列表失败: {response.status_code}")
                return []
                
        except Exception as e:
            self.logger.error(f"获取模型列表异常: {e}")
            return []
    
    def analyze_slide_image(self, image_path: str, context: str = "") -> APIResponse:
        """
        分析幻灯片图片
        
        Args:
            image_path: 图片路径
            context: 上下文信息
            
        Returns:
            APIResponse: 分析结果
        """
        try:
            # 读取并编码图片
            image_data = self._encode_image(image_path)
            if not image_data:
                return APIResponse(
                    success=False,
                    content="",
                    error_message="图片编码失败"
                )
            
            # 构建请求消息
            messages = self._build_analysis_messages(image_data, context)
            
            # 发送请求
            return self._make_api_call(messages)
            
        except Exception as e:
            self.logger.error(f"分析幻灯片图片失败: {e}")
            return APIResponse(
                success=False,
                content="",
                error_message=str(e)
            )
    
    def generate_script(self, slide_content: str, context: str = "", 
                       duration: int = 3) -> APIResponse:
        """
        生成讲稿内容
        
        Args:
            slide_content: 幻灯片内容
            context: 前文上下文
            duration: 建议讲解时长（分钟）
            
        Returns:
            APIResponse: 生成结果
        """
        try:
            # 构建讲稿生成消息
            messages = self._build_script_messages(slide_content, context, duration)
            
            # 发送请求
            return self._make_api_call(messages)
            
        except Exception as e:
            self.logger.error(f"生成讲稿失败: {e}")
            return APIResponse(
                success=False,
                content="",
                error_message=str(e)
            )
    
    def batch_analyze_slides(self, image_paths: List[str], 
                           context_list: List[str] = None) -> List[APIResponse]:
        """
        批量分析幻灯片
        
        Args:
            image_paths: 图片路径列表
            context_list: 上下文列表
            
        Returns:
            List[APIResponse]: 分析结果列表
        """
        context_list = context_list or [""] * len(image_paths)
        results = []
        
        for i, (image_path, context) in enumerate(zip(image_paths, context_list)):
            self.logger.info(f"分析幻灯片 {i+1}/{len(image_paths)}: {Path(image_path).name}")
            
            # 分析单张幻灯片
            result = self.analyze_slide_image(image_path, context)
            results.append(result)
            
            # 如果失败，记录错误但继续处理
            if not result.success:
                self.logger.error(f"幻灯片 {i+1} 分析失败: {result.error_message}")
            
            # 添加延迟避免频率限制
            if i < len(image_paths) - 1:
                time.sleep(self.retry_delay)
        
        return results
    
    def _encode_image(self, image_path: str) -> str:
        """
        编码图片为base64
        
        Args:
            image_path: 图片路径
            
        Returns:
            str: base64编码的图片数据
        """
        try:
            with open(image_path, 'rb') as image_file:
                image_data = image_file.read()
                base64_data = base64.b64encode(image_data).decode('utf-8')
                
                # 获取图片格式
                image_format = Path(image_path).suffix.lower().lstrip('.')
                if image_format == 'jpg':
                    image_format = 'jpeg'
                
                return f"data:image/{image_format};base64,{base64_data}"
                
        except Exception as e:
            self.logger.error(f"图片编码失败: {image_path}, 错误: {e}")
            return ""
    
    def _build_analysis_messages(self, image_data: str, context: str) -> List[Dict[str, Any]]:
        """
        构建分析消息
        
        Args:
            image_data: base64编码的图片数据
            context: 上下文信息
            
        Returns:
            List[Dict[str, Any]]: 消息列表
        """
        system_prompt = """你是一个专业的PPT内容分析助手，专门帮助分析幻灯片内容并提取关键信息。
        请仔细分析提供的幻灯片图片，并按照要求的格式返回结果。"""
        
        user_prompt = PROMPT_TEMPLATES['slide_analysis']
        if context:
            user_prompt += f"\n\n前文上下文：\n{context}"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user", 
                "content": [
                    {"type": "text", "text": user_prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": image_data}
                    }
                ]
            }
        ]
        
        return messages
    
    def _build_script_messages(self, slide_content: str, context: str, 
                             duration: int) -> List[Dict[str, Any]]:
        """
        构建讲稿生成消息
        
        Args:
            slide_content: 幻灯片内容
            context: 上下文信息
            duration: 时长
            
        Returns:
            List[Dict[str, Any]]: 消息列表
        """
        system_prompt = """你是一个专业的大学教师，擅长制作高质量的课程讲稿。
        请根据提供的幻灯片内容，生成自然流畅、逻辑清晰的讲稿。"""
        
        user_prompt = PROMPT_TEMPLATES['script_generation'].format(
            slide_content=slide_content,
            context=context,
            duration=duration
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return messages
    
    def _make_api_call(self, messages: List[Dict[str, Any]]) -> APIResponse:
        """
        执行API调用
        
        Args:
            messages: 消息列表
            
        Returns:
            APIResponse: 响应结果
        """
        for attempt in range(self.max_retries):
            try:
                start_time = time.time()
                
                # 构建请求数据
                request_data = {
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": SUPPORTED_MODELS.get(self.model, {}).get('max_tokens', 4096),
                    "temperature": AI_ANALYSIS['temperature'],
                    "top_p": AI_ANALYSIS['top_p']
                }
                
                # 发送请求
                url = f"{self.api_base}/chat/completions"
                response = self.session.post(
                    url,
                    json=request_data,
                    timeout=self.timeout
                )
                
                response_time = time.time() - start_time
                
                # 记录API调用
                self.logger.log_api_call(
                    endpoint=url,
                    method='POST',
                    status_code=response.status_code,
                    duration=response_time
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # 提取响应内容
                    content = data['choices'][0]['message']['content']
                    usage = data.get('usage', {})
                    
                    return APIResponse(
                        success=True,
                        content=content,
                        usage=usage,
                        response_time=response_time,
                        status_code=response.status_code
                    )
                
                else:
                    # 处理错误响应
                    error_data = response.json() if response.headers.get('content-type') == 'application/json' else {}
                    error_message = error_data.get('error', {}).get('message', f'HTTP {response.status_code}')
                    
                    self.logger.error(f"API调用失败 (尝试 {attempt + 1}/{self.max_retries}): {error_message}")
                    
                    # 如果是速率限制，等待后重试
                    if response.status_code == 429:
                        wait_time = self.retry_delay * (2 ** attempt)
                        self.logger.info(f"触发速率限制，等待 {wait_time:.1f}s 后重试")
                        time.sleep(wait_time)
                        continue
                    
                    # 其他错误直接返回
                    return APIResponse(
                        success=False,
                        content="",
                        error_message=error_message,
                        response_time=response_time,
                        status_code=response.status_code
                    )
                    
            except requests.exceptions.Timeout:
                self.logger.error(f"API调用超时 (尝试 {attempt + 1}/{self.max_retries})")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                    
            except Exception as e:
                self.logger.error(f"API调用异常 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
        
        # 所有重试都失败
        return APIResponse(
            success=False,
            content="",
            error_message="达到最大重试次数，调用失败"
        )
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """
        获取使用统计
        
        Returns:
            Dict[str, Any]: 使用统计信息
        """
        # 这里可以实现使用量统计
        return {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_tokens': 0,
            'average_response_time': 0.0
        }
    
    def close(self):
        """关闭客户端"""
        if hasattr(self, 'session'):
            self.session.close()
        self.logger.info("AI客户端已关闭")
    
    def __del__(self):
        """析构函数"""
        self.close()


class AsyncAIClient(AIClient):
    """异步AI客户端"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session = None
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession(
            headers={
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
                'User-Agent': 'PPT-Lecture-Generator/1.0'
            },
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    async def analyze_slide_image_async(self, image_path: str, 
                                      context: str = "") -> APIResponse:
        """
        异步分析幻灯片图片
        
        Args:
            image_path: 图片路径
            context: 上下文信息
            
        Returns:
            APIResponse: 分析结果
        """
        try:
            # 读取并编码图片
            image_data = self._encode_image(image_path)
            if not image_data:
                return APIResponse(
                    success=False,
                    content="",
                    error_message="图片编码失败"
                )
            
            # 构建请求消息
            messages = self._build_analysis_messages(image_data, context)
            
            # 发送异步请求
            return await self._make_async_api_call(messages)
            
        except Exception as e:
            self.logger.error(f"异步分析幻灯片图片失败: {e}")
            return APIResponse(
                success=False,
                content="",
                error_message=str(e)
            )
    
    async def _make_async_api_call(self, messages: List[Dict[str, Any]]) -> APIResponse:
        """
        执行异步API调用
        
        Args:
            messages: 消息列表
            
        Returns:
            APIResponse: 响应结果
        """
        for attempt in range(self.max_retries):
            try:
                start_time = time.time()
                
                # 构建请求数据
                request_data = {
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": SUPPORTED_MODELS.get(self.model, {}).get('max_tokens', 4096),
                    "temperature": AI_ANALYSIS['temperature'],
                    "top_p": AI_ANALYSIS['top_p']
                }
                
                # 发送异步请求
                url = f"{self.api_base}/chat/completions"
                async with self.session.post(url, json=request_data) as response:
                    response_time = time.time() - start_time
                    
                    # 记录API调用
                    self.logger.log_api_call(
                        endpoint=url,
                        method='POST',
                        status_code=response.status,
                        duration=response_time
                    )
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        # 提取响应内容
                        content = data['choices'][0]['message']['content']
                        usage = data.get('usage', {})
                        
                        return APIResponse(
                            success=True,
                            content=content,
                            usage=usage,
                            response_time=response_time,
                            status_code=response.status
                        )
                    
                    else:
                        # 处理错误响应
                        try:
                            error_data = await response.json()
                            error_message = error_data.get('error', {}).get('message', f'HTTP {response.status}')
                        except:
                            error_message = f'HTTP {response.status}'
                        
                        self.logger.error(f"异步API调用失败 (尝试 {attempt + 1}/{self.max_retries}): {error_message}")
                        
                        # 如果是速率限制，等待后重试
                        if response.status == 429:
                            wait_time = self.retry_delay * (2 ** attempt)
                            self.logger.info(f"触发速率限制，等待 {wait_time:.1f}s 后重试")
                            await asyncio.sleep(wait_time)
                            continue
                        
                        # 其他错误直接返回
                        return APIResponse(
                            success=False,
                            content="",
                            error_message=error_message,
                            response_time=response_time,
                            status_code=response.status
                        )
                        
            except asyncio.TimeoutError:
                self.logger.error(f"异步API调用超时 (尝试 {attempt + 1}/{self.max_retries})")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                    continue
                    
            except Exception as e:
                self.logger.error(f"异步API调用异常 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                    continue
        
        # 所有重试都失败
        return APIResponse(
            success=False,
            content="",
            error_message="达到最大重试次数，调用失败"
        )