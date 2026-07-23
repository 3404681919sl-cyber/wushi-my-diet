/** 统一 API 请求封装：baseURL + JWT 注入 + 错误归一化。替代 services/http.ts。 */

import Taro from "@tarojs/taro";
import { API_PREFIX, API_BASE_URL } from "../config";

const TOKEN_KEY = "wushi_token";

/** 读取本地缓存的 JWT。 */
export function getToken(): string {
  return Taro.getStorageSync(TOKEN_KEY) || "";
}

/** 存入 JWT。 */
export function setToken(token: string): void {
  Taro.setStorageSync(TOKEN_KEY, token);
}

/** 清除 JWT。 */
export function removeToken(): void {
  Taro.removeStorageSync(TOKEN_KEY);
}

export interface RequestOptions {
  url: string;
  method?: "GET" | "POST" | "PUT" | "DELETE";
  data?: Record<string, unknown>;
  auth?: boolean;
}

/** 归一化 API 错误（携带 HTTP 状态码与后端 detail）。 */
export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

/**
 * 统一请求方法。
 * - 自动拼接 `${API_BASE_URL}${API_PREFIX}${url}`。
 * - 若 auth=true 且本地有 token，则注入 `Authorization: Bearer <token>`。
 * - 状态码 ≥ 400 时抛出 ApiError（尽量提取后端 detail 作为 message）。
 */
export async function request<T = unknown>(options: RequestOptions): Promise<T> {
  const headers: Record<string, string> = { "content-type": "application/json" };
  if (options.auth) {
    const token = getToken();
    if (token) headers.Authorization = `Bearer ${token}`;
  }

  const res = await Taro.request({
    url: `${API_BASE_URL}${API_PREFIX}${options.url}`,
    method: options.method || "GET",
    data: options.data as unknown as string,
    header: headers,
  });

  if (res.statusCode >= 400) {
    let message = `请求失败（${res.statusCode}）`;
    try {
      const body = res.data as Record<string, unknown> | undefined;
      if (body && typeof body.detail === "string") message = body.detail;
      else if (body && typeof body.message === "string") message = body.message;
    } catch {
      /* 忽略解析错误，使用默认文案 */
    }
    throw new ApiError(res.statusCode, message);
  }

  return res.data as T;
}

export const get = <T = unknown>(url: string, auth = true) =>
  request<T>({ url, method: "GET", auth });

export const post = <T = unknown>(url: string, data?: object, auth = true) =>
  request<T>({ url, method: "POST", data: data as Record<string, unknown>, auth });

export const put = <T = unknown>(url: string, data?: object, auth = true) =>
  request<T>({ url, method: "PUT", data: data as Record<string, unknown>, auth });

export const del = <T = unknown>(url: string, auth = true) =>
  request<T>({ url, method: "DELETE", auth });
