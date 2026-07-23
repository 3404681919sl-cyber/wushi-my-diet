"""食物地图相关 Pydantic 模型（T2 三色 + 三剂量）。"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.food import FoodOut


class ConflictOut(BaseModel):
    """冲突响应。"""

    dimension: str
    condition_name: str
    food_attribute: str
    severity: str
    message: str


class FoodSafetyOut(BaseModel):
    """单食物安全评估响应。"""

    food: FoodOut
    level: str
    reason: str
    safe_g: int
    caution_g: int
    unsafe_g: int
    conflicts: list[ConflictOut] = Field(default_factory=list)


class MapOut(BaseModel):
    """食物地图响应（多食物）。"""

    items: list[FoodSafetyOut] = Field(default_factory=list)


class MapFoodOut(BaseModel):
    """成长地图中单食物的精简安全信息（T2 /map 路由使用）。"""

    food_id: int
    name: str
    safety_level: str
    safe_g: int
    caution_g: int
    unsafe_g: int
    n_obs: int
