/** 小程序入口：创建 Vue 应用并挂载 Pinia 状态管理。 */

import { createApp } from "vue";
import { createPinia } from "pinia";
import App from "./App.vue";

const app = createApp(App);
app.use(createPinia());
app.mount();
