"""账号与鉴权 Schema。

字段校验规则与《接口契约》第 6.2 ~ 6.10 节严格对应。
"""

import re
from typing import Optional

from pydantic import BaseModel, Field, field_validator

USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_]{4,20}$")
PHONE_PATTERN = re.compile(r"^1[3-9]\d{9}$")
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _check_password_strength(value: str) -> str:
    """密码 8~32 位且同时包含字母和数字。"""
    if not 8 <= len(value) <= 32:
        raise ValueError("密码长度需为 8~32 位")
    if not re.search(r"[A-Za-z]", value) or not re.search(r"\d", value):
        raise ValueError("密码必须同时包含字母和数字")
    return value


# ---------- 注册 ----------

class RegisterRequest(BaseModel):
    username: str = Field(..., description="用户名，4~20 位字母/数字/下划线")
    password: str = Field(..., description="密码，8~32 位含字母和数字")
    email: Optional[str] = Field(default=None, description="邮箱")
    phone: Optional[str] = Field(default=None, description="手机号")
    nickname: Optional[str] = Field(default=None, max_length=20, description="昵称，默认等于用户名")

    @field_validator("username")
    @classmethod
    def _v_username(cls, v: str) -> str:
        if not USERNAME_PATTERN.match(v):
            raise ValueError("用户名需 4~20 位字母、数字或下划线")
        return v

    @field_validator("password")
    @classmethod
    def _v_password(cls, v: str) -> str:
        return _check_password_strength(v)

    @field_validator("email")
    @classmethod
    def _v_email(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return None
        v = v.strip().lower()  # 邮箱统一小写保存
        if not EMAIL_PATTERN.match(v):
            raise ValueError("邮箱格式不正确")
        return v

    @field_validator("phone")
    @classmethod
    def _v_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return None
        v = v.strip()
        if not PHONE_PATTERN.match(v):
            raise ValueError("手机号格式不正确")
        return v


# ---------- 登录 ----------

class LoginRequest(BaseModel):
    account: str = Field(..., description="用户名 / 邮箱 / 手机号")
    password: str = Field(..., description="密码")
    device_id: Optional[str] = Field(default=None, max_length=128, description="设备标识")


# ---------- Token ----------

class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., description="刷新令牌")


class LogoutRequest(BaseModel):
    refresh_token: Optional[str] = Field(default=None, description="不传则吊销当前设备全部令牌")
    all_devices: bool = Field(default=False, description="是否吊销所有设备令牌")


class TokenData(BaseModel):
    """登录/注册/刷新的统一返回。"""

    user_id: int
    username: str
    nickname: Optional[str] = None
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int


# ---------- 个人中心 ----------

class UpdateProfileRequest(BaseModel):
    nickname: Optional[str] = Field(default=None, max_length=20)
    avatar_url: Optional[str] = Field(default=None, max_length=500)
    email: Optional[str] = None
    phone: Optional[str] = None

    @field_validator("email")
    @classmethod
    def _v_email(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return None
        v = v.strip().lower()
        if not EMAIL_PATTERN.match(v):
            raise ValueError("邮箱格式不正确")
        return v

    @field_validator("phone")
    @classmethod
    def _v_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return None
        v = v.strip()
        if not PHONE_PATTERN.match(v):
            raise ValueError("手机号格式不正确")
        return v


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., description="原密码")
    new_password: str = Field(..., description="新密码")

    @field_validator("new_password")
    @classmethod
    def _v_new_password(cls, v: str) -> str:
        return _check_password_strength(v)


class UserProfileData(BaseModel):
    user_id: int
    username: str
    nickname: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = Field(default=None, description="已脱敏")
    avatar_url: Optional[str] = None
    role: str
    status: str
    points_balance: int
    continuous_days: int = 0
    total_checkin_days: int = 0
    badge_count: int = 0
    last_login_at: Optional[str] = None
    created_at: Optional[str] = None


# ---------- 用户设置 ----------

class UserSettingData(BaseModel):
    theme_mode: str
    notification_enabled: bool
    language: str
    weather_city_code: Optional[str] = None
    updated_at: Optional[str] = None


class UpdateSettingRequest(BaseModel):
    theme_mode: str = Field(default="system", description="system/light/dark")
    notification_enabled: bool = Field(default=True)
    language: str = Field(default="zh-CN")
    weather_city_code: Optional[str] = Field(default=None, max_length=50)

    @field_validator("theme_mode")
    @classmethod
    def _v_theme(cls, v: str) -> str:
        if v not in ("system", "light", "dark"):
            raise ValueError("theme_mode 只能是 system/light/dark")
        return v
