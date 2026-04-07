# import torch
# from transformers import AutoTokenizer, AutoModelForCausalLM
#
# tokenizer = AutoTokenizer.from_pretrained("deepseek-ai/deepseek-coder-6.7b-instruct", trust_remote_code=True)
# model = AutoModelForCausalLM.from_pretrained("deepseek-ai/deepseek-coder-6.7b-instruct", trust_remote_code=True, torch_dtype=torch.bfloat16).cuda()
# messages=[
#     { 'role': 'user', 'content': "write a quick sort algorithm in python."}
# ]
# inputs = tokenizer.apply_chat_template(messages, add_generation_prompt=True, return_tensors="pt").to(model.device)
# # tokenizer.eos_token_id is the id of <|EOT|> token
# outputs = model.generate(inputs, max_new_tokens=512, do_sample=False, top_k=50, num_return_sequences=1, eos_token_id=tokenizer.eos_token_id)
# print(tokenizer.decode(outputs[0][len(inputs[0]):], skip_special_tokens=True))


import json
import openai
from openai import OpenAI
import os
import re
import time
import threading
from typing import List, Dict, Any
import logging
import glob
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor, as_completed
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 设置CUDA同步调试（如果需要）
os.environ['CUDA_LAUNCH_BLOCKING'] = '0'  # 设为0可以提高性能，设为1便于调试


class SafeParallelGenerator:
    def __init__(self, model_name: str = "deepseek-ai/deepseek-coder-6.7b-instruct"):
        """
        安全的并行生成器，使用单个模型实例但线程安全的生成方法
        """
        self.model_name = model_name

        # 初始化tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            trust_remote_code=True,
            padding_side="left"
        )

        # 确保有pad_token
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
            logger.info(f"Set pad_token to eos_token: {self.tokenizer.eos_token_id}")

        # 初始化模型
        logger.info(f"Loading model {model_name}...")
        try:
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
                trust_remote_code=True,
                torch_dtype=torch.float16,
                device_map="auto",
                low_cpu_mem_usage=True
            )
            self.model.eval()
            logger.info(f"Model loaded on device: {self.model.device}")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

        # 创建线程锁，确保模型生成时的线程安全
        self.generation_lock = threading.Lock()

    def _prepare_inputs(self, messages: List[Dict[str, str]]) -> Dict[str, torch.Tensor]:
        """准备单个输入的tokenized tensors"""
        try:
            # 应用聊天模板
            text = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )

            # Tokenize并添加padding
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=4096,
                pad_to_multiple_of=8
            )

            # 移动到正确的设备
            inputs = {k: v.to(self.model.device) for k, v in inputs.items()}

            return inputs

        except Exception as e:
            logger.error(f"Error preparing inputs: {e}")
            raise

    def _batch_prepare_inputs(self, messages_list: List[List[Dict[str, str]]]) -> Dict[str, torch.Tensor]:
        """批量准备输入"""
        batch_texts = []

        for messages in messages_list:
            try:
                text = self.tokenizer.apply_chat_template(
                    messages,
                    tokenize=False,
                    add_generation_prompt=True
                )
                batch_texts.append(text)
            except Exception as e:
                logger.error(f"Error applying chat template: {e}")
                # 添加安全的默认文本
                batch_texts.append("Write a Python function.")

        # 批量编码
        inputs = self.tokenizer(
            batch_texts,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=4096,
            pad_to_multiple_of=8
        )

        # 移动到正确的设备
        inputs = {k: v.to(self.model.device) for k, v in inputs.items()}

        return inputs

    def generate_single(self, messages: List[Dict[str, str]], max_new_tokens: int = 512) -> str:
        """线程安全的单个生成"""
        with self.generation_lock:  # 使用锁确保线程安全
            try:
                inputs = self._prepare_inputs(messages)

                with torch.no_grad():
                    outputs = self.model.generate(
                        **inputs,
                        max_new_tokens=max_new_tokens,
                        do_sample=False,
                        temperature=0.,
                        top_p=0.95,
                        top_k=50,
                        eos_token_id=self.tokenizer.eos_token_id,
                        pad_token_id=self.tokenizer.pad_token_id,
                        # attention_mask=inputs.get('attention_mask')
                    )

                # 解码输出
                generated_ids = outputs[0, inputs['input_ids'].shape[1]:]
                text = self.tokenizer.decode(generated_ids, skip_special_tokens=True)

                return text.strip()

            except Exception as e:
                logger.error(f"Generation error: {e}")
                return f"Generation failed: {str(e)}"

    def generate_batch(self, messages_list: List[List[Dict[str, str]]], max_new_tokens: int = 512) -> List[str]:
        """线程安全的批量生成"""
        with self.generation_lock:  # 使用锁确保线程安全
            try:
                inputs = self._batch_prepare_inputs(messages_list)

                with torch.no_grad():
                    outputs = self.model.generate(
                        **inputs,
                        max_new_tokens=max_new_tokens,
                        do_sample=False,
                        temperature=0.,
                        top_p=0.95,
                        top_k=50,
                        eos_token_id=self.tokenizer.eos_token_id,
                        pad_token_id=self.tokenizer.pad_token_id,
                        # attention_mask=inputs.get('attention_mask')
                    )

                # 解码所有结果
                results = []
                for i in range(len(messages_list)):
                    generated_ids = outputs[i, inputs['input_ids'].shape[1]:]
                    text = self.tokenizer.decode(generated_ids, skip_special_tokens=True)
                    results.append(text.strip())

                return results

            except Exception as e:
                logger.error(f"Batch generation error: {e}")
                return [f"Generation failed: {str(e)}"] * len(messages_list)


