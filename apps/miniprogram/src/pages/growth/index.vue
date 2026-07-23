<template>
  <view class="wushi-page">
    <view class="wushi-header">
      <view>
        <view class="wushi-title">我的成长</view>
        <view class="wushi-sub">耐受进展一览</view>
      </view>
    </view>

    <!-- 概览统计 -->
    <view class="stat-row">
      <view class="stat">
        <view class="stat-num green">{{ counts.green }}</view>
        <view class="wushi-muted">安全</view>
      </view>
      <view class="stat">
        <view class="stat-num yellow">{{ counts.yellow }}</view>
        <view class="wushi-muted">探索</view>
      </view>
      <view class="stat">
        <view class="stat-num red">{{ counts.red }}</view>
        <view class="wushi-muted">禁忌</view>
      </view>
    </view>

    <view class="stat-row">
      <view class="stat">
        <view class="stat-num">{{ challenge.list.length }}</view>
        <view class="wushi-muted">进行中挑战</view>
      </view>
      <view class="stat">
        <view class="stat-num">{{ symptom.logs.length }}</view>
        <view class="wushi-muted">症状记录</view>
      </view>
      <view class="stat">
        <view class="stat-num">{{ condition.conditions.length }}</view>
        <view class="wushi-muted">病症</view>
      </view>
    </view>

    <!-- 耐受分布饼图 -->
    <view class="wushi-card">
      <view class="block-title">耐受分布</view>
      <EChart :option="pieOption" canvas-id="growth-pie" :height="240" />
    </view>

    <!-- 近期挑战阈值 -->
    <view class="wushi-card">
      <view class="block-title">近期挑战阈值</view>
      <view v-for="c in challenge.list" :key="c.id" class="inner">
        <view class="wushi-flex">
          <text class="food-name">{{ foodName(c.food_id) }}</text>
          <text class="wushi-muted">{{ c.n_obs }} 次观测</text>
        </view>
        <view class="wushi-dose-row">
          <view class="wushi-dose"><b>{{ formatGrams(c.safe_g) }}</b>安全</view>
          <view class="wushi-dose"><b>{{ formatGrams(c.caution_g) }}</b>谨慎</view>
          <view class="wushi-dose"><b>{{ formatGrams(c.unsafe_g) }}</b>危险</view>
        </view>
      </view>
      <nut-empty
        v-if="!challenge.list.length"
        description="还没有挑战，去微挑战页试试"
      />
    </view>

    <TabBar :active="4" />
    <LoginModal v-model="showLogin" />
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import TabBar from "../../components/TabBar.vue";
import LoginModal from "../../components/LoginModal.vue";
import EChart from "../../components/EChart.vue";
import { useConditionStore } from "../../stores/condition";
import { useChallengeStore } from "../../stores/challenge";
import { useSymptomStore } from "../../stores/symptom";
import { useRequireAuth } from "../../composables/requireAuth";
import { formatGrams } from "../../utils/format";

const condition = useConditionStore();
const challenge = useChallengeStore();
const symptom = useSymptomStore();
const { showLogin } = useRequireAuth(onAuthed);

const counts = ref({ green: 0, yellow: 0, red: 0 });

const pieOption = computed(() => ({
  tooltip: { trigger: "item" },
  legend: { bottom: 0 },
  series: [
    {
      type: "pie",
      radius: ["38%", "66%"],
      center: ["50%", "44%"],
      label: { fontSize: 11 },
      data: [
        { value: counts.value.green, name: "安全", itemStyle: { color: "#2BA471" } },
        { value: counts.value.yellow, name: "探索", itemStyle: { color: "#E37318" } },
        { value: counts.value.red, name: "禁忌", itemStyle: { color: "#D54941" } },
      ],
    },
  ],
}));

function foodName(id: number): string {
  const f = condition.foodMap.find((x) => x.food.id === id);
  return f ? f.food.name : `食物#${id}`;
}

async function onAuthed(): Promise<void> {
  await condition.loadMap();
  await challenge.loadList();
  symptom.refreshLogs();
  let g = 0;
  let y = 0;
  let r = 0;
  for (const item of condition.foodMap) {
    if (item.level === "green") g += 1;
    else if (item.level === "yellow") y += 1;
    else if (item.level === "red") r += 1;
  }
  counts.value = { green: g, yellow: y, red: r };
}
</script>

<style>
.block-title {
  font-size: 26px;
  font-weight: 600;
  color: #1f2d27;
}
.food-name {
  font-size: 30px;
  font-weight: 600;
  color: #1f2d27;
}
.stat-row {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
}
.stat {
  flex: 1;
  background: #fff;
  border-radius: 16px;
  padding: 20px 0;
  text-align: center;
  box-shadow: 0 2px 8px rgba(31, 45, 39, 0.04);
}
.stat-num {
  font-size: 44px;
  font-weight: 700;
  color: var(--wushi-sage);
}
.stat-num.green {
  color: #2ba471;
}
.stat-num.yellow {
  color: #e37318;
}
.stat-num.red {
  color: #d54941;
}
.inner {
  border-top: 1px solid #f0f2f1;
  padding-top: 16px;
  margin-top: 16px;
}
</style>
