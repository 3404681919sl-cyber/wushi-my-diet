/** 登录态守卫：未登录时弹出登录框；登录成功后触发数据加载回调。 */

import { onMounted, ref, watch } from "vue";
import { useAuthStore } from "../stores/auth";

/**
 * 在每个页面 setup 中调用，统一处理「未登录→弹登录框→登录后加载数据」流程。
 * @param onAuthed 用户已登录（含登录成功瞬间）时执行的副作用，通常为拉取页面数据。
 */
export function useRequireAuth(onAuthed?: () => void | Promise<void>) {
  const auth = useAuthStore();
  const showLogin = ref(false);

  async function run(): Promise<void> {
    if (!auth.isLoggedIn) {
      showLogin.value = true;
      return;
    }
    if (onAuthed) await onAuthed();
  }

  onMounted(run);

  // 登录弹窗成功关闭后，auth.isLoggedIn 变为 true，自动加载数据
  watch(
    () => auth.isLoggedIn,
    (val) => {
      if (val && onAuthed) onAuthed();
    }
  );

  return { auth, showLogin };
}
