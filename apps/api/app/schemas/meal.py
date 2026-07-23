"""餐日志相关 Pydantic 模型（请求 / 响应，T2 路由使用，本期先于路由定义）。"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class MealItemCreate(BaseModel):
    """餐条目创建请求。"""

    food_id: int = Field(..., description="食物 ID")
    amount_g: float = Field(default=0.0, ge=0.0, description="摄入量（克）")


class MealLogCreate(BaseModel):
    """餐日志创建请求。"""

    note: str = Field(default="", max_length=512, description="备注")
    items: list[MealItemCreate] = Field(default_factory=list, description="餐条目列表")


class MealItemOut(BaseModel):
    """餐条目响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    food_id: int
    amount_g: float


class MealLogOut(BaseModel):
    """餐日志响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    logged_at: datetime
    note: str
    items: list[MealItemOut] = Field(default_factory=list)
