"""自定义异常"""

from typing import Optional


class AppException(Exception):
    def __init__(self, message: str, code: str = "APP_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class NotFoundError(AppException):
    def __init__(self, resource: str, identifier: Optional[str] = None):
        msg = f"{resource} '{identifier}' 不存在" if identifier else f"{resource} 不存在"
        super().__init__(msg, code="NOT_FOUND")


class ValidationError(AppException):
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(message, code="VALIDATION_ERROR")
        self.field = field
