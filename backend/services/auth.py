# -*- coding: utf-8 -*-
"""
认证服务

处理密码哈希、JWT Token 生成和验证。
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

import jwt
from passlib.context import CryptContext

from config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """认证服务类"""

    def __init__(self):
        self.settings = get_settings()

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """生成密码哈希"""
        return pwd_context.hash(password)

    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """
        生成 JWT Token
        
        Args:
            data: Token 载荷
            expires_delta: 过期时间
            
        Returns:
            Token 字符串
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=self.settings.auth.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode, 
            self.settings.auth.jwt_secret, 
            algorithm=self.settings.auth.jwt_algorithm
        )
        return encoded_jwt

    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        解码并验证 Token
        
        Args:
            token: JWT Token
            
        Returns:
            解码后的数据，验证失败返回 None
        """
        try:
            payload = jwt.decode(
                token, 
                self.settings.auth.jwt_secret, 
                algorithms=[self.settings.auth.jwt_algorithm]
            )
            return payload
        except jwt.PyJWTError:
            return None

    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        验证用户凭证
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            用户信息（含ID），验证失败返回 None
        """
        conn = self.settings.db.get_connection(use_dict_cursor=True)
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, username, password_hash FROM users WHERE username = %s",
                    (username,)
                )
                user = cur.fetchone()
                
                if not user:
                    return None
                    
                if not self.verify_password(password, user["password_hash"]):
                    return None
                    
                return user
        finally:
            conn.close()


# ==================== 依赖注入 ====================

def get_auth_service() -> AuthService:
    """获取认证服务实例"""
    return AuthService()