class TestCodeGenerator:
    def __init__(self, api_key: str = None, model: str = "gpt-4o-mini", use_api: bool = True):
        """
        初始化测试代码生成器

        Args:
            api_key: OpenAI API密钥
            model: 使用的模型名称
            use_api: 是否使用API
        """
        self.use_api = use_api

        if use_api:
            self.api_key = api_key
            self.model_name = model
            openai.api_key = api_key
            logger.info(f"Using API model: {model}")
        else:
            # 使用本地模型
            self.model_name = model
            self.generator = SafeParallelGenerator(model_name=model)
            logger.info(f"Using local model: {model}")

    def generate_test_prompt(self, test_framework: str, function_info: Dict[str, Any]) -> str:
        """
        为给定函数生成测试提示

        Args:
            test_framework: 测试框架名称
            function_info: 函数信息字典

        Returns:
            生成的提示字符串
        """
        function_name = function_info['name']
        function_code = function_info['code']
        # signature = function_code.split(':\n')[0]
        signature = function_code.split('{', 1)[0].rstrip()

        match = re.search(r'^def\s+\w+\([^)]*\)(?:\s*->\s*[^:]+)?:', function_code, re.MULTILINE)
        if match:
            signature = match.group(0)

        class_name = None
        class_info = {}
        if function_info['type'] == "method":
            class_name = function_info.get('class_name')
            class_info['class_name'] = class_name
            if function_info.get('class_constructor'):
                class_info['class_constructor'] = function_info['class_constructor']
            if function_info.get('class_fields'):
                class_info['class_fields'] = function_info['class_fields']
            # if function_info.get('class_variables'):
            #     class_info['class_variables'] = function_info['class_variables']

        file_path = function_info['src_file']
        test_path = function_info['test_file']
        specification = function_info['specification']

#         prompt = f"""
# Please generate a test class for the following function.
#
# Function Information:
# - Src file: {file_path}
# - Function name: {function_name}
# - Class: {class_info if class_name else 'Standalone function'}
# - Is async: {function_info.get('is_async', False)}
#
# Function Specification:
# ```python
# {signature}
# ```{specification}```
#
# Requirements:
# Use {test_framework} framework for writing tests.
# Your job is to output corresponding test class that obtains high coverage and invokes the code under test.
# Each test case must be a function starting with test_.
# The test code should be written into {test_path}. Please make sure the imports are correct.
# Return ONLY code without explanations, non-code text, or markdown formatting.
#
# ```python
# <test code>
# """


