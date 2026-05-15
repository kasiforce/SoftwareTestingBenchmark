# # from python_focal_extractor import FocalExtractor

# # if __name__ == "__main__":
# #     extractor = FocalExtractor("./django")
# #     extractor.save_to_json("django_focal.json")


# import json
# import openai
# from openai import OpenAI
# import os
# import time
# from typing import List, Dict, Any
# import logging

# # 配置日志
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# class TestCodeGenerator:
#     def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
#         """
#         初始化测试代码生成器

#         Args:
#             api_key: OpenAI API密钥
#             model: 使用的模型名称
#         """
#         self.api_key = api_key
#         self.model = model
#         openai.api_key = api_key

#     def generate_test_prompt(self, test_framework, function_info: Dict[str, Any]) -> str:
#         """
#         为给定函数生成测试提示

#         Args:
#             function_info: 函数信息字典

#         Returns:
#             生成的提示字符串
#         """
#         function_name = function_info['name']
#         function_code = function_info['code']
#         # imports = '\n'.join(function_info['imports']['imports'])
#         # from_imports = '\n'.join(function_info['imports']['from_imports'])
#         # all_imports = imports + '\n' + from_imports + '\n'
#         class_name = None
#         if function_info['type'] == "method":
#             class_name = function_info.get('class_name')
#         file_path = function_info['src_file']
#         test_path = function_info['test_file']
#         prompt = f"""
# Please generate a test class for the following function.

# Function Information:
# - Src file: {file_path}
# - Function name: {function_name}
# - Class: {class_name if class_name else 'Standalone function'}
# - Is async: {function_info.get('is_async', False)}

# Function Code:
# ```python
# {function_code}
# Requirements:

# Use {test_framework} framework for writing tests

# Your job is to output corresponding test class that obtains high coverage and invokes the code under test.
# Each test case must be a function starting with test_.
# The test code should be written into {test_path}.
# Return ONLY code without explanations, non-code text, or markdown formatting.
# Please make sure the imports are correct.
# ```python
# class Testfunction_name
# """
# # The test code will be written into the file /mnt/dc2024/Untitled/benchmark/markitdown/tests/generated/test_{function_name}.py.
# # Please make sure the imports are correct.
#         return prompt


#     def call_llm(self, prompt: str, max_K: int = 1) -> str:
#         """
#         调用大模型API生成测试代码

#         Args:
#             prompt: 提示文本
#             max_K: 最多生成测试用例数量

#         Returns:
#             生成的测试代码
#         """
#         message = [ {"role": "system", "content": "You are a professional Python test engineer specializing in writing high-quality unit test code."},
#                     {"role": "user", "content": prompt}
#                   ]
#         tests = []
#         client = OpenAI(api_key=self.api_key,
#                     base_url="https://api.agicto.cn/v1")
#         for k in range(max_K):
#             try:
#                 response = client.chat.completions.create(
#                     model=self.model,
#                     messages=message,
#                     temperature=0.2,
#                     max_tokens=1024
#                 )
#                 if response.choices and len(response.choices) > 0:
#                     message_content = response.choices[0].message.content
#                     if message_content:
#                         test = self._extract_code(message_content)
#                         tests.append(test)
#                         message.append({"role": "assistant", "content": test})
#                         message.append({"role": "user", "content": "Generate another test method for the function under test. Your answer must be different from previously-generated test cases and should cover different statements and branches."})


#             except openai.RateLimitError:
#                 wait_time = 2 ** k  # 指数退避
#                 logger.warning(f"速率限制，等待 {wait_time} 秒后重试...")
#                 time.sleep(wait_time)

#             except openai.APIError as e:
#                 logger.error(f"API错误: {e}")
#                 if k >= 1:
#                     raise
#                 time.sleep(1)

#             except Exception as e:
#                 logger.error(f"未知错误: {e}")
#                 if k >= 1:
#                     raise
#                 time.sleep(1)

#         return tests

#     def generate_test_for_function(self, function_info: Dict[str, Any]) -> Dict[str, Any]:
#         """
#         为单个函数生成测试代码

