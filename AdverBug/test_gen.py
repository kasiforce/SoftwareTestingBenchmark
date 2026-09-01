import os
import openai
from openai import OpenAI
from llm_config import LLMConfig
import logging
import re

logger = logging.getLogger(__name__)

class TestGenerationAgent:
    def __init__(self, llm_config: LLMConfig):
        self.llm_config = llm_config
        self.client = OpenAI(api_key=self.llm_config.API_KEY, base_url=self.llm_config.API_ENDPOINT)
        self.model = self.llm_config.MODEL_NAME

    def init_test_prompt(self, erroneous_code: str, function_info: dict) -> str:
        system_prompt = """You are a professional test engineer specializing in writing high-quality unit test code"""

        function_name = function_info['name']
        function_code = function_info['code']
        imports = function_info.get('import', '')
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

#         user_prompt = f"""
# Please generate a test class for the following function.

# Function Information:
# - Src file: {file_path}
# - Function name: {function_name}
# - Class: {class_info if class_name else 'Standalone function'}
# - Is async: {function_info.get('is_async', False)}

# Function Code:
# ```java
# {erroneous_code}
# ```

# Requirements:
# Use JUnit 4 framework for writing tests.
# Your job is to output a corresponding test class that focuses on detecting errors and unexpected behaviors in the code under test.
# The test code should be written into {test_path}. Please make sure the imports are correct.
# Return ONLY code without explanations, non-code text, or markdown formatting.

# ```java
# <test code>
# ```
# """   
#         user_prompt = f"""
# Your task is to design tests that ensure only correct implementations (following the specification) pass, while incorrect implementations would fail.
# You are given the following information:
# - Code under test
# - Specification

# Your tasks:
# 1. Infer the **intended behavior** from the specification.
# 2. Design a set of **test cases** that cover:
# - Basic functionality with valid inputs and expected outputs.
# - Boundary conditions and edge cases.
# - Invalid inputs and error handling.
# - Potential issues with dependency interactions.
# 3. Write executable test code using Java 8 and JUnit 4.
# 4. The test code should be written into {test_path}. Please make sure the imports are correct.
# 5. Ensure tests are designed to differentiate between correct and incorrect implementations:
# - At least one test should be able to expose an incorrect implementation if it does not fully follow the behavior of the specification.
# - A correct implementation should pass all tests.

# ## Input Method ({function_name}):
# ```java
# {erroneous_code}
# ```

# ## Method Context:
# - Src file: {file_path}
# - Class: {class_info if class_name else 'Standalone function'}
# - Is async: {function_info.get('is_async', False)}

# ## Specification:
# {specification}


