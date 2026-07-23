"""食谱路由（T3）：DeepSeek V4 Pro 优先，模板回退。

统一前缀：``/api/v1/recipe``
- ``POST /``：优先调用 DeepSeek V4 Pro 生成食谱（LLM 层）；
  无 key / 调用失败 → 静默回退 T2 模板生成（``template.generate_recipe``）。
- 响应附带 ``engine`` 字段（"llm" / "template"）标识实际引擎，便于前端区分。

安全红线：API key 仅服务端从环境变量 ``DEEPSEEK_API_KEY`` 读取，绝不透传到小程序端；
环境变量缺省时静默回退模板，不会报错。
"""

from __future__ import annotations

import os

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_session
from app.models.user import User
from app.schemas.recipe import RecipeOut, RecipeRequest
from app.services.recipe.llm import generate_recipe_llm
from app.services.recipe.template import generate_recipe

router = APIRouter(prefix="/recipe", tags=["recipe"])

# 目标（goal）→ 多目标权重映射，供 LLM 理解用户侧重。
_GOAL_WEIGHTS: dict[str, dict] = {
    "gut_stability": {"gut": 0.7, "glucose": 0.2, "fat_loss": 0.1},
    "blood_sugar": {"gut": 0.2, "glucose": 0.7, "fat_loss": 0.1},
    "fat_loss": {"gut": 0.2, "glucose": 0.1, "fat_loss": 0.7},
}


def _target_weights_from_goal(goal: str | None) -> dict:
    """根据目标返回多目标权重；缺省按肠道稳定优先。"""
    return _GOAL_WEIGHTS.get(goal or "", {"gut": 0.7, "glucose": 0.2, "fat_loss": 0.1})


@router.post("", response_model=RecipeOut)
async def create_recipe(
    payload: RecipeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> RecipeOut:
    """生成食谱：DeepSeek LLM 优先，失败回退模板。"""
    # key 仅服务端持有：显式参数 → 环境变量 → （未来 admin DB 配置）。当前用环境变量。
    api_key = os.getenv("DEEPSEEK_API_KEY")

    recipe = await generate_recipe_llm(
        db,
        user_id=current_user.id,
        target_weights=_target_weights_from_goal(payload.goal),
        body_state=payload.body_state,
        exclude_food_ids=payload.avoid_food_ids,
        api_key=api_key,
    )
    if recipe is not None:
        recipe["engine"] = "llm"
        recipe["generated_by"] = "llm"
        recipe.setdefault("note", "")
        recipe.setdefault("title", "吾食个性化食谱（DeepSeek）")
        return RecipeOut.model_validate(recipe)

    # 回退：T2 模板生成（保持原有行为，无回归）。
    recipe = await generate_recipe(
        db,
        user_id=current_user.id,
        exclude_food_ids=payload.avoid_food_ids,
    )
    recipe["engine"] = "template"
    return RecipeOut.model_validate(recipe)
