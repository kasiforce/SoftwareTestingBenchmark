# import os
# import subprocess
# import sys
# import json
# import shutil

# def create_and_run_js(dockerfile_path, gen_tests_dir, cover_source, repo_name):
#     cwd = os.getcwd()
#     print(f"当前工作目录: {cwd}")

#     # 读取原始 Dockerfile
#     with open(dockerfile_path, "r") as f:
#         content = f.read()

#     # 在文件末尾追加测试相关指令
#     content += f'''
# # 显示当前 Node.js 和 npm 版本
# RUN node --version
# RUN npm --version

# # 安装测试依赖 - 保持简单通用
# RUN npm install --save-dev \\
#     jest \\
#     jest-junit \\
#     jest-json-reporter

# # 注意：这里不需要复制任何测试代码或源代码
# # 因为项目已经通过 git clone 在 /testbed 中
# '''

#     # 确保 test_results 目录
#     test_results_dir = os.path.join(cwd, "test_results")
#     test_results_dir = os.path.join(test_results_dir, repo_name)
#     os.makedirs(test_results_dir, exist_ok=True)

#     # 写入 Dockerfile.test
#     dockerfile_test_path = os.path.join(test_results_dir, "Dockerfile.test")
#     with open(dockerfile_test_path, "w") as f:
#         f.write(content)
#     print("写入 Dockerfile.test")

#     # 构建镜像
#     print("开始构建镜像...")
#     try:
#         result = subprocess.run([
#             "docker", "build",
#             "-t", "js-repo-with-test",
#             "-f", dockerfile_test_path,
#             "."
#         ], check=True, cwd=cwd, capture_output=True, text=True)
#         print(f"镜像构建输出: {result.stdout}")
#     except subprocess.CalledProcessError as e:
#         print(f"镜像构建失败: {e}")
#         print(f"错误输出: {e.stderr}")
#         sys.exit(1)

#     print("镜像构建成功")

#     # 运行测试
#     print("运行测试...")
#     try:
#         # 创建更通用的测试脚本，适配任何项目配置
#         test_script = '''#!/bin/bash
# set -e  # 遇到错误立即退出
# cd /testbed

# echo "=== 当前目录结构 ==="
# ls -la

# # 创建结果目录
# mkdir -p /results

# # 1. 检查 package.json 和项目结构
# echo "=== 检查项目结构 ==="
# if [ -f package.json ]; then
#     echo "package.json 存在"
#     cat package.json | head -50
# else
#     echo "警告: 未找到 package.json"
# fi

# echo "=== 检查测试文件 ==="
# find . -name "*.test.js" -o -name "*.spec.js" -o -name "*test*.js" | grep -v node_modules | head -20 || true
# find test/ -name "*.js" 2>/dev/null | head -20 || true

# # 2. 创建兼容性的 Jest 配置
# # 根据项目是 ES 模块还是 CommonJS 来调整
# cat > jest.runner.js << 'EOF'
# // 动态的 Jest 运行器，自动适配项目类型
# const fs = require('fs');
# const path = require('path');

# // 读取 package.json
# let packageJson = {};
# try {
#     packageJson = JSON.parse(fs.readFileSync('./package.json', 'utf8'));
# } catch (e) {
#     console.log('无法读取 package.json:', e.message);
# }

# const isEsm = packageJson.type === 'module';

# // 基础配置
# const baseConfig = {
#     testEnvironment: 'node',
#     testMatch: [
#         '**/test/**/*.js',
#         '**/tests/**/*.js',
#         '**/*.test.js',
#         '**/*.spec.js'
#     ],
#     testPathIgnorePatterns: [
#         '/node_modules/',
#         '/build/',
#         '/dist/',
#         '/coverage/'
#     ],
#     collectCoverage: true,
#     coverageDirectory: '/results/coverage',
#     coverageReporters: ['json', 'text'],
#     reporters: [
#         'default',
#         ['jest-json-reporter', {
#             outputPath: '/results/jest-report.json'
#         }],
#         ['jest-junit', {
#             outputDirectory: '/results',
#             outputName: 'junit.xml'
#         }]
#     ],
#     verbose: true
# };

# // 如果是 ES 模块，需要特殊配置
# if (isEsm) {
#     console.log('检测到 ES 模块项目，使用相应的 Jest 配置');

