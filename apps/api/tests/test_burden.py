"""组合负担测试：FODMAP 六类负载汇总 / 高 GI 餐后 GL 预警。

纯函数单测（Food 对象，无需 DB）。
"""

from __future__ import annotations

from app.models.food import Food
from app.services.burden import compute_burden

_FODMAP_NONE = {
    "fructan": "none",
    "gos": "low",
    "lactose": "none",
    "fructose": "none",
    "sorbitol": "none",
    "mannitol": "none",
}


def _rice() -> Food:
    """高 GI 米饭（gi=73, gl_per_100g=23）。"""
    return Food(
        name="米饭(白)",
        fodmap_category=dict(_FODMAP_NONE),
        gi=73,
        gl_per_100g=23.0,
        histamine_level="low",
        nutrients={"kcal": 130, "protein_g": 2.7, "fat_g": 0.3, "carb_g": 28.2},
    )


def _chicken() -> Food:
    """低 FODMAP 高营养、零 GL。"""
    return Food(
        name="鸡肉",
        fodmap_category=dict(_FODMAP_NONE),
        gi=0,
        gl_per_100g=0.0,
        histamine_level="moderate",
        nutrients={"kcal": 165, "protein_g": 31.0, "fat_g": 3.6, "carb_g": 0.0},
    )


def _onion() -> Food:
    """高 FODMAP（fructan high）。"""
    return Food(
        name="洋葱",
        fodmap_category={
            "fructan": "high",
            "gos": "low",
            "lactose": "none",
            "fructose": "low",
            "sorbitol": "none",
            "mannitol": "none",
        },
        gi=15,
        gl_per_100g=1.0,
        histamine_level="low",
        nutrients={"kcal": 40, "protein_g": 1.1, "fat_g": 0.1, "carb_g": 9.3},
    )


def test_high_gi_meal_gl_warning() -> None:
    """高 GI 餐后（米饭 200g + 鸡肉 100g）GL > 20 → 预警。"""
    burden = compute_burden([(_rice(), 200.0), (_chicken(), 100.0)])
    assert burden.total_gl > 20
    assert burden.warning_level in ("yellow", "red")
    assert any("血糖" in m for m in burden.messages)


def test_low_gl_meal_no_warning() -> None:
    """零 GL 餐（仅鸡肉）→ 无预警。"""
    burden = compute_burden([(_chicken(), 100.0)])
    assert burden.total_gl == 0.0
    assert burden.warning_level == "green"
    assert burden.messages == []


def test_fodmap_load_sums_six_categories() -> None:
    """洋葱 100g：fructan 维度负载 > 0，六类求和 > 0。"""
    burden = compute_burden([(_onion(), 100.0)])
    assert burden.total_fodmap_load > 0
    assert burden.per_category["fructan"] > 0
    # 其余维度为 none/low，负载为 0
    assert burden.per_category["lactose"] == 0
