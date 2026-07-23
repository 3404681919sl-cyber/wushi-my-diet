/**
 * 吾食（Wushi）前后端共享 TS 接口。
 * 后端 Pydantic schema 与之保持字段语义一致（传输层 snake_case 由别名兼容）。
 */

import type { FodmapCategory, GoalType, HistamineLevel, SafetyLevel } from "./enums";

/** 三色安全徽章（展示用）。 */
export interface SafetyBadge {
  level: SafetyLevel;
  /** 展示文案，如「超级安全」「待探索」「心爱禁忌」。 */
  label: string;
}

/** 目标权重：各维度权重（和约 1）。 */
export type TargetWeight = Record<GoalType, number>;

/** 食物 FODMAP 标注（六类等级）。 */
export type FodmapFlags = Partial<Record<FodmapCategory, "none" | "low" | "moderate" | "high">>;

/** 基础营养素。 */
export interface Nutrition {
  kcal: number;
  proteinG: number;
  fatG: number;
  carbG: number;
}

/** 个性化耐受阈值数据传输对象（前端镜像展示）。 */
export interface ToleranceDTO {
  foodId: number;
  safety: SafetyLevel;
  safeDoseG: number;
  cautionDoseG: number;
  unsafeDoseG: number;
  nObs: number;
}

/** 食谱单项。 */
export interface RecipeItemDTO {
  food: string;
  amountG: number;
  safety: SafetyLevel;
  replaceableWith: string[];
  reason: string;
}

/** 食谱 JSON（DeepSeek 生成 / 模板回退的统一结构）。 */
export interface RecipeJSON {
  recipeId: string;
  title: string;
  targetWeights: Partial<Record<GoalType, number>>;
  items: RecipeItemDTO[];
  totalFodmapLoad: number;
  totalGl: number;
  burdenWarning: string | null;
  steps: string[];
  nutrition: Nutrition;
  exploratoryInserts: string[];
}

/** 食物（前端展示雏形）。 */
export interface FoodDTO {
  id: number;
  name: string;
  fodmapCategory: FodmapFlags;
  gi: number;
  glPer100g: number;
  histamineLevel: HistamineLevel;
  nutrients: Nutrition;
  isPreset: boolean;
}
