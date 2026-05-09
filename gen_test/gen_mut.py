import os 
import json
import re
import time
from argparse import ArgumentParser
import subprocess
import openai
from openai import OpenAI

# def gen_prompt(mut_num, code):
#     prompt="""    
# Below is the original code from a Java project. your task is to generate %s mutants in original code(notice:mutant refers to mutant in software engineering, i.e. making subtle alterations to the original code):
# code:java```
# %s\n
# ```

# as follows are some examples of mutants which you can refer to:
#     {
#     "precode": "n = (n & (n - 1));",
#     "aftercode": " n = (n ^ (n - 1));"                                        
#     },
#     {
#     "precode": "  while (!queue.isEmpty()) {",
#     "aftercode": " while (true) { "             
#     },                                        
#     {
#     "precode": "return depth==0;",
#     "aftercode": "return true;"
#     },                                        
#     {
#     "precode": "ArrayList r = new 
#     ArrayList();r.add(first).addll(subset);to_add(r)",
#     "aftercode": "to_add.addAll(subset);"
#     },                               
#     {
#     "precode": "c = bin_op.apply(b,a);",
#     "aftercode": "c = bin_op.apply(a,b);",    
#     },                              
#     {
#     "precode":"while (Math.abs(x-approx*approx) > epsilon) { "     
#     "aftercode": " while (Math.abs(x-approx) > epsilon) {"
#     },                          
# #Requirement:
# 1.Provide generated mutants directly
# 2.A mutation can only occur on one line
# 3.Your output must be like:
# "
# [
#     {
#         "id":,
#         "line":,
#         "precode":"",
#         "aftercode":""
#     }
# ]
# "(both brackets are required)
# Where "id" stand for mutant serlal number,"Line" represent the line number of the mutated(please refer to the original code line number),"precode" represent the line of code before mutation and it can't be empty,"aftercode" represent the line of code after mutation
# 4.Prohibit generating the exact same mutants
# 5.Do not generate equivalent mutants: for example generating on comments are completely useless.
# 6.all write in a json file
# 7.Please ensure that your mutant contains ONLY ONE LINE and pay attention to line breaks. Some statements may be split into two lines. 
# """%(min(mut_num,10),code)

def gen_prompt(mut_num, code):
    prompt = f"""
Below is the original code from a Java project.

Your task is to generate {min(mut_num,20)} faulty variants of the code (called mutants).
These mutants should include BOTH:

1. Traditional mutation testing changes (small syntactic changes)
2. Semantic / logic-level faults (more realistic bugs)

--------------------------------
Mutation Type Requirements:

You MUST generate a MIX of the following:

(A) Syntactic Mutations (about 60%):
- Change operators (>, <, ==, !=, +, -, etc.)
- Modify constants (+1, -1, boundary changes)
- Swap variables
- Modify conditions slightly

(B) Semantic / Logic Faults (about 40%):
- Incorrect boundary handling (off-by-one but meaningful)
- Wrong condition logic (e.g., missing edge cases)
- Incorrect variable usage (wrong variable but type-correct)
- Missing or incorrect function behavior
- Subtle logical errors that still compile

--------------------------------
STRICT Constraints:

1. Each mutant MUST modify ONLY ONE LINE
2. The code MUST remain COMPILABLE (very important)
3. DO NOT generate trivial or meaningless changes:
   - Do NOT modify comments
   - Do NOT produce equivalent mutants (same semantics)
4. Semantic faults should be:
   - Realistic (similar to real bugs)
   - Non-trivial (not always "return true")
5. Avoid overly obvious bugs (e.g., infinite loops like while(true) unless justified)
6. Each mutation must be UNIQUE

--------------------------------
Code:
```java
{code}

Output Format (STRICT JSON):
[
{{
"id": 1,
"line": <line_number>,
"type": "syntactic" | "semantic",
"precode": "<original line>",
"aftercode": "<mutated line>"
}}
]

Notes:
"type" indicates whether this is a syntactic mutation or a semantic fault
Ensure a balanced mix of both types
Line numbers must match the original code
"""
    return prompt

