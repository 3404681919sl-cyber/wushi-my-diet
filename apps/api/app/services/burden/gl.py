"""血糖负荷（GL）计算（T2）。

GL = Σ (amount_g / 100 × gl_per_100g)，按食物累加。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Iterable

if TYPE_CHECKING:
    from app.models.food import Food


@dataclass
class GlResult:
    """血糖负荷结果。"""

    total_gl: float
    per_food: list = field(default_factory=list)


def compute_gl(items: Iterable[tuple["Food", float]]) -> GlResult:
    """计算一份餐食的血糖负荷。

    Args:
        items: 可迭代的 ``(Food, amount_g)`` 二元组。

    Returns:
        ``GlResult``：总 GL 与按食物的明细。
    """
    total = 0.0
    per_food: list[dict] = []
    for food, amount in items:
        gl = (max(amount, 0.0) / 100.0) * (food.gl_per_100g or 0.0)
        total += gl
        per_food.append(
            {"food_id": food.id, "name": food.name, "amount_g": amount, "gl": gl}
        )
    return GlResult(total_gl=round(total, 3), per_food=per_food)
