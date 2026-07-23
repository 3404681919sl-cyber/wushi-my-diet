<template>
  <view class="wushi-page">
    <view class="wushi-header">
      <view>
        <view class="wushi-title">症状日志</view>
        <view class="wushi-sub">记录反应 · 追踪耐受</view>
      </view>
    </view>

    <!-- 录入表单 -->
    <view class="wushi-card">
      <view class="block-title">选择症状</view>
      <nut-radiogroup v-model="selectedDefId" direction="horizontal">
        <nut-radio v-for="d in symptom.defs" :key="d.id" :value="d.id">
          {{ d.name }}
        </nut-radio>
      </nut-radiogroup>
      <nut-empty
        v-if="!symptom.defs.length"
        description="暂无症状词典，请先在后端录入"
      />

      <view class="block-title" style="margin-top: 20px">严重度（0~10）</view>
      <view class="sev-row">
        <nut-range v-model="severity" :max="10" :min="0" :step="1" />
        <text class="sev-val">{{ severity }}</text>
      </view>

      <view class="block-title" style="margin-top: 20px">发生时间</view>
      <picker mode="date" :value="date" @change="onDate">
        <view class="picker">{{ date }}</view>
      </picker>
      <picker mode="time" :value="time" @change="onTime" style="margin-top: 12px">
        <view class="picker">{{ time }}</view>
      </picker>

      <nut-button
        block
        type="primary"
        :loading="submitting"
        :disabled="!selectedDefId"
        style="margin-top: 24px"
        @click="submit"
      >
        记录症状
      </nut-button>
      <view v-if="lastPersisted" class="persist-tip">{{ lastPersisted }}</view>
    </view>

    <!-- 历史倒序 -->
    <view class="wushi-header" style="margin-top: 8px">
      <view class="wushi-title" style="font-size: 30px">历史记录</view>
      <text class="wushi-muted">{{ symptom.logs.length }} 条</text>
    </view>

    <view
      v-for="log in symptom.logs"
      :key="log.id"
      class="wushi-card log-item"
    >
      <view class="wushi-flex">
        <text class="log-name">{{ log.symptom_name }}</text>
        <text class="log-sev" :style="{ background: sevColor(log.severity) }">
          {{ log.severity }}
        </text>
      </view>
      <view class="wushi-muted">{{ formatDateTime(log.logged_at) }}</view>
    </view>

    <nut-empty
      v-if="!symptom.logs.length"
      description="还没有记录，先记一条吧"
    />

    <TabBar :active="1" />
    <LoginModal v-model="showLogin" />
  </view>
</template>

<script setup lang="ts">
import { ref } from "vue";
import TabBar from "../../components/TabBar.vue";
import LoginModal from "../../components/LoginModal.vue";
import { useSymptomStore } from "../../stores/symptom";
import { useRequireAuth } from "../../composables/requireAuth";
import { formatDateTime } from "../../utils/format";

interface PickerChange {
  detail: { value: string };
}

const symptom = useSymptomStore();
const { showLogin } = useRequireAuth(onAuthed);

const selectedDefId = ref<number | null>(null);
const severity = ref(3);
const submitting = ref(false);
const lastPersisted = ref("");
const date = ref(curDate());
const time = ref(curTime());

function pad(n: number): string {
  return `${n}`.padStart(2, "0");
}

function curDate(): string {
  const d = new Date();
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

function curTime(): string {
  const d = new Date();
  return `${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

async function onAuthed(): Promise<void> {
  await symptom.loadDefs();
  if (symptom.defs.length && selectedDefId.value === null) {
    selectedDefId.value = symptom.defs[0].id;
  }
  symptom.refreshLogs();
}

function onDate(e: PickerChange): void {
  date.value = e.detail.value;
}

function onTime(e: PickerChange): void {
  time.value = e.detail.value;
}

function sevColor(s: number): string {
  if (s >= 7) return "#D54941";
  if (s >= 4) return "#E37318";
  return "#2BA471";
}

async function submit(): Promise<void> {
  if (selectedDefId.value === null) return;
  const def = symptom.defs.find((d) => d.id === selectedDefId.value);
  if (!def) return;
  submitting.value = true;
  lastPersisted.value = "";
  try {
    const persisted = await symptom.addLog({
      symptom_def_id: def.id,
      symptom_name: def.name,
      severity: severity.value,
      logged_at: `${date.value} ${time.value}:00`,
    });
    lastPersisted.value =
      persisted === "local"
        ? "后端暂未提供日志接口，已本地保存（演示用）"
        : "已提交到服务器";
    severity.value = 3;
  } finally {
    submitting.value = false;
  }
}
</script>

<style>
.block-title {
  font-size: 26px;
  font-weight: 600;
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
.picker {
  background: #f5f7f6;
  border-radius: 12px;
  padding: 16px 20px;
  font-size: 28px;
  color: #1f2d27;
}
.persist-tip {
  margin-top: 16px;
  font-size: 22px;
  color: #6b7d76;
}
.log-name {
  font-size: 30px;
  font-weight: 600;
}
.log-sev {
  display: inline-block;
  width: 44px;
  height: 44px;
  line-height: 44px;
  text-align: center;
  border-radius: 50%;
  color: #fff;
  font-size: 24px;
}
</style>
