"""SQLAlchemy 模型聚合导入。

导入本模块会触发所有模型子模块加载，确保 ``Base.metadata`` 收集到全部表定义，
供 ``create_all`` 与 Alembic autogenerate 使用。
"""

from app.models.user import User
from app.models.profile import Profile
from app.models.condition import Condition
from app.models.symptom import SymptomDef, SymptomLog
from app.models.meal import MealLog, MealItem
from app.models.challenge import Challenge, ChallengeStep
from app.models.food import Food
from app.models.tolerance import ToleranceThreshold

__all__ = [
    "User",
    "Profile",
    "Condition",
    "SymptomDef",
    "SymptomLog",
    "MealLog",
    "MealItem",
    "Challenge",
    "ChallengeStep",
    "Food",
    "ToleranceThreshold",
]
