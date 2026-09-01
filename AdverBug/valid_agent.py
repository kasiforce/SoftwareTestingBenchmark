import os
import json
import openai
from openai import OpenAI
from llm_config import LLMConfig
import logging

logger = logging.getLogger(__name__)

class ValidAgent:
    def __init__(self, llm_config: LLMConfig):
        self.llm_config = llm_config
        self.client = OpenAI(api_key=self.llm_config.API_KEY, base_url=self.llm_config.API_ENDPOINT)
        self.model = self.llm_config.MODEL_NAME

    def validate(self, code, buggy_code, tests):
        system_prompt = """
You are a software verification expert with strong experience in program analysis, debugging, and semantic equivalence checking.

Your task is to determine whether a modified buggy version of Java code introduces a real semantic difference compared with the original correct version.

You should analyze the behavioral differences between the two implementations, rather than only comparing syntactic changes.

A buggy version is considered VALID if there exists at least one possible input, program state, execution path, or environmental condition where:
- the original code produces the expected behavior, and
- the buggy code produces different observable behavior.

A buggy version should be considered INVALID if:
- the modification does not change program behavior,
- the change is only cosmetic or structural,
- the modified code is likely behaviorally equivalent to the original code,
- the changed code affects unreachable or dead code,
- the difference cannot lead to any observable behavioral change.

Important:
- Do not judge based only on whether existing tests pass or fail.
- Passing tests only indicate that the bug may not be covered by tests.
- Focus on semantic behavior differences.
- If you can identify a plausible scenario where the two implementations behave differently, return true.
- If no meaningful behavioral difference can be identified, return false.

Return only a JSON object.
"""

        user_prompt = f"""
You are given three pieces of information from a Java project.

## Original Correct Code
```java
{code}
```
## Generated Buggy Code
```java
{buggy_code}
```
## Related Test Code
```java
{tests}
```

Your task is to determine whether the generated buggy code contains a real semantic bug compared with the original code.

Analyze the two implementations from a behavioral perspective.

Consider:

What behavior does the original implementation provide?
What behavior does the buggy implementation provide?
Whether there exists any valid input, state, or execution path that can distinguish them.
Whether the difference affects observable program behavior.

The provided tests are only reference information. They should not be used as the sole criterion because the bug may intentionally escape current tests.

Return the result in exactly this format:
```json
{{
    "is_valid_bug": True or False,
    "reason": "<brief explanation of the semantic difference or why no meaningful difference was found>"
}}
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
                temperature=0.3, # Lower temperature for more deterministic validation
                max_tokens=4096
            )
            valid_result = response.choices[0].message.content.strip()
            # Ensure we only get JSON object if LLM adds markdown
            if valid_result.startswith("```json") and valid_result.endswith("```"):
                valid_result = valid_result[len("```json"):-len("```")].strip()
                valid_result = json.loads(valid_result)
                print(f"valid result: {valid_result}")
            return valid_result
        except Exception as e:
            logger.error(f"Error calling LLM for validation: {e}")
            return {
                        "is_valid_bug": False,
                        "reason": "Error occurred during validation. Unable to determine if the bug is valid."
                    }



if __name__ == "__main__":
    # Example usage (will require actual API key and endpoint)
    llm_config_instance = LLMConfig(api_key=os.getenv("LLM_API_KEY", "sk-hIrt8jKCY6fysHpf79w5jQwtxlSRuQYAFQ5nWwWRfGMYmOB3"),
                                    api_endpoint=os.getenv("LLM_API_ENDPOINT", "https://api.agicto.cn/v1"),
                                    model_name=os.getenv("LLM_MODEL_NAME", "gpt-5.4-mini"))

    agent = ValidAgent(llm_config=llm_config_instance)
    
    with open("commons-cli_bug_junit4_gpt5nano.json", "r") as f:
        result_data = json.load(f)

    for item in result_data:
        original_code = item.get("code", "")
        buggy_code = item.get("buggy_code", "")
        test_code = item.get("generated_tests", "")
        validation_result = agent.validate(original_code, buggy_code, test_code)
        item["validation_result"] = validation_result
        print(f"Validation result for buggy code:\n{validation_result}\n")
    
    with open("commons-cli_bug_junit4_gpt5nano_validated.json", "w") as f:
        json.dump(result_data, f, indent=4)
        
