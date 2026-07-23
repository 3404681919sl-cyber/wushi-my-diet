/** 画像 / 病症 / 症状词典 API（对齐后端 /api/v1/profile）。
 * 说明：症状词典列表实际路径为 /profile/symptoms（非任务描述的 /symptoms）。
 * 病症目前仅提供 增(GET/POST) 与 查(GET)，改/删接口后端尚未实现（见汇报 gap）。
 */

import { del, get, post, put } from "./request";
import type { ConditionOut, ProfileOut, SymptomDefOut } from "./types";

export interface ConditionPayload {
  name: string;
  fodmap_flags?: Record<string, boolean>;
  glucose_flag?: boolean;
  histamine_flag?: boolean;
  is_active?: boolean;
  note?: string;
}

export const getProfile = () => get<ProfileOut>("/profile", true);

export const updateProfile = (target_weights: Record<string, number>) =>
  put<ProfileOut>("/profile", { target_weights }, true);

/** 录入一条健康状况。 */
export const createCondition = (payload: ConditionPayload) =>
  post<ConditionOut>("/profile/conditions", payload, true);

/** 列出全部健康状况。 */
export const listConditions = () => get<ConditionOut[]>("/profile/conditions", true);

/** 更新健康状况（后端当前未实现，调用会 404，见汇报 gap）。 */
export const updateCondition = (id: number, payload: Partial<ConditionPayload>) =>
  put<ConditionOut>(`/profile/conditions/${id}`, payload, true);

/** 删除健康状况（后端当前未实现，调用会 404，见汇报 gap）。 */
export const deleteCondition = (id: number) =>
  del<void>(`/profile/conditions/${id}`, true);

/** 全部食物 × 当前 active 状况的冲突列表。 */
export const listConflicts = () =>
  get<Array<Record<string, unknown>>>("/profile/conflicts", true);

/** 列出症状词典（实际路径 /profile/symptoms）。 */
export const listSymptoms = () => get<SymptomDefOut[]>("/profile/symptoms", true);

/** 新增自定义症状词典条目。 */
export const createSymptom = (payload: {
  name: string;
  scale_max?: number;
  is_custom?: boolean;
}) => post<SymptomDefOut>("/profile/symptoms", payload, true);