#     // ES 模块配置 - 使用实验性功能
#     const esmConfig = {
#         ...baseConfig,
#         extensionsToTreatAsEsm: ['.js'],
#         transform: {},
#         moduleNameMapper: {
#             '^(\\.{1,2}/.*)\\.js$': '$1'
#         }
#     };

#     // 写入配置文件
#     fs.writeFileSync(
#         '/results/jest-esm.config.js',
#         `export default ${JSON.stringify(esmConfig, null, 2)};`
#     );

#     // 设置环境变量以便使用 ES 模块配置
#     process.env.NODE_OPTIONS = '--experimental-vm-modules';
#     process.env.JEST_CONFIG_PATH = '/results/jest-esm.config.js';
# } else {
#     console.log('检测到 CommonJS 项目，使用标准的 Jest 配置');

#     // CommonJS 配置
#     const cjsConfig = {
#         ...baseConfig
#     };

#     // 写入配置文件
#     fs.writeFileSync(
#         '/results/jest-cjs.config.js',
#         `module.exports = ${JSON.stringify(cjsConfig, null, 2)};`
#     );

#     process.env.JEST_CONFIG_PATH = '/results/jest-cjs.config.js';
# }

# console.log('Jest 配置文件已创建');
# EOF

# # 3. 运行 Jest 配置生成器
# echo "=== 生成 Jest 配置 ==="
# node jest.runner.js

# # 4. 运行测试
# echo "=== 开始运行测试 ==="

# if [ -f "/results/jest-esm.config.js" ]; then
#     echo "使用 ES 模块配置运行 Jest"
#     # 对于 ES 模块，使用特殊标志
#     NODE_OPTIONS="--experimental-vm-modules" npx jest --config=/results/jest-esm.config.js --testLocationInResults --json --outputFile=/results/jest-raw.json 2>&1 || echo "Jest执行完成"
# else
#     echo "使用 CommonJS 配置运行 Jest"
#     npx jest --config=/results/jest-cjs.config.js --testLocationInResults --json --outputFile=/results/jest-raw.json 2>&1 || echo "Jest执行完成"
# fi

# # 5. 处理测试结果
# echo "=== 处理测试结果 ==="
# if [ -f "/results/jest-raw.json" ]; then
#     cp /results/jest-raw.json /results/jest-report.json
#     echo "测试报告已复制"

#     # 检查测试结果
#     if [ -f "/results/jest-report.json" ]; then
#         echo "测试结果摘要:"
#         node -e "
#         try {
#             const report = require('/results/jest-report.json');
#             const total = report.numTotalTests || 0;
#             const passed = report.numPassedTests || 0;
#             const failed = report.numFailedTests || 0;
#             console.log('总测试数:', total);
#             console.log('通过数:', passed);
#             console.log('失败数:', failed);
#             console.log('通过率:', total > 0 ? ((passed / total) * 100).toFixed(2) + '%' : 'N/A');
#         } catch (e) {
#             console.log('无法解析测试报告:', e.message);
#         }
#         "
#     fi
# else
#     echo "未生成原始测试报告，创建空的报告"
#     echo '{"numTotalTests": 0, "numPassedTests": 0, "numFailedTests": 0, "numPendingTests": 0, "testResults": []}' > /results/jest-report.json
# fi

# # 6. 处理覆盖率
# echo "=== 处理覆盖率 ==="
# if [ -d "/results/coverage" ]; then
#     echo "覆盖率目录已生成"

#     # 如果存在 coverage-final.json，尝试生成 summary
#     if [ -f "/results/coverage/coverage-final.json" ]; then
#         echo "生成覆盖率摘要"
#         node -e "
#         const fs = require('fs');
#         try {
#             const coverage = JSON.parse(fs.readFileSync('/results/coverage/coverage-final.json', 'utf8'));
#             let totalStatements = 0, coveredStatements = 0;
#             let totalBranches = 0, coveredBranches = 0;
#             let totalFunctions = 0, coveredFunctions = 0;
#             let totalLines = 0, coveredLines = 0;

