<template>
  <nut-tabbar
    :model-value="active"
    bottom
    unactive-color="#9aa8a2"
    active-color="hsl(150 18% 32%)"
    @tab-switch="onSwitch"
  >
    <nut-tabbar-item
      v-for="(p, idx) in pages"
      :key="p.path"
      :tab-title="p.title"
    />
  </nut-tabbar>
</template>

<script setup lang="ts">
import Taro from "@tarojs/taro";

defineProps<{ active: number }>();

interface PageEntry {
  path: string;
  title: string;
}

const pages: PageEntry[] = [
  { path: "/pages/food-map/index", title: "图谱" },
  { path: "/pages/symptom-log/index", title: "症状" },
  { path: "/pages/challenge/index", title: "挑战" },
  { path: "/pages/recipe/index", title: "食谱" },
  { path: "/pages/growth/index", title: "成长" },
];

function onSwitch(index: number): void {
  const target = pages[index];
  if (!target) return;
  Taro.redirectTo({ url: target.path }).catch(() => {
    Taro.navigateTo({ url: target.path });
  });
}
</script>
