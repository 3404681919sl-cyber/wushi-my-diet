/**
 * 吾食（Wushi）共享枚举。
 * 前后端（小程序 / 后端 schema）统一引用，避免安全等级、症状维度等硬编码漂移。
 */

/** 三色安全等级：🟢 超级安全 / 🟡 待探索冲突食物 / 🔴 心爱禁忌。 */
export enum SafetyLevel {
  GREEN = "green",
  YELLOW = "yellow",
  RED = "red",
}

/** FODMAP 六类（发酵性短链碳水化合物）。 */
export enum FodmapCategory {
  FRUCTAN = "fructan",
  GOS = "gos",
  LACTOSE = "lactose",
  FRUCTOSE = "fructose",
  SORBITOL = "sorbitol",
  MANNITOL = "mannitol",
}

/** FODMAP 各维度等级（用于食物标注与冲突计算）。 */
export enum FodmapLevel {
  NONE = "none",
  LOW = "low",
  MODERATE = "moderate",
  HIGH = "high",
}

/** 组胺等级。 */
export enum HistamineLevel {
  UNKNOWN = "unknown",
  LOW = "low",
  MODERATE = "moderate",
  HIGH = "high",
}

/** 多目标加权维度（与后端 Profile.target_weights 键一致）。 */
export enum GoalType {
  GUT_STABILITY = "gut_stability",
  BLOOD_SUGAR = "blood_sugar",
  FAT_LOSS = "fat_loss",
}

/** 冲突 / 矛盾维度（状况可触发其中若干）。 */
export enum SymptomDim {
  FODMAP = "fodmap",
  GLUCOSE = "glucose",
  HISTAMINE = "histamine",
}
