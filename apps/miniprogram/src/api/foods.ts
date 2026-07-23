/** 食物目录 API（对齐后端 /api/v1/foods）。

 * 返回系统预设 + 用户自建食物目录（含 fodmap_category / gi / gl_per_100g /
 * histamine_level 等），供食物选择场景使用；三色安全评估仍走 /map。
 */

import { get } from "./request";
import type { FoodOut } from "./types";

/** 获取食物目录（按 id 升序）。 */
export const listFoods = () => get<FoodOut[]>("/foods", true);
