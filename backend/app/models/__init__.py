"""模型统一导出。

Alembic 迁移与应用启动都从这里导入，确保所有模型被注册到 Base.metadata。
"""

from app.models.base import Base, PkMixin, SoftDeleteMixin, TimestampMixin, VersionMixin
from app.models.checkin import (
    Badge,
    CheckinRecord,
    PointTransaction,
    UserBadge,
)
from app.models.sync import (
    AccountingCategory,
    AccountingRecord,
    ContentItem,
    Memo,
    Todo,
    WeatherCache,
)
from app.models.user import RefreshToken, User, UserSetting

__all__ = [
    # 基类与混入
    "Base",
    "PkMixin",
    "TimestampMixin",
    "VersionMixin",
    "SoftDeleteMixin",
    # 用户
    "User",
    "UserSetting",
    "RefreshToken",
    # 打卡积分
    "CheckinRecord",
    "PointTransaction",
    "Badge",
    "UserBadge",
    # 同步业务
    "Todo",
    "Memo",
    "AccountingCategory",
    "AccountingRecord",
    "ContentItem",
    "WeatherCache",
]