def call_llm(prompt: str, max_K: int = 3) -> str:
        """
        调用大模型API生成测试代码

        Args:
            prompt: 提示文本
            max_K: 最多生成测试用例数量

        Returns:
            生成的测试代码
        """
        message = [{"role": "system",
                    "content": "You are a talented Java programmer and experienced in software testing. Your ability of writing unit tests is excellent. And you have the knowledge on Everything about Java & JUnit. Also, you have the ability of critical thinking and logical reasoning. That will help you to write bugless code and help debugging."},
                   {"role": "user", "content": prompt}
                   ]
        tests = []
        client = OpenAI(api_key="sk-BllRs4ogYnB8HXsCPK2PBNsemvtgfgIbETE6jXUufmlKSRIw", 
                        # base_url="https://api.apiyi.com/v1")
                        base_url="https://api.agicto.cn/v1")
        # print(self.model)
        mu = None
        for k in range(max_K):
            try:
                response = client.chat.completions.create(
                    model="gpt-5-nano",
                    messages=message,
                    temperature=0.3,
                    max_tokens=16384
                )
                # print(message)
                # print(response)
                if response.choices and len(response.choices) > 0:
                    message_content = response.choices[0].message.content
                    print(message_content)
                    # with open("mut.txt",'w') as f:
                    #     f.write(message_content)
                    if message_content:
                        # test = self._extract_code(message_content)
                        pattern = r'\[.*\]'
                        print("Generated text real",message_content)
                        generated_text = re.findall(pattern,message_content,re.DOTALL)
                        print("Generated text",generated_text)
                        # if not test.strip():
                        #     print(f"第 {k} 次尝试失败")
                        #     time.sleep(1)
                        #     continue
                        # try:
                        mu=json.loads(generated_text[0])
                        with open("mut2.json", 'w', encoding='utf-8') as f:
                            json.dump(mu, f, indent=2, ensure_ascii=False)
                        print(mu)
                        
                        
                        # tests.append(test)
                        break
                        # message.append({"role": "assistant", "content": test})
                        # message.append({"role": "user",
                                        # "content": "Generate another test method for the function under test. Your answer must be different from previously-generated test cases and should cover different statements and branches."})

            except openai.RateLimitError:
                wait_time = 2 ** k  # 指数退避
                print(f"速率限制，等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)

            except openai.APIError as e:
                print(f"API错误: {e}")
                if k >= 1:
                    raise
                time.sleep(1)

            except Exception as e:
                print(f"未知错误: {e}")
                if k >= 1:
                    raise
                time.sleep(1)

        return mu


def replace_by_line(text, target_line, old, new):
    """
    按 mutant 给出的行号替换，避免同一语句多次出现时误替换到第一处。
    行号使用 1-based；仅替换目标行的第一次 old->new。
    """
    if target_line is None:
        return None
    try:
        line_no = int(target_line)
    except (TypeError, ValueError):
        return None

    lines = text.splitlines(keepends=True)
    idx = line_no - 1
    if idx < 0 or idx >= len(lines):
        return None

    line_text = lines[idx]
    if old not in line_text:
        return None

    lines[idx] = line_text.replace(old, new, 1)
    return "".join(lines)


def apply_mutation_in_function(source_text, function_code, relative_line, precode, aftercode):
    """
    mutant 的 line 是相对 function_code 的行号（1-based），不是相对整个文件。
    先在源码中定位 function_code，再用相对行号映射到文件绝对行号进行替换。
    """
    if not function_code:
        return None

    start_idx = source_text.find(function_code)
    if start_idx < 0:
        return None

    start_line = source_text[:start_idx].count("\n") + 1
    try:
        abs_line = start_line + int(relative_line) - 1
    except (TypeError, ValueError):
        return None

    return replace_by_line(source_text, abs_line, precode, aftercode)

def write_mut(src_file, function_code, relative_line, precode, aftercode):
    with open(src_file, 'r') as f:
        src = f.read()

    mut_code = apply_mutation_in_function(src, function_code, relative_line, precode, aftercode)
    # print(src)
    # print(function_code)
    print(mut_code)
    with open(src_file, "w", encoding="utf-8") as f:
        f.write(mut_code)

def run_mut(data_path):
    with open(data_path, 'r') as f:
        data = json.load(f)

    for d in data:
        muts = d.get('mut', [])
        if not muts:
            continue
        for mut in muts:
            src_file = d['src_file']
            function_code = d['code']
            relative_line = mut['line']
            precode = mut['precode']
            aftercode = mut['aftercode']
            write_mut(src_file, function_code, relative_line, precode, aftercode)
            result = subprocess.run(
                # ["mvn", "compile", "-Drat.skip=true"],   # -q 静默模式，只输出关键信息
                ["javac", "-sourcepath", "src/main/java", src_file],  # 编译单个文件
                capture_output=True,
                text=True
            )
            print("=== STDOUT ===")
            print(result.stdout)
            if result.returncode == 0:
                print("Maven 编译成功")
                print(precode, "->", aftercode)
                break
            else:
                print("Maven 编译失败")
                print(result.stderr)
                write_mut(src_file, function_code, relative_line, aftercode, precode)  # 回退修改
                

if __name__ == "__main__":
    # parser = ArgumentParser()
    
    # parser.add_argument(
    #     "--data-path",
    #     type=str,
    #     help="Path to data.",
    # )
    # args = parser.parse_args()

    # run_mut(args.data_path)
    prompt = gen_prompt(20, "public CharSequence pad(final boolean addIndent, final CharSequence text) {\n        if (text.length() >= maxWidth) {\n            return text;\n        }\n        String indentPad;\n        String rest;\n        final StringBuilder sb = new StringBuilder();\n        switch (alignment) {\n        case CENTER:\n            int padLen;\n            if (maxWidth == UNSET_MAX_WIDTH) {\n                padLen = addIndent ? indent : 0;\n            } else {\n                padLen = maxWidth - text.length();\n            }\n            final int left = padLen / 2;\n            indentPad = Util.repeatSpace(left);\n            rest = Util.repeatSpace(padLen - left);\n            sb.append(indentPad).append(text).append(rest);\n            break;\n        case LEFT:\n        case RIGHT:\n        default: // default should never happen. It is here to keep code coverage happy.\n            if (maxWidth == UNSET_MAX_WIDTH) {\n                indentPad = addIndent ? Util.repeatSpace(indent) : \"\";\n                rest = \"\";\n            } else {\n                int restLen = maxWidth - text.length();\n                if (addIndent && restLen > indent) {\n                    indentPad = Util.repeatSpace(indent);\n                    restLen -= indent;\n                } else {\n                    indentPad = \"\";\n                }\n                rest = Util.repeatSpace(restLen);\n            }\n\n            if (alignment == Alignment.LEFT) {\n                sb.append(indentPad).append(text).append(rest);\n            } else {\n                sb.append(indentPad).append(rest).append(text);\n            }\n            break;\n        }\n        return sb.toString();\n    }")
    call_llm(prompt)

