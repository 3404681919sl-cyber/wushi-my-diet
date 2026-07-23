/** 兼容层：统一请求已迁移至 src/api/request.ts，此处仅做再导出，避免历史引用断裂。 */

export {
  request,
  get,
  post,
  put,
  del,
  getToken,
  setToken,
  removeToken,
  ApiError,
} from "../api/request";
