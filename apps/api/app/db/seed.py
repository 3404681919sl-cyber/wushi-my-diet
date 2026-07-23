"""A6 内置食物预设数据（冷启动先验知识库）。

内置 18 种常见食物，标注 FODMAP 各维度等级（fodmap_category）、升糖指数（gi）、
每 100g 血糖负荷（gl_per_100g）、组胺等级（histamine_level）与基础营养素（nutrients）。

``fodmap_category`` 取值为六类 FODMAP 的等级（"high" / "moderate" / "low" / "none"），
用于后续冲突引擎与组合负担计算；``is_preset=True`` 标记为系统内置、用户不可随意删除。
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.food import Food

# fodmap 六类：fructan / gos / lactose / fructose / sorbitol / mannitol
PRESET_FOODS: list[dict] = [
    {
        "name": "洋葱",
        "fodmap_category": {"fructan": "high", "gos": "low", "lactose": "none", "fructose": "low", "sorbitol": "none", "mannitol": "none"},
        "gi": 15, "gl_per_100g": 1.0, "histamine_level": "low",
        "nutrients": {"kcal": 40, "protein_g": 1.1, "fat_g": 0.1, "carb_g": 9.3},
    },
    {
        "name": "大蒜",
        "fodmap_category": {"fructan": "high", "gos": "low", "lactose": "none", "fructose": "low", "sorbitol": "none", "mannitol": "none"},
        "gi": 15, "gl_per_100g": 1.0, "histamine_level": "low",
        "nutrients": {"kcal": 149, "protein_g": 6.4, "fat_g": 0.5, "carb_g": 33.1},
    },
    {
        "name": "豆类(鹰嘴豆)",
        "fodmap_category": {"fructan": "moderate", "gos": "high", "lactose": "none", "fructose": "low", "sorbitol": "none", "mannitol": "none"},
        "gi": 28, "gl_per_100g": 8.0, "histamine_level": "low",
        "nutrients": {"kcal": 164, "protein_g": 8.9, "fat_g": 2.6, "carb_g": 27.4},
    },
    {
        "name": "牛油果",
        "fodmap_category": {"fructan": "none", "gos": "low", "lactose": "none", "fructose": "moderate", "sorbitol": "none", "mannitol": "none"},
        "gi": 15, "gl_per_100g": 1.0, "histamine_level": "low",
        "nutrients": {"kcal": 160, "protein_g": 2.0, "fat_g": 14.7, "carb_g": 8.5},
    },
    {
        "name": "芒果",
        "fodmap_category": {"fructan": "none", "gos": "low", "lactose": "none", "fructose": "high", "sorbitol": "none", "mannitol": "none"},
        "gi": 51, "gl_per_100g": 5.0, "histamine_level": "low",
        "nutrients": {"kcal": 60, "protein_g": 0.8, "fat_g": 0.4, "carb_g": 15.0},
    },
    {
        "name": "苹果",
        "fodmap_category": {"fructan": "none", "gos": "low", "lactose": "none", "fructose": "high", "sorbitol": "low", "mannitol": "none"},
        "gi": 36, "gl_per_100g": 5.0, "histamine_level": "low",
        "nutrients": {"kcal": 52, "protein_g": 0.3, "fat_g": 0.2, "carb_g": 13.8},
    },
    {
        "name": "小麦(全麦面包)",
        "fodmap_category": {"fructan": "high", "gos": "low", "lactose": "none", "fructose": "low", "sorbitol": "none", "mannitol": "none"},
        "gi": 51, "gl_per_100g": 11.0, "histamine_level": "low",
        "nutrients": {"kcal": 247, "protein_g": 13.0, "fat_g": 3.4, "carb_g": 41.0},
    },
    {
        "name": "燕麦",
        "fodmap_category": {"fructan": "low", "gos": "low", "lactose": "none", "fructose": "low", "sorbitol": "none", "mannitol": "none"},
        "gi": 55, "gl_per_100g": 13.0, "histamine_level": "low",
        "nutrients": {"kcal": 389, "protein_g": 16.9, "fat_g": 6.9, "carb_g": 66.3},
    },
    {
        "name": "牛奶",
        "fodmap_category": {"fructan": "none", "gos": "low", "lactose": "high", "fructose": "none", "sorbitol": "none", "mannitol": "none"},
        "gi": 39, "gl_per_100g": 1.0, "histamine_level": "low",
        "nutrients": {"kcal": 61, "protein_g": 3.2, "fat_g": 3.3, "carb_g": 4.8},
    },
    {
        "name": "酸奶",
        "fodmap_category": {"fructan": "none", "gos": "low", "lactose": "moderate", "fructose": "none", "sorbitol": "none", "mannitol": "none"},
        "gi": 35, "gl_per_100g": 1.0, "histamine_level": "low",
        "nutrients": {"kcal": 59, "protein_g": 3.5, "fat_g": 3.3, "carb_g": 4.7},
    },
    {
        "name": "香蕉(熟)",
        "fodmap_category": {"fructan": "low", "gos": "low", "lactose": "none", "fructose": "low", "sorbitol": "moderate", "mannitol": "none"},
        "gi": 51, "gl_per_100g": 12.0, "histamine_level": "low",
        "nutrients": {"kcal": 89, "protein_g": 1.1, "fat_g": 0.3, "carb_g": 22.8},
    },
    {
        "name": "西兰花",
        "fodmap_category": {"fructan": "moderate", "gos": "low", "lactose": "none", "fructose": "low", "sorbitol": "none", "mannitol": "high"},
        "gi": 15, "gl_per_100g": 1.0, "histamine_level": "low",
        "nutrients": {"kcal": 34, "protein_g": 2.8, "fat_g": 0.4, "carb_g": 6.6},
    },
    {
        "name": "胡萝卜",
        "fodmap_category": {"fructan": "none", "gos": "low", "lactose": "none", "fructose": "low", "sorbitol": "none", "mannitol": "low"},
        "gi": 39, "gl_per_100g": 2.0, "histamine_level": "low",
        "nutrients": {"kcal": 41, "protein_g": 0.9, "fat_g": 0.2, "carb_g": 9.6},
    },
    {
        "name": "米饭(白)",
        "fodmap_category": {"fructan": "none", "gos": "low", "lactose": "none", "fructose": "none", "sorbitol": "none", "mannitol": "none"},
        "gi": 73, "gl_per_100g": 23.0, "histamine_level": "low",
        "nutrients": {"kcal": 130, "protein_g": 2.7, "fat_g": 0.3, "carb_g": 28.2},
    },
    {
        "name": "鸡蛋",
        "fodmap_category": {"fructan": "none", "gos": "low", "lactose": "none", "fructose": "none", "sorbitol": "none", "mannitol": "none"},
        "gi": 0, "gl_per_100g": 0.0, "histamine_level": "low",
        "nutrients": {"kcal": 143, "protein_g": 12.6, "fat_g": 9.5, "carb_g": 0.7},
    },
    {
        "name": "鸡肉",
        "fodmap_category": {"fructan": "none", "gos": "low", "lactose": "none", "fructose": "none", "sorbitol": "none", "mannitol": "none"},
        "gi": 0, "gl_per_100g": 0.0, "histamine_level": "moderate",
        "nutrients": {"kcal": 165, "protein_g": 31.0, "fat_g": 3.6, "carb_g": 0.0},
    },
    {
        "name": "鱼(三文鱼)",
        "fodmap_category": {"fructan": "none", "gos": "low", "lactose": "none", "fructose": "none", "sorbitol": "none", "mannitol": "none"},
        "gi": 0, "gl_per_100g": 0.0, "histamine_level": "high",
        "nutrients": {"kcal": 208, "protein_g": 20.0, "fat_g": 13.0, "carb_g": 0.0},
    },
    {
        "name": "坚果(杏仁)",
        "fodmap_category": {"fructan": "none", "gos": "low", "lactose": "none", "fructose": "low", "sorbitol": "high", "mannitol": "none"},
        "gi": 15, "gl_per_100g": 1.0, "histamine_level": "low",
        "nutrients": {"kcal": 579, "protein_g": 21.2, "fat_g": 49.9, "carb_g": 21.6},
    },
    {
        "name": "菠菜",
        "fodmap_category": {"fructan": "none", "gos": "low", "lactose": "none", "fructose": "low", "sorbitol": "none", "mannitol": "low"},
        "gi": 15, "gl_per_100g": 1.0, "histamine_level": "low",
        "nutrients": {"kcal": 23, "protein_g": 2.9, "fat_g": 0.4, "carb_g": 3.6},
    },
]


async def seed_preset_foods(session: AsyncSession) -> int:
    """将 A6 预设食物写入 ``foods`` 表（已存在同名则跳过）。

    返回本次实际新增的食物数量。
    """
    existing = set(
        (await session.scalars(select(Food.name))).all()
    )
    added = 0
    for item in PRESET_FOODS:
        if item["name"] in existing:
            continue
        session.add(
            Food(
                name=item["name"],
                fodmap_category=item["fodmap_category"],
                gi=item["gi"],
                gl_per_100g=item["gl_per_100g"],
                histamine_level=item["histamine_level"],
                nutrients=item["nutrients"],
                is_preset=True,
            )
        )
        added += 1
    if added:
        await session.commit()
    return added
