"""备忘录数据模型定义 (Pydantic Schemas)。

对应《接口契约》7.2。
"""

from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class MemoItem(BaseModel):
    """备忘录单项数据。"""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="备忘录 ID")
    client_id: str = Field(..., description="客户端 UUID 幂等标识")
    title: Optional[str] = Field(None, description="标题（可空）")
    content: str = Field(..., description="正文内容")
    is_pinned: bool = Field(False, description="是否置顶")
    color: Optional[str] = Field(None, description="展示颜色标识")
    version: int = Field(1, description="乐观锁版本号")
    created_at: str = Field(..., description="创建时间 ISO 8601")
    updated_at: str = Field(..., description="更新时间 ISO 8601")


class CreateMemoRequest(BaseModel):
    """新增备忘录请求体。"""

    client_id: str = Field(..., min_length=1, max_length=36, description="客户端生成 UUID，用于幂等控制")
    content: str = Field(..., min_length=1, description="正文内容")
    title: Optional[str] = Field(None, max_length=200, description="标题")
    is_pinned: Optional[bool] = Field(False, description="是否置顶")
    color: Optional[str] = Field(None, max_length=30, description="展示颜色标识")


class UpdateMemoRequest(BaseModel):
    """修改备忘录请求体。"""

    version: int = Field(..., description="乐观锁版本号，必传")
    title: Optional[str] = Field(None, max_length=200, description="标题")
    content: Optional[str] = Field(None, min_length=1, description="正文内容")
    is_pinned: Optional[bool] = Field(None, description="是否置顶")
    color: Optional[str] = Field(None, max_length=30, description="展示颜色标识")
