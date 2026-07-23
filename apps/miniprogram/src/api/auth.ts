/** 鉴权相关 API（对齐后端 /api/v1/auth）。注意：后端使用邮箱登录，而非手机号。 */

import { get, post } from "./request";
import type { TokenOut, UserOut } from "./types";

export interface RegisterPayload {
  email: string;
  password: string;
  nickname?: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

/** 注册（邮箱 + 密码 + 昵称），后端返回 UserOut。 */
export const register = (payload: RegisterPayload) =>
  post<UserOut>("/auth/register", payload, false);

/** 登录（邮箱 + 密码），后端返回 JWT。 */
export const login = (payload: LoginPayload) =>
  post<TokenOut>("/auth/login", payload, false);

/** 获取当前登录用户。 */
export const fetchMe = () => get<UserOut>("/auth/me", true);

// 微信登录占位（后端返回 501），预留接口：
// export const wechatLogin = (code: string) => post("/auth/wechat-login", { code }, false);
