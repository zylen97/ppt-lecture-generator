"""
应用中间件
"""

import time
import uuid
from datetime import datetime
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)


class RequestMiddleware:
    """请求处理中间件"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)
            
            # 生成请求ID
            request_id = str(uuid.uuid4())
            request.state.request_id = request_id
            
            # 记录请求开始时间
            start_time = time.time()
            request.state.start_time = start_time
            
            # 记录请求日志
            logger.info(
                f"Request started: {request.method} {request.url.path}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "query_params": str(request.query_params),
                    "client_ip": request.client.host if request.client else None
                }
            )
            
            # 处理响应
            async def send_wrapper(message):
                if message["type"] == "http.response.start":
                    # 记录处理时间
                    process_time = time.time() - start_time
                    
                    # 添加自定义响应头
                    headers = dict(message.get("headers", []))
                    headers[b"x-request-id"] = request_id.encode()
                    headers[b"x-process-time"] = str(round(process_time, 4)).encode()
                    message["headers"] = [(k, v) for k, v in headers.items()]
                    
                    # 记录响应日志
                    status_code = message["status"]
                    logger.info(
                        f"Request completed: {request.method} {request.url.path} - {status_code}",
                        extra={
                            "request_id": request_id,
                            "method": request.method,
                            "path": request.url.path,
                            "status_code": status_code,
                            "process_time": process_time
                        }
                    )
                
                elif message["type"] == "http.response.body":
                    # 为JSON响应添加时间戳和请求ID
                    if hasattr(request.state, "response_body"):
                        body = message.get("body", b"")
                        if body:
                            try:
                                import json
                                response_data = json.loads(body.decode())
                                if isinstance(response_data, dict):
                                    response_data["timestamp"] = datetime.utcnow().isoformat() + "Z"
                                    response_data["request_id"] = request_id
                                    message["body"] = json.dumps(response_data).encode()
                            except (json.JSONDecodeError, UnicodeDecodeError):
                                # 不是JSON响应，不处理
                                pass
                
                await send(message)
            
            await self.app(scope, receive, send_wrapper)
        else:
            await self.app(scope, receive, send)


class CORSMiddleware:
    """CORS中间件"""
    
    def __init__(self, app, allow_origins=None, allow_methods=None, allow_headers=None):
        self.app = app
        self.allow_origins = allow_origins or ["*"]
        self.allow_methods = allow_methods or ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        self.allow_headers = allow_headers or ["*"]
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope)
            
            # 处理预检请求
            if request.method == "OPTIONS":
                response = Response()
                response.headers["Access-Control-Allow-Origin"] = ", ".join(self.allow_origins)
                response.headers["Access-Control-Allow-Methods"] = ", ".join(self.allow_methods)
                response.headers["Access-Control-Allow-Headers"] = ", ".join(self.allow_headers)
                response.headers["Access-Control-Allow-Credentials"] = "true"
                await response(scope, receive, send)
                return
            
            # 处理普通请求
            async def send_wrapper(message):
                if message["type"] == "http.response.start":
                    headers = dict(message.get("headers", []))
                    headers[b"access-control-allow-origin"] = ", ".join(self.allow_origins).encode()
                    headers[b"access-control-allow-credentials"] = b"true"
                    headers[b"access-control-expose-headers"] = b"x-request-id, x-process-time"
                    message["headers"] = [(k, v) for k, v in headers.items()]
                
                await send(message)
            
            await self.app(scope, receive, send_wrapper)
        else:
            await self.app(scope, receive, send)


class SecurityMiddleware:
    """安全中间件"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            async def send_wrapper(message):
                if message["type"] == "http.response.start":
                    headers = dict(message.get("headers", []))
                    
                    # 添加安全响应头
                    headers[b"x-content-type-options"] = b"nosniff"
                    headers[b"x-frame-options"] = b"DENY"
                    headers[b"x-xss-protection"] = b"1; mode=block"
                    headers[b"referrer-policy"] = b"strict-origin-when-cross-origin"
                    
                    message["headers"] = [(k, v) for k, v in headers.items()]
                
                await send(message)
            
            await self.app(scope, receive, send_wrapper)
        else:
            await self.app(scope, receive, send)


def setup_middleware(app):
    """设置中间件"""
    # 注意：中间件的添加顺序很重要，后添加的先执行
    app.add_middleware(SecurityMiddleware)
    app.add_middleware(RequestMiddleware)