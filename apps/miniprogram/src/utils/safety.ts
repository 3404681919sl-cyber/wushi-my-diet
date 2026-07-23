/**
 * 三色安全等级计算（与后端 app/services/safety.py 规则一致）。
 *
 * 规则（docs/system_design.md §9.4）：
 *   conflict = 食物与任一 active 状况存在硬冲突
 *   has_data = nObs ≥ 3
 *   if conflict && !has_data:        RED
 *   else if !conflict && safeG ≥ serving:  GREEN
 *   else:                                 YELLOW
 * 用户手动标记 🔴（overrideRed）强制 RED。
 */

import { FodmapCategory, SafetyLevel } from "@wushi/shared";

export interface FoodLike {
  fodmapCategory?: Partial<Record<FodmapCategory, string>>;
  gi?: number;
  histamineLevel?: string;
}

export interface ConditionLike {
  isActive?: boolean;
  fodmapFlags?: Record<string, boolean>;
  glucoseFlag?: boolean;
  histamineFlag?: boolean;
  name?: string;
}

export interface ThresholdLike {
  safeG?: number;
  nObs?: number;
}

export interface Conflict {
  source: string;
  dimension: string;
  isHard: boolean;
  note: string;
}

const DEFAULT_SERVING_G = 100;
const MIN_OBS_FOR_DATA = 3;
const HIGH_GI = 70;
const HARD_FODMAP_LEVEL = "high";
const HISTAMINE_CONFLICT = ["moderate", "high"];

export function findConflicts(food: FoodLike, conditions: ConditionLike[]): Conflict[] {
  const result: Conflict[] = [];
  for (const cond of conditions) {
    if (cond.isActive === false) continue;
    const name = cond.name ?? "condition";
    const fodmapFlags = cond.fodmapFlags ?? {};
    for (const [dim, flag] of Object.entries(fodmapFlags)) {
      if (!flag) continue;
      const level = (food.fodmapCategory?.[dim as FodmapCategory] ?? "").toLowerCase();
      if (level === "moderate" || level === "high") {
        result.push({
          source: name,
          dimension: `fodmap:${dim}`,
          isHard: level === HARD_FODMAP_LEVEL,
          note: `${name} 忌 ${dim}`,
        });
      }
    }
    if (cond.glucoseFlag && (food.gi ?? 0) >= HIGH_GI) {
      result.push({ source: name, dimension: "glucose", isHard: true, note: `${name} 需控糖` });
    }
    const hist = (food.histamineLevel ?? "unknown").toLowerCase();
    if (cond.histamineFlag && HISTAMINE_CONFLICT.includes(hist)) {
      result.push({
        source: name,
        dimension: "histamine",
        isHard: hist === "high",
        note: `${name} 忌组胺`,
      });
    }
  }
  return result;
}

export function hasHardConflict(food: FoodLike, conditions: ConditionLike[]): boolean {
  return findConflicts(food, conditions).some((c) => c.isHard);
}

export function computeSafety(
  food: FoodLike,
  conditions: ConditionLike[],
  threshold?: ThresholdLike | null,
  opts?: { overrideRed?: boolean; servingG?: number }
): { level: SafetyLevel; reason: string } {
  if (opts?.overrideRed) {
    return { level: SafetyLevel.RED, reason: "用户手动标记心爱禁忌" };
  }
  const conflict = hasHardConflict(food, conditions);
  const hasData = !!threshold && (threshold.nObs ?? 0) >= MIN_OBS_FOR_DATA;
  const serving = opts?.servingG ?? DEFAULT_SERVING_G;
  const safeG = threshold?.safeG ?? 0;

  if (conflict && !hasData) {
    return { level: SafetyLevel.RED, reason: "与当前状况硬冲突且无充分耐受数据" };
  }
  if (!conflict && safeG >= serving) {
    return {
      level: SafetyLevel.GREEN,
      reason: `无冲突且安全剂量 ${safeG}g ≥ 常用份量 ${serving}g`,
    };
  }
  return { level: SafetyLevel.YELLOW, reason: "数据不足 / 部分冲突，待探索" };
}
