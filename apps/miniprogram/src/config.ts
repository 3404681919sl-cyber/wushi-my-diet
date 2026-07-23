/** 运行时配置（API 地址、主题色等）。已从 config/index.ts 迁移，避免与 Taro 编译配置冲突。 */

import { API_BASE } from "@wushi/shared";

/** API 路径前缀（来自 @wushi/shared，默认 /api/v1）。 */
export const API_PREFIX = API_BASE;

/** 后端基础地址：本地联调默认 localhost:8000；生产构建可经环境变量覆盖。 */
export const API_BASE_URL = "http://localhost:8000";

/** 主题色：鼠尾草绿。 */
export const THEME_COLOR = "hsl(150 18% 32%)";
