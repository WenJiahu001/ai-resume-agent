# -*- coding: utf-8 -*-
"""
认证路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from deps import get_current_user
from models import Token, LoginRequest
from response import success, ApiResponse
from services.auth import AuthService, get_auth_service

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post(
    "/login",
    response_model=ApiResponse[Token],
    summary="用户登录",
    description="使用用户名和密码登录，获取 JWT Token。",
)
def login(
    req: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """用户登录"""
    user = auth_service.authenticate_user(req.username, req.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = auth_service.create_access_token(
        data={"sub": user["id"]}
    )
    
    return success(
        data={
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": user["id"],
            "username": user["username"]
        },
        message="登录成功"
    )

@router.get(
    "/me",
    summary="获取当前用户",
    description="获取当前登录用户的详细信息。",
)
def read_users_me(current_user: dict = Depends(get_current_user)):
    """获取当前用户"""
    return success(data=current_user)
