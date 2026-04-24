import openai
from openai import OpenAI
import json
import os

def analyze_error(error_message, test_code_snippet):
    system_prompt = """
你是一位软件测试专家，擅长分析自动化测试生成过程中出现的错误。请根据提供的错误信息和相关代码上下文，推断错误的**语义含义**，并用一个简短的短语概括错误的**核心类别**。

## 输入格式

你将收到以下信息：
- **错误信息**：编译器、解释器或测试框架输出的原始错误文本。
- **测试代码片段**：触发该错误的测试代码片段。

## 输出格式

请严格按照以下 JSON 格式输出，不要添加任何额外的解释文字：

{
  "error_summary": "用一句话描述错误的具体表现",
  "semantic_category": "用简短的短语概括错误的语义类别（见参考列表）",
  "reasoning": "简要说明归类依据，引用错误信息中的关键词"
}

## 语义类别参考

请从以下类别中选择最匹配的一项作为 `semantic_category`。如果都不匹配，可以创建新的类别，但尽量控制在 20 字以内。

- 导入的模块或符号不存在
- 模块路径正确但符号不存在
- 实例化被测类时遗漏必需参数
- 使用未定义的变量或函数
- 传入参数的类型与函数签名不匹配
- 传入参数的数量不正确
- 访问了对象上不存在的属性或方法
- Mock对象的接口与被替代对象不一致
- 对返回值的类型做出了错误假设
- 对返回值的具体数值预期错误
- 断言条件永远成立，无法检测错误
- 测试框架的注解或装饰器使用错误
- 测试代码命名不符合测试框架规范
- 断言方法使用错误
- 未正确捕获或断言预期的异常


## 示例

### 示例 1

输入：
- 错误信息：`TypeError: BaseAsyncIOLoop.initialize() missing 1 required positional argument: 'asyncio_loop'`
- 测试代码片段：`loop = BaseAsyncIOLoop()`

输出：
{
  "error_summary": "调用 BaseAsyncIOLoop 时未传入必需的 asyncio_loop 参数",
  "semantic_category": "实例化被测类时遗漏必需参数",
  "reasoning": "错误信息明确指出缺少必需的位置参数 'asyncio_loop'"
}

### 示例 2

输入：
- 错误信息：`ImportError: cannot import name 'UndocumentedNodes' from 'pylint.utils.utils'`
- 测试代码片段：`from pylint.utils.utils import UndocumentedNodes`

输出：
{
  "error_summary": "从 pylint.utils.utils 模块导入不存在的 UndocumentedNodes 类",
  "semantic_category": "模块路径正确但符号不存在",
  "reasoning": "导入路径 pylint.utils.utils 存在，但 UndocumentedNodes 符号未定义"
}

### 示例 3

输入：
- 错误信息：
assert False

where False = isinstance(10, float)

text
- 测试代码片段：`assert isinstance(result, float)`

输出：
{
  "error_summary": "断言失败，期望 result 为 float 类型，但实际是 int 类型",
  "semantic_category": "对返回值的类型做出了错误假设",
  "reasoning": "isinstance 检查返回 False，表明实际类型与断言预期不符"
}
"""

    user_prompt = f"""
## 现在请分析以下输入

- 错误信息：
{error_message}

- 测试代码片段：
{test_code_snippet}
"""
    message = [{"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
    client = OpenAI(api_key="", 
                    base_url="")
    # print(self.model)
    for k in range(3):
        try:
            response = client.chat.completions.create(
                model="gpt-5-nano",
                messages=message,
                temperature=1.,
                max_tokens=2048
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error during OpenAI API call: {e}")
            if k < 2:
                print(f"Retrying... ({k + 1}/3)")
            else:
                print("Max retries reached. Returning error message.")
                return json.dumps({
                    "error_summary": "API调用失败",
                    "semantic_category": "API调用错误",
                    "reasoning": str(e)
                })


for root, dirs, files in os.walk("tests/test_gen/python/fix_flask"):
    error_analysis_results = []
    for file in files:
        if "repaired" in file:
            with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                data = json.load(f)

            item = data['items']
            for i in item:
                repaired_history = i.get("repair_history", [])
                if repaired_history:
                    for history in repaired_history:
                        if history.get("stage") == "run":
                            error_message = history.get("feedback", "")
                            test_code_snippet = history.get("test_code", "")
                            analysis_result = analyze_error(error_message, test_code_snippet)
                            error_analysis_results.append({
                                "error_message": error_message,
                                "test_code_snippet": test_code_snippet,
                                "analysis_result": analysis_result
                            })

with open("runtime_error_analysis_results.json", "w", encoding="utf-8") as f:
    json.dump(error_analysis_results, f, ensure_ascii=False, indent=2)
                            

                            