<template>
  <nut-popup
    :visible="visible"
    position="bottom"
    round
    :style="{ height: 'auto' }"
    @update:visible="(v: boolean) => emit('update:visible', v)"
  >
    <view class="login-card">
      <view class="login-title">{{ isRegister ? "注册吾食" : "登录吾食" }}</view>
      <nut-input v-model="email" placeholder="邮箱（登录名）" />
      <nut-input v-model="password" type="password" placeholder="密码（至少 6 位）" />
      <nut-input
        v-if="isRegister"
        v-model="nickname"
        placeholder="昵称（可选）"
      />
      <nut-button block type="primary" @click="submit">
        {{ isRegister ? "注册并登录" : "登录" }}
      </nut-button>
      <nut-button block plain @click="toggle">
        {{ isRegister ? "已有账号？去登录" : "没有账号？去注册" }}
      </nut-button>
      <view class="login-tip">微信登录即将上线（/auth/wechat-login 占位 501）</view>
    </view>
  </nut-popup>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { Toast } from "@nutui/nutui-taro";
import { useAuthStore } from "../stores/auth";

const props = defineProps<{ modelValue: boolean }>();
const emit = defineEmits<{
  (e: "update:modelValue", v: boolean): void;
  (e: "success"): void;
}>();

const auth = useAuthStore();
const visible = computed({
  get: () => props.modelValue,
  set: (v) => emit("update:modelValue", v),
});
const isRegister = ref(false);
const email = ref("");
const password = ref("");
const nickname = ref("");

function toggle(): void {
  isRegister.value = !isRegister.value;
}

async function submit(): Promise<void> {
  if (!email.value || !password.value) {
    Toast.text("请填写邮箱和密码");
    return;
  }
  try {
    if (isRegister.value) {
      await auth.register(email.value, password.value, nickname.value);
    } else {
      await auth.login(email.value, password.value);
    }
    visible.value = false;
    emit("success");
    Toast.success("登录成功");
  } catch (e) {
    const msg = e instanceof Error ? e.message : "操作失败";
    Toast.fail(msg);
  }
}
</script>

<style>
.login-card {
  padding: 32px 24px 48px;
}
.login-title {
  font-size: 36px;
  font-weight: 700;
  margin-bottom: 24px;
  color: #1f2d27;
}
.login-tip {
  margin-top: 16px;
  font-size: 22px;
  color: #9aa8a2;
  text-align: center;
}
</style>
