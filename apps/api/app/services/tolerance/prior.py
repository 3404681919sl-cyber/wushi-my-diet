"""冷启动先验：基于 A6 食物知识库构造 log 空间耐受阈值先验（T2）。

返回 ``(mean, var)``，二者均在 ``log(克)`` 空间中：

- 高 FODMAP 或高组胺食物 → 保守先验 ``μ ≈ log(20)``，``σ ≈ 0.6``；
- 低 FODMAP 且高营养（高蛋白、低净碳水）→ 宽松先验 ``μ ≈ log(80)``；
- 其余（未知 / 中等）→ 中间先验 ``μ = log(30)``，``σ = 0.7``；
- 高升糖指数（GI ≥ 70）追加惩罚，剂量下调 20%。
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.food import Food

# 先验剂量锚点（克）
LOW_DOSE = 20.0
MID_DOSE = 30.0
HIGH_DOSE = 80.0

# 先验方差（log 空间）
LOW_VAR = 0.6 ** 2
MID_VAR = 0.7 ** 2
HIGH_VAR = 0.5 ** 2

# 高升糖惩罚系数与阈值
GI_PENALTY = 0.8
GI_HIGH_THRESHOLD = 70.0

# 高营养判定阈值（高蛋白、低净碳水）
HIGH_NUTRITION_PROTEIN = 10.0
HIGH_NUTRITION_CARB = 15.0


def is_high_fodmap(food: "Food") -> bool:
    """食物是否含任一高 FODMAP 维度。"""
    fodmap = food.fodmap_category or {}
    return "high" in fodmap.values()


def is_high_histamine(food: "Food") -> bool:
    """食物是否为高组胺等级。"""
    return (food.histamine_level or "unknown").lower() == "high"


def is_high_gi(food: "Food") -> bool:
    """食物升糖指数是否偏高。"""
    return (food.gi or 0.0) >= GI_HIGH_THRESHOLD


def is_high_nutrition(food: "Food") -> bool:
    """食物是否高蛋白、低净碳水（营养密度高）。"""
    nutrients = food.nutrients or {}
    protein = nutrients.get("protein_g", 0) or 0.0
    carb = nutrients.get("carb_g", 0) or 0.0
    return protein >= HIGH_NUTRITION_PROTEIN and carb <= HIGH_NUTRITION_CARB


def build_prior(food: "Food") -> tuple[float, float]:
    """根据食物知识库构造 log 空间先验 ``(mean, var)``。

    Args:
        food: 食物模型实例，需含 ``fodmap_category`` / ``gi`` /
            ``histamine_level`` / ``nutrients``。

    Returns:
        ``(mean, var)``：log 空间下的先验均值与方差。
    """
    restrictive = is_high_fodmap(food) or is_high_histamine(food)
    generous = is_high_nutrition(food)

    if restrictive:
        dose, var = LOW_DOSE, LOW_VAR
    elif generous:
        dose, var = HIGH_DOSE, HIGH_VAR
    else:
        dose, var = MID_DOSE, MID_VAR

    # 高升糖追加惩罚（升糖维度同样挤压耐受空间）
    if is_high_gi(food):
        dose *= GI_PENALTY

    mean = math.log(max(dose, 0.5))
    return mean, var
