"""
统一错误处理模块
"""

from typing import Dict, Any, Optional
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorCode(Enum):
    """错误代码枚举"""
    # 通用错误 1000-1999
    UNKNOWN_ERROR = 1000
    VALIDATION_ERROR = 1001
    PERMISSION_DENIED = 1002
    RESOURCE_NOT_FOUND = 1003
    
    # 文件相关错误 2000-2999
    FILE_NOT_FOUND = 2000
    FILE_TOO_LARGE = 2001
    UNSUPPORTED_FILE_TYPE = 2002
    FILE_UPLOAD_FAILED = 2003
    FILE_PROCESSING_FAILED = 2004
    
    # 任务相关错误 3000-3999
    TASK_NOT_FOUND = 3000
    TASK_CREATION_FAILED = 3001
    TASK_EXECUTION_FAILED = 3002
    INVALID_TASK_STATUS = 3003
    
    # 媒体处理错误 4000-4999
    MEDIA_PROCESSING_ERROR = 4000
    TRANSCRIPTION_FAILED = 4001
    INVALID_MEDIA_FORMAT = 4002
    WHISPER_SERVICE_UNAVAILABLE = 4003
    FFMPEG_NOT_AVAILABLE = 4004
    
    # API配置错误 5000-5999
    INVALID_API_KEY = 5000
    API_QUOTA_EXCEEDED = 5001
    API_SERVICE_UNAVAILABLE = 5002


class StandardError(Exception):
    """标准业务异常基类"""
    
    def __init__(
        self, 
        error_code: ErrorCode, 
        message: str,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 500
    ):
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        self.status_code = status_code
        super().__init__(self.message)


class ValidationError(StandardError):
    """验证错误"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            error_code=ErrorCode.VALIDATION_ERROR,
            message=message,
            details=details,
            status_code=400
        )


class ResourceNotFoundError(StandardError):
    """资源不存在错误"""
    
    def __init__(self, resource: str, identifier: str):
        super().__init__(
            error_code=ErrorCode.RESOURCE_NOT_FOUND,
            message=f"{resource}不存在",
            details={"resource": resource, "identifier": identifier},
            status_code=404
        )


class MediaProcessingError(StandardError):
    """媒体处理错误"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            error_code=ErrorCode.MEDIA_PROCESSING_ERROR,
            message=message,
            details=details,
            status_code=400
        )


class TaskExecutionError(StandardError):
    """任务执行错误"""
    
    def __init__(self, task_id: int, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            error_code=ErrorCode.TASK_EXECUTION_FAILED,
            message=f"任务执行失败: {message}",
            details={"task_id": task_id, **(details or {})},
            status_code=500
        )


class ErrorResponse:
    """标准错误响应格式"""
    
    @staticmethod
    def build_error_response(
        error_code: ErrorCode,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """构建标准错误响应"""
        return {
            "success": False,
            "error": {
                "code": error_code.value,
                "message": message,
                "details": details or {},
            },
            "data": None,
            "timestamp": None,  # 将在中间件中设置
            "request_id": request_id
        }
    
    @staticmethod
    def build_success_response(
        data: Any = None,
        message: str = "操作成功",
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """构建标准成功响应"""
        return {
            "success": True,
            "error": None,
            "data": data,
            "message": message,
            "timestamp": None,  # 将在中间件中设置
            "request_id": request_id
        }


async def standard_error_handler(request: Request, exc: StandardError) -> JSONResponse:
    """标准错误处理器"""
    request_id = getattr(request.state, "request_id", None)
    
    logger.error(
        f"StandardError: {exc.error_code.name} - {exc.message}",
        extra={
            "error_code": exc.error_code.value,
            "details": exc.details,
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method
        }
    )
    
    response = ErrorResponse.build_error_response(
        error_code=exc.error_code,
        message=exc.message,
        details=exc.details,
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """HTTP异常处理器"""
    request_id = getattr(request.state, "request_id", None)
    
    # 映射HTTP状态码到错误代码
    error_code_mapping = {
        404: ErrorCode.RESOURCE_NOT_FOUND,
        400: ErrorCode.VALIDATION_ERROR,
        403: ErrorCode.PERMISSION_DENIED,
        500: ErrorCode.UNKNOWN_ERROR
    }
    
    error_code = error_code_mapping.get(exc.status_code, ErrorCode.UNKNOWN_ERROR)
    
    logger.error(
        f"HTTPException: {exc.status_code} - {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "detail": exc.detail,
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method
        }
    )
    
    response = ErrorResponse.build_error_response(
        error_code=error_code,
        message=str(exc.detail),
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """请求验证异常处理器"""
    request_id = getattr(request.state, "request_id", None)
    
    logger.error(
        f"ValidationError: {exc.errors()}",
        extra={
            "errors": exc.errors(),
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method
        }
    )
    
    # 格式化验证错误信息
    error_details = []
    for error in exc.errors():
        error_details.append({
            "field": " -> ".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    response = ErrorResponse.build_error_response(
        error_code=ErrorCode.VALIDATION_ERROR,
        message="请求参数验证失败",
        details={"validation_errors": error_details},
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=422,
        content=response
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """通用异常处理器"""
    request_id = getattr(request.state, "request_id", None)
    
    logger.error(
        f"UnexpectedError: {type(exc).__name__} - {str(exc)}",
        extra={
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method
        },
        exc_info=True
    )
    
    response = ErrorResponse.build_error_response(
        error_code=ErrorCode.UNKNOWN_ERROR,
        message="服务器内部错误",
        details={"exception_type": type(exc).__name__} if logger.getEffectiveLevel() <= logging.DEBUG else {},
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=500,
        content=response
    )


def setup_error_handlers(app):
    """设置错误处理器"""
    app.add_exception_handler(StandardError, standard_error_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)