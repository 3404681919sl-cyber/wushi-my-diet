/** Taro 编译配置（构建用）。运行时配置已迁移至 src/config.ts。 */

import { defineConfig } from "@tarojs/cli";
import devConfig from "./dev";
import prodConfig from "./prod";

export default defineConfig({
  ...(process.env.NODE_ENV === "production" ? prodConfig : devConfig),
  projectName: "wushi-miniprogram",
  date: "2025-07-23",
  designWidth: 750,
  deviceRatio: {
    640: 2.34 / 2,
    750: 1,
    375: 2,
    828: 1.81 / 2,
  },
  sourceRoot: "src",
  outputRoot: "dist",
  plugins: [
    "@tarojs/plugin-platform-weapp",
    "@tarojs/plugin-framework-vue3",
  ],
  defineConstants: {},
  copy: {
    patterns: [],
    options: {},
  },
  framework: "vue3",
  compiler: "webpack5",
  mini: {
    postcss: {
      autoprefixer: { enable: true },
      cssModules: { enable: false },
    },
  },
  h5: {
    publicPath: "/",
    staticDirectory: "static",
    postcss: {
      autoprefixer: { enable: true },
      cssModules: { enable: false },
    },
  },
});
