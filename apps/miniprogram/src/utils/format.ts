/** 通用格式化工具（前端）。演示从 @wushi/shared 引入共享枚举 / 常量。 */

import { SAFETY_LABELS, type SafetyLevel } from "@wushi/shared";

/** 将三色安全等级转换为展示文案。 */
export function safetyLabel(level: SafetyLevel): string {
  return SAFETY_LABELS[level];
}

/** 克数格式化（保留 0~1 位小数）。 */
export function formatGrams(value: number): string {
  return `${Number(value.toFixed(1))} g`;
}