# ### Output Format ###:
# Return ONLY code without explanations, non-code text, or markdown formatting.
# ```java
# <test code>
# ```
# """
#         
        user_prompt = f"""
Your task is to design tests that ensure only correct implementations (following the specification) pass, while incorrect implementations would fail.
You are given the following information:
- Code under test
- Specification

Your tasks:
1. Infer the **intended behavior** from the specification.
2. Design a set of **test cases** that cover:
- Basic functionality with valid inputs and expected outputs.
- Boundary conditions and edge cases.
- Invalid inputs and error handling.
- Potential issues with dependency interactions.
3. Write executable test code using Java 8 and JUnit 4.
4. The test code should be written into {test_path}. Please make sure the imports are correct.
5. Ensure tests are designed to differentiate between correct and incorrect implementations:
- At least one test should be able to expose an incorrect implementation if the code were incorrect.
- A correct implementation should pass all tests.

## Input Method ({function_name}):
```java
{erroneous_code}
```

## Method Context:
- Src file: {file_path}
- Imports: {imports}
- Class: {class_info if class_name else 'Standalone function'}
- Is async: {function_info.get('is_async', False)}

## Specification:
{specification}

### Output Format ###:
Return ONLY code without explanations, non-code text, or markdown formatting.
```java
<test code>
```
"""

        message = [{"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                    ]
        # return message
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=message,
                temperature=0.7, # Higher temperature for more creative tests
                max_tokens=16384
            )
            test_code = response.choices[0].message.content.strip()
            # Ensure we only get Java code block if LLM adds markdown
            test_code = test_code.split("```java")[-1].split("```")[0].strip()
            # if test_code.startswith("```java") and test_code.endswith("```"):
            #     test_code = test_code[len("```java"):-len("```")].strip()
            return test_code
        except Exception as e:
            logger.error(f"Error calling LLM for test generation: {e}")
            return "" # Return empty string on error


    def enhance_test_prompt(self, erroneous_code: str, function_info: dict, test: str) -> str:
        system_prompt = """You are a professional test engineer specializing in writing high-quality unit test code"""

        function_name = function_info['name']
        function_code = function_info['code']
        imports = function_info.get('import', '')
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

#         user_prompt = f"""
# Please generate a test class for the following function.

# Function Information:
# - Src file: {file_path}
# - Function name: {function_name}
# - Class: {class_info if class_name else 'Standalone function'}
# - Is async: {function_info.get('is_async', False)}

# Function Code:
# ```java
# {erroneous_code}
# ```

# Existing Test Code:
# ```java
# {test}
# ```

# Requirements:
# Use JUnit 4 framework for writing tests.
# Your job is to output a corresponding test class that focuses on detecting errors and unexpected behaviors in the code under test.
# The testcases must be different from the existing test code.
# The test code should be written into {test_path}. Please make sure the imports are correct.
# Return ONLY code without explanations, non-code text, or markdown formatting.

# ```java
# <test code>
# ```
# """

#         user_prompt = f"""
# Your task is to design tests that ensure only correct implementations (following the specification) pass, while incorrect implementations would fail.
# You are given the following information:
# - Code under test
# - Specification
# - Existing Test Code

# Your tasks:
# 1. Infer the **intended behavior** from the specification.
# 2. Design a set of **test cases** that cover:
# - Basic functionality with valid inputs and expected outputs.
# - Boundary conditions and edge cases.
# - Invalid inputs and error handling.
# - Potential issues with dependency interactions.
# 3. Write executable test code using Java 8 and JUnit 4.
# 4. The test code should be written into {test_path}. Please make sure the imports are correct.
# 5. Ensure tests are designed to differentiate between correct and incorrect implementations:
# - At least one test should be able to expose an incorrect implementation if it does not fully follow the behavior of the specification.
# - A correct implementation should pass all tests.
# 6. The generated test cases must be different from the existing test code.

# ## Input Method ({function_name}):
# ```java
# {erroneous_code}
# ```

# ## Method Context:
# - Src file: {file_path}
# - Class: {class_info if class_name else 'Standalone function'}
# - Is async: {function_info.get('is_async', False)}

# ## Specification:
# {specification}

# ## Existing Test Code:
# ```java
# {test}
# ```

# ### Output Format ###:
# Return ONLY code without explanations, non-code text, or markdown formatting.
# ```java
# <test code>
# ```
# """

        user_prompt = f"""
Your task is to design tests that ensure only correct implementations pass, while incorrect implementations would fail.


Your tasks:
1. Design a set of **test cases** that cover:
- Basic functionality with valid inputs and expected outputs.
- Boundary conditions and edge cases.
- Invalid inputs and error handling.
- Potential issues with dependency interactions.
2. Write executable test code using Java 8 and JUnit 4.
3. The test code should be written into {test_path}. Please make sure the imports are correct.
4. Ensure tests are designed to differentiate between correct and incorrect implementations:
- At least one test should be able to expose an incorrect implementation if the code were incorrect.
- A correct implementation should pass all tests.
5. The generated test cases must be different from the existing test code.

## Input Method ({function_name}):
```java
{erroneous_code}
```

## Method Context:
- Src file: {file_path}
- Imports: {imports}
- Class: {class_info if class_name else 'Standalone function'}
- Is async: {function_info.get('is_async', False)}

## Existing Test Code:
```java
{test}
```

### Output Format ###:
Return ONLY code without explanations, non-code text, or markdown formatting.
```java
<test code>
```
"""

        message = [{"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                    ]
        # return message
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=message,
                temperature=0.7, # Higher temperature for more creative tests
                max_tokens=16384
            )
            test_code = response.choices[0].message.content.strip()
            # Ensure we only get Java code block if LLM adds markdown
            test_code = test_code.split("```java")[-1].split("```")[0].strip()
            # if test_code.startswith("```java") and test_code.endswith("```"):
            #     test_code = test_code[len("```java"):-len("```")].strip()
            return test_code
        except Exception as e:
            logger.error(f"Error calling LLM for test generation: {e}")
            return "" # Return empty string on error

    def fix_test_prompt(self, test: str, error: str) -> str:
        prompt = f"""The tests below are failing with the following error message:
        Tests:
        ```java
        {test}
        ```

        Error:
        ```
        {error}
        ```

        Please provide a corrected version of the test code that addresses the error.
        ```java
        <corrected test code>
        ```
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": "You are a helpful assistant that fixes failing test code."},
                          {"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=16384
            )
            fixed_test_code = response.choices[0].message.content.strip()
            # Ensure we only get Java code block if LLM adds markdown
            fixed_test_code = fixed_test_code.split("```java")[-1].split("```")[0].strip()
            return fixed_test_code
        except Exception as e:
            logger.error(f"Error calling LLM for test fixing: {e}")
            return test # Return original test code on error

    


if __name__ == "__main__":
    # Example usage (will require actual API key and endpoint)
    llm_config_instance = LLMConfig(api_key=os.getenv("LLM_API_KEY", "YOUR_LLM_API_KEY"),
                                    api_endpoint=os.getenv("LLM_API_ENDPOINT", "https://api.apiyi.com/v1"),
                                    model_name=os.getenv("LLM_MODEL_NAME", "gpt-4o-mini"))

    agent = TestGenerationAgent(llm_config=llm_config_instance)
    sample_original_code = """
def add(a, b):
    return a + b
"""
    sample_buggy_code = """
def add(a, b):
    return a - b # Bug: should be a + b
"""
    print("原始代码:\n", sample_original_code)
    print("错误代码:\n", sample_buggy_code)

    # To run this, you'll need to set LLM_API_KEY environment variable
    # generated_tests = agent.generate_tests(sample_original_code, sample_buggy_code)
    # if generated_tests:
    #     print("\n生成的测试:\n", generated_tests[0])
    #     agent.integrate_with_execution_environment(generated_tests, {"test_output_dir": "./output_tests"})

    agent.integrate_with_execution_environment([], {"test_output_dir": "./output_tests"}) # Example to create dir
