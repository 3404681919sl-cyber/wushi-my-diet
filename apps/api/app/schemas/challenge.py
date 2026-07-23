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
    severity: Optional[int] = None
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
    # 当前耐受阈值（随 record_step 重算），便于前端直接展示三色剂量与学习进度
    n_obs: int = 0
    safe_g: int = 0
    caution_g: int = 0
    unsafe_g: int = 0


class ChallengeStepUpdate(BaseModel):
    """记录微挑战某步骤反应结果请求。"""

    step_no: int = Field(..., ge=1, description="步骤序号")
    severity: int = Field(..., ge=0, le=10, description="反应严重度 0~10，0=无症状")
    dose_g: Optional[int] = Field(default=None, description="本步实际剂量（克）")