#         Args:
#             function_info: 函数信息

#         Returns:
#             包含测试代码的增强函数信息
#         """
#         logger.info(f"为函数 {function_info['name']} 生成测试代码...")

#         try:
#             prompt = self.generate_test_prompt("pytest", function_info)
#             tests = self.call_llm(prompt)
#             result = function_info.copy()
#             result['generated_tests'] = tests
#             result['test_generation_status'] = 'success'

#             logger.info(f"成功为 {function_info['name']} 生成测试代码")

#         except Exception as e:
#             logger.error(f"为 {function_info['name']} 生成测试代码失败: {e}")
#             result = function_info.copy()
#             result['generated_tests'] = []
#             result['test_generation_status'] = f'failed: {str(e)}'

#         return result

#     def generate_tests_for_functions(self, functions: List[Dict[str, Any]],
#                                 output_file: str = None,
#                                 batch_delay: int = 1) -> List[Dict[str, Any]]:
#         """
#         为函数列表批量生成测试代码

#         Args:
#             functions: 函数信息列表
#             output_file: 输出文件路径（可选）
#             batch_delay: 批次之间的延迟（秒）

#         Returns:
#             包含测试代码的函数列表
#         """
#         results = []
#         total = len(functions)

#         for i, func in enumerate(functions, 1):
#             logger.info(f"处理进度: {i}/{total}")

#             result = self.generate_test_for_function(func)
#             # print(result)
#             results.append(result)

#             # 保存中间结果
#             if output_file and i % 10 == 0:
#                 self.save_results(results, f"{output_file}.partial")

#             # 避免速率限制
#             time.sleep(batch_delay)

#         # 保存最终结果
#         if output_file:
#             self.save_results(results, output_file)

#         return results

#     def _extract_code(self, s: str):
#         # 使用 '```python' 和 '```' 来分割字符串
#         parts = s.split('```python')
#         if len(parts) > 1:
#             # 移除后面的 '```'
#             code = parts[1].rsplit('```', 1)[0]
#             return code.strip("\n").strip()
#         return s.strip("\n").strip()

#     def save_results(self, results: List[Dict[str, Any]], output_file: str):
#         """
#         保存结果到JSON文件

#         Args:
#             results: 结果列表
#             output_file: 输出文件路径
#         """
#         try:
#             with open(output_file, 'w', encoding='utf-8') as f:
#                 json.dump(results, f, indent=2, ensure_ascii=False)
#             logger.info(f"结果已保存到: {output_file}")
#         except Exception as e:
#             logger.error(f"保存结果失败: {e}")

# def main():
#     # 从环境变量获取API密钥
#     api_key = ""
#     if not api_key:
#         raise ValueError("请设置 OPENAI_API_KEY 环境变量")


#     # 初始化生成器
#     generator = TestCodeGenerator(api_key=api_key, model="gpt-4o-mini")

#     # 加载函数数据
#     input_file = "astropy_focal.json"  # 替换为您的输入文件路径
#     with open(input_file, 'r', encoding='utf-8') as f:
#         functions_data = json.load(f)

#     logger.info(f"找到 {len(functions_data)} 个需要生成测试的函数")

#     # 生成测试代码
#     output_file = "astropy_tests_class.json"
#     results = generator.generate_tests_for_functions(
#         functions=functions_data,
#         output_file=output_file,
#         batch_delay=1  # 每次调用间隔1秒
#     )

#     # 统计结果
#     success_count = sum(1 for r in results if r.get('test_generation_status') == 'success')
#     logger.info(f"测试生成完成: {success_count}/{len(results)} 成功")

# if __name__ == "__main__":
#     main()