#         prompt = f"""
# Please generate a test class for the following function.
#
# Function Information:
# - Src file: {file_path}
# - Function name: {function_name}
# - Class: {class_info if class_name else 'Standalone function'}
#
# Function Code:
# ```python
# {function_code}
#
# Requirements:
# Use {test_framework} framework for writing tests.
# Your job is to output corresponding test class that obtains high coverage and invokes the code under test.
# The test code should be written into {test_path}. Please make sure the imports are correct.
# Return ONLY code without explanations, non-code text, or markdown formatting.
#
# ```python
# <test code>
# """
        prompt = f"""
Please generate a test class for the following function.

Function Information:
- Src file: {file_path}
- Function name: {function_name}
- Class: {class_info if class_name else 'Standalone function'}

Function Specification:
```java
{signature}
```{specification}```

Requirements:
Java version: Java 8
Use {test_framework} framework for writing tests.
Your job is to output corresponding test class that obtains high coverage and invokes the code under test.
Each test case must be a function starting with test_.
The test code should be written into {test_path}. Please make sure the imports are correct.
Return ONLY code without explanations, non-code text, or markdown formatting.

```java
<test code>
"""
#         prompt = f"""
# Please generate a test class for the following function.
#
# Function Information:
# - Src file: {file_path}
# - Function name: {function_name}
# - Class: {class_info if class_name else 'Standalone function'}
#
# Function Code:
# ```java
# {function_code}
#
# Requirements:
# Java version: Java 8
# Use {test_framework} framework for writing tests.
# Your job is to output corresponding test class that obtains high coverage and invokes the code under test.
# The test code should be written into {test_path}. Please make sure the imports are correct.
# Return ONLY code without explanations, non-code text, or markdown formatting.
#
# ```java
# <test code>
# """
        return prompt

    def create_messages(self, prompt: str) -> List[Dict[str, str]]:
        """创建消息格式"""
        return [
            {"role": "system",
             "content": "You are a professional test engineer specializing in writing high-quality unit test code."},
            {"role": "user", "content": prompt}
        ]

    def call_llm(self, prompt: str, max_K: int = 1) -> List[str]:
        """
        调用大模型生成测试代码

        Args:
            prompt: 提示文本
            max_K: 最多生成测试用例数量

        Returns:
            生成的测试代码列表
        """
        tests = []

        if self.use_api:
            # API调用
            message = self.create_messages(prompt)

            for k in range(max_K):
                try:
                    client = OpenAI(
                        api_key=self.api_key,
                        base_url="https://api.agicto.cn/v1"
                    )
                    response = client.chat.completions.create(
                        model=self.model_name,
                        messages=message,
                        temperature=0.2,
                        max_tokens=4096
                    )

                    if response.choices and len(response.choices) > 0:
                        message_content = response.choices[0].message.content
                        if message_content:
                            test = self._extract_code(message_content)
                            tests.append(test)
                            # 添加历史对话以便生成更多测试
                            message.append({"role": "assistant", "content": test})
                            message.append({"role": "user",
                                            "content": "Generate another test method for the function under test. Your answer must be different from previously-generated test cases and should cover different statements and branches."})

                except Exception as e:
                    logger.error(f"API call error (attempt {k + 1}/{max_K}): {e}")
                    if k >= max_K - 1:  # 最后一次尝试失败
                        raise
                    time.sleep(2 ** k)  # 指数退避
        else:
            # 本地模型调用
            try:
                messages = self.create_messages(prompt)
                generated_text = self.generator.generate_single(messages, max_new_tokens=4096)

                if generated_text:
                    # print(generated_text)
                    test = self._extract_code(generated_text)
                    tests.append(test)

                    # 如果需要生成更多测试用例
                    # for k in range(1, max_K):
                    #     # 添加历史对话
                    #     follow_up_messages = messages + [
                    #         {"role": "assistant", "content": test},
                    #         {"role": "user",
                    #          "content": "Generate another test method for the function under test. Your answer must be different from previously-generated test cases and should cover different statements and branches."}
                    #     ]
                    #
                    #     follow_up_text = self.generator.generate_single(follow_up_messages, max_new_tokens=512)
                    #     if follow_up_text and "Generation failed" not in follow_up_text:
                    #         follow_up_test = self._extract_code(follow_up_text)
                    #         tests.append(follow_up_test)
                    #         test = follow_up_test  # 更新最后一个测试用例

            except Exception as e:
                logger.error(f"Local model generation error: {e}")
                raise

        return tests if tests else [""]

    def generate_test_for_function(self, function_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        为单个函数生成测试代码

        Args:
            function_info: 函数信息

        Returns:
            包含测试代码的增强函数信息
        """
        function_name = function_info['name']
        logger.info(f"为函数 {function_name} 生成测试代码...")

        try:
            prompt = self.generate_test_prompt("JUnit 5", function_info)
            tests = self.call_llm(prompt, max_K=1)  # 默认生成1个测试用例

            result = function_info.copy()
            result['generated_tests'] = tests
            result['test_generation_status'] = 'success'
            # result['generated_at'] = time.strftime('%Y-%m-%d %H:%M:%S')

            logger.info(f"成功为 {function_name} 生成测试代码")

        except Exception as e:
            logger.error(f"为 {function_name} 生成测试代码失败: {e}")
            result = function_info.copy()
            result['generated_tests'] = []
            result['test_generation_status'] = f'failed: {str(e)}'
            # result['generated_at'] = time.strftime('%Y-%m-%d %H:%M:%S')

        return result

    def generate_tests_batch_parallel(self,
                                      functions: List[Dict[str, Any]],
                                      output_file: str = None,
                                      max_workers: int = 4,
                                      batch_size: int = 10,
                                      batch_delay: int = 1) -> List[Dict[str, Any]]:
        """
        批量并行生成测试代码（优化版本）

        Args:
            functions: 函数信息列表
            output_file: 输出文件路径
            max_workers: 最大工作线程数
            batch_size: 每批次处理数量
            batch_delay: 批次间延迟（秒）

        Returns:
            包含测试代码的函数列表
        """
        results = []
        total_functions = len(functions)

        # 创建输出目录（如果不存在）
        if output_file:
            output_dir = os.path.dirname(output_file)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)

        # 处理所有批次
        for batch_start in range(0, total_functions, batch_size):
            batch_end = min(batch_start + batch_size, total_functions)
            batch_functions = functions[batch_start:batch_end]
            batch_num = batch_start // batch_size + 1
            total_batches = (total_functions + batch_size - 1) // batch_size

            logger.info(f"处理批次 {batch_num}/{total_batches}: 函数 {batch_start + 1} 到 {batch_end}")

            batch_results = []

            # 使用线程池处理当前批次
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # 提交所有任务
                future_to_func = {
                    executor.submit(self.generate_test_for_function, func): func
                    for func in batch_functions
                }

                # 收集结果
                for future in as_completed(future_to_func):
                    func = future_to_func[future]
                    try:
                        result = future.result(timeout=120)  # 2分钟超时
                        batch_results.append(result)
                        results.append(result)

                        # 立即保存到JSONL文件
                        if output_file:
                            self._append_result_to_jsonl(result, f"{output_file}.jsonl")

                    except concurrent.futures.TimeoutError:
                        logger.error(f"处理函数 {func['name']} 超时")
                        error_result = func.copy()
                        error_result['generated_tests'] = []
                        error_result['test_generation_status'] = 'failed: timeout'
                        # error_result['generated_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
                        batch_results.append(error_result)
                        results.append(error_result)

                        if output_file:
                            self._append_result_to_jsonl(error_result, f"{output_file}.jsonl")

                    except Exception as e:
                        logger.error(f"处理函数 {func['name']} 时发生错误: {e}")
                        error_result = func.copy()
                        error_result['generated_tests'] = []
                        error_result['test_generation_status'] = f'failed: {str(e)}'
                        # error_result['generated_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
                        batch_results.append(error_result)
                        results.append(error_result)

                        if output_file:
                            self._append_result_to_jsonl(error_result, f"{output_file}.jsonl")

            logger.info(f"批次 {batch_num} 完成: {len(batch_results)}/{len(batch_functions)} 成功")

            # 定期保存完整JSON
            if output_file and batch_end % (batch_size * 5) == 0:
                self.save_results(results, f"{output_file}.partial_{batch_end}.json")

            # 批次间延迟（避免过热）
            if batch_end < total_functions and batch_delay > 0:
                logger.info(f"等待 {batch_delay} 秒后处理下一批...")
                time.sleep(batch_delay)

        # 保存最终结果
        if output_file:
            self.save_results(results, output_file)
            logger.info(f"最终结果已保存到: {output_file}")

            # 将JSONL转换为完整JSON
            jsonl_file = f"{output_file}.jsonl"
            if os.path.exists(jsonl_file):
                self._convert_jsonl_to_json(jsonl_file, f"{output_file}.from_jsonl.json")
                # 可选：删除JSONL文件
                os.remove(jsonl_file)

        return results

    # def generate_tests_batch_parallel(self,
    #                                   functions: List[Dict[str, Any]],
    #                                   output_file: str = None,
    #                                   max_workers: int = 4,
    #                                   batch_size: int = 10,
    #                                   batch_delay: int = 1) -> List[Dict[str, Any]]:
    #     """
    #     批量顺序生成测试代码（原并行版本已改为完全顺序处理）
    #
    #     Args:
    #         functions: 函数信息列表
    #         output_file: 输出文件路径
    #         max_workers: 保留参数（不再使用，仅保持接口兼容）
    #         batch_size: 每批次处理数量
    #         batch_delay: 批次间延迟（秒）
    #
    #     Returns:
    #         包含测试代码的函数列表
    #     """
    #     results = []
    #     total_functions = len(functions)
    #
    #     # 创建输出目录（如果不存在）
    #     if output_file:
    #         output_dir = os.path.dirname(output_file)
    #         if output_dir and not os.path.exists(output_dir):
    #             os.makedirs(output_dir)
    #
    #     # 按批次顺序处理所有函数
    #     for batch_start in range(0, total_functions, batch_size):
    #         batch_end = min(batch_start + batch_size, total_functions)
    #         batch_functions = functions[batch_start:batch_end]
    #         batch_num = batch_start // batch_size + 1
    #         total_batches = (total_functions + batch_size - 1) // batch_size
    #
    #         logger.info(f"处理批次 {batch_num}/{total_batches}: 函数 {batch_start + 1} 到 {batch_end}")
    #
    #         batch_results = []
    #
    #         # 顺序处理当前批次中的每个函数
    #         for func in batch_functions:
    #             try:
    #                 # 直接调用测试生成函数（原为线程池提交）
    #                 result = self.generate_test_for_function(func)
    #                 batch_results.append(result)
    #                 results.append(result)
    #
    #                 # 立即保存到JSONL文件
    #                 if output_file:
    #                     self._append_result_to_jsonl(result, f"{output_file}.jsonl")
    #
    #             except Exception as e:
    #                 logger.error(f"处理函数 {func['name']} 时发生错误: {e}")
    #                 error_result = func.copy()
    #                 error_result['generated_tests'] = []
    #                 error_result['test_generation_status'] = f'failed: {str(e)}'
    #                 batch_results.append(error_result)
    #                 results.append(error_result)
    #
    #                 if output_file:
    #                     self._append_result_to_jsonl(error_result, f"{output_file}.jsonl")
    #
    #         logger.info(f"批次 {batch_num} 完成: {len(batch_results)}/{len(batch_functions)} 成功")
    #
    #         # 定期保存完整JSON
    #         if output_file and batch_end % (batch_size * 5) == 0:
    #             self.save_results(results, f"{output_file}.partial_{batch_end}.json")
    #
    #         # 批次间延迟（避免过热）
    #         if batch_end < total_functions and batch_delay > 0:
    #             logger.info(f"等待 {batch_delay} 秒后处理下一批...")
    #             time.sleep(batch_delay)
    #
    #     # 保存最终结果
    #     if output_file:
    #         self.save_results(results, output_file)
    #         logger.info(f"最终结果已保存到: {output_file}")
    #
    #         # 将JSONL转换为完整JSON
    #         jsonl_file = f"{output_file}.jsonl"
    #         if os.path.exists(jsonl_file):
    #             self._convert_jsonl_to_json(jsonl_file, f"{output_file}.from_jsonl.json")
    #             # 可选：删除JSONL文件
    #             os.remove(jsonl_file)
    #
    #     return results

    def _append_result_to_jsonl(self, result: Dict[str, Any], jsonl_file: str):
        """追加单行结果到JSONL文件"""
        try:
            with open(jsonl_file, 'a', encoding='utf-8') as f:
                json_line = json.dumps(result, ensure_ascii=False)
                f.write(json_line + '\n')
        except Exception as e:
            logger.error(f"写入JSONL文件失败: {e}")

    def _convert_jsonl_to_json(self, jsonl_file: str, json_file: str):
        """将JSONL文件转换为标准JSON"""
        try:
            results = []
            with open(jsonl_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        results.append(json.loads(line))

            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)

            logger.info(f"已从JSONL转换到JSON: {json_file}")
        except Exception as e:
            logger.error(f"转换JSONL文件失败: {e}")

    # def _extract_code(self, s: str) -> str:
        """从响应中提取代码块"""
        # 查找 ```python 代码块
        # python_pattern = r'```python\s*(.*?)\s*```'
        # matches = re.findall(python_pattern, s, re.DOTALL)
        #
        # if matches:
        #     return matches[0].strip()
        #
        # # 查找普通的 ``` 代码块
        # generic_pattern = r'```\s*(.*?)\s*```'
        # matches = re.findall(generic_pattern, s, re.DOTALL)
        #
        # if matches:
        #     return matches[0].strip()
        #
        # # 如果没有代码块标记，返回原始文本
        # return s.strip()

    def _extract_code(self, s: str):
        # 使用 '```python' 和 '```' 来分割字符串
        parts = s.split('```java')
        if len(parts) > 1:
            # 移除后面的 '```'
            code = parts[1].split('```')[0]
            return code.strip("\n").strip()
        return s.split('```')[0].strip("\n").strip()

    def save_results(self, results: List[Dict[str, Any]], output_file: str):
        """保存结果到JSON文件"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            logger.info(f"结果已保存到: {output_file}")
        except Exception as e:
            logger.error(f"保存结果失败: {e}")


def main():
    """主函数"""
    # 配置参数
    USE_API = False  # 是否使用API，False表示使用本地模型
    MODEL_NAME = "codellama/CodeLlama-7b-Instruct-hf"  # 本地模型名称
    # MODEL_NAME = "deepseek-ai/deepseek-coder-6.7b-instruct"

    if USE_API:
        # API配置
        api_key = "sk-WhZar4Km8tqMhzsRhzHn5oIvd6yzP7TZrMMGzkcgF4CDiTRJ"
        if not api_key:
            raise ValueError("请设置 API_KEY")

        generator = TestCodeGenerator(
            api_key=api_key,
            model="gpt-4o-mini",
            use_api=True
        )
    else:
        # 本地模型配置
        generator = TestCodeGenerator(
            model=MODEL_NAME,
            use_api=False
        )

    # 加载函数数据
    input_file = "commons-jxpath.json"
    # input_file = "missing_items.json"
    logger.info(f"加载数据文件: {input_file}")

    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            functions_data = json.load(f)
        logger.info(f"找到 {len(functions_data)} 个需要生成测试的函数")
    except Exception as e:
        logger.error(f"加载数据文件失败: {e}")
        return

    # 生成测试代码
    output_file = "commons-jxpath_lite_specification_junit5_CodeLlama-7b.json"

    results = generator.generate_tests_batch_parallel(
        functions=functions_data,
        output_file=output_file,
        max_workers=4,  # 根据GPU内存调整
        batch_size=8,  # 每批次处理数量
        batch_delay=1  # 批次间延迟
    )

    # 统计结果
    success_count = sum(1 for r in results if r.get('test_generation_status') == 'success')
    failed_count = sum(1 for r in results if r.get('test_generation_status', '').startswith('failed'))

    logger.info(f"测试生成完成:")
    logger.info(f"  成功: {success_count}/{len(results)}")
    logger.info(f"  失败: {failed_count}/{len(results)}")

    # 显示一些失败的例子
    if failed_count > 0:
        logger.info("失败的函数:")
        for r in results:
            if r.get('test_generation_status', '').startswith('failed'):
                logger.info(f"  - {r['name']}: {r['test_generation_status']}")


if __name__ == "__main__":
    main()