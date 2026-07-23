"""贝叶斯耐受阈值相关 Pydantic 模型（响应，T2 路由使用，本期先于路由定义）。"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ToleranceThresholdOut(BaseModel):
    """用户对某食物的个性化耐受阈值响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    food_id: int
    prior_mean: float
    prior_var: float
    post_mean: float
    post_var: float
    safe_g: int
    caution_g: int
    unsafe_g: int
    n_obs: int
    updated_at: datetime
