"""认证服务 — 密码哈希、JWT 生成与验证"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

import jwt
from passlib.context import CryptContext

from services.base import BaseService

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService(BaseService):

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        return pwd_context.hash(password)

    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + (
            expires_delta or timedelta(minutes=self.settings.auth.access_token_expire_minutes)
        )
        to_encode["exp"] = expire
        return jwt.encode(to_encode, self.settings.auth.jwt_secret, algorithm=self.settings.auth.jwt_algorithm)

    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        try:
            return jwt.decode(token, self.settings.auth.jwt_secret, algorithms=[self.settings.auth.jwt_algorithm])
        except jwt.PyJWTError:
            return None

    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, username, password_hash FROM users WHERE username = %s",
                    (username,),
                )
                user = cur.fetchone()
                if not user or not self.verify_password(password, user["password_hash"]):
                    return None
                return user
        finally:
            conn.close()
