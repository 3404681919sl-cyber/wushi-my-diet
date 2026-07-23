"""微挑战相关 Pydantic 模型（请求 / 响应，T2 路由使用，本期先于路由定义）。"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ChallengeCreate(BaseModel):
    """创建微挑战请求：指定目标食物。"""

    food_id: int = Field(..., description="目标食物 ID")


class ChallengeStepOut(BaseModel):
    """微挑战步骤响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    challenge_id: int
    step_no: int
    dose_g: int
    result: Optional[str] = None
    logged_at: Optional[datetime] = None


class ChallengeOut(BaseModel):
    """微挑战响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    food_id: int
    status: str
    created_at: datetime
    steps: list[ChallengeStepOut] = Field(default_factory=list)
