/** 症状词典与症状日志状态管理。症状词典来自 /profile/symptoms；
 * 症状日志写入优先调 /symptoms/log，后端缺失时回落本地存储（见 api/symptomLog.ts）。
 */

import { defineStore } from "pinia";
import { ref } from "vue";
import { listSymptoms } from "../api/profile";
import { getLocalLogs, logSymptom, type LogSymptomInput } from "../api/symptomLog";
import type { SymptomDefOut, SymptomLogLocal } from "../api/types";

export const useSymptomStore = defineStore("symptom", () => {
  const defs = ref<SymptomDefOut[]>([]);
  const logs = ref<SymptomLogLocal[]>(getLocalLogs());
  const loading = ref(false);

  /** 载入症状词典。 */
  async function loadDefs(): Promise<void> {
    defs.value = await listSymptoms();
  }

  /** 记录一条症状日志，返回落库方式（server / local）。 */
  async function addLog(
    input: LogSymptomInput
  ): Promise<"server" | "local"> {
    const res = await logSymptom(input);
    if (res.persisted === "local") {
      logs.value = getLocalLogs();
    } else {
      logs.value = [res.data, ...logs.value];
    }
    return res.persisted;
  }

  /** 从本地存储刷新日志列表。 */
  function refreshLogs(): void {
    logs.value = getLocalLogs();
  }

  return { defs, logs, loading, loadDefs, addLog, refreshLogs };
});
