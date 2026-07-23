/** 微挑战状态管理：创建挑战、加载列表、逐步记录反应并跟踪阈值更新。 */

import { defineStore } from "pinia";
import { ref } from "vue";
import {
  createChallenge,
  getChallenge,
  listChallenges,
  recordStep,
} from "../api/challenge";
import type { ChallengeOut } from "../api/types";

export const useChallengeStore = defineStore("challenge", () => {
  const list = ref<ChallengeOut[]>([]);
  const current = ref<ChallengeOut | null>(null);
  const loading = ref(false);

  /** 载入当前用户全部微挑战。 */
  async function loadList(): Promise<void> {
    list.value = await listChallenges();
  }

  /** 为某食物创建微挑战（后端自动生成 3 步），设为当前挑战。 */
  async function start(foodId: number): Promise<ChallengeOut> {
    const created = await createChallenge(foodId);
    current.value = created;
    list.value = [created, ...list.value.filter((c) => c.id !== created.id)];
    return created;
  }

  /** 载入单个挑战详情。 */
  async function loadOne(id: number): Promise<void> {
    current.value = await getChallenge(id);
  }

  /** 记录某步骤反应严重度，后端重算阈值后更新当前挑战。 */
  async function record(
    id: number,
    stepNo: number,
    severity: number,
    doseG?: number
  ): Promise<ChallengeOut> {
    const updated = await recordStep(id, stepNo, severity, doseG);
    current.value = updated;
    const idx = list.value.findIndex((c) => c.id === id);
    if (idx >= 0) list.value[idx] = updated;
    return updated;
  }

  /** 清空当前挑战（用于「换一种食物」）。 */
  function clear(): void {
    current.value = null;
  }

  return { list, current, loading, loadList, start, loadOne, record, clear };
});
