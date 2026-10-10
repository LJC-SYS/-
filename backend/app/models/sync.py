"""待办、备忘录、记账与内容管理模型。

对应《数据库表设计》3.7 ~ 3.12。
待办、备忘录、记账三张表含 client_id / version / deleted_at，支持离线同步。
"""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, PkMixin, SoftDeleteMixin, TimestampMixin, VersionMixin


class Todo(Base, PkMixin, TimestampMixin, VersionMixin, SoftDeleteMixin):
    """待办事项表。"""

    __tablename__ = "todos"

    client_id: Mapped[str] = mapped_column(String(36), nullable=False, comment="客户端生成的稳定标识，用于离线新增")
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="关联 users.id"
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False, comment="标题")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="详细内容")
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="normal", server_default="normal", comment="low/normal/high")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", server_default="pending", comment="pending/completed/cancelled")
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, comment="截止时间")
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, comment="完成时间")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0", comment="用户自定义排序")

    __table_args__ = (
        UniqueConstraint("user_id", "client_id", name="uq_todos_user_client"),
        Index("ix_todos_user_status_due", "user_id", "status", "due_at"),
        Index("ix_todos_user_updated", "user_id", "updated_at"),
        {"comment": "待办事项表"},
    )


class Memo(Base, PkMixin, TimestampMixin, VersionMixin, SoftDeleteMixin):
    """备忘录表。"""

    __tablename__ = "memos"

    client_id: Mapped[str] = mapped_column(String(36), nullable=False, comment="客户端稳定标识")
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="关联 users.id"
    )
    title: Mapped[str | None] = mapped_column(String(200), nullable=True, comment="标题")
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="正文")
    is_pinned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false", comment="是否置顶")
    color: Mapped[str | None] = mapped_column(String(30), nullable=True, comment="客户端展示颜色标识")

    __table_args__ = (
        UniqueConstraint("user_id", "client_id", name="uq_memos_user_client"),
        Index("ix_memos_user_pinned_updated", "user_id", "is_pinned", "updated_at"),
        {"comment": "备忘录表"},
    )


class AccountingCategory(Base, PkMixin, TimestampMixin):
    """记账分类表。user_id 为 NULL 表示系统默认分类。"""

    __tablename__ = "accounting_categories"

    user_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, comment="NULL 表示系统默认分类"
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False, comment="分类名称")
    category_type: Mapped[str] = mapped_column(String(20), nullable=False, comment="income 或 expense")
    icon: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="图标标识或地址")
    color: Mapped[str | None] = mapped_column(String(30), nullable=True, comment="展示颜色")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0", comment="排序值")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active", server_default="active", comment="active/inactive")

    __table_args__ = (
        # 同一用户下同类目下名称不重复（含系统分类 user_id 为 NULL 的情况）
        UniqueConstraint("user_id", "name", "category_type", name="uq_acc_category_user_name_type"),
        Index("ix_acc_category_user_type", "user_id", "category_type"),
        {"comment": "记账分类表"},
    )


class AccountingRecord(Base, PkMixin, TimestampMixin, VersionMixin, SoftDeleteMixin):
    """记账记录表。"""

    __tablename__ = "accounting_records"

    client_id: Mapped[str] = mapped_column(String(36), nullable=False, comment="客户端稳定标识")
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="关联 users.id"
    )
    category_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("accounting_categories.id"), nullable=False, comment="关联 accounting_categories.id"
    )
    record_type: Mapped[str] = mapped_column(String(20), nullable=False, comment="income 或 expense")
    # 金额使用 NUMERIC，禁止浮点
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, comment="金额，必须大于 0")
    record_date: Mapped[date] = mapped_column(Date, nullable=False, comment="记账所属日期")
    note: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="备注")

    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_acc_record_amount_positive"),
        UniqueConstraint("user_id", "client_id", name="uq_acc_record_user_client"),
        Index("ix_acc_record_user_date", "user_id", "record_date"),
        Index("ix_acc_record_user_category_date", "user_id", "category_id", "record_date"),
        {"comment": "记账记录表"},
    )


class ContentItem(Base, PkMixin, TimestampMixin):
    """内容管理表，管理后台维护的公告、帮助等。"""

    __tablename__ = "content_items"

    title: Mapped[str] = mapped_column(String(200), nullable=False, comment="标题")
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="正文")
    content_type: Mapped[str] = mapped_column(String(30), nullable=False, comment="announcement/help/banner 等")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft", server_default="draft", comment="draft/published/offline")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0", comment="展示顺序")
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, comment="发布时间")
    created_by: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False, comment="关联管理员 users.id"
    )

    __table_args__ = (
        Index("ix_content_type_status_sort", "content_type", "status", "sort_order"),
        {"comment": "内容管理表"},
    )


class WeatherCache(Base, PkMixin, TimestampMixin):
    """天气缓存表。

    第一版使用 PostgreSQL 缓存，不引入 Redis。
    第三方不可用且有缓存时返回缓存并标记 degraded。
    """

    __tablename__ = "weather_cache"

    provider: Mapped[str] = mapped_column(String(50), nullable=False, comment="第三方天气服务名称")
    location_code: Mapped[str] = mapped_column(String(100), nullable=False, comment="第三方位置编码")
    location_name: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="展示名称")
    weather_type: Mapped[str] = mapped_column(String(30), nullable=False, default="current", server_default="current", comment="current/forecast")
    temperature: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True, comment="温度")
    humidity: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="湿度百分比")
    wind_info: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="风向风力说明")
    # 第三方完整响应快照，便于字段扩展
    raw_data: Mapped[str] = mapped_column(Text, nullable=False, comment="第三方完整响应 JSON")
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, comment="获取时间")
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, comment="缓存失效时间")

    __table_args__ = (
        UniqueConstraint("provider", "location_code", "weather_type", name="uq_weather_cache_key"),
        Index("ix_weather_cache_expires", "expires_at"),
        {"comment": "天气缓存表"},
    )
