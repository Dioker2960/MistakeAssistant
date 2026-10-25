from datetime import datetime
from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    """注册请求。"""
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=6, max_length=64)


class UserLogin(BaseModel):
    """登录请求。"""
    username: str
    password: str


class UserResponse(BaseModel):
    """返回给客户端的用户信息（不含密码）。"""
    id: str
    username: str
    role: str
    created_at: datetime
    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """登录成功后返回 token。"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class PasswordChange(BaseModel):
    """改密码请求。"""
    old_password: str = Field(min_length=1)
    new_password: str = Field(min_length=6, max_length=64)
