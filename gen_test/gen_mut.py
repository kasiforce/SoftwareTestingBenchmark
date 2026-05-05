import os 
import json
import re
import time
import openai
from openai import OpenAI

def gen_prompt(mut_num, code):
    prompt="""    
Below is the original code from a Java project. your task is to generate %s mutants in original code(notice:mutant refers to mutant in software engineering, i.e. making subtle alterations to the original code):
code:java```
%s\n
```

as follows are some examples of mutants which you can refer to:
    {
    "precode": "n = (n & (n - 1));",
    "aftercode": " n = (n ^ (n - 1));"                                        
    },
    {
    "precode": "  while (!queue.isEmpty()) {",
    "aftercode": " while (true) { "             
    },                                        
    {
    "precode": "return depth==0;",
    "aftercode": "return true;"
    },                                        
    {
    "precode": "ArrayList r = new 
    ArrayList();r.add(first).addll(subset);to_add(r)",
    "aftercode": "to_add.addAll(subset);"
    },                               
    {
    "precode": "c = bin_op.apply(b,a);",
    "aftercode": "c = bin_op.apply(a,b);",    
    },                              
    {
    "precode":"while (Math.abs(x-approx*approx) > epsilon) { "     
    "aftercode": " while (Math.abs(x-approx) > epsilon) {"
    },                          
#Requirement:
1.Provide generated mutants directly
2.A mutation can only occur on one line
3.Your output must be like:
"
[
    {
        "id":,
        "line":,
        "precode":"",
        "aftercode":""
    }
]
"(both brackets are required)
Where "id" stand for mutant serlal number,"Line" represent the line number of the mutated(please refer to the original code line number),"precode" represent the line of code before mutation and it can't be empty,"aftercode" represent the line of code after mutation
4.Prohibit generating the exact same mutants
5.Do not generate equivalent mutants: for example generating on comments are completely useless.
6.all write in a json file
7.Please ensure that your mutant contains ONLY ONE LINE and pay attention to line breaks. Some statements may be split into two lines. 
"""%(min(mut_num,10),code)

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
        client = OpenAI(api_key="", 
                        # base_url="https://api.apiyi.com/v1")
                        base_url="https://api.agicto.cn/v1")
        # print(self.model)
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
                        # with open("mut.json", 'w', encoding='utf-8') as f:
                        #     json.dump(mu, f, indent=2, ensure_ascii=False)
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