#             Object.values(coverage).forEach(file => {
#                 if (file.s) {
#                     Object.values(file.s).forEach(hit => {
#                         totalStatements++;
#                         if (hit > 0) coveredStatements++;
#                     });
#                 }
#                 if (file.b) {
#                     Object.values(file.b).forEach(branchHits => {
#                         totalBranches++;
#                         if (branchHits.some(hit => hit > 0)) coveredBranches++;
#                     });
#                 }
#                 if (file.f) {
#                     Object.values(file.f).forEach(hit => {
#                         totalFunctions++;
#                         if (hit > 0) coveredFunctions++;
#                     });
#                 }
#                 if (file.l) {
#                     Object.values(file.l).forEach(hit => {
#                         totalLines++;
#                         if (hit > 0) coveredLines++;
#                     });
#                 }
#             });

#             const summary = {
#                 total: {
#                     lines: {
#                         total: totalLines,
#                         covered: coveredLines,
#                         skipped: 0,
#                         pct: totalLines > 0 ? (coveredLines / totalLines * 100).toFixed(2) : 0
#                     },
#                     statements: {
#                         total: totalStatements,
#                         covered: coveredStatements,
#                         skipped: 0,
#                         pct: totalStatements > 0 ? (coveredStatements / totalStatements * 100).toFixed(2) : 0
#                     },
#                     functions: {
#                         total: totalFunctions,
#                         covered: coveredFunctions,
#                         skipped: 0,
#                         pct: totalFunctions > 0 ? (coveredFunctions / totalFunctions * 100).toFixed(2) : 0
#                     },
#                     branches: {
#                         total: totalBranches,
#                         covered: coveredBranches,
#                         skipped: 0,
#                         pct: totalBranches > 0 ? (coveredBranches / totalBranches * 100).toFixed(2) : 0
#                     }
#                 }
#             };

#             fs.writeFileSync('/results/coverage/coverage-summary.json', JSON.stringify(summary, null, 2));
#             console.log('覆盖率摘要已生成');
#         } catch (e) {
#             console.log('生成覆盖率摘要失败:', e.message);
#             // 创建空的摘要
#             fs.writeFileSync('/results/coverage/coverage-summary.json',
#                 JSON.stringify({
#                     total: {
#                         lines: { total: 0, covered: 0, skipped: 0, pct: 0 },
#                         statements: { total: 0, covered: 0, skipped: 0, pct: 0 },
#                         functions: { total: 0, covered: 0, skipped: 0, pct: 0 },
#                         branches: { total: 0, covered: 0, skipped: 0, pct: 0 }
#                     }
#                 }, null, 2)
#             );
#         }
#         "
#     else
#         echo "创建空的覆盖率摘要"
#         echo '{"total": {"lines":{"total":0,"covered":0,"skipped":0,"pct":0},"statements":{"total":0,"covered":0,"skipped":0,"pct":0},"functions":{"total":0,"covered":0,"skipped":0,"pct":0},"branches":{"total":0,"covered":0,"skipped":0,"pct":0}}}' > /results/coverage/coverage-summary.json
#     fi
# else
#     echo "创建空的覆盖率目录"
#     mkdir -p /results/coverage
#     echo '{"total": {"lines":{"total":0,"covered":0,"skipped":0,"pct":0},"statements":{"total":0,"covered":0,"skipped":0,"pct":0},"functions":{"total":0,"covered":0,"skipped":0,"pct":0},"branches":{"total":0,"covered":0,"skipped":0,"pct":0}}}' > /results/coverage/coverage-summary.json
# fi

# # 7. 创建突变测试报告（暂不执行）
# echo "突变测试暂不执行" > /results/mutation.txt

# echo "=== 测试执行完成 ==="
# '''

#         # 运行 Docker 容器执行测试脚本
#         print("执行测试脚本...")
#         result = subprocess.run([
#             "docker", "run", "--rm",
#             "-v", f"{test_results_dir}:/results",
#             "js-repo-with-test",
#             "bash", "-c", test_script
#         ], check=False, cwd=cwd, capture_output=True, text=True)

#         print(f"Docker运行输出: {result.stdout}")
#         if result.stderr:
#             print(f"Docker运行错误: {result.stderr}")

#         # 检查结果目录中的文件
#         print(f"=== 检查结果目录: {test_results_dir} ===")
#         for root, dirs, files in os.walk(test_results_dir):
#             level = root.replace(test_results_dir, '').count(os.sep)
#             indent = ' ' * 2 * level
#             print(f"{indent}{os.path.basename(root)}/")
#             subindent = ' ' * 2 * (level + 1)
#             for file in files:
#                 print(f"{subindent}{file}")

