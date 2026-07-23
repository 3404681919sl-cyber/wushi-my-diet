/** 症状日志 API（对齐任务描述的 /api/v1/symptoms/log）。
 * 重要 gap：后端尚未提供 /symptoms/log 端点（仅有 SymptomLog 模型与 symptom_logs 表）。
 * 为让「症状日志页」在本地联调中可用，前端优先调用真实接口；若后端返回 404，则回落到
 * 本地存储（Taro storage），并在页面提示该 gap。前端不私自改动后端。
 */

import Taro from "@tarojs/taro";
import { post } from "./request";
import type { SymptomLogLocal } from "./types";

const LOG_KEY = "wushi_symptom_logs";

/** 读取本地症状日志（按时间倒序）。 */
export function getLocalLogs(): SymptomLogLocal[] {
  return (Taro.getStorageSync(LOG_KEY) as SymptomLogLocal[]) || [];
}

export interface LogSymptomInput {
  symptom_def_id: number;
  symptom_name: string;
  severity: number;
  logged_at: string;
}

/**
 * 记录一条症状日志。
 * @returns persisted 标记落库位置（"server"=后端成功 / "local"=后端缺失，已本地兜底）。
 */
export async function logSymptom(
  input: LogSymptomInput
): Promise<{ persisted: "server" | "local"; data: SymptomLogLocal }> {
  const entry: SymptomLogLocal = {
    id: `local-${Date.now()}`,
    symptom_def_id: input.symptom_def_id,
    symptom_name: input.symptom_name,
    severity: input.severity,
    logged_at: input.logged_at,
  };

  try {
    await post(
      "/symptoms/log",
      {
        symptom_def_id: input.symptom_def_id,
        severity: input.severity,
        logged_at: input.logged_at,
      },
      true
    );
    return { persisted: "server", data: entry };
  } catch {
    // 后端 gap：本地兜底保存，保证页面可用
    const logs = getLocalLogs();
    logs.unshift(entry);
    Taro.setStorageSync(LOG_KEY, logs);
    return { persisted: "local", data: entry };
  }
}
