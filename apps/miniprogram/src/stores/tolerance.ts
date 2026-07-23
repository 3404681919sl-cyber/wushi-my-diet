/**
 * 三色与耐受阈值前端镜像 store（与后端计算保持一致，用于首页即时展示；
 * 服务端重算为准）。统一经 services/* 调 /api/v1 写操作，本 store 仅做本地镜像。
 */

import { defineStore } from "pinia";
import { computed, ref } from "vue";
import { SafetyLevel } from "@wushi/shared";
import { computeSafety, type ConditionLike, type FoodLike, type ThresholdLike } from "../utils/safety";

export interface ToleranceItem {
  foodId: number;
  foodName: string;
  safety: SafetyLevel;
  safeG: number;
  cautionG: number;
  unsafeG: number;
  nObs: number;
}

export const useToleranceStore = defineStore("tolerance", () => {
  const items = ref<ToleranceItem[]>([]);
  const loading = ref(false);

  const counts = computed(() => {
    const c = { green: 0, yellow: 0, red: 0 };
    for (const it of items.value) {
      if (it.safety === SafetyLevel.GREEN) c.green += 1;
      else if (it.safety === SafetyLevel.YELLOW) c.yellow += 1;
      else if (it.safety === SafetyLevel.RED) c.red += 1;
    }
    return c;
  });

  function setItems(next: ToleranceItem[]) {
    items.value = next;
  }

  function computeOne(
    food: FoodLike,
    conditions: ConditionLike[],
    threshold?: ThresholdLike | null
  ) {
    return computeSafety(food, conditions, threshold);
  }

  return { items, loading, counts, setItems, computeOne };
});
