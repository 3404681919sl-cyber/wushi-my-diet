/** API 请求封装（基于 Taro.request）：统一 baseURL、JWT 注入、错误归一化。 */

import Taro from "@tarojs/taro";
import { API_BASE } from "@wushi/shared";
import appConfig from "../config/index";

const TOKEN_KEY = "wushi_token";

/** 读取本地缓存的 JWT。 */
export function getToken(): string {
  return Taro.getStorageSync(TOKEN_KEY) || "";
}

/** 存入 JWT。 */
export function setToken(token: string): void {
  Taro.setStorageSync(TOKEN_KEY, token);
}

export interface RequestOptions {
  url: string;
  method?: "GET" | "POST" | "PUT" | "DELETE";
  data?: Record<string, unknown>;
  auth?: boolean;
}

/** 统一请求方法（本期骨架，T4/T5 完善错误处理与重试）。 */
export async function request<T = unknown>(options: RequestOptions): Promise<T> {
  const headers: Record<string, string> = { "content-type": "application/json" };
  if (options.auth) {
    const token = getToken();
    if (token) headers.Authorization = `Bearer ${token}`;
  }

  const res = await Taro.request({
    url: `${appConfig.apiBaseUrl}${API_BASE}${options.url}`,
    method: options.method || "GET",
    data: options.data as unknown as string,
    header: headers,
  });

  if (res.statusCode >= 400) {
    throw new Error(`请求失败：${res.statusCode}`);
  }
  return res.data as T;
}
