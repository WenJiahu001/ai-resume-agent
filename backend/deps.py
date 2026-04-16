"""依赖注入"""

from typing import Dict, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from services.auth import AuthService
from services.user import UserService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

_UNAUTHORIZED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(AuthService),
    user_service: UserService = Depends(UserService),
) -> Dict[str, Any]:
    payload = auth_service.decode_token(token)
    if not payload:
        raise _UNAUTHORIZED

    user_id: str = payload.get("sub")
    if not user_id or not user_service.get_user(user_id):
        raise _UNAUTHORIZED

    return user_service.get_user(user_id)


async def get_current_user_id(current_user: Dict[str, Any] = Depends(get_current_user)) -> str:
    return current_user["id"]
