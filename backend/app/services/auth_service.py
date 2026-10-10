"""账号与鉴权服务层。

业务逻辑集中在此，路由层只做参数接收与响应包装。
"""

import logging
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import ErrorCode
from app.core.exceptions import BusinessException, UnauthorizedError
from app.core.security import (
    TOKEN_TYPE_REFRESH,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_token_expire_at,
    hash_password,
    hash_token,
    verify_password,
)
from app.models import User, UserSetting
from app.models.user import RefreshToken
from app.schemas.auth import RegisterRequest, TokenData

logger = logging.getLogger(__name__)


# ---------- 内部工具 ----------

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _find_user_by_account(db: Session, account: str) -> User | None:
    """按用户名/邮箱/手机号三选一识别用户。

    识别规则：
        含 @        -> 邮箱
        纯 11 位数字 -> 手机号
        其他        -> 用户名
    """
    account = account.strip()

    if "@" in account:
        stmt = select(User).where(func.lower(User.email) == account.lower())
    elif account.isdigit() and len(account) == 11:
        stmt = select(User).where(User.phone == account)
    else:
        stmt = select(User).where(User.username == account)

    return db.execute(stmt).scalar_one_or_none()


def _issue_tokens(db: Session, user: User, device_id: str | None = None) -> TokenData:
    """签发 access + refresh，并把 refresh 哈希落库。"""
    access_token = create_access_token(user.id, user.username, user.role)
    refresh_token = create_refresh_token(user.id, user.username, user.role)

    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_token(refresh_token),
            device_id=device_id,
            expires_at=get_token_expire_at(TOKEN_TYPE_REFRESH),
            created_at=_now(),
        )
    )
    db.commit()

    return TokenData(
        user_id=user.id,
        username=user.username,
        nickname=user.nickname,
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="Bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_SECONDS,
    )


# ---------- 注册 ----------

def register(db: Session, payload: RegisterRequest) -> TokenData:
    """用户注册。

    注册成功直接返回 Token，客户端无需再调登录。
    """
    # email 与 phone 至少填一项
    if not payload.email and not payload.phone:
        raise BusinessException(ErrorCode.PARAM_INVALID, "邮箱和手机号至少填写一项")

    # 唯一性校验
    if db.execute(select(User.id).where(User.username == payload.username)).first():
        raise BusinessException(ErrorCode.USERNAME_EXISTS)
    if payload.email and db.execute(
        select(User.id).where(func.lower(User.email) == payload.email.lower())
    ).first():
        raise BusinessException(ErrorCode.EMAIL_EXISTS)
    if payload.phone and db.execute(
        select(User.id).where(User.phone == payload.phone)
    ).first():
        raise BusinessException(ErrorCode.PHONE_EXISTS)

    user = User(
        username=payload.username,
        email=payload.email,
        phone=payload.phone,
        password_hash=hash_password(payload.password),
        nickname=payload.nickname or payload.username,
        role="user",
        status="active",
        points_balance=0,
        last_login_at=_now(),
    )
    db.add(user)
    db.flush()  # 取 user.id

    # 同步创建默认设置
    db.add(UserSetting(user_id=user.id))

    db.commit()
    db.refresh(user)

    logger.info("[register] user_id=%s username=%s", user.id, user.username)
    return _issue_tokens(db, user)


# ---------- 登录 ----------

def login(db: Session, account: str, password: str, device_id: str | None = None) -> TokenData:
    """用户登录。"""
    user = _find_user_by_account(db, account)

    # 账号不存在与密码错误对外统一提示，避免账号枚举
    if user is None:
        logger.info("[login] account not found: %s", account)
        raise BusinessException(ErrorCode.PASSWORD_WRONG)

    if not verify_password(password, user.password_hash):
        logger.info("[login] password wrong: user_id=%s", user.id)
        raise BusinessException(ErrorCode.PASSWORD_WRONG)

    if user.status == "disabled":
        raise BusinessException(ErrorCode.ACCOUNT_DISABLED)
    if user.status == "deleted":
        raise BusinessException(ErrorCode.ACCOUNT_DELETED)

    user.last_login_at = _now()
    db.commit()

    logger.info("[login] success user_id=%s", user.id)
    return _issue_tokens(db, user, device_id)


# ---------- 刷新 ----------

