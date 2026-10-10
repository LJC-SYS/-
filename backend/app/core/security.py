"""密码哈希与 JWT 工具。

安全约定：
- 密码只保存 bcrypt 哈希，无法还原明文。
- JWT 密钥来自环境变量 JWT_SECRET_KEY，禁止硬编码。
- Refresh Token 落库存哈希，不存明文。
"""

import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import bcrypt
import jwt

from app.core.config import settings
from app.core.errors import ErrorCode
from app.core.exceptions import UnauthorizedError

TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"

# bcrypt 算法本身限制密码最长 72 字节，超出部分会被静默截断。
# 这里显式截断，避免不同实现行为不一致。
_BCRYPT_MAX_BYTES = 72


def _prepare_password(plain: str) -> bytes:
    """把明文密码转为 bcrypt 可接受的字节串。

    bcrypt 只处理前 72 字节，这里显式截断而不是依赖底层静默处理，
    保证与任何 bcrypt 版本的校验结果一致。
    """
    return plain.encode("utf-8")[:_BCRYPT_MAX_BYTES]


# ---------- 密码 ----------

def hash_password(plain: str) -> str:
    """生成密码哈希（bcrypt）。"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(_prepare_password(plain), salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """校验密码。"""
    try:
        return bcrypt.checkpw(_prepare_password(plain), hashed.encode("utf-8"))
    except Exception:
        return False


# ---------- JWT ----------

def _create_token(payload: Dict[str, Any], expires_delta: timedelta, token_type: str) -> str:
    now = datetime.now(timezone.utc)
    to_encode = {
        **payload,
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
        "jti": uuid.uuid4().hex,
    }
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_access_token(user_id: int, username: str, role: str) -> str:
    """签发 Access Token。"""
    return _create_token(
        {"sub": str(user_id), "username": username, "role": role},
        timedelta(seconds=settings.ACCESS_TOKEN_EXPIRE_SECONDS),
        TOKEN_TYPE_ACCESS,
    )


def create_refresh_token(user_id: int, username: str, role: str) -> str:
    """签发 Refresh Token。"""
    return _create_token(
        {"sub": str(user_id), "username": username, "role": role},
        timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        TOKEN_TYPE_REFRESH,
    )


def decode_token(token: str, expected_type: Optional[str] = None) -> Dict[str, Any]:
    """解析并校验 Token。

    Raises:
        UnauthorizedError: Token 过期、无效或类型不符。
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except jwt.ExpiredSignatureError:
        raise UnauthorizedError(ErrorCode.TOKEN_EXPIRED)
    except jwt.PyJWTError:
        raise UnauthorizedError(ErrorCode.TOKEN_INVALID)

    if expected_type and payload.get("type") != expected_type:
        raise UnauthorizedError(ErrorCode.TOKEN_INVALID)

    return payload


def get_token_expire_at(token_type: str) -> datetime:
    """计算 Token 的过期时间。"""
    if token_type == TOKEN_TYPE_REFRESH:
        return datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return datetime.now(timezone.utc) + timedelta(seconds=settings.ACCESS_TOKEN_EXPIRE_SECONDS)


def hash_token(token: str) -> str:
    """计算 Token 的 SHA-256 哈希，用于落库，不保存明文。"""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
