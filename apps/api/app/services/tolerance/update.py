"""区间删失观测下的 log-normal 剂量阈值闭式共轭更新（T2）。

模型：用户对某食物的耐受阈值 ``θ``（克）服从 log-normal，即
``z = log θ ~ Normal(μ, σ²)``。微挑战 / 餐日志给出**区间删失**观测：

- 无反应（severity = 0）：``θ > dose`` → 阈值在剂量之上（软下界）；
- 有反应（severity > 0）：``θ < dose`` → 阈值在剂量之下（软上界）。

将删失观测折算为带噪声的伪点观测 ``z_i``，按正态共轭闭式更新：

    τ0 = 1 / var0
    s_i² = 观测噪声（≈ 0.5²）
    τn = τ0 + Σ 1/s_i²
    μn = (τ0·μ0 + Σ z_i / s_i²) / τn
    varn = 1 / τn

注：伪点观测方向保证物理正确——无反应把后验往上拉（更能耐受），
有反应把后验往下拉（更敏感）；边距 ``m`` 随 severity 增大而收缩
（反应越强，越确信阈值就落在剂量之下）。
"""

from __future__ import annotations

import math
from dataclasses import dataclass

# 观测噪声标准差（log 空间）；对应方差 0.25，单条观测精度 4
OBS_NOISE = 0.5
# 软边距基准（log 空间）；随 severity 增大而收缩
BASE_MARGIN = 0.5
# 三色分位对应的标准正态分位数（5% / 50% / 95%）
Z_QUANTILE = 1.645


@dataclass
class UpdateResult:
    """共轭更新结果。"""

    mean: float
    var: float
    n_obs: int


def _censored_point(dose: float, severity: int) -> float:
    """将一条区间删失观测折算为 log 空间伪点估计 ``z_i``。

    - 无反应（severity ≤ 0）：阈值高于剂量，估计落在 ``log(dose)`` 之上；
    - 有反应（severity > 0）：阈值低于剂量，估计落在 ``log(dose)`` 之下，
      边距 ``m = BASE_MARGIN / (1 + severity)`` 随严重度收缩。
    """
    dose = max(dose, 0.5)
    margin = BASE_MARGIN / (1.0 + max(severity, 0))
    if severity <= 0:
        return math.log(dose) + margin
    return math.log(dose) - margin


def conjugate_update(
    mean0: float,
    var0: float,
    observations: list[tuple[float, int]],
) -> UpdateResult:
    """对 log 空间正态先验做区间删失观测的闭式共轭更新。

    Args:
        mean0: 先验均值（log 空间）。
        var0: 先验方差（log 空间）。
        observations: 观测列表，元素为 ``(dose_g, severity)``；
            ``severity == 0`` 表示无反应，``> 0`` 表示有反应。

    Returns:
        ``UpdateResult``：更新后的 ``(mean, var)`` 与观测条数。
    """
    if var0 <= 0:
        var0 = 1e-6
    tau = 1.0 / var0
    weighted = tau * mean0
    noise2 = OBS_NOISE ** 2

    for dose, severity in observations:
        z = _censored_point(dose, severity)
        tau += 1.0 / noise2
        weighted += z / noise2

    var = 1.0 / tau
    mean = weighted / tau
    return UpdateResult(mean=mean, var=var, n_obs=len(observations))


def quantile_doses(mean: float, var: float) -> tuple[int, int, int]:
    """由 log 空间后验产出三色分位剂量（克，整数）。

    按架构修正版（safe/unsafe 与文档原始方向相反）：

        safe_g    = exp(μ − 1.645σ)   # 5% 分位：高度安全剂量
        caution_g = exp(μ)            # 中位数：谨慎剂量
        unsafe_g  = exp(μ + 1.645σ)   # 95% 分位：可能不安全剂量
    """
    sigma = math.sqrt(max(var, 1e-9))
    safe = int(round(math.exp(mean - Z_QUANTILE * sigma)))
    caution = int(round(math.exp(mean)))
    unsafe = int(round(math.exp(mean + Z_QUANTILE * sigma)))
    return safe, caution, unsafe
