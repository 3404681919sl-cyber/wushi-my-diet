/** 病症 / 食物地图 / 冲突 状态管理。复用 T2 的 tolerance store 仅做本地镜像时可用；
 * 此处以服务端 /map 计算为准，缓存食物三色安全、个性化剂量与冲突列表。
 */

import { defineStore } from "pinia";
import { ref } from "vue";
import {
  createCondition,
  deleteCondition,
  listConditions,
  listConflicts,
  updateCondition,
  type ConditionPayload,
} from "../api/profile";
import { getMap } from "../api/map";
import type { ConditionOut, FoodSafetyOut } from "../api/types";

export const useConditionStore = defineStore("condition", () => {
  const conditions = ref<ConditionOut[]>([]);
  const foodMap = ref<FoodSafetyOut[]>([]);
  const conflicts = ref<Record<string, unknown>[]>([]);
  const loading = ref(false);

  /** 载入健康状况列表。 */
  async function loadConditions(): Promise<void> {
    conditions.value = await listConditions();
  }

  /** 新增健康状况，成功后刷新地图（安全等级依赖病症）。 */
  async function addCondition(payload: ConditionPayload): Promise<ConditionOut> {
    const created = await createCondition(payload);
    conditions.value = [...conditions.value, created];
    await loadMap();
    return created;
  }

  /**
   * 删除健康状况。
   * 注意：后端暂未实现 DELETE /profile/conditions/{id}（gap），调用会抛 ApiError；
   * 这里本地先行移除以保持 UI 一致，并把错误向上抛出，由页面提示该 gap。
   */
  async function removeCondition(id: number): Promise<void> {
    try {
      await deleteCondition(id);
    } catch (err) {
      conditions.value = conditions.value.filter((c) => c.id !== id);
      throw err;
    }
    conditions.value = conditions.value.filter((c) => c.id !== id);
    await loadMap();
  }

  /**
   * 更新健康状况（后端暂未实现 PUT /profile/conditions/{id}，gap）。
   */
  async function editCondition(
    id: number,
    payload: Partial<ConditionPayload>
  ): Promise<ConditionOut> {
    const updated = await updateCondition(id, payload);
    const idx = conditions.value.findIndex((c) => c.id === id);
    if (idx >= 0) conditions.value[idx] = updated;
    await loadMap();
    return updated;
  }

  /** 载入食物地图（三色安全 + 三剂量 + 冲突）；可按名称过滤。 */
  async function loadMap(category?: string): Promise<void> {
    loading.value = true;
    try {
      const map = await getMap(category);
      foodMap.value = map.items;
    } finally {
      loading.value = false;
    }
  }

  /** 载入全部冲突。 */
  async function loadConflicts(): Promise<void> {
    conflicts.value = await listConflicts();
  }

  return {
    conditions,
    foodMap,
    conflicts,
    loading,
    loadConditions,
    addCondition,
    removeCondition,
    editCondition,
    loadMap,
    loadConflicts,
  };
});
