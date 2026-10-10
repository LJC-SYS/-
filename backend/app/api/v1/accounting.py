"""记账本 API 路由。

对应《接口契约》7.3。
包含记账分类、记账明细列表、新增记账、修改记账、删除记账、收支月度/区间汇总。
"""

from datetime import date
from typing import Optional
from fastapi import APIRouter, Path, Query, Request

from app.api.deps import CurrentUser, DbSession
from app.core.response import ApiResponse, PageData
from app.schemas.accounting import (
    AccountingCategoryListData,
    AccountingRecordItem,
    AccountingSummaryData,
    CreateAccountingRecordRequest,
    UpdateAccountingRecordRequest,
)
from app.services.accounting_service import accounting_service

router = APIRouter(prefix="/accounting", tags=["记账本"])


def _rid(request: Request) -> str:
    return getattr(request.state, "request_id", "")


@router.get(
    "/categories",
    summary="记账分类",
    description="获取系统默认分类及当前用户的自定义分类合集。",
    response_model=ApiResponse[AccountingCategoryListData],
)
def list_categories(
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
    category_type: Optional[str] = Query(None, description="分类类型筛选: income/expense"),
) -> ApiResponse:
    data = accounting_service.list_categories(
        db=db,
        user_id=current_user.id,
        category_type=category_type,
    )
    return ApiResponse.ok(data=data, request_id=_rid(request))


@router.get(
    "/records",
    summary="记账记录列表",
    description="分页获取当前用户的记账明细，支持按类型、分类、日期区间筛选。",
    response_model=ApiResponse[PageData[AccountingRecordItem]],
)
def list_records(
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
    record_type: Optional[str] = Query(None, description="记录类型: income/expense"),
    category_id: Optional[int] = Query(None, description="分类 ID"),
    start_date: Optional[date] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[date] = Query(None, description="结束日期 YYYY-MM-DD"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
) -> ApiResponse:
    page_data = accounting_service.list_records(
        db=db,
        user_id=current_user.id,
        record_type=record_type,
        category_id=category_id,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size,
    )
    return ApiResponse.ok(data=page_data, request_id=_rid(request))


@router.post(
    "/records",
    summary="新增记账记录",
    description="新增记账记录。支持 client_id 幂等防重；校验金额大于 0 及分类类型匹配。",
    response_model=ApiResponse[AccountingRecordItem],
)
def create_record(
    request: Request,
    payload: CreateAccountingRecordRequest,
    db: DbSession,
    current_user: CurrentUser,
) -> ApiResponse:
    item = accounting_service.create_record(
        db=db,
        user_id=current_user.id,
        req=payload,
    )
    return ApiResponse.ok(data=item, request_id=_rid(request))


@router.patch(
    "/records/{id}",
    summary="修改记账记录",
    description="修改记账记录。必须携带 version 进行乐观锁校验，版本冲突返回 1407。",
    response_model=ApiResponse[AccountingRecordItem],
)
def update_record(
    request: Request,
    payload: UpdateAccountingRecordRequest,
    db: DbSession,
    current_user: CurrentUser,
    id: int = Path(..., description="记录 ID"),
) -> ApiResponse:
    item = accounting_service.update_record(
        db=db,
        user_id=current_user.id,
        record_id=id,
        req=payload,
    )
    return ApiResponse.ok(data=item, request_id=_rid(request))


@router.delete(
    "/records/{id}",
    summary="删除记账记录",
    description="软删除记账记录。必须携带 version 进行乐观锁校验，版本冲突返回 1407。",
    response_model=ApiResponse[None],
)
def delete_record(
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
    id: int = Path(..., description="记录 ID"),
    version: int = Query(..., description="乐观锁版本号"),
) -> ApiResponse:
    accounting_service.delete_record(
        db=db,
        user_id=current_user.id,
        record_id=id,
        version=version,
    )
    return ApiResponse.ok(data=None, request_id=_rid(request))


@router.get(
    "/summary",
    summary="记账汇总",
    description="统计指定日期区间的总收入、总支出、净结余，并支持按分类或按日期分组明细。",
    response_model=ApiResponse[AccountingSummaryData],
)
def get_summary(
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
    start_date: date = Query(..., description="开始日期 YYYY-MM-DD"),
    end_date: date = Query(..., description="结束日期 YYYY-MM-DD"),
    group_by: Optional[str] = Query("category", description="分组维度: category / date"),
) -> ApiResponse:
    summary_data = accounting_service.get_summary(
        db=db,
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
        group_by=group_by,
    )
    return ApiResponse.ok(data=summary_data, request_id=_rid(request))