import json
import openai
from openai import OpenAI
import os
import re
import time
from typing import List, Dict, Any
import logging
import glob
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestCodeGenerator:
    def __init__(self, api_key: str, input: str, testframe: str, model: str = "gpt-4o-mini"):
        """
        初始化测试代码生成器

        Args:
            api_key: OpenAI API密钥
            testframe: 测试框架名称
            model: 使用的模型名称
            model: 使用的模型名称
        """
        self.api_key = api_key
        self.model = model
        self.input = input
        self.testframe = testframe
        openai.api_key = api_key

    def generate_test_prompt(self, test_framework, function_info: Dict[str, Any]) -> str:
        """
        为给定函数生成测试提示

        Args:
            function_info: 函数信息字典

        Returns:
            生成的提示字符串
        """
        function_name = function_info['name']
        function_code = function_info['code']
        # signature = function_code.split(':\n')[0]
        signature = function_code.split('{', 1)[0].rstrip()
        print(signature)

        # match = re.search(r'^def\s+\w+\([^)]*\)(?:\s*->\s*[^:]+)?:', function_code, re.MULTILINE)
        # if match:
        #     signature = match.group(0)

        class_name = None
        class_info = {}
        if function_info['type'] == "method":
            class_name = function_info.get('class_name')
            class_info['class_name'] = class_name
            if function_info['class_constructor']:
                class_info['class_constructor'] = function_info['class_constructor']
            if function_info['class_fields']:
                class_info['class_fields'] = function_info['class_fields']
            # if function_info['class_variables']:
            #     class_info['class_variables'] = function_info['class_variables']

        specification = function_info['specification']
        file_path = function_info['src_file']
        test_path = function_info['test_file']

        if self.input == "specification":
            prompt = f"""
Please generate a test class for the following function.

Function Information:
- Src file: {file_path}
- Function name: {function_name}
- Class: {class_info if class_name else 'Standalone function'}
- Is async: {function_info.get('is_async', False)}

Function Specification:
```javascript
{signature}
```{specification}```


Requirements:
Use {test_framework} framework for writing tests.
Your job is to output corresponding test class that obtains high coverage and invokes the code under test.
The test code should be written into {test_path}. Please make sure the imports are correct.
Return ONLY code without explanations, non-code text, or markdown formatting.

```javascript
<test code>
"""

#             prompt = f"""
# Please generate a test class for the following function.

# Function Information:
# - Src file: {file_path}
# - Function name: {function_name}
# - Class: {class_info if class_name else 'Standalone function'}

# Function Code:
# ```python
# {function_code}

# Requirements:
# Use {test_framework} framework for writing tests.
# Your job is to output corresponding test class that obtains high coverage and invokes the code under test.
# Each test case must be a function starting with test_.
# The test code should be written into {test_path}. Please make sure the imports are correct.
# Return ONLY code without explanations, non-code text, or markdown formatting.

# ```python
# <test code>
# """

        # print(test_framework)
        else:
            prompt = f"""
Please generate a test class for the following function.

Function Information:
- Src file: {file_path}
- Function name: {function_name}
- Class: {class_info if class_name else 'Standalone function'}
- Is async: {function_info.get('is_async', False)}

Function Code:
```javascript
{function_code}


Requirements:
Use {test_framework} framework for writing tests.
Your job is to output corresponding test class that obtains high coverage and invokes the code under test.
The test code should be written into {test_path}. Please make sure the imports are correct.
Return ONLY code without explanations, non-code text, or markdown formatting.

```javascript
<test code>
"""
#             prompt = f"""
# Please generate a test class for the following function.

# Function Information:
# - Src file: {file_path}
# - Function name: {function_name}
# - Class: {class_info if class_name else 'Standalone function'}
# - Is async: {function_info.get('is_async', False)}

# Function Specification:
# ```python
# {signature}
# ```{specification}```

# Requirements:
# Use {test_framework} framework for writing tests.
# Your job is to output corresponding test class that obtains high coverage and invokes the code under test.
# Each test case must be a function starting with test_.
# The test code should be written into {test_path}. Please make sure the imports are correct.
# Return ONLY code without explanations, non-code text, or markdown formatting.

