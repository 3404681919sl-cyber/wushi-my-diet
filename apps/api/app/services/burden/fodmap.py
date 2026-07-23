"""FODMAP 六类负荷计算（T2）。

将一份餐食（若干 ``(Food, amount_g)``）折算为各 FODMAP 维度的累计负荷：
每个食物按其在某维度的等级给出权重（high=3 / moderate=2 / low=1 / none=0），
再按摄入量（每 100g 为 1 份）累加。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Iterable

if TYPE_CHECKING:
    from app.models.food import Food

# FODMAP 六类维度
FODMAP_DIMENSIONS = ["fructan", "gos", "lactose", "fructose", "sorbitol", "mannitol"]
# 等级 → 权重
FODMAP_LEVEL_WEIGHT = {"high": 3.0, "moderate": 2.0, "low": 1.0, "none": 0.0}


@dataclass
class FodmapLoad:
    """FODMAP 负荷结果。"""

    total_fodmap_load: float
    per_category: dict = field(default_factory=dict)


def compute_fodmap_load(items: Iterable[tuple["Food", float]]) -> FodmapLoad:
    """计算一份餐食的 FODMAP 六类累计负荷。

    Args:
        items: 可迭代的 ``(Food, amount_g)`` 二元组。

    Returns:
        ``FodmapLoad``：总负荷与按维度的明细。
    """
    per_category = {c: 0.0 for c in FODMAP_DIMENSIONS}
    total = 0.0
    for food, amount in items:
        fraction = max(amount, 0.0) / 100.0
        fodmap = food.fodmap_category or {}
        for dim in FODMAP_DIMENSIONS:
            level = fodmap.get(dim, "none")
            weight = FODMAP_LEVEL_WEIGHT.get(level, 0.0)
            contrib = weight * fraction
            per_category[dim] += contrib
            total += contrib
    return FodmapLoad(total_fodmap_load=round(total, 3), per_category=per_category)
