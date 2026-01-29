# -*- coding: utf-8 -*-
"""
统一响应模块

定义 API 统一响应格式，所有接口返回值都应使用此格式。
"""
from typing import TypeVar, Generic, Optional, Any
from pydantic import BaseModel, Field

T = TypeVar('T')


class ApiResponse(BaseModel, Generic[T]):
    """
    统一 API 响应格式
    
    格式：{code: "xxx", message: "已xxxx", data: ...}
    """
    code: str = Field(default="SUCCESS", description="响应状态码")
    message: str = Field(default="操作成功", description="响应消息")
    data: Optional[T] = Field(default=None, description="响应数据")


def success(data: Any = None, message: str = "操作成功") -> dict:
    """
    构建成功响应
    
    Args:
        data: 响应数据
        message: 成功消息
        
    Returns:
        统一格式的成功响应字典
    """
    return {"code": "SUCCESS", "message": message, "data": data}


def fail(code: str = "ERROR", message: str = "操作失败", data: Any = None) -> dict:
    """
    构建失败响应
    
    Args:
        code: 错误码
        message: 错误消息
        data: 附加数据（可选）
        
    Returns:
        统一格式的失败响应字典
    """
    return {"code": code, "message": message, "data": data}