#         # 解析测试结果
#         compile_result = calculate_js_compile_pass_rate(test_results_dir)
#         coverage_result = get_js_coverage_rate(test_results_dir)
#         # mutation_result = get_js_mutation_rate(test_results_dir)

#         summary = {**compile_result, **coverage_result}

#         with open(os.path.join(test_results_dir, "summary.json"), 'w', encoding='utf-8') as f:
#             json.dump(summary, f, indent=2, ensure_ascii=False)

#         print("测试完成")
#         print(f"报告位置: {test_results_dir}")
#         print(f"总结报告: {json.dumps(summary, indent=2)}")

#     except Exception as e:
#         print(f"测试运行失败: {e}")
#         import traceback
#         traceback.print_exc()

#         # 即使失败也尝试生成一个空的总结报告
#         summary = {
#             "total_tests": 0,
#             "passed_tests": 0,
#             "failed_tests": 0,
#             "test_pass_rate": 0,
#             "statement_coverage": 0,
#             "branch_coverage": 0,
#             "function_coverage": 0,
#             "line_coverage": 0,
#             "total_mutants": 0,
#             "killed_mutants": 0,
#             "survived_mutants": 0,
#             "timeout_mutants": 0,
#             "no_coverage_mutants": 0,
#             "mutation_score": 0
#         }

#         with open(os.path.join(test_results_dir, "summary.json"), 'w', encoding='utf-8') as f:
#             json.dump(summary, f, indent=2, ensure_ascii=False)

#         sys.exit(1)


# def calculate_js_compile_pass_rate(test_results_dir):
#     """计算 JavaScript 测试通过率"""
#     report_paths = [
#         os.path.join(test_results_dir, "jest-report.json"),
#         os.path.join(test_results_dir, "jest-raw.json")
#     ]

#     for report_path in report_paths:
#         if os.path.exists(report_path):
#             try:
#                 with open(report_path, 'r') as f:
#                     report = json.load(f)

#                 # 尝试从不同格式中提取测试结果
#                 total = 0
#                 passed = 0
#                 failed = 0

#                 # 格式1: Jest的标准JSON输出
#                 if 'numTotalTests' in report:
#                     total = report.get('numTotalTests', 0)
#                     passed = report.get('numPassedTests', 0)
#                     failed = report.get('numFailedTests', 0)
#                 # 格式2: 包含testResults数组
#                 elif 'testResults' in report:
#                     for suite in report['testResults']:
#                         if 'assertionResults' in suite:
#                             for test in suite['assertionResults']:
#                                 total += 1
#                                 if test.get('status') == 'passed':
#                                     passed += 1
#                                 else:
#                                     failed += 1

#                 pass_rate = (passed / total * 100) if total > 0 else 0

#                 return {
#                     "total_tests": total,
#                     "passed_tests": passed,
#                     "failed_tests": failed,
#                     "test_pass_rate": round(pass_rate, 2)
#                 }
#             except Exception as e:
#                 print(f"解析Jest报告失败 ({report_path}): {e}")
#                 continue

#     print("未找到有效的Jest报告文件")
#     return {
#         "total_tests": 0,
#         "passed_tests": 0,
#         "failed_tests": 0,
#         "test_pass_rate": 0
#     }


# def get_js_coverage_rate(test_results_dir):
#     """获取 JavaScript 代码覆盖率"""
#     coverage_path = os.path.join(test_results_dir, "coverage", "coverage-summary.json")

#     if os.path.exists(coverage_path):
#         try:
#             with open(coverage_path, 'r') as f:
#                 coverage_data = json.load(f)

#             if 'total' in coverage_data:
#                 total = coverage_data['total']
#             else:
#                 total = coverage_data

#             return {
#                 "statement_coverage": float(total.get('statements', {}).get('pct', 0)),
#                 "branch_coverage": float(total.get('branches', {}).get('pct', 0)),
#                 "function_coverage": float(total.get('functions', {}).get('pct', 0)),
#                 "line_coverage": float(total.get('lines', {}).get('pct', 0))
#             }
#         except Exception as e:
#             print(f"解析覆盖率报告失败: {e}")

#     # 尝试查找其他覆盖率文件
#     print("未找到 coverage-summary.json，尝试计算简单覆盖率")
#     return {
#         "statement_coverage": 0,
#         "branch_coverage": 0,
#         "function_coverage": 0,
#         "line_coverage": 0
#     }


