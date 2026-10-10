"""用户路由：个人资料与用户设置。

对应《接口契约》6.6 ~ 6.10。
"""

from datetime import date, timedelta

from fastapi import APIRouter, Request
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DbSession
from app.core.response import ApiResponse
from app.models import Badge, CheckinRecord, UserBadge
from app.schemas.auth import (
    ChangePasswordRequest,
    UpdateProfileRequest,
    UpdateSettingRequest,
    UserProfileData,
)
from app.services import auth_service

router = APIRouter(prefix="/users", tags=["个人中心"])


def _rid(request: Request) -> str:
    return getattr(request.state, "request_id", "")


def _compute_checkin_stats(db, user_id: int) -> dict:
    """计算连续天数、累计天数、徽章数。

    说明：这些数据由成员 2 的打卡积分模块提供，此处按契约要求聚合返回。
    当前实现直接查询，成员 2 完成后可改为调用其服务层，避免重复逻辑。
    """
    total_days = db.execute(
        select(func.count(CheckinRecord.id)).where(CheckinRecord.user_id == user_id)
    ).scalar_one()

    badge_count = db.execute(
        select(func.count(UserBadge.id)).where(UserBadge.user_id == user_id)
    ).scalar_one()

    # 连续天数：查询近 400 天记录，从今天（或昨天）向前推
    rows = db.execute(
        select(CheckinRecord.checkin_date)
        .where(CheckinRecord.user_id == user_id)
        .order_by(CheckinRecord.checkin_date.desc())
        .limit(400)
    ).scalars().all()

    dates = set(rows)
    today = date.today()
    # 若今天未打卡，从昨天开始算连续
    cursor = today if today in dates else today - timedelta(days=1)
    continuous = 0
    while cursor in dates:
        continuous += 1
        cursor -= timedelta(days=1)

    return {
        "continuous_days": continuous,
        "total_checkin_days": int(total_days),
        "badge_count": int(badge_count),
    }


@router.get("/me", summary="获取个人资料", response_model=ApiResponse)
def get_me(request: Request, db: DbSession, user: CurrentUser) -> ApiResponse:
    stats = _compute_checkin_stats(db, user.id)

    data = UserProfileData(
        user_id=user.id,
        username=user.username,
        nickname=user.nickname,
        email=user.email,
        phone=user.masked_phone,
        avatar_url=user.avatar_url,
        role=user.role,
        status=user.status,
        points_balance=user.points_balance,
        continuous_days=stats["continuous_days"],
        total_checkin_days=stats["total_checkin_days"],
        badge_count=stats["badge_count"],
        last_login_at=user.last_login_at.isoformat() if user.last_login_at else None,
        created_at=user.created_at.isoformat() if user.created_at else None,
    )
    return ApiResponse.ok(data.model_dump(), request_id=_rid(request))


@router.patch("/me", summary="修改个人资料", response_model=ApiResponse)
def update_me(payload: UpdateProfileRequest, request: Request, db: DbSession, user: CurrentUser) -> ApiResponse:
    updated = auth_service.update_profile(db, user, payload)
    stats = _compute_checkin_stats(db, updated.id)

    data = UserProfileData(
        user_id=updated.id,
        username=updated.username,
        nickname=updated.nickname,
        email=updated.email,
        phone=updated.masked_phone,
        avatar_url=updated.avatar_url,
        role=updated.role,
        status=updated.status,
        points_balance=updated.points_balance,
        continuous_days=stats["continuous_days"],
        total_checkin_days=stats["total_checkin_days"],
        badge_count=stats["badge_count"],
        last_login_at=updated.last_login_at.isoformat() if updated.last_login_at else None,
        created_at=updated.created_at.isoformat() if updated.created_at else None,
    )
    return ApiResponse.ok(data.model_dump(), request_id=_rid(request))


@router.post("/me/password", summary="修改密码", description="改密成功后吊销全部令牌")
def change_password(payload: ChangePasswordRequest, request: Request, db: DbSession, user: CurrentUser) -> ApiResponse:
    auth_service.change_password(db, user, payload.old_password, payload.new_password)
    return ApiResponse.ok(None, request_id=_rid(request))


@router.get("/me/settings", summary="获取用户设置", description="无记录时返回默认值，不报错")
def get_settings(request: Request, db: DbSession, user: CurrentUser) -> ApiResponse:
    setting = auth_service.get_or_create_setting(db, user)
    return ApiResponse.ok(
        {
            "theme_mode": setting.theme_mode,
            "notification_enabled": setting.notification_enabled,
            "language": setting.language,
            "weather_city_code": setting.weather_city_code,
            "updated_at": setting.updated_at.isoformat() if setting.updated_at else None,
        },
        request_id=_rid(request),
    )


@router.put("/me/settings", summary="更新用户设置")
def update_settings(payload: UpdateSettingRequest, request: Request, db: DbSession, user: CurrentUser) -> ApiResponse:
    setting = auth_service.update_setting(db, user, payload)
    return ApiResponse.ok(
        {
            "theme_mode": setting.theme_mode,
            "notification_enabled": setting.notification_enabled,
            "language": setting.language,
            "weather_city_code": setting.weather_city_code,
            "updated_at": setting.updated_at.isoformat() if setting.updated_at else None,
        },
        request_id=_rid(request),
    )
