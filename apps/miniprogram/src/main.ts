/** 小程序入口：创建 Vue 应用，挂载 Pinia 与 NutUI，引入全局样式。 */

import { createApp } from "vue";
import { createPinia } from "pinia";
import NutUI from "@nutui/nutui-taro";
import "@nutui/nutui-taro/dist/style.css";
import App from "./App.vue";
import "./styles/global.css";

const app = createApp(App);
app.use(createPinia());
// 全局注册 NutUI 全部组件（nut-button / nut-popup / nut-tag 等）
app.use(NutUI);
// Taro 运行时会忽略挂载容器参数，仅用于满足 Vue 类型签名
app.mount("#app");
