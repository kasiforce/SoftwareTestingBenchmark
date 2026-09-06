import os
import json
import openai
from openai import OpenAI
from llm_config import LLMConfig
import logging

logger = logging.getLogger(__name__)

class BugGenerationAgent:
    def __init__(self, llm_config: LLMConfig):
        self.llm_config = llm_config
        self.client = OpenAI(api_key=self.llm_config.API_KEY, base_url=self.llm_config.API_ENDPOINT)
        self.model = self.llm_config.MODEL_NAME

    def init_bug_prompt(self, code, tests_context=None):
        system_prompt = """You are a talented Java programmer and experienced in realistic bug synthesis."""

    #     user_prompt = f"""
    # Below is the original Java code from a real project:
    # ```java
    # {code}
    # ````

    # Your task is to generate **buggy version** of the code that keep the existing tests PASS.

    # ## Goal
    # Create buggy version of the code that:
    # - remains valid and compilable Java,
    # - pass the existing tests.

    # ## Critical constraint – No equivalent mutations
    # Do not produce code that is behaviorally identical to the original. Examples of forbidden “no-op” changes:
    # - renaming variables or reformatting,
    # - swapping loops or conditions that always evaluate to the same result,
    # - adding redundant null‑checks or always‑true/always‑false conditions,
    # - any other change that leaves the observable output or side effects exactly the same in every possible execution.
    # The buggy code must exhibit incorrect behavior in at least one scenario that the tests happen to miss.

    # ## Bug types to consider
    # The bug should resemble a plausible human coding mistake, such as: 
    # - an off-by-one or boundary error, 
    # - a wrong branch condition, 
    # - incorrect handling of empty/singleton inputs, 
    # - a wrong default value or parameter handling mistake, 
    # - a subtle collection-processing mistake, 
    # - a missing/incorrect state update, 
    # - incorrect exception handling or fallback behavior.


    # ## Output format

    # Return a JSON object exactly in the following format:

    # ```json
    # {{
    # "bug_type": "<bug category>",
    # "bug_summary": "<2-3 sentences summary>",
    # "buggy_code": "<full buggy Java code>"
    # }}
    # ```
    # """

        user_prompt = f"""
    Below is the original Java code from a real project:
    ```java
    {code}
    ````

    Your task is to generate **buggy version** of the code that keep the existing tests PASS.

    ## Goal
    Create buggy version of the code that:
    - remains valid and compilable Java,
    - pass the existing tests.

    ## Critical constraint – No equivalent mutations
    Do not produce code that is behaviorally identical to the original. Examples of forbidden “no-op” changes:
    - renaming variables or reformatting,
    - swapping loops or conditions that always evaluate to the same result,
    - adding redundant null‑checks or always‑true/always‑false conditions,
    - any other change that leaves the observable output or side effects exactly the same in every possible execution.
    
    ## Note:
    The buggy code must exhibit incorrect behavior in at least one scenario that the tests happen to miss.
    
    ## Output format

    Return a JSON object exactly in the following format:

    ```json
    {{
    "bug_summary": "<2-3 sentences summary>",
    "buggy_code": "<full buggy Java code>"
    }}
    ```
    """
        if tests_context:
            user_prompt += f"""
## Existing Test Suite (all of them must keep passing)
The project already contains the tests below for this code. The buggy version must not change any behavior they rely on — every test below must still pass on the buggy code:
```java
{tests_context}
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
                temperature=0.7, # Higher temperature for more creative bugs
                max_tokens=16384
            )
            buggy_code = response.choices[0].message.content.strip()
            # Ensure we only get JSON object if LLM adds markdown
            buggy_code = buggy_code.split("```json")[-1].split("```")[0].strip()
            if not buggy_code.startswith("{"):
                text = buggy_code.split("{")[0]
                buggy_code = buggy_code.split(text)[-1].strip()
            print(f"Generated buggy code: {buggy_code}")
            return json.loads(buggy_code)
            # if buggy_code.startswith("```json") and buggy_code.endswith("```"):
            #     buggy_code = buggy_code[len("```json"):-len("```")].strip()
            #     buggy_code = json.loads(buggy_code)
            #     print(f"Generated buggy code: {buggy_code}")
            # else:
            #     buggy_code = json.loads(buggy_code)
            # return buggy_code
        except Exception as e:
            logger.error(f"Error calling LLM for bug generation: {e}")
            return code # Return original code on error

    def enhance_bug_prompt(self, code, buggy_code, test_info, tests_context=None):
        system_prompt = """You are a talented Java programmer and experienced in realistic bug synthesis."""

    #     user_prompt = f"""
    # Below is the original Java code from a real project:
    # ```java
    # {code}
    # ````

    # We have already generated a buggy version of the code:
    # ```java
    # {buggy_code}
    # ```

    # And the bug is detected by existing tests:
    # {test_info}

    # Your task is to generate another **buggy version** of the code that keep the tests PASS.

    # ## Goal
    # Create an buggy version of the code that:
    # - remains valid and compilable Java,
    # - pass the existing tests.

    # ## Critical constraint – No equivalent mutations
    # Do not produce code that is behaviorally identical to the original. Examples of forbidden “no-op” changes:
    # - renaming variables or reformatting,
    # - swapping loops or conditions that always evaluate to the same result,
    # - adding redundant null‑checks or always‑true/always‑false conditions,
    # - any other change that leaves the observable output or side effects exactly the same in every possible execution.
    # The buggy code must exhibit incorrect behavior in at least one scenario that the tests happen to miss.

    # ## Bug types to consider
    # The bug should resemble a plausible human coding mistake, such as: 
    # - an off-by-one or boundary error, 
    # - a wrong branch condition, 
    # - incorrect handling of empty/singleton inputs, 
    # - a wrong default value or parameter handling mistake, 
    # - a subtle collection-processing mistake, 
    # - a missing/incorrect state update, 
    # - incorrect exception handling or fallback behavior.


    # ## Output format

    # Return a JSON object exactly in the following format:

    # ```json
    # {{
    # "bug_type": "<bug category>",
    # "bug_summary": "<2-3 sentences summary>",
    # "buggy_code": "<full buggy Java code>"
    # }}
    # ```
    # """

        user_prompt = f"""
    Below is the original Java code from a real project:
    ```java
    {code}
    ````

    We have already generated a buggy version of the code:
    ```java
    {buggy_code}
    ```

    And the bug is detected by existing tests:
    {test_info}

    Your task is to generate another **buggy version** of the code that keep the tests PASS.

    ## Goal
    Create an buggy version of the code that:
    - remains valid and compilable Java,
    - different from the previous buggy version,
    - pass the existing tests.

    ## Critical constraint – No equivalent mutations
    Do not produce code that is behaviorally identical to the original. Examples of forbidden “no-op” changes:
    - renaming variables or reformatting,
    - swapping loops or conditions that always evaluate to the same result,
    - adding redundant null‑checks or always‑true/always‑false conditions,
    - any other change that leaves the observable output or side effects exactly the same in every possible execution.
    
    ## Note:
    The buggy code must exhibit incorrect behavior in at least one scenario that the tests happen to miss.

    ## Output format

    Return a JSON object exactly in the following format:

    ```json
    {{
    "bug_summary": "<2-3 sentences summary>",
    "buggy_code": "<full buggy Java code>"
    }}
    ```
    """
        if tests_context:
            user_prompt += f"""
## Existing Test Suite (all of them must keep passing)
The project already contains the tests below for this code. The buggy version must not change any behavior they rely on — every test below must still pass on the buggy code:
```java
{tests_context}
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
                temperature=0.7, # Higher temperature for more creative bugs
                max_tokens=16384
            )
            buggy_code = response.choices[0].message.content.strip()

            buggy_code = buggy_code.split("```json")[-1].split("```")[0].strip()
            if not buggy_code.startswith("{"):
                text = buggy_code.split("{")[0]
                buggy_code = buggy_code.split(text)[-1].strip()
            # buggy_code = buggy_code.replace("```json", "").replace("```", "").strip()
            print(f"Enhanced buggy code: {buggy_code}")
            return json.loads(buggy_code)
            # print(f"Enhanced buggy code: {buggy_code}")
            # Ensure we only get JSON object if LLM adds markdown
            # if buggy_code.startswith("```json") and buggy_code.endswith("```"):
            #     buggy_code = buggy_code[len("```json"):-len("```")].strip()
            #     buggy_code = json.loads(buggy_code)
            #     print(f"Enhanced buggy code: {buggy_code}")
            # else:
            #     buggy_code = json.loads(buggy_code)
            # return buggy_code
        except Exception as e:
            logger.error(f"Error calling LLM for bug generation: {e}")
            return code # Return original code on error

    def debug(self):
        system_prompt = """You are a talented Java programmer and experienced in realistic bug synthesis."""

        user_prompt = """
    Below is the original Java code from a real project:
    ```java
    protected List<Queue<String>> makeColumnQueues(final List<String> columnData, final List<TextStyle> styles) {\n        final List<Queue<String>> result = new ArrayList<>();\n        for (int i = 0; i < columnData.size(); i++) {\n            result.add(makeColumnQueue(columnData.get(i), styles.get(i)));\n        }\n        return result;\n    }
    ````

    We have already generated a buggy version of the code:
    ```java
    protected List<Queue<String>> makeColumnQueues(final List<String> columnData, final List<TextStyle> styles) {\n    final List<Queue<String>> result = new ArrayList<>();\n    for (int i = 0; i + 1 < columnData.size(); i++) {\n        result.add(makeColumnQueue(columnData.get(i), styles.get(i)));\n    }\n    return result;\n}
    ```

    And the bug is detected by existing tests:
    ```java
    package org.apache.commons.cli.help;\n\nimport org.junit.Test;\nimport static org.junit.Assert.*;\nimport java.util.*;\n\npublic class MakeColumnQueuesTests {\n\n    public static class TestableTextHelpAppendable extends TextHelpAppendable {\n        public List<String> capturedData = new ArrayList<>();\n        public List<TextStyle> capturedStyles = new ArrayList<>();\n\n        public TestableTextHelpAppendable(final Appendable output) {\n            super(output);\n        }\n\n        protected Queue<String> makeColumnQueue(final String data, final TextStyle style) {\n            capturedData.add(data);\n            capturedStyles.add(style);\n            Queue<String> q = new LinkedList<>();\n            q.add(\"Q:\" + data);\n            return q;\n        }\n    }\n\n    @Test\n    public void testMakeColumnQueues_basic() {\n        TestableTextHelpAppendable helper = new TestableTextHelpAppendable(new StringBuilder());\n\n        List<String> columnData = Arrays.asList(\"one\", \"two\", \"three\");\n        List<TextStyle> styles = Arrays.asList((TextStyle) null, (TextStyle) null, (TextStyle) null);\n\n        List<Queue<String>> result = helper.makeColumnQueues(columnData, styles);\n\n        assertEquals(columnData.size(), result.size());\n        assertEquals(columnData.size(), helper.capturedData.size());\n\n        assertEquals(\"one\", helper.capturedData.get(0));\n        assertNull(helper.capturedStyles.get(0));\n\n        assertEquals(\"Q:one\", result.get(0).peek());\n\n        assertEquals(\"two\", helper.capturedData.get(1));\n        assertNull(helper.capturedStyles.get(1));\n        assertEquals(\"Q:two\", result.get(1).peek());\n\n        assertEquals(\"three\", helper.capturedData.get(2));\n        assertNull(helper.capturedStyles.get(2));\n        assertEquals(\"Q:three\", result.get(2).peek());\n    }\n\n    @Test\n    public void testMakeColumnQueues_empty() {\n        TestableTextHelpAppendable helper = new TestableTextHelpAppendable(new StringBuilder());\n\n        List<String> columnData = Collections.emptyList();\n        List<TextStyle> styles = Collections.emptyList();\n\n        List<Queue<String>> result = helper.makeColumnQueues(columnData, styles);\n\n        assertEquals(0, result.size());\n        assertTrue(helper.capturedData.isEmpty());\n        assertTrue(helper.capturedStyles.isEmpty());\n    }\n}
    <testcase name="testMakeColumnQueues_basic" classname="org.apache.commons.cli.help.MakeColumnQueuesTests" time="0.002">
    <error type="java.lang.NullPointerException"><![CDATA[java.lang.NullPointerException
	at org.apache.commons.cli.help.TextHelpAppendable.makeColumnQueue(TextHelpAppendable.java:312)
	at org.apache.commons.cli.help.TextHelpAppendable.makeColumnQueues(TextHelpAppendable.java:341)
	at org.apache.commons.cli.help.MakeColumnQueuesTests.testMakeColumnQueues_basic(MakeColumnQueuesTests.java:35)
	at java.lang.reflect.Method.invoke(Method.java:498)
]]></error>

    Your task is to generate another **buggy version** of the code that keep the tests PASS.

    ## Goal
    Create an buggy version of the code that:
    - remains valid and compilable Java,
    - pass the existing tests.

    ## Critical constraint – No equivalent mutations
    Do not produce code that is behaviorally identical to the original. Examples of forbidden “no-op” changes:
    - renaming variables or reformatting,
    - swapping loops or conditions that always evaluate to the same result,
    - adding redundant null‑checks or always‑true/always‑false conditions,
    - any other change that leaves the observable output or side effects exactly the same in every possible execution.
    The buggy code must exhibit incorrect behavior in at least one scenario that the tests happen to miss.

    ## Bug types to consider
    The bug should resemble a plausible human coding mistake, such as: 
    - an off-by-one or boundary error, 
    - a wrong branch condition, 
    - incorrect handling of empty/singleton inputs, 
    - a wrong default value or parameter handling mistake, 
    - a subtle collection-processing mistake, 
    - a missing/incorrect state update, 
    - incorrect exception handling or fallback behavior.


    ## Output format

    Return a JSON object exactly in the following format:

    ```json
    {
    "bug_type": "<bug category>",
    "bug_summary": "<2-3 sentences summary>",
    "buggy_code": "<full buggy Java code>"
    }
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
                temperature=0.7, # Higher temperature for more creative bugs
                max_tokens=16384
            )
            buggy_code = response.choices[0].message.content.strip()
            # Ensure we only get JSON object if LLM adds markdown
            if buggy_code.startswith("```json") and buggy_code.endswith("```"):
                buggy_code = buggy_code[len("```json"):-len("```")].strip()
                buggy_code = json.loads(buggy_code)
                print(f"Enhanced buggy code: {buggy_code}")
            return buggy_code
        except Exception as e:
            logger.error(f"Error calling LLM for bug generation: {e}")
            return code # Return original code on error

    def fix_bug_prompt(self, bug_code: str, error: str) -> str:
        prompt = f"""The code below has errors:
        Code:
        ```java
        {bug_code}
        ```

        Error:
        ```
        {error}
        ```

        Please provide a corrected version of the code that addresses the error.
        ```java
        <corrected code>
        ```
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": "You are a helpful assistant that fixes buggy code."},
                          {"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=16384
            )
            fixed_code = response.choices[0].message.content.strip()
            # Ensure we only get Java code block if LLM adds markdown
            if fixed_code.startswith("```java") and fixed_code.endswith("```"):
                fixed_code = fixed_code[len("```java"):-len("```")].strip()
            return fixed_code
        except Exception as e:
            logger.error(f"Error calling LLM for bug_code fixing: {e}")
            return bug_code # Return original bug code on error



if __name__ == "__main__":
    # Example usage (will require actual API key and endpoint)
    llm_config_instance = LLMConfig(api_key=os.getenv("LLM_API_KEY", "sk-f9iJyNvXH7W8Zc4TC6k3c7gzEpN42jpBOhyqgGfGsay4iEkB"),
                                    api_endpoint=os.getenv("LLM_API_ENDPOINT", "https://api.agicto.cn/v1"),
                                    model_name=os.getenv("LLM_MODEL_NAME", "gpt-5.4-mini"))

    agent = BugGenerationAgent(llm_config=llm_config_instance)
    print(agent.debug())
