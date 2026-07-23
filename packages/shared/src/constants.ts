/**
 * 吾食（Wushi）前后端共享常量。
 * API 路径、安全等级文案、默认目标权重等集中管理。
 */

import { GoalType, SafetyLevel } from "./enums";
import type { TargetWeight } from "./types";

/** API 基础路径前缀（与后端 main.py 挂载前缀一致）。 */
export const API_BASE = "/api/v1";

/** 各业务域路由前缀。 */
export const API_PATHS = {
  auth: `${API_BASE}/auth`,
  profile: `${API_BASE}/profile`,
  challenge: `${API_BASE}/challenge`,
  recipe: `${API_BASE}/recipe`,
  map: `${API_BASE}/map`,
} as const;

/** 三色安全等级展示文案。 */
export const SAFETY_LABELS: Record<SafetyLevel, string> = {
  [SafetyLevel.GREEN]: "超级安全",
  [SafetyLevel.YELLOW]: "待探索",
  [SafetyLevel.RED]: "心爱禁忌",
};

/** 三色对应的主题色（前端 UI 使用）。 */
export const SAFETY_COLORS: Record<SafetyLevel, string> = {
  [SafetyLevel.GREEN]: "#2BA471",
  [SafetyLevel.YELLOW]: "#E37318",
  [SafetyLevel.RED]: "#D54941",
};

/** 默认目标权重（与后端 Profile.target_weights 默认一致）。 */
export const DEFAULT_TARGET_WEIGHTS: TargetWeight = {
  [GoalType.GUT_STABILITY]: 0.7,
  [GoalType.BLOOD_SUGAR]: 0.2,
  [GoalType.FAT_LOSS]: 0.1,
};

/** 组合负担默认值（医学建议，可在 B3 中微调）。 */
export const BURDEN_LIMITS = {
  /** 单餐 FODMAP 总阈值（gram，示例值）。 */
  fodmapPerMeal: 0.5,
  /** 单餐血糖负荷（GL）中负荷阈值。 */
  glPerMeal: 20,
} as const;

/** 微信类目定位文案（健康 / 食品管理，非医疗诊断）。 */
export const PRODUCT_POSITIONING = "健康/食品管理（非医疗诊断）";