def refresh(db: Session, refresh_token: str, device_id: str | None = None) -> TokenData:
    """刷新令牌（轮换策略）。

    旧 refresh 立即吊销。若检测到已吊销的 refresh 被复用，
    吊销该用户全部令牌并拒绝（防盗用）。
    """
    payload = decode_token(refresh_token, expected_type=TOKEN_TYPE_REFRESH)
    user_id = int(payload["sub"])

    token_hash = hash_token(refresh_token)
    record = db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    ).scalar_one_or_none()

    if record is None:
        raise BusinessException(ErrorCode.REFRESH_TOKEN_INVALID)

    # 已吊销 => 疑似令牌盗用，全部吊销
    if record.revoked_at is not None:
        logger.warning("[refresh] reused revoked token, revoke all. user_id=%s", user_id)
        _revoke_all(db, user_id)
        raise BusinessException(ErrorCode.REFRESH_TOKEN_INVALID)

    if record.expires_at.replace(tzinfo=timezone.utc) < _now():
        raise BusinessException(ErrorCode.REFRESH_TOKEN_EXPIRED)

    user = db.get(User, user_id)
    if user is None:
        raise BusinessException(ErrorCode.REFRESH_TOKEN_INVALID)
    if user.status == "disabled":
        raise BusinessException(ErrorCode.ACCOUNT_DISABLED)
    if user.status == "deleted":
        raise BusinessException(ErrorCode.ACCOUNT_DELETED)

    # 吊销旧令牌（轮换）
    record.revoked_at = _now()
    db.commit()

    return _issue_tokens(db, user, device_id or record.device_id)


# ---------- 登出 ----------

def logout(
    db: Session,
    user: User,
    refresh_token: str | None = None,
    all_devices: bool = False,
) -> None:
    """登出。幂等，重复调用同样成功。"""
    if all_devices:
        _revoke_all(db, user.id)
        return

    if refresh_token:
        record = db.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == hash_token(refresh_token),
                RefreshToken.user_id == user.id,
            )
        ).scalar_one_or_none()
        if record and record.revoked_at is None:
            record.revoked_at = _now()
    else:
        # 未传 refresh_token 时，吊销该用户全部未吊销令牌
        _revoke_all(db, user.id)

    db.commit()


def _revoke_all(db: Session, user_id: int) -> None:
    """吊销该用户全部未吊销的 refresh token。"""
    now = _now()
    records = db.execute(
        select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None),
        )
    ).scalars().all()
    for r in records:
        r.revoked_at = now


# ---------- 个人中心 ----------

def update_profile(db: Session, user: User, payload) -> User:
    """修改个人资料，字段为 None 表示不修改。"""
    data = payload.model_dump(exclude_unset=True)

    if "nickname" in data and data["nickname"]:
        user.nickname = data["nickname"]

    if "avatar_url" in data:
        user.avatar_url = data["avatar_url"]

    if data.get("email") and data["email"] != user.email:
        exists = db.execute(
            select(User.id).where(
                func.lower(User.email) == data["email"].lower(),
                User.id != user.id,
            )
        ).first()
        if exists:
            raise BusinessException(ErrorCode.EMAIL_EXISTS)
        user.email = data["email"]

    if data.get("phone") and data["phone"] != user.phone:
        exists = db.execute(
            select(User.id).where(User.phone == data["phone"], User.id != user.id)
        ).first()
        if exists:
            raise BusinessException(ErrorCode.PHONE_EXISTS)
        user.phone = data["phone"]

    db.commit()
    db.refresh(user)
    return user


def change_password(db: Session, user: User, old_password: str, new_password: str) -> None:
    """修改密码，成功后吊销全部令牌（强制其它设备重新登录）。"""
    if not verify_password(old_password, user.password_hash):
        raise BusinessException(ErrorCode.OLD_PASSWORD_WRONG)

    user.password_hash = hash_password(new_password)
    _revoke_all(db, user.id)
    db.commit()

    logger.info("[change_password] user_id=%s", user.id)


# ---------- 用户设置 ----------

def get_or_create_setting(db: Session, user: User) -> UserSetting:
    """获取用户设置，无记录时返回默认（不落库，读取不产生副作用）。"""
    setting = db.execute(
        select(UserSetting).where(UserSetting.user_id == user.id)
    ).scalar_one_or_none()

    if setting is None:
        setting = UserSetting(
            user_id=user.id,
            theme_mode="system",
            notification_enabled=True,
            language="zh-CN",
            weather_city_code=None,
        )
    return setting


def update_setting(db: Session, user: User, payload) -> UserSetting:
    """全量更新用户设置。"""
    setting = db.execute(
        select(UserSetting).where(UserSetting.user_id == user.id)
    ).scalar_one_or_none()

    if setting is None:
        setting = UserSetting(user_id=user.id)
        db.add(setting)

    setting.theme_mode = payload.theme_mode
    setting.notification_enabled = payload.notification_enabled
    setting.language = payload.language
    setting.weather_city_code = payload.weather_city_code

    db.commit()
    db.refresh(setting)
    return setting