# def get_js_mutation_rate(test_results_dir):
#     """获取 JavaScript 突变测试结果"""
#     mutation_path = os.path.join(test_results_dir, "mutation.txt")

#     if os.path.exists(mutation_path):
#         try:
#             with open(mutation_path, 'r') as f:
#                 content = f.read()

#             # 检查是否有突变测试结果
#             if "突变测试暂不执行" in content:
#                 return {
#                     "total_mutants": 0,
#                     "killed_mutants": 0,
#                     "survived_mutants": 0,
#                     "timeout_mutants": 0,
#                     "no_coverage_mutants": 0,
#                     "mutation_score": 0,
#                     "note": "突变测试未执行"
#                 }

#             # 尝试解析突变测试结果
#             lines = content.split('\n')
#             killed = 0
#             survived = 0

#             for line in lines:
#                 if '✓' in line and 'killed' in line.lower():
#                     killed += 1
#                 elif '✗' in line and 'survived' in line.lower():
#                     survived += 1
#                 elif 'Killed:' in line:
#                     # 提取数字
#                     import re
#                     match = re.search(r'Killed:\s*(\d+)', line)
#                     if match:
#                         killed = int(match.group(1))
#                 elif 'Survived:' in line:
#                     import re
#                     match = re.search(r'Survived:\s*(\d+)', line)
#                     if match:
#                         survived = int(match.group(1))

#             total_mutants = killed + survived

#             if total_mutants > 0:
#                 mutation_score = (killed / total_mutants) * 100
#             else:
#                 mutation_score = 0

#             return {
#                 "total_mutants": total_mutants,
#                 "killed_mutants": killed,
#                 "survived_mutants": survived,
#                 "timeout_mutants": 0,
#                 "no_coverage_mutants": 0,
#                 "mutation_score": round(mutation_score, 2)
#             }
#         except Exception as e:
#             print(f"解析突变测试报告失败: {e}")

#     return {
#         "total_mutants": 0,
#         "killed_mutants": 0,
#         "survived_mutants": 0,
#         "timeout_mutants": 0,
#         "no_coverage_mutants": 0,
#         "mutation_score": 0
#     }


# # 使用示例
# if __name__ == "__main__":
#     # 参数说明：
#     # dockerfile_path: 原始 Dockerfile 路径
#     # gen_tests_dir: 生成的测试代码目录
#     # cover_source: 要覆盖的源代码目录
#     # repo_name: 仓库名称（用于创建结果目录）

#     create_and_run_js(
#         dockerfile_path="output/gpt-4.1/three/three.js/Dockerfile",
#         gen_tests_dir="",
#         cover_source="",
#         repo_name="three"
#     )


# !/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import os
import sys
import json
from pathlib import Path
from argparse import ArgumentParser
# from cal_jest_cov import parse_coverage


def syntax_analyse_js(project_root, gen_tests_dir):
    """
    对生成的 JS 测试文件做语法检查（使用 node --check）。
    有语法错误的测试文件会被删除。
    返回：{total, syntax_correct, syntax_correct_rate}
    """
    test_dir = os.path.join(project_root, gen_tests_dir)
    p = Path(test_dir)
    if not p.exists():
        print(f"测试目录不存在: {test_dir}")
        return {"total": 0, "syntax_correct": 0, "syntax_correct_rate": 0}

    total = 0
    syntax_correct = 0
    for js_file in p.rglob("*.js"):
        name_low = js_file.name.lower()
        # 仅处理看起来像测试的文件（包含 test）
        if "test" in name_low or name_low.startswith("spec") or name_low.endswith(".spec.js"):
            total += 1
            try:
                # node --check filename 仅做语法校验（Node 10+ 支持）
                res = subprocess.run(["node", "--check", str(js_file)], capture_output=True, text=True)
                if res.returncode == 0:
                    syntax_correct += 1
                else:
                    print(f"[语法错误] 删除文件 {js_file}:\n{res.stderr.strip()}")
                    try:
                        js_file.unlink()
                    except Exception as e:
                        print(f"删除失败: {e}")
            except FileNotFoundError:
                # 本地没有 node，可选择不做本地检查或用其它方式
                print("本地未找到 node，可跳过本地语法检查（Docker 内仍会检查）。")
                # 认为语法未知，保留文件
                syntax_correct += 1

    rate = (syntax_correct / total) if total > 0 else 0
    return {"total": total, "syntax_correct": syntax_correct, "syntax_correct_rate": rate}


