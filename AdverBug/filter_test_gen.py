"""
过滤阶段的测试生成器。

与评测协议严格同源：直接复用评测管线 gen_test/llm_gentests.py 的
TestCodeGenerator（specification 模式模板、temperature=0、max_tokens=16384、
max_K=3 重试），输入为"错误代码 + 规范"——与被评测模型看到的信息完全一致，
过滤准则即"在评测协议下该模型未检出此 bug"。

容器内由 eval_java_adver.py 将 gen_test/llm_gentests.py 挂载到 /testbed 下。
"""
import logging

from openai import OpenAI

from llm_config import LLMConfig

try:
    from test_gen import TestGenerationAgent
except ImportError:  # 本地开发目录无 llm_gentests，容器内由挂载提供
    TestGenerationAgent = None

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = "You are a professional test engineer specializing in writing high-quality unit test code."


class FilterTestGenerationAgent:
    def __init__(self, llm_config: LLMConfig, suite_retries: int = 2):
        if TestGenerationAgent is None:
            raise ImportError(
                "test_gen.py 未找到：请将 gen_test/test_gen.py 挂载到 /testbed 下"
                "（eval_java_adver.py 已包含该挂载）"
            )
        self.llm_config = llm_config
        self.model_name = llm_config.MODEL_NAME
        self.suite_retries = suite_retries
        # specification 模式 + JUnit 4，与评测管线 main() 中的配置一致
        self.generator = TestGenerationAgent(
            llm_config=llm_config
        )
        self.client = OpenAI(api_key=llm_config.API_KEY, base_url=llm_config.API_ENDPOINT)

    @staticmethod
    def _function_info(entry, bug_code):
        """构造评测同款输入：generate_test_prompt 会取 buggy_code[-1] 放入 prompt。"""
        return {
            "name": entry.get("name", ""),
            "buggy_code": [bug_code],
            "code": entry.get("code", ""),
            "import": entry.get("import", ""),
            "type": entry.get("type", "method"),
            "class_name": entry.get("class_name", None),
            "class_constructor": entry.get("class_constructor", []),
            "class_fields": entry.get("class_fields", []),
            "specification": entry.get("specification", ""),
            "src_file": entry.get("src_file", ""),
            "test_file": entry.get("test_file", ""),
            "is_async": entry.get("is_async", False),
        }

    def generate_tests(self, entry, bug_code):
        """按评测协议为当前 bug 生成一套测试，失败返回空字符串。"""
        try:
            tests = self.generator.init_test_prompt(
                bug_code, entry)
            # tests = self.generator.call_llm(prompt)
        except Exception as e:
            logger.error(f"[{self.model_name}] 测试生成失败: {e}")
            return ""
        # if tests and tests[0].strip():
        #     return tests[0].strip()
        return tests.strip()

    def _call(self, system, user, temperature=0.):
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "system", "content": system},
                          {"role": "user", "content": user}],
                temperature=0.,
                max_tokens=16384,
            )
            content = response.choices[0].message.content.strip()
            return content.split("```java")[-1].split("```")[0].strip()
        except Exception as e:
            logger.error(f"[{self.model_name}] LLM 调用失败: {e}")
            return ""

    def fix_compile(self, tests, error):
        """修复编译错误（复制自 test_gen.fix_test_prompt 的语义）。"""
        prompt = f"""The test code below fails to compile with the following error:
        Tests:
        ```java
        {tests}
        ```

        Error:
        ```
        {error}
        ```

        Please provide a corrected version of the test code that compiles.
        ```java
        <corrected test code>
        ```
        """
        print(f"修复编译错误, {prompt}")
        return self._call("You are a helpful assistant that fixes failing test code.", prompt)

    def repair_tests(self, tests, failure_output):
        """修复执行错误、编译错误或误报（failure_output 中说明具体问题）。"""
        prompt = f"""The test code below has the following problems:
        Tests:
        ```java
        {tests}
        ```

        Error:
        ```
        {failure_output}
        ```

        Please provide a corrected version of the test code that compiles and passes on the correct implementation.
        ```java
        <corrected test code>
        ```
        """
        print(f"修复测试, {prompt}")
        return self._call("You are a helpful assistant that fixes failing test code.", prompt)
        
