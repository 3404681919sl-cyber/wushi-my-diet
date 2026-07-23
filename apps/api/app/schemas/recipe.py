"""食谱相关 Pydantic 模型（T2 模板生成）。"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class RecipeRequest(BaseModel):
    """生成食谱请求。"""

    goal: Optional[str] = Field(
        default=None, description="目标：gut_stability / blood_sugar / fat_loss"
    )
    avoid_food_ids: list[int] = Field(default_factory=list, description="需规避的食物 ID")
    category: Optional[str] = Field(default=None, description="食物名称子串过滤")
    body_state: Optional[str] = Field(default=None, description="近期身体状态备注（可选）")


class RecipeItemOut(BaseModel):
    """食谱条目响应。

    ``food_id`` 允许为 ``None``：当 LLM 仅给出食物名、且库中无匹配时，
    回退为 ``None``（前端按名称展示）。模板生成始终带有效 id。
    """

    food_id: int | None = None
    name: str
    amount_g: int
    safety: str | None = None
    replaceable_with: list[str] = Field(default_factory=list)
    reason: str | None = None


class RecipeOut(BaseModel):
    """食谱响应。

    - ``generated_by``：生成方式标识（template / llm），T2 已存在，保持必需。
    - ``engine``：T3 新增的可选字段，标识实际使用的引擎（"template" / "llm"），
      默认 ``"template"`` 以保证向后兼容（T2 测试不受影响）。
    """

    generated_by: str
    engine: str = Field(default="template", description="实际使用的生成引擎：llm 或 template")
    title: str
    items: list[RecipeItemOut] = Field(default_factory=list)
    note: str = ""
