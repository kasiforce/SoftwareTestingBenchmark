import json
import os
from bug_generation_agent import BugGenerationAgent
from test_gen import TestGenerationAgent
from llm_config import LLMConfig

def main(data_path):
    llm_config = LLMConfig("sk-hIrt8jKCY6fysHpf79w5jQwtxlSRuQYAFQ5nWwWRfGMYmOB3", "https://api.agicto.cn/v1", "gpt-5.4-mini")
    bug_agent = BugGenerationAgent(llm_config)
    test_agent = TestGenerationAgent(llm_config)
    final_results = []
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    for entry in data:
        code = entry.get("code", "")
        src_file = entry.get("src_file", "")
        test_file = entry.get("test_file", "")
        bug_code = ""
        test_info = ""
        flag = "src_test_fail"
        bug_code_list = []
        test_code_list = []
        for i in range(5):
            if i == 0:
                bug_json = bug_agent.init_bug_prompt(code)
                bug_code = bug_json.get("buggy_code", "")
            else:
                bug_json = bug_agent.enhance_bug_prompt(code, bug_code, test_info)
                bug_code = bug_json.get("buggy_code", "")

            with open(src_file, 'r', encoding='utf-8') as f:
                src = f.read()
            # for item in bug_json:
            #     bug_code = item.get("buggy_code", "")
            if code in src:
                src = src.replace(code, bug_code)
                with open(src_file, 'w', encoding='utf-8') as f:
                    f.write(src)
                print(f"已将源代码替换为错误代码")

            result = subprocess.run(
                ["mvn", "compile", "-Drat.skip=true", "-q"],
                cwd="/testbed",
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                error_message = result.stdout
                f = False
                for i in range(3):
                    bug_code_fix = bug_agent.fix_bug_prompt(bug_code, error_message)
                    src = src.replace(bug_code, bug_code_fix)
                    with open(src_file, 'w', encoding='utf-8') as f:
                        f.write(src)

                    result = subprocess.run(
                        ["mvn", "compile", "-Drat.skip=true", "-q"],
                        cwd="/testbed",
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        bug_code = bug_code_fix
                        print(f"已将错误代码修复")
                        f = True
                        break
                    else:
                        error_message = result.stdout
                        bug_code = bug_code_fix
                        print(f"修复尝试 {i+1} 失败，错误信息:\n{error_message}")

                if not f:
                    with open(src_file, 'r', encoding='utf-8') as f:
                        src = f.read()
                    src = src.replace(bug_code, code)
                    with open(src_file, 'w', encoding='utf-8') as f:
                        f.write(src)
                    continue


            result = subprocess.run(
                ["mvn", "test", "-Drat.skip=true", "-q"],
                cwd="/testbed",
                capture_output=True,
                text=True
            )
            
            bug_code_list.append(bug_code)

            print(result.stdout)
            if result.returncode != 0:
                with open(src_file, 'r', encoding='utf-8') as f:
                    src = f.read()
                src = src.replace(bug_code, code)
                with open(src_file, 'w', encoding='utf-8') as f:
                    f.write(src)
                # print("测试失败，详细信息：\n", result.stdout[-1000:])
                output = result.stdout.split("ERROR]")[0].strip()
                output1 = output.split(output)[0].strip()
                test_info = result.stdout  # Get the last 1000 characters of stdout
                print("测试失败，详细信息：\n", test_info[-1000:])
                continue
            
            else:
                print("原有测试通过")
                flag = "src_test_pass"
                tests = test_agent.init_test_prompt(bug_code, entry)
                test_file = entry.get("test_file", "")
                os.makedirs(os.path.dirname(test_file), exist_ok=True)
                with open(test_file, 'w', encoding='utf-8') as f:
                    f.write(tests)

                result = subprocess.run(
                    ["mvn", "test-compile", "-Drat.skip=true", "-q"],
                    cwd="/testbed",
                    capture_output=True,
                    text=True
                )
                if result.returncode != 0:
                    error_message = result.stdout
                    for i in range(5):
                        test_code_fix = test_agent.fix_test_prompt(tests, error_message)
                        with open(test_file, 'w', encoding='utf-8') as f:
                            f.write(test_code_fix)

                        result = subprocess.run(
                            ["mvn", "test-compile", "-Drat.skip=true", "-q"],
                            cwd="/testbed",
                            capture_output=True,
                            text=True
                        )
                        if result.returncode == 0:
                            tests = test_code_fix
                            print(f"已将错误测试代码修复")
                            break
                        else:
                            error_message = result.stdout
                            tests = test_code_fix
                            print(f"测试修复尝试 {i+1} 失败，错误信息:\n{error_message}")

                result = subprocess.run(
                    ["mvn", "test", "-Drat.skip=true", "-q"],
                    cwd="/testbed",
                    capture_output=True,
                    text=True
                )
                
                test_code_list.append(tests)

                print(result.stdout)
                if result.returncode != 0:
                    with open(src_file, 'r', encoding='utf-8') as f:
                        src = f.read()
                    src = src.replace(bug_code, code)
                    with open(src_file, 'w', encoding='utf-8') as f:
                        f.write(src)
                    os.remove(test_file)
                    print("生成的测试失败，详细信息：\n", result.stdout[-1000:])
                    output = result.stdout.split("ERROR]")[0].strip()
                    output1 = output.split(output)[0].strip()
                    test_info = tests + "\n" + result.stdout  # Get the last 1000 characters of stdout  
                    continue
                else:
                    print("生成的测试通过")
                    flag = "generated_test_pass"
                    break
                    tests = test_agent.enhance_test_prompt(bug_code, entry, tests)
                    with open(test_file, 'w', encoding='utf-8') as f:
                        f.write(tests)
                    result = subprocess.run(
                        ["mvn", "test-compile", "-Drat.skip=true", "-q"],
                        cwd="/testbed",
                        capture_output=True,
                        text=True
                    )
                    if result.returncode != 0:
                        error_message = result.stdout
                        for i in range(5):
                            test_code_fix = test_agent.fix_test_prompt(tests, error_message)
                            with open(test_file, 'w', encoding='utf-8') as f:
                                f.write(test_code_fix)

                            result = subprocess.run(
                                ["mvn", "test-compile", "-Drat.skip=true", "-q"],
                                cwd="/testbed",
                                capture_output=True,
                                text=True
                            )
                            if result.returncode == 0:
                                tests = test_code_fix
                                print(f"已将错误测试代码修复")
                                break
                            else:
                                error_message = result.stdout
                                tests = test_code_fix
                                print(f"测试修复尝试 {i+1} 失败，错误信息:\n{error_message}")

                    test_code_list.append(tests)
                    
                    result = subprocess.run(
                        ["mvn", "test", "-Drat.skip=true", "-q"],
                        cwd="/testbed",
                        capture_output=True,
                        text=True
                    )
                    if result.returncode != 0:
                        with open(src_file, 'r', encoding='utf-8') as f:
                            src = f.read()
                        src = src.replace(bug_code, code)
                        with open(src_file, 'w', encoding='utf-8') as f:
                            f.write(src)
                        os.remove(test_file)
                        print("增强的测试失败，详细信息：\n", result.stdout[-1000:])
                        output = result.stdout.split("ERROR]")[0].strip()
                        output1 = output.split(output)[0].strip()
                        test_info = tests + "\n" + result.stdout  # Get the last 1000 characters of stdout
                        continue
                    else:
                        print("增强的测试通过")
                        flag = "enhanced_test_pass"
                        break
        
        with open(src_file, 'r', encoding='utf-8') as f:
            src = f.read()
        src = src.replace(bug_code, code)
        with open(src_file, 'w', encoding='utf-8') as f:
            f.write(src)
        if test_file and os.path.exists(test_file):
            os.remove(test_file)     

        entry["buggy_code"] = bug_code_list
        entry["tests"] = test_code_list
        # entry["bug_info"] = bug_json
        entry["flag"] = flag
        
        final_results.append(entry)
        with open("/testbed/final_results.json", 'w', encoding='utf-8') as f:
            json.dump(final_results, f, ensure_ascii=False, indent=4)

        subprocess.run(
            ["cp", "/testbed/final_results.json", "/testbed/results/"],
            cwd="/testbed",
            capture_output=True,
            text=True
        )
        print(f"最终生成的错误代码:\n{bug_code}")

    

if __name__ == "__main__":
    import argparse
    import subprocess

    parser = argparse.ArgumentParser(description="Generate bugs and tests for Java code.")
    parser.add_argument("--data-path", type=str, required=True, help="Path to the JSON data file.")
    args = parser.parse_args()

    main(args.data_path)
                
        
        

        