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
    from llm_gentests import TestCodeGenerator
except ImportError:  # 本地开发目录无 llm_gentests，容器内由挂载提供
    TestCodeGenerator = None

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = "You are a professional test engineer specializing in writing high-quality unit test code."


class FilterTestGenerationAgent:
    def __init__(self, llm_config: LLMConfig, suite_retries: int = 2):
        if TestCodeGenerator is None:
            raise ImportError(
                "llm_gentests.py 未找到：请将 gen_test/llm_gentests.py 挂载到 /testbed 下"
                "（eval_java_adver.py 已包含该挂载）"
            )
        self.llm_config = llm_config
        self.model_name = llm_config.MODEL_NAME
        self.suite_retries = suite_retries
        # specification 模式 + JUnit 4，与评测管线 main() 中的配置一致
        self.generator = TestCodeGenerator(
            api_key=llm_config.API_KEY,
            input="specification",
            testframe="JUnit 4",
            model=llm_config.MODEL_NAME,
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
            prompt = self.generator.generate_test_prompt(
                "JUnit 4", self._function_info(entry, bug_code))
            tests = self.generator.call_llm(prompt)
        except Exception as e:
            logger.error(f"[{self.model_name}] 测试生成失败: {e}")
            return ""
        if tests and tests[0].strip():
            return tests[0].strip()
        return ""

    def _call(self, system, user, temperature=0.5):
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "system", "content": system},
                          {"role": "user", "content": user}],
                temperature=temperature,
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
        return self._call("You are a helpful assistant that fixes failing test code.", prompt)

    def repair_tests(self, tests, failure_output):
        """套件在正确实现上失败（误报）时，修复测试期望值。

        注意：只修复"正确实现应通过"的期望，不削弱对规范的覆盖
        （覆盖不足属于可选增强的 JaCoCo 检查范畴）。
        """
        prompt = f"""The test suite below was designed against a specification, but some of its test cases FAIL even against a CORRECT implementation of the specification (false positives caused by wrong expectations).

        Failing test run output:
        ```
        {failure_output}
        ```

        Tests:
        ```java
        {tests}
        ```

        Please fix the test suite so that:
        - A correct implementation (following the specification) passes ALL tests.
        - The tests still thoroughly cover the specification (boundary conditions, invalid inputs, error handling, etc.), so that an incorrect implementation would still fail.
        - Keep the same test class name and file layout.
        ```java
        <corrected test code>
        ```
        """
        return self._call(SYSTEM_PROMPT, prompt)
