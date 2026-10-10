"""用户账号、设置与令牌模型。

对应《数据库表设计》3.1 / 3.2 与扩展表 4.1。
"""

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, PkMixin, TimestampMixin


class User(Base, PkMixin, TimestampMixin):
    """用户表。"""

    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(50), nullable=False, comment="登录名")
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="邮箱")
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True, comment="手机号")
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False, comment="密码哈希")
    nickname: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="昵称")
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="头像地址")
    role: Mapped[str] = mapped_column(String(30), nullable=False, default="user", server_default="user", comment="角色")
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active", server_default="active", comment="状态")
    points_balance: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0, server_default="0", comment="当前积分余额")
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, comment="最后登录时间")

    setting: Mapped["UserSetting | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    tokens: Mapped[list["RefreshToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("username", name="uq_users_username"),
        UniqueConstraint("email", name="uq_users_email"),
        UniqueConstraint("phone", name="uq_users_phone"),
        Index("ix_users_role", "role"),
        Index("ix_users_status", "status"),
        {"comment": "用户表"},
    )

    # ---------- 便捷属性 ----------

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def is_active(self) -> bool:
        return self.status == "active"

    @property
    def masked_phone(self) -> str | None:
        """手机号脱敏：138****8000"""
        if not self.phone or len(self.phone) < 7:
            return self.phone
        return f"{self.phone[:3]}****{self.phone[-4:]}"


class UserSetting(Base, PkMixin, TimestampMixin):
    """用户设置表，一个用户一条。"""

    __tablename__ = "user_settings"

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="关联 users.id"
    )
    theme_mode: Mapped[str] = mapped_column(String(20), nullable=False, default="system", server_default="system", comment="主题模式")
    notification_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true", comment="是否允许通知")
    language: Mapped[str] = mapped_column(String(20), nullable=False, default="zh-CN", server_default="zh-CN", comment="语言偏好")
    weather_city_code: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="默认天气城市编码")

    user: Mapped["User"] = relationship(back_populates="setting")

    __table_args__ = (
        UniqueConstraint("user_id", name="uq_user_settings_user_id"),
        {"comment": "用户设置表"},
    )


class RefreshToken(Base, PkMixin):
    """刷新令牌表，支持轮换、主动退出与吊销。"""

    __tablename__ = "refresh_tokens"

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="关联 users.id"
    )
    token_hash: Mapped[str] = mapped_column(String(128), nullable=False, comment="令牌哈希，不存明文")
    device_id: Mapped[str | None] = mapped_column(String(128), nullable=True, comment="设备标识")
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, comment="过期时间")
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, comment="吊销时间")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, comment="创建时间")

    user: Mapped["User"] = relationship(back_populates="tokens")

    __table_args__ = (
        Index("ix_refresh_tokens_token_hash", "token_hash", unique=True),
        Index("ix_refresh_tokens_user_id", "user_id"),
        {"comment": "刷新令牌表"},
    )
