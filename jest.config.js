// proton, 
// module.exports = {
//   // 设置根目录
//   rootDir: '.',
// module.exports = {
//   // 设置根目录
//   rootDir: '.',
  
//   // 测试环境，如果测试涉及 DOM，使用 'jsdom'；否则用 'node'
//   testEnvironment: 'jsdom', // 或 'jsdom'，根据你的代码是否需要浏览器 API
//   // 测试环境，如果测试涉及 DOM，使用 'jsdom'；否则用 'node'
//   testEnvironment: 'jsdom', // 或 'jsdom'，根据你的代码是否需要浏览器 API
  
//   // 模块解析：让 Jest 在查找模块时也搜索 src 目录
//   moduleDirectories: ['node_modules', 'src'],
//   // 模块解析：让 Jest 在查找模块时也搜索 src 目录
//   moduleDirectories: ['node_modules', 'src'],
  
//   // 或者使用更明确的映射（推荐）
//   moduleNameMapper: {
//     '^src/(.*)$': '<rootDir>/src/$1',
//   },
//   // 或者使用更明确的映射（推荐）
//   moduleNameMapper: {
//     '^src/(.*)$': '<rootDir>/src/$1',
//   },
  
//   // 使用 Babel 转换 JS 文件
//   transform: {
//     '^.+\\.js$': 'babel-jest',
//   },
//   // 使用 Babel 转换 JS 文件
//   transform: {
//     '^.+\\.js$': 'babel-jest',
//   },
  
//   // 忽略 node_modules 的转换（默认）
//   transformIgnorePatterns: ['/node_modules/'],
//   // reporters: [
//   //   "default",                           // 保留默认输出
//   //   ["jest-junit", { outputFile: "/results/test-report.xml" }]
//   // ],
//   // 如果需要收集测试覆盖率
//   coverageProvider: 'babel',
//   collectCoverage: true,
//   // 忽略 node_modules 的转换（默认）
//   transformIgnorePatterns: ['/node_modules/'],
//   // reporters: [
//   //   "default",                           // 保留默认输出
//   //   ["jest-junit", { outputFile: "/results/test-report.xml" }]
//   // ],
//   // 如果需要收集测试覆盖率
//   coverageProvider: 'babel',
//   collectCoverage: true,
  
//   collectCoverageFrom: [
//     "src/**/*.js",
//   collectCoverageFrom: [
//     "src/**/*.js",

//     //  排除测试
//     "!**/*.test.js",
//     "!**/__tests__/**",
//   ],
// };
//     //  排除测试
//     "!**/*.test.js",
//     "!**/__tests__/**",
//   ],
// };


// pdf, modern-error
// export default {
//   // 设置根目录
//   rootDir: '.',
  
//   // 测试环境
//   testEnvironment: 'node', // 或 'jsdom'
  
//   // 模块解析
//   moduleDirectories: ['node_modules', 'src'],
  
//   // 模块名称映射
//   moduleNameMapper: {
//     '^src/(.*)$': '<rootDir>/src/$1',
//   },
  
//   // 使用 Babel 转换
//   transform: {
//     '^.+\\.js$': 'babel-jest',
//   },
  
//   // 忽略转换的路径
//   // pdf
//   // transformIgnorePatterns: ['/node_modules/'],
//   // modern-error
//   transformIgnorePatterns: ['/node_modules/(?!(merge-error-cause|set-error-class|set-error-stack|set-error-props|normalize-exception|is-error-instance|is-plain-obj|redefine-property|wrap-error-message|set-error-message|filter-obj)/)'],
  
//   // 收集覆盖率
//   collectCoverage: true,
// };


export default {
  rootDir: '.',
  // modern-error,simple-statistics
  testEnvironment: 'node',

  // pdf
  // testEnvironment: 'jsdom', 
  
// modern-error,simple-statistics,pdf
  moduleDirectories: ['node_modules', 'src'],

  moduleNameMapper: {
    '^src/(.*)$': '<rootDir>/src/$1',
  },
  

  transform: {
    '^.+\\.js$': 'babel-jest',
  },
  

  // 忽略转换的路径
  // pdf,simple-statistics
  // transformIgnorePatterns: ['/node_modules/'],
  // modern-error
  transformIgnorePatterns: ['/node_modules/(?!(merge-error-cause|set-error-class|set-error-stack|set-error-props|normalize-exception|is-error-instance|is-plain-obj|redefine-property|wrap-error-message|set-error-message|filter-obj)/)'],

  coverageProvider: 'babel',
  collectCoverage: true,
  

  
  collectCoverageFrom: [
    "**/*.js",

    //  排除测试
    "!**/*.test.js",
    "!**/__tests__/**",
    

    //  排除依赖
    "!**/node_modules/**",

    //  排除文档 / 静态资源
    "!**/docs/**",
    "!**/dist/**",
    "!**/build/**",
    

    //  排除 coverage 自身
    "!**/coverage/**"
  ]
};
    