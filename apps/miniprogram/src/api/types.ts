/** 前端 API 类型定义（字段严格对齐后端 Pydantic schema 的 JSON wire 格式，snake_case）。 */

/** 食物响应（对齐 FoodOut）。 */
export interface FoodOut {
  id: number;
  name: string;
  fodmap_category: Record<string, string>;
  gi: number;
  gl_per_100g: number;
  histamine_level: string;
  nutrients: Record<string, number>;
  is_preset: boolean;
}

/** 单条冲突（对齐 ConflictOut）。 */
export interface ConflictOut {
  dimension: string;
  condition_name: string;
  food_attribute: string;
  severity: string; // "hard" | "soft"
  message: string;
}

/** 单食物安全评估（对齐 FoodSafetyOut）。 */
export interface FoodSafetyOut {
  food: FoodOut;
  level: string; // "green" | "yellow" | "red"
  reason: string;
  safe_g: number;
  caution_g: number;
  unsafe_g: number;
  conflicts: ConflictOut[];
}

/** 食物地图响应（对齐 MapOut）。 */
export interface MapOut {
  items: FoodSafetyOut[];
}

/** 健康状况（对齐 ConditionOut）。 */
export interface ConditionOut {
  id: number;
  user_id: number;
  name: string;
  fodmap_flags: Record<string, boolean>;
  glucose_flag: boolean;
  histamine_flag: boolean;
  is_active: boolean;
  note: string;
}

/** 症状词典条目（对齐 SymptomDefOut）。 */
export interface SymptomDefOut {
  id: number;
  user_id: number;
  name: string;
  scale_max: number;
  is_custom: boolean;
}

/** 画像响应（对齐 ProfileOut）。 */
export interface ProfileOut {
  user_id: number;
  target_weights: Record<string, number>;
  created_at: string;
  updated_at: string;
  conditions: ConditionOut[];
  symptom_defs: SymptomDefOut[];
}

/** 微挑战步骤（对齐 ChallengeStepOut）。 */
export interface ChallengeStepOut {
  id: number;
  challenge_id: number;
  step_no: number;
  dose_g: number;
  result: string | null;
  severity: number | null;
  logged_at: string | null;
}

/** 微挑战响应（对齐 ChallengeOut）。 */
export interface ChallengeOut {
  id: number;
  user_id: number;
  food_id: number;
  status: string;
  created_at: string;
  steps: ChallengeStepOut[];
  n_obs: number;
  safe_g: number;
  caution_g: number;
  unsafe_g: number;
}

/** 食谱单项（对齐 RecipeItemOut）。 */
export interface RecipeItemOut {
  food_id: number | null;
  name: string;
  amount_g: number;
  safety: string | null;
  replaceable_with: string[];
  reason: string | null;
}

/** 食谱响应（对齐 RecipeOut）。 */
export interface RecipeOut {
  generated_by: string;
  engine: string; // "llm" | "template"
  title: string;
  items: RecipeItemOut[];
  note: string;
}

/** 登录 / 注册令牌（对齐 Token）。 */
export interface TokenOut {
  access_token: string;
  token_type: string;
}

/** 用户公开信息（对齐 UserOut）。 */
export interface UserOut {
  id: number;
  nickname: string;
  phone: string | null;
  email: string | null;
  created_at: string;
}

/** 症状日志本地落库结构（后端 /symptoms/log 尚未提供，前端本地兜底）。 */
export interface SymptomLogLocal {
  id: string;
  symptom_def_id: number;
  symptom_name: string;
  severity: number;
  logged_at: string;
}
