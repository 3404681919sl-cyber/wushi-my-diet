import type { AppConfig } from "./index";

/** 生产环境配置（线上域名，需在小程序后台配置 request 合法域名）。 */
const prodConfig: AppConfig = {
  apiBaseUrl: "https://api.wushi.app",
  isProd: true,
};

export default prodConfig;