# ```python
# <test code>
# """
        # print(prompt)
        return prompt

    def call_llm(self, prompt: str, max_K: int = 3) -> str:
        """
        调用大模型API生成测试代码

        Args:
            prompt: 提示文本
            max_K: 最多生成测试用例数量

        Returns:
            生成的测试代码
        """
        message = [{"role": "system",
                    "content": "You are a professional test engineer specializing in writing high-quality unit test code."},
                   {"role": "user", "content": prompt}
                   ]
        tests = []
        client = OpenAI(api_key=self.api_key, 
                        base_url="https://api.apiyi.com/v1")
                        # base_url="https://api.agicto.cn/v1")
        # print(self.model)
        for k in range(max_K):
            try:
                response = client.chat.completions.create(
                    model=self.model,
                    messages=message,
                    temperature=0.,
                    max_tokens=16384
                )
                # print(message)
                # print(response)
                if response.choices and len(response.choices) > 0:
                    message_content = response.choices[0].message.content
                    # print(message_content)
                    if message_content:
                        test = self._extract_code(message_content)
                        if not test.strip():
                            print(f"第 {k} 次尝试失败")
                            time.sleep(1)
                            continue
                        tests.append(test)
                        break
                        # message.append({"role": "assistant", "content": test})
                        # message.append({"role": "user",
                                        # "content": "Generate another test method for the function under test. Your answer must be different from previously-generated test cases and should cover different statements and branches."})

            except openai.RateLimitError:
                wait_time = 2 ** k  # 指数退避
                logger.warning(f"速率限制，等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)

            except openai.APIError as e:
                logger.error(f"API错误: {e}")
                if k >= 1:
                    raise
                time.sleep(1)

            except Exception as e:
                logger.error(f"未知错误: {e}")
                if k >= 1:
                    raise
                time.sleep(1)

        return tests

    def generate_test_for_function(self, function_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        为单个函数生成测试代码

        Args:
            function_info: 函数信息

        Returns:
            包含测试代码的增强函数信息
        """
        logger.info(f"为函数 {function_info['name']} 生成测试代码...")

        try:
            prompt = self.generate_test_prompt(self.testframe, function_info)
            tests = self.call_llm(prompt)
            result = function_info.copy()
            result['generated_tests'] = tests
            result['test_generation_status'] = 'success'

            logger.info(f"成功为 {function_info['name']} 生成测试代码")

        except Exception as e:
            logger.error(f"为 {function_info['name']} 生成测试代码失败: {e}")
            result = function_info.copy()
            result['generated_tests'] = []
            result['test_generation_status'] = f'failed: {str(e)}'

        return result

    def generate_tests_for_functions_parallel(self,
                                              functions: List[Dict[str, Any]],
                                              output_file: str = None,
                                              max_workers: int = 5,
                                              save_interval: int = 10) -> List[Dict[str, Any]]:
        """
        为函数列表批量生成测试代码（并行版本）

        Args:
            functions: 函数信息列表
            output_file: 输出文件路径（可选）
            max_workers: 最大并行工作线程数
            save_interval: 保存间隔（每处理多少个函数保存一次）

        Returns:
            包含测试代码的函数列表
        """
        results = []
        total = len(functions)

        # 创建线程池
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_function = {
                executor.submit(self.generate_test_for_function, func): func
                for func in functions
            }

            # 处理完成的任务
            completed_count = 0
            for future in as_completed(future_to_function):
                func = future_to_function[future]
                try:
                    result = future.result()
                    results.append(result)
                    completed_count += 1

                    # 更新进度
                    logger.info(f"处理进度: {completed_count}/{total} (完成 {func['name']})")

                    # 定期保存中间结果
                    if output_file and completed_count % save_interval == 0:
                        partial_file = f"{output_file}.partial_{completed_count}"
                        self.save_results(results, partial_file)
                        logger.info(f"已保存中间结果到: {partial_file}")

                except Exception as e:
                    logger.error(f"处理函数 {func['name']} 时发生错误: {e}")
                    # 创建错误结果
                    error_result = func.copy()
                    error_result['generated_tests'] = []
                    error_result['test_generation_status'] = f'failed: {str(e)}'
                    results.append(error_result)
                    completed_count += 1

        # 保存最终结果
        if output_file:
            self.save_results(results, output_file)
            logger.info(f"最终结果已保存到: {output_file}")

            # 删除所有中间文件
            self._cleanup_partial_files(output_file)

        return results

    def generate_tests_for_functions_parallel_batch(self,
                                                    functions: List[Dict[str, Any]],
                                                    output_file: str = None,
                                                    max_workers: int = 5,
                                                    batch_size: int = 20,
                                                    batch_delay: int = 1) -> List[Dict[str, Any]]:
        """
        为函数列表批量生成测试代码（使用JSONL格式的中间文件）

        Args:
            functions: 函数信息列表
            output_file: 输出文件路径
            max_workers: 最大并行工作线程数
            batch_size: 每批次处理的函数数量
            batch_delay: 批次之间的延迟（秒）

        Returns:
            包含测试代码的函数列表
        """
        results = []
        total = len(functions)

        # 打开中间结果文件（JSONL格式）
        partial_file = None
        partial_fp = None

        try:
            if output_file:
                partial_file = f"{output_file}.partial.jsonl"
                # 打开文件，如果存在则覆盖
                partial_fp = open(partial_file, 'w', encoding='utf-8')
                logger.info(f"中间结果将保存到: {partial_file}")

            # 按批次处理
            for i in range(0, total, batch_size):
                batch = functions[i:i + batch_size]
                batch_num = i // batch_size + 1
                total_batches = (total + batch_size - 1) // batch_size

                logger.info(f"开始处理批次 {batch_num}/{total_batches} ({len(batch)} 个函数)")

                # 使用线程池并行处理当前批次
                batch_results = []
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    future_to_function = {
                        executor.submit(self.generate_test_for_function, func): func
                        for func in batch
                    }

                    # 处理完成的任务
                    for future in as_completed(future_to_function):
                        func = future_to_function[future]
                        try:
                            result = future.result()
                            batch_results.append(result)
                            results.append(result)

                            # 立即写入单行JSON（JSONL格式）
                            if partial_fp:
                                json_line = json.dumps(result, ensure_ascii=False)
                                partial_fp.write(json_line + '\n')
                                partial_fp.flush()  # 确保立即写入磁盘

                        except Exception as e:
                            logger.error(f"处理函数 {func['name']} 时发生错误: {e}")
                            error_result = func.copy()
                            error_result['generated_tests'] = []
                            error_result['test_generation_status'] = f'failed: {str(e)}'
                            batch_results.append(error_result)
                            results.append(error_result)

                            if partial_fp:
                                json_line = json.dumps(error_result, ensure_ascii=False)
                                partial_fp.write(json_line + '\n')
                                partial_fp.flush()

                logger.info(f"批次 {batch_num} 处理完成，已追加到中间文件")

                # 如果不是最后一批，等待一段时间
                if i + batch_size < total and batch_delay > 0:
                    logger.info(f"等待 {batch_delay} 秒后处理下一批...")
                    time.sleep(batch_delay)

            # 保存最终结果
            if output_file:
                self.save_results(results, output_file)
                logger.info(f"最终结果已保存到: {output_file}")

                # 关闭并删除中间文件
                if partial_fp:
                    partial_fp.close()

                    # 删除中间文件
                    # self._cleanup_partial_files(partial_file)
                    os.remove(partial_file)

        except Exception as e:
            logger.error(f"处理过程中发生错误: {e}")
            if partial_fp:
                partial_fp.close()
            raise

        finally:
            # 确保文件被关闭
            if partial_fp:
                partial_fp.close()

        return results

    def _convert_jsonl_to_json(self, jsonl_file: str, json_file: str):
        """将JSONL文件转换为标准JSON文件"""
        try:
            results = []
            with open(jsonl_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        result = json.loads(line)
                        results.append(result)

            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)

            logger.info(f"已从JSONL转换到JSON: {json_file}")
        except Exception as e:
            logger.error(f"转换JSONL文件时出错: {e}")

    def _cleanup_partial_files(self, output_file: str):
        """
        清理中间结果文件

        Args:
            output_file: 最终输出文件路径
        """
        try:
            # 获取所有以output_file为前缀的中间文件
            base_name = os.path.basename(output_file)
            dir_name = os.path.dirname(output_file) or "."

            # 查找所有中间文件
            pattern = os.path.join(dir_name, f"{base_name}.partial*")
            partial_files = glob.glob(pattern)

            # 删除找到的文件
            deleted_count = 0
            for file_path in partial_files:
                try:
                    os.remove(file_path)
                    logger.info(f"已删除中间文件: {file_path}")
                    deleted_count += 1
                except Exception as e:
                    logger.warning(f"删除中间文件失败 {file_path}: {e}")

            logger.info(f"共删除 {deleted_count} 个中间文件")

        except Exception as e:
            logger.error(f"清理中间文件时出错: {e}")

    def _extract_code(self, s: str):
        # 使用 '```python' 和 '```' 来分割字符串
        parts = s.split('```javascript')
        if len(parts) > 1:
            # 移除后面的 '```'
            code = parts[1].split('```')[0]
            return code.strip("\n").strip()
        return s.split('```')[0].strip("\n").strip()

    def save_results(self, results: List[Dict[str, Any]], output_file: str):
        """
        保存结果到JSON文件

        Args:
            results: 结果列表
            output_file: 输出文件路径
        """
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            logger.info(f"结果已保存到: {output_file}")
        except Exception as e:
            logger.error(f"保存结果失败: {e}")


def main():
    # 从环境变量获取API密钥
   
    api_key = ""
    
    if not api_key:
        raise ValueError("请设置 OPENAI_API_KEY 环境变量")

    # 初始化生成器
    generator = TestCodeGenerator(api_key=api_key, input="specification", testframe="Jest", model="gpt-5-nano")
    # generator1 = TestCodeGenerator(api_key=api_key, input="specification", testframe="Jest", model="gpt-5-nano")
    # generator2 = TestCodeGenerator(api_key=api_key, input="code", testframe="Jest", model="gpt-5-nano")
    generator3 = TestCodeGenerator(api_key=api_key, input="code", testframe="Jest", model="gpt-5-nano")

    # 加载函数数据
    input_file = "modern-errors_lite_specification.json"  # 替换为您的输入文件路径
    # input_file = "test_output.json"
    with open(input_file, 'r', encoding='utf-8') as f:
        functions_data = json.load(f)

    logger.info(f"找到 {len(functions_data)} 个需要生成测试的函数")

    # 生成测试代码 - 使用并行版本
    output_file = "modern-errors_lite_specification_jest_gpt5nano.json"
    # output_file1 = "tornado_lite_specification_pytest_gpt5nano.json"
    # output_file2= "tornado_lite_pytest_gpt5nano.json"
    output_file3 = "modern-errors_lite_jest_gpt5nano.json"

    # 方法1: 完全并行处理
    # results = generator.generate_tests_for_functions_parallel(
    #     functions=functions_data,
    #     output_file=output_file,
    #     max_workers=5,  # 根据您的API限制调整这个值
    #     save_interval=10
    # )

    # 方法2: 批量并行处理（推荐，可控制速率）
    results = generator.generate_tests_for_functions_parallel_batch(
        functions=functions_data,
        output_file=output_file,
        max_workers=5,
        batch_size=20,
        batch_delay=2
    )

    # results1 = generator1.generate_tests_for_functions_parallel_batch(
    #     functions=functions_data,
    #     output_file=output_file1,
    #     max_workers=5,
    #     batch_size=20,
    #     batch_delay=2
    # )

    # results2 = generator2.generate_tests_for_functions_parallel_batch(
    #     functions=functions_data,
    #     output_file=output_file2,
    #     max_workers=5,
    #     batch_size=20,
    #     batch_delay=2
    # )

    results3 = generator3.generate_tests_for_functions_parallel_batch(
        functions=functions_data,
        output_file=output_file3,
        max_workers=5,
        batch_size=20,
        batch_delay=2
    )
    # 统计结果
    success_count = sum(1 for r in results if r.get('test_generation_status') == 'success')
    logger.info(f"测试生成完成: {success_count}/{len(results)} 成功")


if __name__ == "__main__":
    main()