# def calculate_test_metrics_js(report_file):
#     """
#     解析 Jest JSON 报告（npx jest --json --outputFile=...）。
#     返回：compile (suites passed count)，testcase dict 包含传递率等
#     """
#     if not os.path.exists(report_file):
#         print(f"未找到测试报告: {report_file}")
#         return {"compile_pass": 0}, {"testcase": {}}

#     with open(report_file, 'r', encoding='utf-8') as f:
#         report = json.load(f)

#     # Jest JSON output fields: numTotalTests, numPassedTests, numFailedTests, numTotalTestSuites, testResults(list)
#     test_results = report.get("testResults", [])
#     total_suites = len(test_results)
#     passed_suites = sum(1 for s in test_results if s.get("status") == "passed")
#     # 当 Jest 返回 top-level fields:
#     total_tests = report.get("numTotalTests", sum(s.get("assertionResults", []) and len(s.get("assertionResults", [])) for s in test_results))
#     passed_tests = report.get("numPassedTests", sum(len([a for a in s.get("assertionResults", []) if a.get("status") == "passed"]) for s in test_results))
#     failed_tests = report.get("numFailedTests", sum(len([a for a in s.get("assertionResults", []) if a.get("status") == "failed"]) for s in test_results))
#     skipped_tests = report.get("numPendingTests", sum(len([a for a in s.get("assertionResults", []) if a.get("status") in ("pending","skipped")]) for s in test_results))

#     testcase_summary = {
#         "total": total_tests,
#         "passed": passed_tests,
#         "failed": failed_tests,
#         "skipped": skipped_tests,
#     }

#     # 计算率，保护除零
#     test_pass_rate = (passed_tests / total_tests) if total_tests > 0 else 0
#     run_pass_rate = ((total_tests - report.get("numRuntimeErrorTestSuites", 0) - failed_tests) / total_tests) if total_tests > 0 else 0

#     testcase_summary.update({
#         "test_pass_rate": test_pass_rate,
#         "run_pass_rate": run_pass_rate,
#         "num_total_suites": total_suites,
#         "num_passed_suites": passed_suites,
#         "num_reported_test_suites": report.get("numTotalTestSuites", total_suites)
#     })

#     compile = {
#         "compile_pass": passed_suites,
#         "compile_total": total_suites,
#         # compile_pass_rate 在汇总处计算（可以基于 syntax_analyse 的 total）
#     }

#     return compile, {"testcase": testcase_summary}

