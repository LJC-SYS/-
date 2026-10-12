"""记账本数据模型定义 (Pydantic Schemas)。

对应《接口契约》7.3。
"""

from datetime import date
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class AccountingCategoryItem(BaseModel):
    """记账分类单项。"""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="分类 ID")
    name: str = Field(..., description="分类名称")
    category_type: str = Field(..., description="分类类型: income/expense")
    icon: Optional[str] = Field(None, description="分类图标")
    color: Optional[str] = Field(None, description="分类颜色")
    sort_order: int = Field(0, description="排序")
    is_system: bool = Field(..., description="是否为系统默认分类")


class AccountingCategoryListData(BaseModel):
    """记账分类列表响应数据。"""

    list: List[AccountingCategoryItem]


class AccountingRecordItem(BaseModel):
    """记账记录单项。"""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="记录 ID")
    client_id: str = Field(..., description="客户端 UUID 幂等标识")
    category_id: int = Field(..., description="分类 ID")
    category_name: str = Field(..., description="分类名称")
    record_type: str = Field(..., description="记录类型: income/expense")
    amount: str = Field(..., description="金额字符串，保留两位小数")
    record_date: str = Field(..., description="记账日期 YYYY-MM-DD")
    note: Optional[str] = Field(None, description="备注说明")
    version: int = Field(1, description="乐观锁版本号")
    created_at: str = Field(..., description="创建时间 ISO 8601")
    updated_at: str = Field(..., description="更新时间 ISO 8601")


class CreateAccountingRecordRequest(BaseModel):
    """新增记账记录请求体。"""

    client_id: str = Field(..., min_length=1, max_length=36, description="客户端生成 UUID")
    category_id: int = Field(..., description="关联记账分类 ID")
    record_type: str = Field(..., description="记录类型: income/expense")
    amount: Decimal = Field(..., gt=0, description="记账金额，必须大于 0")
    record_date: date = Field(..., description="记账所属日期 YYYY-MM-DD")
    note: Optional[str] = Field(None, max_length=500, description="备注")


class UpdateAccountingRecordRequest(BaseModel):
    """修改记账记录请求体。"""

    version: int = Field(..., description="乐观锁版本号，必传")
    category_id: Optional[int] = Field(None, description="关联记账分类 ID")
    record_type: Optional[str] = Field(None, description="记录类型: income/expense")
    amount: Optional[Decimal] = Field(None, gt=0, description="记账金额，必须大于 0")
    record_date: Optional[date] = Field(None, description="记账所属日期 YYYY-MM-DD")
    note: Optional[str] = Field(None, max_length=500, description="备注")


class AccountingSummaryGroupItem(BaseModel):
    """记账汇总分组单项。"""

    key: str = Field(..., description="分组标识（如分类名称或日期）")
    category_id: Optional[int] = Field(None, description="分类 ID")
    record_type: Optional[str] = Field(None, description="记录类型: income/expense")
    amount: str = Field(..., description="分组总额字符串")
    count: int = Field(..., description="记账笔数")


class AccountingSummaryData(BaseModel):
    """记账月度/区间汇总数据。"""

    start_date: str = Field(..., description="开始日期")
    end_date: str = Field(..., description="结束日期")
    total_income: str = Field(..., description="总收入金额")
    total_expense: str = Field(..., description="总支出金额")
    balance: str = Field(..., description="净结余金额 (income - expense)")
    groups: List[AccountingSummaryGroupItem] = Field(default_factory=list, description="分组统计详情")
