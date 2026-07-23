"""组合负担：FODMAP 负荷 + 血糖负荷 + 联合告警（T2）。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Iterable

from .fodmap import FodmapLoad, compute_fodmap_load
from .gl import GlResult, compute_gl

if TYPE_CHECKING:
    from app.models.food import Food

# 联合告警阈值
GL_YELLOW = 20.0
GL_RED = 30.0
FODMAP_YELLOW = 6.0
FODMAP_RED = 12.0


@dataclass
class CombinedBurden:
    """组合负担结果。"""

    total_fodmap_load: float
    total_gl: float
    warning_level: str
    messages: list = field(default_factory=list)
    per_category: dict = field(default_factory=dict)
    per_food_gl: list = field(default_factory=list)


def compute_burden(items: Iterable[tuple["Food", float]]) -> CombinedBurden:
    """计算一份餐食的 FODMAP + GL 组合负担并给出告警等级。

    Args:
        items: 可迭代的 ``(Food, amount_g)`` 二元组。

    Returns:
        ``CombinedBurden``：总负荷、告警等级与提示信息。
    """
    fodmap: FodmapLoad = compute_fodmap_load(items)
    gl: GlResult = compute_gl(items)

    messages: list[str] = []
    level = "green"

    if fodmap.total_fodmap_load > FODMAP_RED:
        level = "red"
        messages.append(
            f"FODMAP 总负荷 {fodmap.total_fodmap_load:.1f} 过高（阈值 {FODMAP_RED}）"
        )
    elif fodmap.total_fodmap_load > FODMAP_YELLOW:
        level = "yellow"
        messages.append(
            f"FODMAP 总负荷 {fodmap.total_fodmap_load:.1f} 偏高（阈值 {FODMAP_YELLOW}）"
        )

    if gl.total_gl > GL_RED:
        level = "red"
        messages.append(f"血糖负荷 GL {gl.total_gl:.1f} 过高（阈值 {GL_RED}）")
    elif gl.total_gl > GL_YELLOW:
        level = "yellow"
        messages.append(f"血糖负荷 GL {gl.total_gl:.1f} 偏高（阈值 {GL_YELLOW}）")

    return CombinedBurden(
        total_fodmap_load=fodmap.total_fodmap_load,
        total_gl=gl.total_gl,
        warning_level=level,
        messages=messages,
        per_category=fodmap.per_category,
        per_food_gl=gl.per_food,
    )
