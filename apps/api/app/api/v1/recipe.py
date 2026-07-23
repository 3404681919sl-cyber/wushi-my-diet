"""食谱路由：模板生成（T2，非 LLM）。

统一前缀：``/api/v1/recipe``
- ``POST /``：根据目标与规避列表生成模板食谱（``generated_by = "template"``）
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_session
from app.models.user import User
from app.schemas.recipe import RecipeOut, RecipeRequest
from app.services.recipe.template import generate_recipe

router = APIRouter(prefix="/recipe", tags=["recipe"])


@router.post("", response_model=RecipeOut)
async def create_recipe(
    payload: RecipeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> RecipeOut:
    """生成模板食谱（本期由规则生成，T3 将接入 DeepSeek LLM）。"""
    recipe = await generate_recipe(
        db,
        user_id=current_user.id,
        exclude_food_ids=payload.avoid_food_ids,
    )
    return RecipeOut.model_validate(recipe)
