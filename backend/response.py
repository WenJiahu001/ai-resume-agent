"""统一 API 响应"""

from typing import Any


def success(data: Any = None, message: str = "操作成功") -> dict:
    return {"code": "SUCCESS", "message": message, "data": data}


def fail(code: str = "ERROR", message: str = "操作失败", data: Any = None) -> dict:
    return {"code": code, "message": message, "data": data}
