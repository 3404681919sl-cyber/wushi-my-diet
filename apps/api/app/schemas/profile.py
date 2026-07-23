"""画像相关 Pydantic 模型（请求 / 响应）。"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ConditionCreate(BaseModel):
    """录入 / 更新健康状况请求。"""

    name: str = Field(..., max_length=128, description="状况名称")
    fodmap_flags: dict = Field(default_factory=dict, description="FODMAP 各维度触发标记")
    glucose_flag: bool = False
    histamine_flag: bool = False
    is_active: bool = True
    note: str = ""


class ConditionOut(BaseModel):
    """健康状况响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    name: str
    fodmap_flags: dict
    glucose_flag: bool
    histamine_flag: bool
    is_active: bool
    note: str


class SymptomDefCreate(BaseModel):
    """新增症状词典条目请求。"""

    name: str = Field(..., max_length=128, description="症状名称")
    scale_max: int = Field(default=10, ge=1, le=100, description="严重度量表上限")
    is_custom: bool = True


class SymptomDefOut(BaseModel):
    """症状词典条目响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    name: str
    scale_max: int
    is_custom: bool


class ProfileUpdate(BaseModel):
    """更新画像请求（仅暴露可写字段）。"""

    target_weights: Optional[dict] = None


class ProfileOut(BaseModel):
    """画像响应（含状况与症状词典）。"""

    model_config = ConfigDict(from_attributes=True)

    user_id: int
    target_weights: dict
    created_at: datetime
    updated_at: datetime
    conditions: list[ConditionOut] = Field(default_factory=list)
    symptom_defs: list[SymptomDefOut] = Field(default_factory=list)
