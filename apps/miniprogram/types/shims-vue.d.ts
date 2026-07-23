/** Vue 单文件组件类型声明（供 tsc / vue-tsc 解析 `*.vue` 导入）。 */

declare module "*.vue" {
  import type { DefineComponent } from "vue";
  const component: DefineComponent<Record<string, unknown>, Record<string, unknown>, unknown>;
  export default component;
}
