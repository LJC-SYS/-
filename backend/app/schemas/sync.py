"""云端增量同步数据模型定义 (Pydantic Schemas)。

对应《接口契约》8.1 与 8.2。
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SyncPushChangeItem(BaseModel):
    """客户端推送的单项变更。"""

    entity_type: str = Field(..., description="实体类型: todo / memo / accounting")
    client_id: str = Field(..., description="客户端 UUID 标识")
    action: str = Field(..., description="操作类型: create / update / delete")
    version: int = Field(0, description="本地版本号: create 传 0，update/delete 传本地版本")
    data: Optional[Dict[str, Any]] = Field(None, description="变更载荷数据，delete 时为 null")


class SyncPushRequest(BaseModel):
    """推送本地变更请求体。"""

    device_id: str = Field(..., description="客户端设备标识")
    last_sync_at: Optional[str] = Field(None, description="上次同步时间 ISO 8601")
    changes: List[SyncPushChangeItem] = Field(default_factory=list, description="变更项列表")


class SyncPushResultItem(BaseModel):
    """单项变更同步结果。"""

    client_id: str = Field(..., description="客户端 UUID 标识")
    entity_type: str = Field(..., description="实体类型")
    status: str = Field(..., description="处理状态: created / updated / deleted / skipped / conflict")
    server_id: Optional[int] = Field(None, description="服务端自增 ID")
    version: Optional[int] = Field(None, description="变更后服务端最新版本号")
    server_version: Optional[int] = Field(None, description="冲突时服务端的当前版本号")
    server_data: Optional[Dict[str, Any]] = Field(None, description="冲突时服务端的当前数据")


class SyncPushResponseData(BaseModel):
    """推送本地变更响应数据。"""

    results: List[SyncPushResultItem] = Field(default_factory=list, description="各项同步结果")
    partial_failure: bool = Field(False, description="是否存在冲突或失败项")
    server_time: str = Field(..., description="服务端处理时间 ISO 8601")


class SyncPullChangeItem(BaseModel):
    """服务端下发的单项增量变更。"""

    entity_type: str = Field(..., description="实体类型: todo / memo / accounting")
    server_id: int = Field(..., description="服务端自增 ID")
    client_id: str = Field(..., description="客户端 UUID 标识")
    version: int = Field(..., description="实体版本号")
    deleted: bool = Field(False, description="是否已被软删除")
    updated_at: str = Field(..., description="更新时间 ISO 8601")
    data: Optional[Dict[str, Any]] = Field(None, description="实体数据载荷（已删除时为 null）")


class SyncPullResponseData(BaseModel):
    """拉取增量响应数据。"""

    server_time: str = Field(..., description="服务端时间 ISO 8601")
    has_more: bool = Field(False, description="是否还有更多增量数据需要分页拉取")
    changes: List[SyncPullChangeItem] = Field(default_factory=list, description="增量变更项列表")
