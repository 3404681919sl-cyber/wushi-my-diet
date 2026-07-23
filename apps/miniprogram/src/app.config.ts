/** 小程序全局配置（Taro）：注册 5 个核心页面与窗口样式。 */

export default defineAppConfig({
  pages: [
    "pages/food-map/index",
    "pages/symptom-log/index",
    "pages/challenge/index",
    "pages/recipe/index",
    "pages/growth/index",
  ],
  window: {
    backgroundTextStyle: "light",
    navigationBarBackgroundColor: "#ffffff",
    navigationBarTitleText: "吾食",
    navigationBarTextStyle: "black",
  },
});
