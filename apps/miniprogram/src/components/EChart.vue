<template>
  <canvas
    :id="canvasId"
    type="2d"
    :style="{ width: width + 'px', height: height + 'px' }"
  />
</template>

<script setup lang="ts">
import { onMounted, watch, onUnmounted } from "vue";
import Taro from "@tarojs/taro";
import * as echarts from "echarts";

const props = withDefaults(
  defineProps<{
    canvasId?: string;
    option: Record<string, unknown>;
    width?: number;
    height?: number;
  }>(),
  {
    canvasId: "wushi-echart",
    width: 330,
    height: 260,
  }
);

/* eslint-disable @typescript-eslint/no-explicit-any */
let chart: any = null;
let retryTimer: ReturnType<typeof setTimeout> | null = null;

function getDpr(): number {
  try {
    const info = Taro.getWindowInfo ? Taro.getWindowInfo() : Taro.getSystemInfoSync();
    return info.pixelRatio || 2;
  } catch {
    return 2;
  }
}

function renderChart(): void {
  const query = Taro.createSelectorQuery();
  query
    .select("#" + props.canvasId)
    .fields({ node: true, size: true })
    .exec((res: any) => {
      if (!res || !res[0] || !res[0].node) {
        // 元素尚未就绪，稍后重试
        retryTimer = setTimeout(renderChart, 200);
        return;
      }
      const canvas = res[0].node;
      const ctx = canvas.getContext("2d");
      canvas.setContext(ctx);
      const dpr = getDpr();
      canvas.width = res[0].width * dpr;
      canvas.height = res[0].height * dpr;
      chart = echarts.init(canvas, "", {
        width: res[0].width,
        height: res[0].height,
        devicePixelRatio: dpr,
      });
      chart.setOption(props.option);
    });
}

watch(
  () => props.option,
  (opt) => {
    if (chart) chart.setOption(opt, true);
  },
  { deep: true }
);

onMounted(() => {
  renderChart();
});

onUnmounted(() => {
  if (retryTimer) clearTimeout(retryTimer);
  if (chart) chart.dispose();
});
/* eslint-enable @typescript-eslint/no-explicit-any */
</script>