def calculate_test_metrics_js(report_file):
    """
    解析 Jest JSON 报告（npx jest --json --outputFile=...）。
    返回：compile (suites passed count)，testcase dict 包含传递率等
    """
    if not os.path.exists(report_file):
        print(f"未找到测试报告: {report_file}")
        return {"compile_pass": 0}, {"testcase": {}}

    with open(report_file, 'r', encoding='utf-8') as f:
        report = json.load(f)

    # Jest JSON output fields: numTotalTests, numPassedTests, numFailedTests, numTotalTestSuites, testResults(list)
    test_results = report.get("testResults", [])

    # 安全地计算测试套件统计
    total_suites = len(test_results)
    passed_suites = sum(1 for s in test_results if isinstance(s, dict) and s.get("status") == "passed")

    # 修复：安全地计算 total_tests
    # 首先检查 report 中是否有 numTotalTests
    total_tests = report.get("numTotalTests", 0)

    # 如果没有 numTotalTests，则从 testResults 中计算
    if total_tests == 0 and test_results:
        total_tests = 0
        for suite in test_results:
            if isinstance(suite, dict):
                assertion_results = suite.get("assertionResults", [])
                if isinstance(assertion_results, list):
                    total_tests += len(assertion_results)

    # 安全地计算 passed_tests
    passed_tests = report.get("numPassedTests", 0)
    if passed_tests == 0 and test_results:
        passed_tests = 0
        for suite in test_results:
            if isinstance(suite, dict):
                assertion_results = suite.get("assertionResults", [])
                if isinstance(assertion_results, list):
                    passed_tests += len(
                        [a for a in assertion_results if isinstance(a, dict) and a.get("status") == "passed"])

    # 安全地计算 failed_tests
    failed_tests = report.get("numFailedTests", 0)
    if failed_tests == 0 and test_results:
        failed_tests = 0
        for suite in test_results:
            if isinstance(suite, dict):
                assertion_results = suite.get("assertionResults", [])
                if isinstance(assertion_results, list):
                    failed_tests += len(
                        [a for a in assertion_results if isinstance(a, dict) and a.get("status") == "failed"])

    # 安全地计算 skipped_tests
    skipped_tests = report.get("numPendingTests", 0)
    if skipped_tests == 0 and test_results:
        skipped_tests = 0
        for suite in test_results:
            if isinstance(suite, dict):
                assertion_results = suite.get("assertionResults", [])
                if isinstance(assertion_results, list):
                    skipped_tests += len([a for a in assertion_results if
                                          isinstance(a, dict) and a.get("status") in ("pending", "skipped")])

    # 如果 total_tests 仍然为 0，尝试使用其他方法计算
    if total_tests == 0:
        total_tests = passed_tests + failed_tests + skipped_tests

    # 创建测试用例摘要
    testcase_summary = {
        "total": total_tests,
        "passed": passed_tests,
        "failed": failed_tests,
        "skipped": skipped_tests,
    }

    # 计算率，保护除零
    test_pass_rate = (passed_tests / total_tests) if total_tests > 0 else 0

    # 修复：确保 run_pass_rate 计算安全
    runtime_errors = report.get("numRuntimeErrorTestSuites", 0)
    if total_tests > 0:
        run_pass_rate = ((total_tests - runtime_errors - failed_tests) / total_tests)
    else:
        run_pass_rate = 0

    testcase_summary.update({
        "test_pass_rate": test_pass_rate,
        "run_pass_rate": run_pass_rate,
        "num_total_suites": total_suites,
        "num_passed_suites": passed_suites,
        "num_reported_test_suites": report.get("numTotalTestSuites", total_suites)
    })

    compile = {
        "compile_pass": passed_suites,
        "compile_total": total_suites,
        # compile_pass_rate 在汇总处计算（可以基于 syntax_analyse 的 total）
    }

    return compile, {"testcase": testcase_summary}


def get_coverage_rate_js(coverage_summary_file):
    """
    解析 Istanbul/nyc 生成的 coverage-summary.json（位于 coverage/coverage-summary.json）。
    返回类似你原来 get_coverage_rate 的结构。
    """
    if not os.path.exists(coverage_summary_file):
        print(f"未找到 coverage summary: {coverage_summary_file}")
        return {
            "total_line_coverage": 0,
            "total_branch_coverage": 0,
            "total_function_coverage": 0,
            "total_statement_coverage": 0,
            "file_coverage": {},
            "summary": {}
        }

    with open(coverage_summary_file, 'r', encoding='utf-8') as f:
        coverage = json.load(f)

    # coverage-summary.json 的结构通常包含 "total" 字段以及每个文件的 coverage object
    totals = coverage.get("total", {})
    result = {
        "total_line_coverage": totals.get("lines", {}).get("pct", 0),
        "total_branch_coverage": totals.get("branches", {}).get("pct", 0),
        "total_function_coverage": totals.get("functions", {}).get("pct", 0),
        "total_statement_coverage": totals.get("statements", {}).get("pct", 0),
        "file_coverage": {},
        "summary": {
            "lines": totals.get("lines", {}),
            "branches": totals.get("branches", {}),
            "functions": totals.get("functions", {}),
            "statements": totals.get("statements", {})
        }
    }

    # 逐文件记录
    for file_path, data in coverage.items():
        if file_path == "total":
            continue
        # 每个文件数据示例： { "lines": {"total": X, "covered": Y, "skipped": 0, "pct": Z}, ... }
        file_entry = {
            "line_coverage": data.get("lines", {}).get("pct", 0),
            "branch_coverage": data.get("branches", {}).get("pct", 0),
            "function_coverage": data.get("functions", {}).get("pct", 0),
            "statement_coverage": data.get("statements", {}).get("pct", 0),
            "lines": data.get("lines", {}),
            "branches": data.get("branches", {}),
            "functions": data.get("functions", {}),
            "statements": data.get("statements", {})
        }
        result["file_coverage"][file_path] = file_entry

    return result


