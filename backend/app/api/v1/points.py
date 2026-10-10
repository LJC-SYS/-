"""积分路由。

对应《接口契约》6.16（积分余额）与 6.17（积分流水）。
属于成员 2 核心职责模块。
"""

from typing import Optional

from fastapi import APIRouter, Query, Request

from app.api.deps import CurrentUser, DbSession
from app.core.response import ApiResponse, PageData
from app.schemas.checkin import PointsBalanceResponseData, PointTransactionItem
from app.services.checkin_service import checkin_service

router = APIRouter(prefix="/points", tags=["积分"])


def _rid(request: Request) -> str:
    """提取统一请求 ID。"""
    return getattr(request.state, "request_id", "")


@router.get(
    "/balance",
    summary="积分余额",
    description="查询当前用户的积分余额、今日获得积分及历史累计总获得积分。",
    response_model=ApiResponse[PointsBalanceResponseData],
)
def get_points_balance(
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
) -> ApiResponse:
    """获取积分余额与汇总。"""
    data = checkin_service.get_points_balance(db=db, user=current_user)
    return ApiResponse.ok(data, request_id=_rid(request))


@router.get(
    "/transactions",
    summary="积分流水",
    description=(
        "分页获取用户积分变动历史明细。\n\n"
        "- 统一采用标准分页响应结构 PageData。\n"
        "- 支持按 transaction_type 筛选。"
    ),
    response_model=ApiResponse[PageData[PointTransactionItem]],
)
def get_point_transactions(
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
    page: int = Query(default=1, ge=1, description="页码，从 1 开始"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页条数，1~100"),
    transaction_type: Optional[str] = Query(default=None, description="变动类型，如 checkin"),
) -> ApiResponse:
    """分页获取积分流水。"""
    page_data = checkin_service.get_point_transactions(
        db=db,
        user=current_user,
        page=page,
        page_size=page_size,
        transaction_type=transaction_type,
    )
    return ApiResponse.ok(page_data, request_id=_rid(request))
