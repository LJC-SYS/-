"""打卡、积分与徽章 Schema。

严格对应《接口契约》第 6.13 ~ 6.18 节。
"""

from typing import List, Optional
from pydantic import BaseModel, Field


# ---------- 打卡 ----------

class CheckinRequest(BaseModel):
    """打卡请求体。"""

    client_id: Optional[str] = Field(default=None, description="幂等标识(UUID)，防重复提交")
    remark: Optional[str] = Field(default=None, max_length=255, description="备注，≤255字")


class NewBadgeItem(BaseModel):
    """新获得徽章项。"""

    code: str = Field(..., description="徽章编码")
    name: str = Field(..., description="徽章名称")
    icon_url: Optional[str] = Field(default=None, description="图标地址")


class CheckinResponseData(BaseModel):
    """打卡成功出参。"""

    checkin_id: int = Field(..., description="打卡记录ID")
    checkin_date: str = Field(..., description="打卡日期 YYYY-MM-DD")
    checkin_time: str = Field(..., description="打卡时间 ISO 8601")
    points_earned: int = Field(..., description="本次获得积分")
    continuous_days: int = Field(..., description="连续打卡天数")
    points_balance: int = Field(..., description="最新积分余额")
    new_badges: List[NewBadgeItem] = Field(default=[], description="本次新获得的徽章列表")


class CheckinCalendarItem(BaseModel):
    """日历中的单条打卡明细。"""

    checkin_date: str
    checkin_time: str
    points_earned: int
    continuous_days: int
    remark: Optional[str] = None


class CheckinCalendarResponseData(BaseModel):
    """打卡日历出参。"""

    year: int = Field(..., description="年份")
    month: int = Field(..., description="月份 1~12")
    checkin_days: List[int] = Field(..., description="当月已打卡日期列表，用于日历高亮")
    month_total: int = Field(..., description="当月打卡总天数")
    list: List[CheckinCalendarItem] = Field(..., description="打卡记录明细")


class CheckinStatsResponseData(BaseModel):
    """打卡统计出参。"""

    continuous_days: int = Field(..., description="当前连续打卡天数")
    max_continuous_days: int = Field(..., description="历史最长连续打卡天数")
    total_checkin_days: int = Field(..., description="累计打卡总天数")
    current_month_days: int = Field(..., description="当月打卡天数")
    last_checkin_date: Optional[str] = Field(default=None, description="最近打卡日期")
    today_checked: bool = Field(..., description="今日是否已打卡")


# ---------- 积分 ----------

class PointsBalanceResponseData(BaseModel):
    """积分余额出参。"""

    points_balance: int = Field(..., description="当前积分余额")
    today_earned: int = Field(..., description="今日已获得积分")
    total_earned: int = Field(..., description="累计已获得积分")


class PointTransactionItem(BaseModel):
    """单条积分流水项。"""

    id: int = Field(..., description="流水ID")
    change_amount: int = Field(..., description="变动额度")
    balance_after: int = Field(..., description="变动后余额")
    transaction_type: str = Field(..., description="变动类型")
    description: Optional[str] = Field(default=None, description="变动描述")
    created_at: str = Field(..., description="创建时间 ISO 8601")


# ---------- 徽章 ----------

class BadgeItem(BaseModel):
    """徽章信息项。"""

    code: str = Field(..., description="徽章唯一编码")
    name: str = Field(..., description="徽章名称")
    description: Optional[str] = Field(default=None, description="徽章描述")
    icon_url: Optional[str] = Field(default=None, description="图标地址")
    rule_type: str = Field(..., description="规则类型")
    rule_value: int = Field(..., description="达标数值")
    earned: bool = Field(..., description="当前用户是否已获得")
    earned_at: Optional[str] = Field(default=None, description="获得时间 ISO 8601")


class BadgeListResponseData(BaseModel):
    """徽章列表出参。"""

    earned_count: int = Field(..., description="已解锁徽章数")
    total_count: int = Field(..., description="徽章总数")
    list: List[BadgeItem] = Field(..., description="全部徽章列表")
