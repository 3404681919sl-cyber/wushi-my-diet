"""食谱相关 Pydantic 模型（T2 模板生成）。"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class RecipeRequest(BaseModel):
    """生成食谱请求。"""

    goal: Optional[str] = Field(
        default=None, description="目标：gut_stability / blood_sugar / fat_loss"
    )
    avoid_food_ids: list[int] = Field(default_factory=list, description="需规避的食物 ID")
    category: Optional[str] = Field(default=None, description="食物名称子串过滤")


class RecipeItemOut(BaseModel):
    """食谱条目响应。"""

    food_id: int
    name: str
    amount_g: int
    safety: str | None = None
    replaceable_with: list[str] = Field(default_factory=list)
    reason: str | None = None


class RecipeOut(BaseModel):
    """食谱响应（``generated_by`` 标识生成方式）。"""

    generated_by: str
    title: str
    items: list[RecipeItemOut] = Field(default_factory=list)
    note: str = ""
