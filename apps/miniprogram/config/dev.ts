import type { AppConfig } from "./index";

/** 开发环境配置（本地联调）。 */
const devConfig: AppConfig = {
  apiBaseUrl: "http://localhost:8000",
  isProd: false,
};

export default devConfig;
