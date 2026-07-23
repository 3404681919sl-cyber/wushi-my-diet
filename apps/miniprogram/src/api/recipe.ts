/** 智能食谱 API（对齐后端 /api/v1/recipe）。 */

import { post } from "./request";
import type { RecipeOut } from "./types";

export interface RecipePayload {
  goal?: string; // "gut_stability" | "blood_sugar" | "fat_loss"
  avoid_food_ids?: number[];
  category?: string;
  body_state?: string;
}

/** 生成食谱：优先 LLM，无 key / 失败静默回退模板。 */
export const createRecipe = (payload: RecipePayload) =>
  post<RecipeOut>("/recipe", payload, true);
