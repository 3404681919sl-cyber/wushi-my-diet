/** Taro 开发环境编译片段（与 config/index.ts 合并）。 */

export default {
  logger: {
    quiet: false,
    stats: true,
  },
  mini: {
    productionSourceMap: false,
  },
  h5: {
    esnextModules: [],
  },
};
