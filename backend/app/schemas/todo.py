"""待办事项数据模型定义 (Pydantic Schemas)。

对应《接口契约》7.1。
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class TodoItem(BaseModel):
    """待办事项单项数据。"""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="待办 ID")
    client_id: str = Field(..., description="客户端 UUID 幂等标识")
    title: str = Field(..., description="标题")
    description: Optional[str] = Field(None, description="详细描述")
    priority: str = Field("normal", description="优先级: low/normal/high")
    status: str = Field("pending", description="状态: pending/completed/cancelled")
    due_at: Optional[str] = Field(None, description="截止时间 ISO 8601")
    completed_at: Optional[str] = Field(None, description="完成时间 ISO 8601")
    sort_order: int = Field(0, description="自定义排序")
    version: int = Field(1, description="乐观锁版本号")
    created_at: str = Field(..., description="创建时间 ISO 8601")
    updated_at: str = Field(..., description="更新时间 ISO 8601")


class CreateTodoRequest(BaseModel):
    """新增待办请求体。"""

    client_id: str = Field(..., min_length=1, max_length=36, description="客户端生成 UUID，用于幂等控制")
    title: str = Field(..., min_length=1, max_length=200, description="待办标题")
    description: Optional[str] = Field(None, description="详细描述")
    priority: Optional[str] = Field("normal", description="优先级: low/normal/high")
    due_at: Optional[datetime] = Field(None, description="截止时间")
    sort_order: Optional[int] = Field(0, description="排序值")


class UpdateTodoRequest(BaseModel):
    """修改待办请求体。"""

    version: int = Field(..., description="乐观锁版本号，必传")
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="待办标题")
    description: Optional[str] = Field(None, description="详细描述")
    priority: Optional[str] = Field(None, description="优先级: low/normal/high")
    status: Optional[str] = Field(None, description="状态: pending/completed/cancelled")
    due_at: Optional[datetime] = Field(None, description="截止时间")
    sort_order: Optional[int] = Field(None, description="排序值")
