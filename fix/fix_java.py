import argparse
import concurrent.futures
import json
import os
import subprocess
import tempfile
import time
import traceback
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import openai
from openai import OpenAI
import javalang


SYSTEM_PROMPT = "You are a professional test engineer specializing in writing high-quality unit test code."


class JavaGeneratedTestRepairer:
    def __init__(
        self,
        api_key: str,
        model: str,
        dockerfile_path: str,
        data_file: str,
        max_rounds: int = 3,
        base_url: Optional[str] = None,
        reuse_container: bool = True,
        parallel_workers: int = 1,
        _skip_client_init: bool = False,
    ):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.dockerfile_path = dockerfile_path
        self.data_file = data_file
        self.max_rounds = max_rounds
        self.client = None if _skip_client_init else (
            OpenAI(api_key=api_key, base_url=base_url) if base_url else OpenAI(api_key=api_key)
        )
        openai.api_key = api_key
        self.reuse_container = reuse_container
        self.parallel_workers = max(1, parallel_workers)
        self.container_name: Optional[str] = None
        self._run_id = f"{os.getpid()}_{int(time.time())}"

        # Token 统计
        self.usage_stats = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "cost": 0.0,
        }

        # 模型定价（人民币/百万 tokens）
        self.model_pricing = {
            "gpt-5-nano": {"prompt": 0.35, "completion": 2.80},
            "gpt-4o": {"prompt": 17.5, "completion": 70.00},
            "deepseek-v3.2": {"prompt": 2.00, "completion": 3.00},
            "glm-4.7": {"prompt": 4.00, "completion": 16.00},
            "qwen3-coder-480b-a35b-instruct": {"prompt": 6.00, "completion": 24.00},
        }.get(self.model, {"prompt": 0.0, "completion": 0.0})

    @staticmethod
    def _extract_code(text: str) -> str:
        if not text:
            return ""
        if "```java" in text:
            return text.split("```java", 1)[1].split("```", 1)[0].strip()
        if "```" in text:
            return text.split("```", 1)[1].split("```", 1)[0].strip()
        return text.strip()

    @staticmethod
    def _build_initial_prompt(item: Dict[str, Any], category: str, test_framework: str) -> str:
        function_name = item.get("name", "")
        function_code = item.get("code", "")
        file_path = item.get("src_file", "")
        test_path = item.get("test_file", "")
        signature = function_code.split('{', 1)[0].rstrip()

        class_name = None
        class_info = {}
        if item.get('type') == "method":
            class_name = item.get('class_name')
            class_info['class_name'] = class_name
            if item.get('class_constructor'):
                class_info['class_constructor'] = item['class_constructor']
            if item.get('class_fields'):
                class_info['class_fields'] = item['class_fields']

        specification = item.get('specification', '')

        if category == "specification":
            return f"""
Please generate a test class for the following function.

Function Information:
- Src file: {file_path}
- Function name: {function_name}
- Class: {class_info if class_name else 'Standalone function'}
- Is async: {item.get('is_async', False)}

Function Specification:
```java
{signature}
```{specification}```

Requirements:
Java version: Java 17
Use {test_framework} framework for writing tests.
Your job is to output corresponding test class that obtains high coverage and invokes the code under test.
The test code should be written into {test_path}. Please make sure the imports are correct.
Return ONLY code without explanations, non-code text, or markdown formatting.

```java
<test code>
""".strip()
        else:
            return f"""
Please generate a test class for the following function.

Function Information:
- Src file: {file_path}
- Function name: {function_name}
- Class: {class_info if class_name else 'Standalone function'}
- Is async: {item.get('is_async', False)}

Function Code:
```java
{function_code}

Requirements:
Java version: Java 17
Use {test_framework} framework for writing tests.
Your job is to output corresponding test class that obtains high coverage and invokes the code under test.
The test code should be written into {test_path}. Please make sure the imports are correct.
Return ONLY code without explanations, non-code text, or markdown formatting.

```java
<test code>
""".strip()

    @staticmethod
    def _build_error_feedback(error_messages: str) -> str:
        return (
            "Here are the error messages from the tests:\n"
            f"{error_messages}\n\n"
            "Errors exist in the generated unit tests.\n\n"
            "Please fix the unit tests to address these errors and return ONLY the correct unit tests."
        )

    def _syntax_check(self, code: str) -> Tuple[bool, str]:
        try:
            javalang.parse.parse(code)
            return True, ""
        except Exception as e:
            return False, "".join(traceback.format_exception_only(type(e), e)).strip()

    def _call_llm(self, messages: List[Dict[str, str]]) -> str:
        if self.client is None:
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url) if self.base_url else OpenAI(api_key=self.api_key)
        # print(messages)
        time.sleep(1)  # 每次调用前等待1秒，避免过快调用API
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.0,
            max_tokens=16384,
        )

        if response.usage:
            prompt_tokens = response.usage.prompt_tokens
            completion_tokens = response.usage.completion_tokens
            total_tokens = response.usage.total_tokens

            prompt_cost = (prompt_tokens / 1_000_000) * self.model_pricing["prompt"]
            completion_cost = (completion_tokens / 1_000_000) * self.model_pricing["completion"]
            call_cost = prompt_cost + completion_cost

            self.usage_stats["prompt_tokens"] += prompt_tokens
            self.usage_stats["completion_tokens"] += completion_tokens
            self.usage_stats["total_tokens"] += total_tokens
            self.usage_stats["cost"] += call_cost

        content = response.choices[0].message.content if response.choices else ""
        return self._extract_code(content or "")

    def _build_docker_image(self) -> None:
        repo_name = Path(self.dockerfile_path).parent.name
        self.image_name = f"java-repo-{repo_name}"
        subprocess.run(
            ["docker", "build", "-t", self.image_name, "-f", self.dockerfile_path, "."],
            check=True,
        )

    def _start_reusable_container(self) -> None:
        if not self.reuse_container:
            return
        self.container_name = f"java-test-repair-{self._run_id}"
        subprocess.run(
            [
                "docker", "run", "-d", "--name", self.container_name,
                self.image_name, "bash", "-c", "sleep infinity"
            ],
            check=True,
        )

    def _stop_reusable_container(self) -> None:
        if not self.container_name:
            return
        subprocess.run(["docker", "rm", "-f", self.container_name], check=False)
        self.container_name = None

    def _evaluate_single_test(self, item: Dict[str, Any], test_code: str, item_idx: int) -> Dict[str, Any]:
        # 1. 语法检查
        syntax_ok, syntax_error = self._syntax_check(test_code)
        if not syntax_ok:
            return {"ok": False, "stage": "syntax", "error": syntax_error}

        # 2. 编译 + 运行检查
        with tempfile.TemporaryDirectory(prefix="java_repair_") as td:
            td_path = Path(td)
            item_data = deepcopy(item)
            item_data["generated_tests"] = [test_code]
            item_json = td_path / "item.json"
            item_json.write_text(json.dumps([item_data], ensure_ascii=False, indent=2), encoding="utf-8")

            compile_result = td_path / "compile.txt"
            test_result = td_path / "test.txt"
            run_cmd = f"""
# set -e
cd /testbed
touch /tmp/compile.txt /tmp/test.txt
if ! grep -q "<artifactId>junit</artifactId>" pom.xml; then
    sed -i '/<\/dependencies>/i \
<dependency>\
<groupId>junit</groupId>\
<artifactId>junit</artifactId>\
<version>4.13.2</version>\
<scope>test</scope>\
</dependency>' pom.xml
fi

if ! grep -q "<artifactId>junit-vintage-engine</artifactId>" pom.xml; then
    sed -i '/<\/dependencies>/i \
    <dependency>\
        <groupId>org.junit.vintage</groupId>\
        <artifactId>junit-vintage-engine</artifactId>\
        <version>5.13.3</version>\
        <scope>test</scope>\
    </dependency>' pom.xml
fi

if ! grep -q "<artifactId>mockito-core</artifactId>" pom.xml; then
    sed -i '/<\/dependencies>/i \
    <dependency>\
        <groupId>org.mockito</groupId>\
        <artifactId>mockito-core</artifactId>\
        <version>4.11.0</version>\
        <scope>test</scope>\
    </dependency>' pom.xml
fi

# sed -i 's|<argLine>-javaagent:src/test/resources/agent.jar</argLine>|<argLine>@{{argLine}} -javaagent:src/test/resources/agent.jar</argLine>|' pom.xml

if ! grep -q "<artifactId>jakarta.xml.bind-api</artifactId>" pom.xml; then
    sed -i '/<\/dependencies>/i \
    <dependency>\
        <groupId>jakarta.xml.bind</groupId>\
        <artifactId>jakarta.xml.bind-api</artifactId>\
        <version>4.0.0</version>\
    </dependency>' pom.xml
fi

if ! grep -q "<artifactId>jaxb-runtime</artifactId>" pom.xml; then
    sed -i '/<\/dependencies>/i \
    <dependency>\
        <groupId>org.glassfish.jaxb</groupId>\
        <artifactId>jaxb-runtime</artifactId>\
        <version>4.0.3</version>\
        <scope>runtime</scope>\
    </dependency>' pom.xml
fi

# 安装 Python3
if ! command -v python3 &> /dev/null; then
    apt-get update && apt-get install -y python3
fi
python3 /testbed/gentests_files.py --project-root /testbed --data-path /tmp/item.json
mvn -q test-compile -Drat.skip=true >/tmp/compile.log 2>&1
MVN_EXIT_CODE=$?       
if [ $MVN_EXIT_CODE -eq 0 ]; then
    mvn -q -Dtest={Path(item.get('test_file', '')).stem} test -Drat.skip=true >/tmp/test.log 2>&1
    TEST_EXIT_CODE=$?
    if [ $TEST_EXIT_CODE -ne 0 ]; then
        sed -i 's/\x1b\[[0-9;]*m//g' /tmp/test.log
        cat /tmp/test.log > /tmp/test.txt
    fi
else
    sed -i 's/\x1b\[[0-9;]*m//g' /tmp/compile.log
    cat /tmp/compile.log > /tmp/compile.txt
fi
"""

            if self.reuse_container and self.container_name:
                subprocess.run(["docker", "cp", str(Path("gen_test/gen_tests_files.py").resolve()), f"{self.container_name}:/testbed/gentests_files.py"], check=True)
                subprocess.run(["docker", "cp", str(item_json.resolve()), f"{self.container_name}:/tmp/item.json"], check=True)
                subprocess.run(["docker", "exec", self.container_name, "bash", "-c", run_cmd], check=True)
                subprocess.run(["docker", "cp", f"{self.container_name}:/tmp/compile.txt", str(compile_result)], check=True)
                subprocess.run(["docker", "cp", f"{self.container_name}:/tmp/test.txt", str(test_result)], check=True)
            else:
                subprocess.run(
                    [
                        "docker", "run", "--rm",
                        "-v", f"{Path('gen_test/gen_tests_files.py').resolve()}:/testbed/gentests_files.py",
                        "-v", f"{item_json.resolve()}:/tmp/item.json",
                        "-v", f"{td_path.resolve()}:/tmp_out",
                        self.image_name,
                        "bash", "-c", run_cmd + "cp /tmp/compile.txt /tmp_out/compile.txt && cp /tmp/test.txt /tmp_out/test.txt",
                    ],
                    check=True,
                )

            compile_output = compile_result.read_text(encoding="utf-8", errors="ignore") if compile_result.exists() else ""
            test_output = test_result.read_text(encoding="utf-8", errors="ignore") if test_result.exists() else ""
            output = compile_output or test_output
            if output.strip() == "":
                return {"ok": True, "stage": "done", "error": ""}

            # 区分编译错误和测试错误
            stage = ""
            if compile_output.strip() != "":
                stage = "compile"
            
            elif test_output.strip() != "":
                stage = "run"  # 默认归类为运行错误

            output_cleaned = self._clean_maven_error(output)

            return {"ok": False, "stage": stage, "error": output_cleaned[:2000]}

    def _clean_maven_error(self, error_text: str) -> str:
        """只保留核心编译/测试错误，去除 Maven 引导信息"""
        lines = error_text.split('\n')
        cleaned = []
        for line in lines:
            if line.startswith('[ERROR] -> [Help') or line.startswith('[ERROR] To see'):
                break   # 从这里开始都是 Maven 的引导，直接丢弃
            cleaned.append(line)
        return '\n'.join(cleaned)

    def repair_item(self, item: Dict[str, Any], item_idx: int, category: str, test_framework: str) -> Dict[str, Any]:
        initial_test = "\n\n".join(item.get("generated_tests", []))
        current_test = initial_test

        messages: List[Dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.append({"role": "user", "content": self._build_initial_prompt(item, category, test_framework)})
        messages.append({"role": "assistant", "content": current_test})

        history: List[Dict[str, Any]] = []
        final_status = "failed"

        for round_idx in range(0, self.max_rounds + 1):
            eval_result = self._evaluate_single_test(item, current_test, item_idx)
            if eval_result["ok"]:
                final_status = "success"
                history.append({"round": round_idx, "stage": "done", "test_code": current_test})
                break

            stage = eval_result.get("stage", "unknown")
            feedback = self._build_error_feedback(eval_result.get("error", ""))
            history.append({
                "round": round_idx,
                "stage": stage,
                "feedback": eval_result.get("error", ""),
                "test_code": current_test,
            })
            messages.append({"role": "user", "content": feedback})
            fixed = self._call_llm(messages)
            messages.append({"role": "assistant", "content": fixed})
            current_test = fixed

        out = deepcopy(item)
        out["generated_tests"] = [current_test]
        out["repair_status"] = final_status
        out["repair_history"] = history
        return out

    def _repair_chunk(self, chunk: List[Tuple[int, Dict[str, Any]]], worker_id: int, category: str, test_framework: str) -> Tuple[List[Tuple[int, Dict[str, Any]]], Dict[str, Any]]:
        worker = JavaGeneratedTestRepairer(
            api_key=self.api_key,
            model=self.model,
            dockerfile_path=self.dockerfile_path,
            data_file=self.data_file,
            max_rounds=self.max_rounds,
            base_url=self.base_url,
            reuse_container=self.reuse_container,
            parallel_workers=1,
            _skip_client_init=True,
        )
        worker._run_id = f"{self._run_id}_w{worker_id}"
        worker._build_docker_image()
        worker._start_reusable_container()
        outputs: List[Tuple[int, Dict[str, Any]]] = []
        try:
            for idx, item in chunk:
                outputs.append((idx, worker.repair_item(item, idx, category, test_framework)))
        finally:
            worker._stop_reusable_container()
        return outputs, worker.usage_stats

    def _print_usage_summary(self, usage: Dict[str, Any]) -> None:
        print("\n" + "=" * 50)
        print("API 使用统计:")
        print(f"  输入 tokens:     {usage.get('prompt_tokens', 0):,}")
        print(f"  输出 tokens:     {usage.get('completion_tokens', 0):,}")
        print(f"  总 tokens:       {usage.get('total_tokens', 0):,}")
        print(f"  预估花费:        ¥{usage.get('cost', 0.0):.4f} 人民币")
        print("=" * 50)

    def repair_file(self, output_file: str) -> None:
        start_time = time.time()

        with open(self.data_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        category = "specification" if "specification" in self.data_file else "code"

        test_framework = "JUnit 5"
        if "junit4" in self.data_file.lower():
            test_framework = "JUnit 4"

        self._build_docker_image()

        # ---- 单线程 ----
        if self.parallel_workers == 1:
            self._start_reusable_container()
            total_usage = deepcopy(self.usage_stats)
            try:
                results_map = {}
                for idx, item in enumerate(data):
                    repaired_item = self.repair_item(item, idx, category, test_framework)
                    results_map[idx] = repaired_item
                    total_usage = deepcopy(self.usage_stats)
                    ordered = [results_map[i] for i in sorted(results_map.keys())]
                    elapsed = time.time() - start_time
                    summary_data = {
                        "items": ordered,
                        "_usage_summary": total_usage,
                        "_elapsed_seconds": elapsed,
                    }
                    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
                    with open(output_file, "w", encoding="utf-8") as wf:
                        json.dump(summary_data, wf, ensure_ascii=False, indent=2)
            finally:
                self._stop_reusable_container()

            # self._print_usage_summary(total_usage)
            return

        # ---- 多线程 ----
        indexed = list(enumerate(data))
        chunks: List[List[Tuple[int, Dict[str, Any]]]] = [[] for _ in range(self.parallel_workers)]
        for i, pair in enumerate(indexed):
            chunks[i % self.parallel_workers].append(pair)
        chunks = [c for c in chunks if c]

        results_map: Dict[int, Dict[str, Any]] = {}
        total_usage = deepcopy(self.usage_stats)

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(chunks)) as executor:
            futures = [executor.submit(self._repair_chunk, chunk, wid, category, test_framework) for wid, chunk in enumerate(chunks)]
            for fut in concurrent.futures.as_completed(futures):
                chunk_outputs, chunk_usage = fut.result()
                for key in total_usage:
                    total_usage[key] += chunk_usage.get(key, 0.0)
                for idx, repaired_item in chunk_outputs:
                    results_map[idx] = repaired_item
                ordered = [results_map[i] for i in sorted(results_map.keys())]
                elapsed = time.time() - start_time
                summary_data = {
                    "items": ordered,
                    "_usage_summary": total_usage,
                    "_elapsed_seconds": elapsed,
                }
                Path(output_file).parent.mkdir(parents=True, exist_ok=True)
                with open(output_file, "w", encoding="utf-8") as wf:
                    json.dump(summary_data, wf, ensure_ascii=False, indent=2)

        # self._print_usage_summary(total_usage)


def main() -> None:
    # parser = argparse.ArgumentParser()
    # parser.add_argument("--api-key", type=str, default="")
    # parser.add_argument("--base-url", type=str, default=None)
    # parser.add_argument("--model", type=str, required=True)
    # parser.add_argument("--dockerfile-path", type=str, required=True)
    # parser.add_argument("--data-file", type=str, required=True)
    # parser.add_argument("--output-file", type=str, required=True)
    # parser.add_argument("--max-rounds", type=int, default=3)
    # parser.add_argument("--parallel-workers", type=int, default=1)
    # args = parser.parse_args()

    for root, dirs, files in os.walk("tests/test_gen/java/nfe"):
            for file in files:
                if "codellama" in  file.lower() or "ds6.7b" in file.lower():
                    continue
                
                if "dsv3.2" in file.lower() or "gpt4o" in file.lower():
                    continue
                
                if "specification_junit4_qwen" in file.lower() or "lite_junit5_gpt5" in file.lower() or "lite_junit5_glm" in file.lower():
                    continue
                
                if "specification_junit4_glm" in file.lower() or "commons-jxpath_lite_specification_junit5_gpt5" in file.lower() or "commons-jxpath_lite_junit4_qwen" in file.lower() or "lite_junit4_glm" in file.lower() or "lite_junit4_gpt5" in file.lower() or "specification_junit5_qwen" in file.lower():
                    continue

                # if "commons-jxpath_lite_junit4_glm-4.7" in file.lower() or "specification_junit4_gpt5" in file.lower() or "commons-jxpath_lite_junit5_dsv3.2" in file.lower() or "commons-jxpath_lite_specification_junit4_gpt4o" in file.lower() or "commons-jxpath_lite_specification_junit5_glm-4.7" in file.lower() or "commons-jxpath_lite_specification_junit4_qwen" in file.lower():
                    # continue
                    

                if "qwen" in file.lower() :
                    model_name = "qwen3-coder-480b-a35b-instruct"
                if "glm" in file.lower():
                    model_name = "glm-4.7"
                if "gpt5" in file.lower():
                    model_name = "gpt-5-nano"
                if "gpt4o" in file.lower():
                    model_name = "gpt-4o"
                if "dsv3.2" in file.lower():
                    model_name = "deepseek-v3.2"

                full_path = os.path.join(root, file)
                print(full_path)
                print(model_name)
                repairer = JavaGeneratedTestRepairer(
                    api_key="",
                    api_key="",
                    model=model_name,
                    dockerfile_path="output/nfe/dockerfile",
                    data_file=full_path,
                    max_rounds=3,
                    base_url="https://api.agicto.cn/v1",
                    reuse_container=False,
                    parallel_workers=1,
                )
                repairer.repair_file("tests/test_gen/java/fix_nfe/repaired_"+file)
                    # time.sleep(10)  # 每次修复后等待10秒，避免过快调用API

    # repairer = JavaGeneratedTestRepairer(
    #                 api_key="",
    #                 api_key="",
    #                 model="gpt-5-nano",
    #                 dockerfile_path="output/commons-jxpath/dockerfile",
    #                 data_file="tests/test_gen/java/commons-jxpath/commons-jxpath_junit4_gpt5nano.json",
    #                 max_rounds=3,
    #                 base_url="",
    #                 reuse_container=False,
    #                 parallel_workers=1,
    #             )
    # repairer.repair_file("tests/test_gen/java/fix_commons-jxpath/repaired_commons-jxpath_junit4_gpt5nano.json")



if __name__ == "__main__":
    main()