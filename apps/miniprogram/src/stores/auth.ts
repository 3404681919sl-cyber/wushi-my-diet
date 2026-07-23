/** 鉴权状态管理：缓存 JWT、登录 / 注册 / 拉取当前用户 / 登出。 */

import { defineStore } from "pinia";
import { computed, ref } from "vue";
import { fetchMe, login as apiLogin, register as apiRegister } from "../api/auth";
import { getToken, removeToken, setToken } from "../api/request";
import type { UserOut } from "../api/types";

export const useAuthStore = defineStore("auth", () => {
  const token = ref<string>(getToken());
  const user = ref<UserOut | null>(null);
  const loading = ref(false);

  const isLoggedIn = computed(() => !!token.value);

  /** 手机号 + 密码登录，成功后拉取用户信息。 */
  async function login(phone: string, password: string): Promise<void> {
    const res = await apiLogin({ phone, password });
    token.value = res.access_token;
    setToken(res.access_token);
    await loadMe();
  }

  /** 注册后立即登录。 */
  async function register(
    phone: string,
    password: string,
    nickname = ""
  ): Promise<void> {
    await apiRegister({ phone, password, nickname });
    await login(phone, password);
  }

  /** 拉取当前登录用户。 */
  async function loadMe(): Promise<void> {
    if (!token.value) return;
    loading.value = true;
    try {
      user.value = await fetchMe();
    } finally {
      loading.value = false;
    }
  }

  /** 登出并清除本地 token。 */
  function logout(): void {
    token.value = "";
    user.value = null;
    removeToken();
  }

  return { token, user, loading, isLoggedIn, login, register, loadMe, logout };
});
