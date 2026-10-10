"""鉴权依赖。

受保护接口通过 Depends(get_current_user) 获取当前用户。
"""

from typing import Annotated

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors import ErrorCode
from app.core.exceptions import BusinessException, ForbiddenError, UnauthorizedError
from app.core.security import TOKEN_TYPE_ACCESS, decode_token
from app.models import User


def get_token_payload(
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> dict:
    """从 Authorization 头解析 Access Token。

    格式要求：`Bearer <token>`
    """
    if not authorization:
        raise UnauthorizedError(ErrorCode.UNAUTHORIZED)

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise UnauthorizedError(ErrorCode.TOKEN_INVALID)

    return decode_token(parts[1], expected_type=TOKEN_TYPE_ACCESS)


def get_current_user(
    payload: Annotated[dict, Depends(get_token_payload)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """获取当前登录用户。

    同时校验账号状态，禁用或注销账号直接拒绝。
    """
    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedError(ErrorCode.TOKEN_INVALID)

    user = db.get(User, int(user_id))
    if user is None:
        raise UnauthorizedError(ErrorCode.TOKEN_INVALID)

    if user.status == "disabled":
        raise BusinessException(ErrorCode.ACCOUNT_DISABLED)
    if user.status == "deleted":
        raise BusinessException(ErrorCode.ACCOUNT_DELETED)

    return user


def get_current_admin(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    """获取当前管理员，非管理员拒绝。"""
    if not user.is_admin:
        raise ForbiddenError(f"{ErrorCode.ADMIN_ONLY}")
    return user


# 类型别名，供路由签名简洁使用
CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentAdmin = Annotated[User, Depends(get_current_admin)]
DbSession = Annotated[Session, Depends(get_db)]
