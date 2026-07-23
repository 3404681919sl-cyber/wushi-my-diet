/** Taro 生产环境编译片段（与 config/index.ts 合并）。 */

export default {
  mini: {
    productionSourceMap: false,
  },
  h5: {
    publicPath: "/",
    esnextModules: [],
  },
};
