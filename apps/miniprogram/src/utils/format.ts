/** 通用格式化工具（前端）。复用 @wushi/shared 的枚举 / 常量。 */

import {
  SAFETY_LABELS,
  SAFETY_COLORS,
  SafetyLevel,
  type FodmapCategory,
} from "@wushi/shared";

/** 将三色安全等级（字符串或枚举）转换为展示文案。 */
export function safetyLabel(level: string | SafetyLevel): string {
  if (typeof level === "string") {
    return SAFETY_LABELS[level as SafetyLevel] ?? level;
  }
  return SAFETY_LABELS[level];
}

/** 将三色安全等级字符串映射为对应的主题色（鼠尾草绿系外的红/黄/绿）。 */
export function safetyColor(level: string | SafetyLevel): string {
  const key = typeof level === "string" ? (level as SafetyLevel) : level;
  return SAFETY_COLORS[key] ?? "#9aa8a2";
}

/** 克数格式化（保留 0~1 位小数）。 */
export function formatGrams(value: number): string {
  return `${Number(value.toFixed(1))} g`;
}

/** FODMAP 维度中文名映射。 */
const FODMAP_CN: Record<string, string> = {
  fructan: "果聚糖",
  gos: "低聚半乳糖",
  lactose: "乳糖",
  fructose: "果糖",
  sorbitol: "山梨醇",
  mannitol: "甘露醇",
};

export function fodmapCn(dim: string): string {
  return FODMAP_CN[dim] ?? dim;
}

export function fodmapCategoriesCn(
  flags: Record<string, string>
): string[] {
  return Object.entries(flags)
    .filter(([, v]) => v === "high" || v === "moderate")
    .map(([k]) => fodmapCn(k as FodmapCategory));
}

/** 时间格式化为 YYYY-MM-DD HH:mm（本地）。 */
export function formatDateTime(iso: string): string {
  const d = new Date(iso);
  if (isNaN(d.getTime())) return iso;
  const pad = (n: number) => `${n}`.padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(
    d.getHours()
  )}:${pad(d.getMinutes())}`;
}
