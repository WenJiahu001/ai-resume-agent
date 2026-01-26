# -*- coding: utf-8 -*-
"""
自定义异常模块

定义应用程序中使用的各类异常。
"""
from typing import Optional


class AppException(Exception):
    """应用程序基础异常"""
    
    def __init__(self, message: str, code: str = "APP_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class NotFoundError(AppException):
    """资源未找到异常"""
    
    def __init__(self, resource: str, identifier: Optional[str] = None):
        message = f"{resource} 不存在"
        if identifier:
            message = f"{resource} '{identifier}' 不存在"
        super().__init__(message, code="NOT_FOUND")
        self.resource = resource
        self.identifier = identifier


class ValidationError(AppException):
    """数据验证异常"""
    
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(message, code="VALIDATION_ERROR")
        self.field = field


class DatabaseError(AppException):
    """数据库操作异常"""
    
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message, code="DATABASE_ERROR")
        self.original_error = original_error


class ExternalServiceError(AppException):
    """外部服务调用异常"""
    
    def __init__(self, service: str, message: str):
        super().__init__(f"{service}: {message}", code="EXTERNAL_SERVICE_ERROR")
        self.service = service
