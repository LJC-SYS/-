"""打卡路由。

对应《接口契约》6.13（打卡）、6.14（打卡日历）与 6.15（打卡统计）。
属于成员 2 核心职责模块。
"""

from fastapi import APIRouter, Query, Request

from app.api.deps import CurrentUser, DbSession
from app.core.response import ApiResponse
from app.schemas.checkin import (
    CheckinCalendarResponseData,
    CheckinRequest,
    CheckinResponseData,
    CheckinStatsResponseData,
)
from app.services.checkin_service import checkin_service

router = APIRouter(prefix="/checkins", tags=["打卡"])


def _rid(request: Request) -> str:
    """提取统一请求 ID。"""
    return getattr(request.state, "request_id", "")


@router.post(
    "",
    summary="用户打卡",
    description=(
        "每日打卡接口。\n\n"
        "- 服务端自主以 Asia/Shanghai 时区计算打卡日期与连续天数。\n"
        "- 每日打卡奖励 10 积分，5 步事务原子落库。\n"
        "- 自动判定并解锁达成徽章（如坚持一周等）。\n"
        "- 支持 client_id 幂等防重放，同 client_id 重复提交返回已有记录。"
    ),
    response_model=ApiResponse[CheckinResponseData],
)
def create_checkin(
    request: Request,
    payload: CheckinRequest,
    db: DbSession,
    current_user: CurrentUser,
) -> ApiResponse:
    """执行每日打卡。"""
    data = checkin_service.do_checkin(
        db=db,
        user=current_user,
        client_id=payload.client_id,
        remark=payload.remark,
    )
    return ApiResponse.ok(data, request_id=_rid(request))


@router.get(
    "/calendar",
    summary="打卡日历",
    description=(
        "按年月查询打卡日历与记录明细。\n\n"
        "- checkin_days 列表专为日历组件设计，包含当月已打卡的所有天数序号（如 [1, 2, 3, 5]）。\n"
        "- 返回当月打卡总天数与打卡记录明细。"
    ),
    response_model=ApiResponse[CheckinCalendarResponseData],
)
def get_checkin_calendar(
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
    year: int = Query(..., description="年份，例如 2026"),
    month: int = Query(..., ge=1, le=12, description="月份，1~12"),
) -> ApiResponse:
    """获取打卡日历。"""
    data = checkin_service.get_calendar(
        db=db,
        user=current_user,
        year=year,
        month=month,
    )
    return ApiResponse.ok(data, request_id=_rid(request))


@router.get(
    "/stats",
    summary="打卡统计",
    description=(
        "获取用户打卡统计概览。\n\n"
        "- 包含当前连续打卡天数、历史最长连续天数、累计打卡天数、当月打卡天数。\n"
        "- 返回 today_checked 标识，供客户端直接控制打卡按钮状态。"
    ),
    response_model=ApiResponse[CheckinStatsResponseData],
)
def get_checkin_stats(
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
) -> ApiResponse:
    """获取打卡统计。"""
    data = checkin_service.get_stats(db=db, user=current_user)
    return ApiResponse.ok(data, request_id=_rid(request))
