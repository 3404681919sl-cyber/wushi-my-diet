/** 微挑战 API（对齐后端 /api/v1/challenge）。 */

import { get, post } from "./request";
import type { ChallengeOut } from "./types";

/** 为某食物创建微挑战，后端自动生成 3 步剂量阶梯。 */
export const createChallenge = (food_id: number) =>
  post<ChallengeOut>("/challenge", { food_id }, true);

/** 列出当前用户全部微挑战。 */
export const listChallenges = () => get<ChallengeOut[]>("/challenge", true);

/** 获取单个微挑战详情。 */
export const getChallenge = (id: number) => get<ChallengeOut>(`/challenge/${id}`, true);

/** 记录某步骤反应结果（severity 0~10），后端重算并返回更新后的阈值。 */
export const recordStep = (
  id: number,
  step_no: number,
  severity: number,
  dose_g?: number
) =>
  post<ChallengeOut>(
    `/challenge/${id}/step`,
    { step_no, severity, dose_g },
    true
  );
