<template>
  <view class="wushi-page">
    <view class="wushi-header wushi-flex">
      <view>
        <view class="wushi-title">食物图谱</view>
        <view class="wushi-sub">三色耐受 · 个性化剂量</view>
      </view>
      <nut-button size="small" @click="showCond = true">管理病症</nut-button>
    </view>

    <!-- 病症 chips -->
    <view class="cond-bar">
      <text
        v-for="c in condition.conditions"
        :key="c.id"
        class="chip"
        @click="removeCondition(c)"
      >
        {{ c.name }} ✕
      </text>
      <text v-if="!condition.conditions.length" class="wushi-muted">尚未添加病症</text>
      <text class="chip chip-add" @click="showCond = true">+ 添加</text>
    </view>

    <!-- 搜索 -->
    <view class="search-bar">
      <nut-input
        v-model="keyword"
        placeholder="搜索食物名称"
        @confirm="onSearch"
      />
      <nut-button size="small" type="primary" @click="onSearch">搜索</nut-button>
    </view>

    <!-- 食物卡片 -->
    <view
      v-for="item in condition.foodMap"
      :key="item.food.id"
      class="wushi-card"
    >
      <view class="wushi-flex">
        <text class="food-name">{{ item.food.name }}</text>
        <SafetyTag :level="item.level" />
      </view>
      <view class="wushi-muted reason">{{ item.reason }}</view>

      <view class="wushi-dose-row">
        <view class="wushi-dose"><b>{{ formatGrams(item.safe_g) }}</b>安全</view>
        <view class="wushi-dose"><b>{{ formatGrams(item.caution_g) }}</b>谨慎</view>
        <view class="wushi-dose"><b>{{ formatGrams(item.unsafe_g) }}</b>危险</view>
      </view>

      <view v-if="item.conflicts.length" class="conflicts">
        <view
          v-for="(cf, i) in item.conflicts"
          :key="i"
          class="conflict"
          :class="{ hard: cf.severity === 'hard' }"
        >
          ⚠ {{ cf.message }}
        </view>
      </view>
    </view>

    <nut-empty
      v-if="!condition.loading && !condition.foodMap.length"
      description="暂无食物数据，请先添加病症"
    />

    <!-- 病症管理弹窗 -->
    <nut-popup v-model:visible="showCond" position="bottom" round>
      <view class="cond-panel">
        <view class="cond-title">添加病症</view>
        <nut-input v-model="condName" placeholder="病症名称，如 IBS / SIBO" />
        <nut-cell-group>
          <nut-cell title="需控糖">
            <template #value>
              <nut-switch v-model="glucoseFlag" />
            </template>
          </nut-cell>
          <nut-cell title="忌组胺">
            <template #value>
              <nut-switch v-model="histamineFlag" />
            </template>
          </nut-cell>
        </nut-cell-group>
        <nut-button block type="primary" :loading="savingCond" @click="submitCondition">
          保存病症
        </nut-button>
      </view>
    </nut-popup>

    <TabBar :active="0" />
    <LoginModal v-model="showLogin" />
  </view>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { Toast } from "@nutui/nutui-taro";
import TabBar from "../../components/TabBar.vue";
import LoginModal from "../../components/LoginModal.vue";
import SafetyTag from "../../components/SafetyTag.vue";
import { useConditionStore } from "../../stores/condition";
import { useRequireAuth } from "../../composables/requireAuth";
import { formatGrams } from "../../utils/format";
import type { ConditionOut } from "../../api/types";

const condition = useConditionStore();
const { showLogin } = useRequireAuth(onAuthed);

const keyword = ref("");
const showCond = ref(false);
const condName = ref("");
const glucoseFlag = ref(false);
const histamineFlag = ref(false);
const savingCond = ref(false);

async function onAuthed(): Promise<void> {
  await condition.loadConditions();
  await condition.loadMap(keyword.value || undefined);
}

function onSearch(): void {
  condition.loadMap(keyword.value || undefined).catch(() => {
    /* 错误已由 store 抛出，页面静默 */
  });
}

async function submitCondition(): Promise<void> {
  if (!condName.value.trim()) {
    Toast.text("请填写病症名称");
    return;
  }
  savingCond.value = true;
  try {
    await condition.addCondition({
      name: condName.value.trim(),
      glucose_flag: glucoseFlag.value,
      histamine_flag: histamineFlag.value,
    });
    condName.value = "";
    glucoseFlag.value = false;
    histamineFlag.value = false;
    showCond.value = false;
    Toast.success("已添加病症");
  } catch (e) {
    Toast.fail(e instanceof Error ? e.message : "添加失败");
  } finally {
    savingCond.value = false;
  }
}

async function removeCondition(c: ConditionOut): Promise<void> {
  try {
    await condition.removeCondition(c.id);
    Toast.success("已删除病症");
  } catch (e) {
    // 后端无 DELETE 接口（gap）：store 已本地移除并抛出，这里仅提示
    Toast.fail("后端暂未支持删除（已本地移除）");
  }
}
</script>

<style>
.cond-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 16px;
  align-items: center;
}
.chip {
  background: var(--wushi-sage-soft);
  color: var(--wushi-sage);
  border-radius: 999px;
  padding: 6px 18px;
  font-size: 24px;
}
.chip-add {
  background: #eef1f0;
  color: #6b7d76;
}
.food-name {
  font-size: 30px;
  font-weight: 600;
  color: #1f2d27;
}
.reason {
  margin-top: 6px;
}
.conflicts {
  margin-top: 12px;
  border-top: 1px solid #f0f2f1;
  padding-top: 12px;
}
.conflict {
  font-size: 22px;
  color: #b9742a;
  line-height: 1.6;
}
.conflict.hard {
  color: #d54941;
  font-weight: 600;
}
.search-bar {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 8px;
}
.cond-panel {
  padding: 32px 24px 48px;
}
.cond-title {
  font-size: 32px;
  font-weight: 700;
  margin-bottom: 20px;
}
</style>
