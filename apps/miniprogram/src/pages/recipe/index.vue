<template>
  <view class="wushi-page">
    <view class="wushi-header">
      <view>
        <view class="wushi-title">智能食谱</view>
        <view class="wushi-sub">按目标 · 避忌口</view>
      </view>
    </view>

    <!-- 配置 -->
    <view class="wushi-card">
      <view class="block-title">优先目标</view>
      <nut-radiogroup v-model="goal" direction="horizontal">
        <nut-radio value="gut_stability">肠道稳定</nut-radio>
        <nut-radio value="blood_sugar">控糖</nut-radio>
        <nut-radio value="fat_loss">减脂</nut-radio>
      </nut-radiogroup>

      <view class="block-title" style="margin-top: 20px">排除食物（可多选）</view>
      <view class="avoid-bar">
        <text
          v-for="f in condition.foodMap"
          :key="f.food.id"
          class="chip"
          :class="{ on: avoidIds.has(f.food.id) }"
          @click="toggleAvoid(f.food.id)"
        >
          {{ f.food.name }}
        </text>
      </view>
      <text v-if="!condition.foodMap.length" class="wushi-muted">
        请先在「图谱」页添加病症以载入食物
      </text>

      <nut-button
        block
        type="primary"
        :loading="generating"
        style="margin-top: 24px"
        @click="generate"
      >
        生成食谱
      </nut-button>
    </view>

    <!-- 结果 -->
    <view v-if="recipe" class="wushi-card">
      <view class="wushi-flex">
        <text class="recipe-title">{{ recipe.title }}</text>
        <text class="engine" :class="recipe.engine === 'llm' ? 'llm' : 'tpl'">
          {{ recipe.engine === "llm" ? "AI 已接入" : "模板模式" }}
        </text>
      </view>
      <view v-if="recipe.note" class="wushi-muted" style="margin-top: 8px">
        {{ recipe.note }}
      </view>

      <view v-for="(it, i) in recipe.items" :key="i" class="recipe-item">
        <view class="wushi-flex">
          <text class="food-name">{{ it.name }}</text>
          <SafetyTag :level="it.safety || 'yellow'" />
        </view>
        <view class="wushi-muted">用量 {{ it.amount_g }} g</view>
        <view v-if="it.reason" class="reason">{{ it.reason }}</view>
        <view
          v-if="it.replaceable_with.length"
          class="wushi-muted replace"
        >
          可替换：{{ it.replaceable_with.join("、") }}
        </view>
      </view>
    </view>

    <nut-empty
      v-if="!generating && !recipe"
      description="选择目标与忌口，生成专属食谱"
    />

    <TabBar :active="3" />
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
import { createRecipe } from "../../api/recipe";
import type { RecipeOut } from "../../api/types";

const condition = useConditionStore();
const { showLogin } = useRequireAuth(onAuthed);

const goal = ref("gut_stability");
const avoidIds = ref<Set<number>>(new Set());
const generating = ref(false);
const recipe = ref<RecipeOut | null>(null);

async function onAuthed(): Promise<void> {
  await condition.loadMap();
}

function toggleAvoid(id: number): void {
  const next = new Set(avoidIds.value);
  if (next.has(id)) next.delete(id);
  else next.add(id);
  avoidIds.value = next;
}

async function generate(): Promise<void> {
  generating.value = true;
  recipe.value = null;
  try {
    recipe.value = await createRecipe({
      goal: goal.value,
      avoid_food_ids: Array.from(avoidIds.value),
    });
    Toast.success("已生成");
  } catch (e) {
    Toast.fail(e instanceof Error ? e.message : "生成失败");
  } finally {
    generating.value = false;
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
.avoid-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 8px;
}
.chip {
  background: #eef1f0;
  color: #6b7d76;
  border-radius: 999px;
  padding: 6px 18px;
  font-size: 24px;
}
.chip.on {
  background: var(--wushi-sage-soft);
  color: var(--wushi-sage);
  font-weight: 600;
}
.recipe-title {
  font-size: 32px;
  font-weight: 700;
  color: #1f2d27;
}
.engine {
  font-size: 22px;
  padding: 4px 14px;
  border-radius: 999px;
  color: #fff;
}
.engine.llm {
  background: #2ba471;
}
.engine.tpl {
  background: #9aa8a2;
}
.recipe-item {
  border-top: 1px solid #f0f2f1;
  padding-top: 16px;
  margin-top: 16px;
}
.reason {
  margin-top: 6px;
  font-size: 24px;
  color: #4a5a53;
  line-height: 1.6;
}
.replace {
  margin-top: 6px;
}
</style>
