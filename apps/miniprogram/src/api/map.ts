/** 食物地图 / 安全评估 API（对齐后端 /api/v1/map）。
 * 注：独立的 /foods 目录端点后端未实现，/map 已包含完整食物目录 + 三色 + 三剂量 + 冲突，
 * 因此前端以 /map 作为食物图谱的数据源（见汇报 gap）。
 */

import { get } from "./request";
import type { MapOut } from "./types";

/** 获取当前用户视角下各食物的安全等级与三色剂量（可按名称子串过滤）。 */
export const getMap = (category?: string) => {
  const url = category ? `/map?category=${encodeURIComponent(category)}` : "/map";
  return get<MapOut>(url, true);
};
