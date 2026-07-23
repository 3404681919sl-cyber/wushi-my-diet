"""食物相关 Pydantic 模型（响应，T2/T3 路由使用，本期先于路由定义）。"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class FoodOut(BaseModel):
    """食物响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    fodmap_category: dict
    gi: float
    gl_per_100g: float
    histamine_level: str
    nutrients: dict
    is_preset: bool
