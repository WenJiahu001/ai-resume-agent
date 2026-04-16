"""认证路由"""

from fastapi import APIRouter, Depends, HTTPException, status

from deps import get_current_user
from models import Token, LoginRequest
from response import success
from services.auth import AuthService

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post("/login", summary="用户登录")
def login(
    req: LoginRequest,
    auth_service: AuthService = Depends(AuthService),
):
    user = auth_service.authenticate_user(req.username, req.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = auth_service.create_access_token(data={"sub": user["id"]})
    return success(
        data={
            "access_token": token,
            "token_type": "bearer",
            "user_id": user["id"],
            "username": user["username"],
        },
        message="登录成功",
    )


@router.get("/me", summary="获取当前用户")
def read_users_me(current_user: dict = Depends(get_current_user)):
    return success(data=current_user)
