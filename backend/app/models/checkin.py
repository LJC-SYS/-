"""打卡、积分与徽章模型。

对应《数据库表设计》3.3 ~ 3.6。
"""

from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, PkMixin, TimestampMixin


class CheckinRecord(Base, PkMixin):
    """每日打卡记录表。"""

    __tablename__ = "checkin_records"

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="关联 users.id"
    )
    checkin_date: Mapped[date] = mapped_column(Date, nullable=False, comment="按业务时区计算的打卡日期")
    checkin_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, comment="实际打卡时间")
    points_earned: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0", comment="本次获得积分")
    continuous_days: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1", comment="本次打卡后的连续天数")
    remark: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="备注或活动说明")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, comment="创建时间")

    __table_args__ = (
        # 同一用户同一天只能打卡一次，这是防重复打卡的数据库级保障
        UniqueConstraint("user_id", "checkin_date", name="uq_checkin_user_date"),
        Index("ix_checkin_user_date_desc", "user_id", "checkin_date"),
        {"comment": "打卡记录表"},
    )


class PointTransaction(Base, PkMixin):
    """积分流水表。"""

    __tablename__ = "point_transactions"

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="关联 users.id"
    )
    change_amount: Mapped[int] = mapped_column(Integer, nullable=False, comment="正数增加，负数扣减")
    balance_after: Mapped[int] = mapped_column(Integer, nullable=False, comment="变更后的余额")
    transaction_type: Mapped[str] = mapped_column(String(30), nullable=False, comment="checkin/reward/admin_adjust 等")
    source_type: Mapped[str | None] = mapped_column(String(30), nullable=True, comment="来源业务类型")
    source_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="来源业务记录 ID")
    description: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="积分变动说明")
    operator_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="后台调整时的管理员 ID")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, comment="创建时间")

    __table_args__ = (
        Index("ix_point_tx_user_created", "user_id", "created_at"),
        # 防止同一来源重复发积分（如重复打卡奖励）
        UniqueConstraint(
            "source_type", "source_id", "transaction_type",
            name="uq_point_tx_source",
        ),
        {"comment": "积分流水表"},
    )


class Badge(Base, PkMixin, TimestampMixin):
    """徽章定义表。"""

    __tablename__ = "badges"

    code: Mapped[str] = mapped_column(String(50), nullable=False, comment="稳定的徽章业务编码")
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="徽章名称")
    description: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="徽章说明")
    icon_url: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="徽章图标地址")
    rule_type: Mapped[str] = mapped_column(String(50), nullable=False, comment="如 continuous_checkin/total_checkin")
    rule_value: Mapped[int] = mapped_column(Integer, nullable=False, comment="达成规则所需数值")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active", server_default="active", comment="active/inactive")

    __table_args__ = (
        UniqueConstraint("code", name="uq_badges_code"),
        {"comment": "徽章定义表"},
    )


class UserBadge(Base, PkMixin):
    """用户徽章获得关系表。"""

    __tablename__ = "user_badges"

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="关联 users.id"
    )
    badge_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("badges.id", ondelete="CASCADE"), nullable=False, comment="关联 badges.id"
    )
    source_type: Mapped[str | None] = mapped_column(String(30), nullable=True, comment="发放来源")
    source_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="来源记录 ID")
    earned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, comment="获得时间")

    __table_args__ = (
        # 同一徽章不重复发放
        UniqueConstraint("user_id", "badge_id", name="uq_user_badge"),
        Index("ix_user_badges_badge_id", "badge_id"),
        {"comment": "用户徽章表"},
    )