def create_and_run_js(dockerfile_path, project_root, data_file, github_token=None):
    """
    主要流程：
      1) 本地做语法检查并删除有语法错误的测试文件
      2) 用 Docker 构建镜像并运行测试（在容器内使用 npm / npx jest）
      3) 解析 /results/report.json 与 /results/coverage/coverage-summary.json，生成 summary.json
    注意：Dockerfile 应包含 Node 环境，能执行 npm / npx / node。
    """
    cwd = os.getcwd()
    print(f"当前工作目录: {cwd}")

    # 先做本地语法检测（可选）
    project_dir = os.path.join(cwd, project_root)
    # syntax_report = syntax_analyse_js(project_dir, gen_tests_dir)

    # 准备测试结果目录（主机）
    test_results_base = os.path.join(cwd, "test_results", "javascript")
    repo_name = project_root
    if "/" in project_root:
        repo_name = project_root.split("/")[1]
    test_results_dir = os.path.join(test_results_base, repo_name, "jest_agent")
    os.makedirs(test_results_dir, exist_ok=True)

    # 构建镜像
    print("开始构建镜像...")
    try:
        subprocess.run([
            "docker", "build",
            "-t", "repo-with-js-test",
            "-f", dockerfile_path,
            "."
        ], check=True, cwd=cwd)
    except subprocess.CalledProcessError as e:
        print(f"镜像构建失败: {e}")
        sys.exit(1)

    print("镜像构建成功，开始运行测试容器...")

    # 在容器中运行：安装依赖并执行 jest（生成 JSON 报告与 coverage）
    # 注意：假设项目根目录包含 package.json 并声明 jest 配置，或者使用 npx jest 命令
    try:
        # 构造要在容器中执行的脚本（多行 bash）
        container_cmd = f"""
            # proton
            # jq '.env.test = {{
            #     "presets": [
            #         [
            #         "@babel/preset-env",
            #         {{
            #             "modules": "commonjs",
            #             "targets": {{ "node": "current" }},
            #             "loose": true,
            #             "bugfixes": true
            #         }}
            #         ]
            #     ]
            # }}' .babelrc.json > .babelrc.json.tmp && mv .babelrc.json.tmp .babelrc.json

            # set -e
            # 安装 Python3
            if ! command -v python3 &> /dev/null; then
                apt update && apt install -y python3
            fi

     
            # 使用 ci 更可重复；若没有 package-lock.json 可改成 npm install
            if [ -f package-lock.json ] || [ -f npm-shrinkwrap.json ]; then
                npm ci --no-audit --no-fund || npm install --no-audit --no-fund
            else
                npm install --no-audit --no-fund
            fi

            export COPILOT_GITHUB_TOKEN="$GITHUB_TOKEN"

            python3 /testbed/agent.py \
                --dataset /testbed/{data_file}
            
        """

        subprocess.run([
            "docker", "run", "--rm",
            "-v", f"{test_results_dir}:/results",
            "-e", f"GITHUB_TOKEN={github_token}",
            # "-v", "/mnt/software-testing/projects/pdf.js/jest.config.js:/testbed/jest.config.js",
            # "-v", "/mnt/software-testing/projects/pdf.js/babel.config.cjs:/testbed/babel.config.cjs",
            "-v", "./agent/agent.py:/testbed/agent.py",
            "-v", "./rollup.temp.config.mjs:/testbed/rollup.temp.config.mjs",
            "-v", "./jest.config.js:/testbed/jest.config.js",
            "-v", "./babel.config.js:/testbed/babel.config.js",
            # "-v", "./babel.config.cjs:/testbed/babel.config.cjs",
            "-v", f"./{data_file}:/testbed/{data_file}",
            "repo-with-js-test",
            "bash", "-c", container_cmd
        ], check=True, cwd=cwd)

    except subprocess.CalledProcessError as e:
        print(f"容器运行/测试失败: {e}")
        # 仍然尝试解析已有报告
        # sys.exit(1)

    


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--dockerfile-path", type=str, default="Dockerfile", help="Dockerfile 路径")
    parser.add_argument("--project-root", type=str, default=".", help="项目根目录（本地）")
    parser.add_argument("--data-file", type=str, help="数据文件路径")
    # parser.add_argument("--github-token", type=str, help="GitHub Token")
    args = parser.parse_args()

    # 示例调用：你可以改成你项目的路径
    create_and_run_js("output/modern-error/dockerfile",
                      project_root="projects/modern-error", data_file="dataset/tem.json", github_token="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")
    # create_and_run_js(args.dockerfile_path, args.test_dir, args.cover_source, args.project_root)
