"""食物相关 Pydantic 模型（响应，对齐前端 FoodOut）。

字段与 ``app.models.food.Food`` 及前端 ``src/api/types.ts#FoodOut`` 保持一致，
便于前端食物图谱 / 选择场景直接消费。
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class FoodOut(BaseModel):
    """食物响应（对齐前端 FoodOut）。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    # FODMAP 六类等级，如 {"fructan": "high", ...}
    fodmap_category: dict[str, str] = {}
    gi: float = 0.0
    gl_per_100g: float = 0.0
    histamine_level: str = "unknown"
    nutrients: dict[str, Any] = {}
    is_preset: bool = False
