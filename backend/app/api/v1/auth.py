"""认证路由：注册、登录、刷新、登出。

对应《接口契约》6.2 ~ 6.5。
"""

from fastapi import APIRouter, Request

from app.api.deps import CurrentUser, DbSession
from app.core.response import ApiResponse, success
from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
)
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["认证"])


def _rid(request: Request) -> str:
    return getattr(request.state, "request_id", "")


@router.post("/register", summary="注册", description="注册成功直接返回 Token，客户端无需再调登录")
def register(payload: RegisterRequest, request: Request, db: DbSession) -> ApiResponse:
    data = auth_service.register(db, payload)
    return ApiResponse.ok(data.model_dump(), request_id=_rid(request))


@router.post("/login", summary="登录", description="account 支持用户名/邮箱/手机号，服务端自动识别")
def login(payload: LoginRequest, request: Request, db: DbSession) -> ApiResponse:
    data = auth_service.login(db, payload.account, payload.password, payload.device_id)
    return ApiResponse.ok(data.model_dump(), request_id=_rid(request))


@router.post("/refresh", summary="刷新 Token", description="轮换策略：旧 refresh 立即失效")
def refresh_token(payload: RefreshRequest, request: Request, db: DbSession) -> ApiResponse:
    data = auth_service.refresh(db, payload.refresh_token)
    return ApiResponse.ok(data.model_dump(), request_id=_rid(request))


@router.post("/logout", summary="登出", description="幂等，重复调用同样返回成功")
def logout(payload: LogoutRequest, request: Request, db: DbSession, user: CurrentUser) -> ApiResponse:
    auth_service.logout(db, user, payload.refresh_token, payload.all_devices)
    return ApiResponse.ok(None, request_id=_rid(request))
