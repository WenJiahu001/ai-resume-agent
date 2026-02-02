# -*- coding: utf-8 -*-
"""
依赖注入

FastAPI 依赖项，用于路由中的参数注入，如获取当前用户。
"""
from typing import Optional, Dict, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from services.auth import AuthService, get_auth_service
from services.user import UserService, get_user_service

# OAuth2 scheme for Swagger UI
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
    user_service: UserService = Depends(get_user_service)
) -> Dict[str, Any]:
    """
    获取当前登录用户
    
    验证 Token 并返回用户信息。如果验证失败，抛出 401 异常。
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = auth_service.decode_token(token)
    if payload is None:
        raise credentials_exception
        
    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception
        
    user = user_service.get_user(user_id)
    if user is None:
        raise credentials_exception
        
    return user


async def get_current_user_id(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> str:
    """获取当前用户 ID"""
    return current_user["id"]
