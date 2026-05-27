// simple-statistics,proton,modern-error,pdf
import resolve from '@rollup/plugin-node-resolve';
import commonjs from '@rollup/plugin-commonjs';

export default {
  input: process.argv[2], // 入口文件从命令行传入
  plugins: [resolve(), commonjs()],
  output: {
    file: 'temp.js', // 临时输出文件
    format: 'esm',   // ES 模块
  },
};

// proton
// rollup.temp.config.js
// import resolve from '@rollup/plugin-node-resolve';
// import commonjs from '@rollup/plugin-commonjs';
// import babel from '@rollup/plugin-babel';
// import path from 'path';

// export default {
//   input: process.argv[2], // 从命令行传入的测试文件路径
//   plugins: [
//     resolve({
//       extensions: ['.js', '.mjs', '.cjs'], // 明确要解析的扩展名
//       // 如果源代码在 src 下，可以设置 rootDir 加快解析
//       rootDir: path.resolve('./'), // 项目根目录
//     }),
//     commonjs(), // 如果有 CommonJS 模块需要转换
//     babel({
//       babelHelpers: 'bundled',
//       exclude: 'node_modules/**',
//       babelrc: true, // 使用项目中的 Babel 配置（.babelrc.json）
//     }),
//   ],
//   output: {
//     file: 'temp.js',
//     format: 'cjs', // 使用 CommonJS 格式，因为 Node 环境更容易兼容
//     sourcemap: false,
//   },
//   // 可选：将 Node 内置模块标记为 external，避免打包它们
//   external: ['assert', 'fs', 'path', 'util'],
// };