"""Schema 统一导出。"""

from app.schemas.accounting import (
    AccountingCategoryItem,
    AccountingCategoryListData,
    AccountingRecordItem,
    AccountingSummaryData,
    AccountingSummaryGroupItem,
    CreateAccountingRecordRequest,
    UpdateAccountingRecordRequest,
)
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    TokenData,
    UpdateProfileRequest,
    UpdateSettingRequest,
    UserProfileData,
    UserSettingData,
)
from app.schemas.checkin import (
    BadgeItem,
    BadgeListResponseData,
    CheckinCalendarItem,
    CheckinCalendarResponseData,
    CheckinRequest,
    CheckinResponseData,
    CheckinStatsResponseData,
    NewBadgeItem,
    PointsBalanceResponseData,
    PointTransactionItem,
)
from app.schemas.memo import (
    CreateMemoRequest,
    MemoItem,
    UpdateMemoRequest,
)
from app.schemas.sync import (
    SyncPullChangeItem,
    SyncPullResponseData,
    SyncPushChangeItem,
    SyncPushRequest,
    SyncPushResultItem,
    SyncPushResponseData,
)
from app.schemas.todo import (
    CreateTodoRequest,
    TodoItem,
    UpdateTodoRequest,
)
from app.schemas.weather import (
    CurrentWeatherOut,
    ForecastItem,
    WeatherForecastOut,
)

__all__ = [
    # 鉴权与用户
    "RegisterRequest",
    "LoginRequest",
    "RefreshRequest",
    "LogoutRequest",
    "TokenData",
    "UserProfileData",
    "UpdateProfileRequest",
    "ChangePasswordRequest",
    "UserSettingData",
    "UpdateSettingRequest",
    # 天气
    "CurrentWeatherOut",
    "ForecastItem",
    "WeatherForecastOut",
    # 打卡积分徽章
    "CheckinRequest",
    "NewBadgeItem",
    "CheckinResponseData",
    "CheckinCalendarItem",
    "CheckinCalendarResponseData",
    "CheckinStatsResponseData",
    "PointsBalanceResponseData",
    "PointTransactionItem",
    "BadgeItem",
    "BadgeListResponseData",
    # 待办
    "TodoItem",
    "CreateTodoRequest",
    "UpdateTodoRequest",
    # 备忘录
    "MemoItem",
    "CreateMemoRequest",
    "UpdateMemoRequest",
    # 记账
    "AccountingCategoryItem",
    "AccountingCategoryListData",
    "AccountingRecordItem",
    "CreateAccountingRecordRequest",
    "UpdateAccountingRecordRequest",
    "AccountingSummaryData",
    "AccountingSummaryGroupItem",
    # 同步
    "SyncPushRequest",
    "SyncPushChangeItem",
    "SyncPushResultItem",
    "SyncPushResponseData",
    "SyncPullResponseData",
    "SyncPullChangeItem",
]
