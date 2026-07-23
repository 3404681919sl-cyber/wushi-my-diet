<template>
  <view class="wushi-page">
    <view class="wushi-header">
      <view>
        <view class="wushi-title">微挑战</view>
        <view class="wushi-sub">小步剂量 · 重算耐受</view>
      </view>
    </view>

    <!-- 选择食物 -->
    <view v-if="!challenge.current" class="wushi-card">
      <view class="block-title">选择要挑战的食物</view>
      <picker mode="selector" :range="foodNames" @change="onPickFood">
        <view class="picker">{{ pickedName || "点击选择食物" }}</view>
      </picker>
      <nut-button
        block
        type="primary"
        :disabled="!pickedId"
        :loading="starting"
        style="margin-top: 20px"
        @click="start"
      >
        生成 3 步剂量挑战
      </nut-button>
    </view>

    <!-- 当前挑战 -->
    <view v-else class="wushi-card">
      <view class="wushi-flex">
        <text class="food-name">{{ currentFoodName }}</text>
        <nut-button size="small" plain @click="reset">换食物</nut-button>
      </view>

      <!-- 阈值摘要 -->
      <view class="wushi-dose-row">
        <view class="wushi-dose"><b>{{ formatGrams(challenge.current.safe_g) }}</b>安全</view>
        <view class="wushi-dose"><b>{{ formatGrams(challenge.current.caution_g) }}</b>谨慎</view>
        <view class="wushi-dose"><b>{{ formatGrams(challenge.current.unsafe_g) }}</b>危险</view>
      </view>

      <EChart :option="doseOption" canvas-id="challenge-dose" :height="200" />

      <!-- 步骤列表 -->
      <view v-for="step in challenge.current.steps" :key="step.id" class="step">
        <view class="wushi-flex">
          <text class="step-name">第 {{ step.step_no }} 步 · {{ step.dose_g }} g</text>
          <text class="step-result" :class="resultClass(step)">{{ stepLabel(step) }}</text>
        </view>
        <view class="sev-row">
          <nut-range v-model="stepSeverity[step.step_no]" :max="10" :min="0" :step="1" />
          <text class="sev-val">{{ stepSeverity[step.step_no] }}</text>
        </view>
        <nut-button
          size="small"
          type="primary"
          :loading="recording === step.step_no"
          @click="record(step)"
        >
          记录此步
        </nut-button>
      </view>
    </view>

    <TabBar :active="2" />
    <LoginModal v-model="showLogin" />
  </view>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from "vue";
import TabBar from "../../components/TabBar.vue";
import LoginModal from "../../components/LoginModal.vue";
import EChart from "../../components/EChart.vue";
import { useConditionStore } from "../../stores/condition";
import { useChallengeStore } from "../../stores/challenge";
import { useRequireAuth } from "../../composables/requireAuth";
import { formatGrams } from "../../utils/format";
import type { ChallengeStepOut } from "../../api/types";

interface PickerChange {
  detail: { value: number | string };
}

const condition = useConditionStore();
const challenge = useChallengeStore();
const { showLogin } = useRequireAuth(onAuthed);

const pickedId = ref<number | null>(null);
const pickedName = ref("");
const starting = ref(false);
const recording = ref(0);
const stepSeverity = reactive<Record<number, number>>({ 1: 0, 2: 0, 3: 0 });

const foodNames = computed(() => condition.foodMap.map((f) => f.food.name));

const currentFoodName = computed(() => {
  if (!challenge.current) return "";
  const f = condition.foodMap.find((x) => x.food.id === challenge.current!.food_id);
  return f ? f.food.name : `食物#${challenge.current.food_id}`;
});

const doseOption = computed(() => {
  const c = challenge.current;
  const safe = c?.safe_g ?? 0;
  const caution = c?.caution_g ?? 0;
  const unsafe = c?.unsafe_g ?? 0;
  return {
    grid: { left: 30, right: 10, top: 20, bottom: 24 },
    xAxis: {
      type: "category",
      data: ["安全", "谨慎", "危险"],
      axisLabel: { fontSize: 11 },
    },
    yAxis: { type: "value", name: "g" },
    series: [
      {
        type: "bar",
        data: [safe, caution, unsafe],
        itemStyle: { color: "hsl(150 18% 32%)" },
        barWidth: "46%",
      },
    ],
  };
});

async function onAuthed(): Promise<void> {
  await condition.loadMap();
  await challenge.loadList();
}

function onPickFood(e: PickerChange): void {
  const idx = Number(e.detail.value);
  const item = condition.foodMap[idx];
  if (!item) return;
  pickedId.value = item.food.id;
  pickedName.value = item.food.name;
}

async function start(): Promise<void> {
  if (pickedId.value === null) return;
  starting.value = true;
  try {
    await challenge.start(pickedId.value);
    stepSeverity[1] = 0;
    stepSeverity[2] = 0;
    stepSeverity[3] = 0;
  } finally {
    starting.value = false;
  }
}

function reset(): void {
  challenge.clear();
  pickedId.value = null;
  pickedName.value = "";
}

function stepLabel(step: ChallengeStepOut): string {
  if (step.severity === null || step.severity === undefined) return "未记录";
  return step.severity > 0 ? `有反应 ${step.severity}` : "无反应";
}

function resultClass(step: ChallengeStepOut): string {
  if (step.severity === null || step.severity === undefined) return "";
  return step.severity > 0 ? "reacted" : "ok";
}

async function record(step: ChallengeStepOut): Promise<void> {
  if (!challenge.current) return;
  recording.value = step.step_no;
  try {
    await challenge.record(
      challenge.current.id,
      step.step_no,
      stepSeverity[step.step_no]
    );
  } finally {
    recording.value = 0;
  }
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
.picker {
  background: #f5f7f6;
  border-radius: 12px;
  padding: 16px 20px;
  font-size: 28px;
  color: #1f2d27;
}
.sev-row {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-top: 8px;
}
.sev-val {
  font-size: 32px;
  font-weight: 700;
  color: var(--wushi-sage);
  min-width: 48px;
  text-align: center;
}
.step {
  border-top: 1px solid #f0f2f1;
  padding-top: 16px;
  margin-top: 16px;
}
.step-name {
  font-size: 26px;
  font-weight: 600;
}
.step-result {
  font-size: 22px;
  color: #9aa8a2;
}
.step-result.reacted {
  color: #d54941;
  font-weight: 600;
}
.step-result.ok {
  color: #2ba471;
  font-weight: 600;
}
</style>
