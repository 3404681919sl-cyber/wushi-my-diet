/** 环境感知配置入口：根据 NODE_ENV 选择 dev / prod。 */

import devConfig from "./dev";
import prodConfig from "./prod";

export interface AppConfig {
  /** 后端 API 基础地址（小程序端走相对路径或完整域名）。 */
  apiBaseUrl: string;
  /** 是否生产环境。 */
  isProd: boolean;
}

const isProd = process.env.NODE_ENV === "production";

const config: AppConfig = isProd ? prodConfig : devConfig;

export default config;
