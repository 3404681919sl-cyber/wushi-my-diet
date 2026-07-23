<template>
  <view class="app-root">
    <slot />
  </view>
</template>

<script setup lang="ts">
// 应用根组件：T4 阶段负责应用启动时的登录态恢复。
import { onMounted } from "vue";
import { useAuthStore } from "./stores/auth";

const auth = useAuthStore();

onMounted(() => {
  // 若本地已有 JWT，则静默拉取当前用户信息，保持登录态
  if (auth.isLoggedIn) {
    auth.loadMe().catch(() => {
      // 令牌失效则忽略，由页面登录弹窗重新登录
    });
  }
});
</script>

<style>
.app-root {
  min-height: 100vh;
}
</style>
