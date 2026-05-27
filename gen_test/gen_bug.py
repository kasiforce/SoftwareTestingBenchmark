import json
import re
import time
import openai
from openai import OpenAI

# system_prompt_modify = f"""
#   You are a software developer doing chaos monkey testing.
#   Your job is to rewrite a function such that it introduces a logical, subtle, plausible, human-like bug that will break existing unit test(s) in a codebase.

#   To this end, some kinds of bugs you might introduce include:
#     - "Alter calculation order for incorrect results: Rearrange the sequence of operations in a calculation to subtly change the output (e.g., change (a + b) * c to a + (b * c))."
#     - "Introduce subtle data transformation errors: Modify data processing logic, such as flipping a sign, truncating a value, or applying the wrong transformation function."
#     - "Change variable assignments to alter computation state: Assign a wrong or outdated value to a variable that affects subsequent logic."
#     - "Mishandle edge cases for specific inputs: Change handling logic to ignore or improperly handle boundary cases, like an empty array or a null input."
#     - "Modify logic in conditionals or loops: Adjust conditions or loop boundaries (e.g., replace <= with <) to change the control flow."
#     - "Introduce off-by-one errors in indices or loop boundaries: Shift an index or iteration boundary by one, such as starting a loop at 1 instead of 0."
#     - "Adjust default values or constants to affect behavior: Change a hardcoded value or default parameter that alters how the function behaves under normal use."
#     - "Reorder operations while maintaining syntax: Rearrange steps in a process so the function produces incorrect intermediate results without breaking the code."
#     - "Swallow exceptions or return defaults silently: Introduce logic that catches an error but doesn't log or handle it properly, leading to silent failures."
  
#   Tips about the bug-introducing task:
#     - "It should not cause compilation errors."
#     - "It should not be a syntax error."
#     - "It should be subtle and challenging to detect."
#     - "It should not modify the function signature."
#     - "It should not modify the documentation significantly."
#     - "Please DO NOT INCLUDE COMMENTS IN THE CODE indicating the bug location or the bug itself."
#     - "You can write different kinds of bugs, but please make sure each bugged version only introduces one bug that differs from others."


#   Your answer should be formatted as follows:

#   [{{"BuggedCode1": "bugged_code", "Explanation": "explanation", "Failing_tests": ["test1", "test2"]}}, {{"BuggedCode2": "bugged_code", "Explanation": "explanation", "Failing_tests": ["test1", "test2"]}}, ...]
# """

system_prompt_modify = f"""
  You are a software developer doing chaos monkey testing.
  Your job is to rewrite a function such that it introduces a subtle, plausible, human-like bug that will break existing unit test(s) in a codebase.

  You MUST select a strategy from the pool below to guide your each mutation:
    A. API Specifications & Contracts
    (e.g., Alter default parameter values; Swap argument order; Substitute exception types)
    B. Boundaries & Conditional Logic
    (e.g., Introduce off-by-one errors; Remove null checks; Invert boolean logic)
    C. Type & Data Shape
    (e.g., Break implicit type coercion; Reduce numerical precision; Confuse text/bytes encoding)
    D. I/O & Stateful Logic Sequences
    (e.g., Break state initialization/reset; Introduce sequential dependencies; Hardcode environment
    paths)
    E. Test-expectation Alignment
    (e.g., Alter error messages to fail assertions; Make implicit behaviors explicit)

  Tips about the bug-introducing task:
    - "It should not cause compilation errors."
    - "It should not be a syntax error."
    - "It should be subtle and challenging to detect."
    - "It should not modify the function signature."
    - "It should not modify the documentation significantly."
    - "Please DO NOT INCLUDE COMMENTS IN THE CODE indicating the bug location or the bug itself."


  Your answer should be formatted as follows:

  [{{"BuggedCode1": "bugged_code", "Explanation": "explanation", "Failing_tests": ["test1", "test2"]}}, {{"BuggedCode2": "bugged_code", "Explanation": "explanation", "Failing_tests": ["test1", "test2"]}}, ...]
"""



def gen_prompt_modify(function_info: dict) -> str:
    function_name = function_info['name']
    function_code = function_info['code']
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

    context = f"""
Function Information:
- Src file: {file_path}
- Function name: {function_name}
- Class: {class_info if class_name else 'Standalone function'}
- Is async: {function_info.get('is_async', False)}

Function Code:
```java
{function_code}

Existing Tests:
```java
class TextStyleTest {{

    static Stream<Arguments> padTestData() {{
        final List<Arguments> lst = new ArrayList<>();
        final TextStyle.Builder builder = TextStyle.builder();
        builder.setIndent(5);
        builder.setLeftPad(5);
        builder.setMinWidth(4);
        builder.setScalable(true);

        // undefined creates result of original text + indent
        builder.setMaxWidth(TextStyle.UNSET_MAX_WIDTH);
        builder.setAlignment(TextStyle.Alignment.LEFT);
        lst.add(Arguments.of(builder.get(), "Hello world", "     Hello world"));

        builder.setAlignment(TextStyle.Alignment.RIGHT);
        lst.add(Arguments.of(builder.get(), "Hello world", "     Hello world"));

        builder.setAlignment(TextStyle.Alignment.CENTER);
        lst.add(Arguments.of(builder.get(), "Hello world", "  Hello world   "));

        // width less than text length creates result of original text
        builder.setMaxWidth(5);
        builder.setAlignment(TextStyle.Alignment.LEFT);
        lst.add(Arguments.of(builder.get(), "Hello world", "Hello world"));

        builder.setAlignment(TextStyle.Alignment.RIGHT);
        lst.add(Arguments.of(builder.get(), "Hello world", "Hello world"));

        builder.setAlignment(TextStyle.Alignment.CENTER);
        lst.add(Arguments.of(builder.get(), "Hello world", "Hello world"));

        // width greater than text length + indent creates result of text length with indent
        builder.setMaxWidth(20);
        builder.setAlignment(TextStyle.Alignment.LEFT);
        lst.add(Arguments.of(builder.get(), "Hello world         ", "     Hello world    "));

        builder.setAlignment(TextStyle.Alignment.RIGHT);
        lst.add(Arguments.of(builder.get(), "         Hello world", "         Hello world"));

        builder.setAlignment(TextStyle.Alignment.CENTER);
        lst.add(Arguments.of(builder.get(), "    Hello world     ", "    Hello world     "));

        // width greater than text length and less than text length + indent creates result of text length + pad
        builder.setMaxWidth(14);
        builder.setAlignment(TextStyle.Alignment.LEFT);
        lst.add(Arguments.of(builder.get(), "Hello world   ", "Hello world   "));

        builder.setAlignment(TextStyle.Alignment.RIGHT);
        lst.add(Arguments.of(builder.get(), "   Hello world", "   Hello world"));

        builder.setAlignment(TextStyle.Alignment.CENTER);
        lst.add(Arguments.of(builder.get(), " Hello world  ", " Hello world  "));

        return lst.stream();
    }}

    @Test
    void testDefaultStyle() {{
        final TextStyle underTest = TextStyle.DEFAULT;
        assertEquals(TextStyle.Alignment.LEFT, underTest.getAlignment());
        assertTrue(underTest.isScalable());
        assertEquals(0, underTest.getLeftPad());
        assertEquals(0, underTest.getMinWidth());
        assertEquals(TextStyle.UNSET_MAX_WIDTH, underTest.getMaxWidth());
    }}

    @ParameterizedTest(name = "{{index}} {{0}}")
    @MethodSource("padTestData")
    void testPad(final TextStyle underTest, final String unindentedString, final String indentedString) {{
        assertEquals(unindentedString, underTest.pad(false, "Hello world"), "Unindented string test failed");
        assertEquals(indentedString, underTest.pad(true, "Hello world"), "Indented string test failed");
    }}
}}
    """

    prompt = f"""
  <INPUT>
  {function_code}

  Existing Tests:
```java
final class TextHelpAppendableTest {{

    private StringBuilder sb;
    private TextHelpAppendable underTest;

    @BeforeEach
    void setUp() {{
        sb = new StringBuilder();
        underTest = new TextHelpAppendable(sb);
    }}

    @Test
    void testAdjustTableFormat() {{
        // test width smaller than header
        // @formatter:off
        final TableDefinition tableDefinition = TableDefinition.from("Testing",
                Collections.singletonList(TextStyle.builder().setMaxWidth(3).get()),
                Collections.singletonList("header"),
                // "data" shorter than "header"
                Collections.singletonList(Collections.singletonList("data"))
        );
        // @formatter:on
        final TableDefinition actual = underTest.adjustTableFormat(tableDefinition);
        assertEquals("header".length(), actual.columnTextStyles().get(0).getMaxWidth());
        assertEquals("header".length(), actual.columnTextStyles().get(0).getMinWidth());
    }}

    @Test
    void testAppendTable() throws IOException {{
        final TextStyle.Builder styleBuilder = TextStyle.builder();
        final List<TextStyle> styles = new ArrayList<>();
        styles.add(styleBuilder.setIndent(2).get());
        styles.add(styleBuilder.setIndent(0).setLeftPad(5).setAlignment(TextStyle.Alignment.RIGHT).get());
        final String[] headers = {{ "fox", "time" }};
        // @formatter:off
        final List<List<String>> rows = Arrays.asList(
                Arrays.asList("The quick brown fox jumps over the lazy dog",
                        "Now is the time for all good people to come to the aid of their country"),
                Arrays.asList("Léimeann an sionnach donn gasta thar an madra leisciúil",
                        "Anois an t-am do na daoine maithe go léir teacht i gcabhair ar a dtír")
        );
        // @formatter:on

        List<String> expected = new ArrayList<>();
        expected.add(" Common Phrases");
        expected.add("");
        expected.add("               fox                                       time                   ");
        expected.add(" The quick brown fox jumps over           Now is the time for all good people to");
        expected.add("   the lazy dog                                 come to the aid of their country");
        expected.add(" Léimeann an sionnach donn gasta       Anois an t-am do na daoine maithe go léir");
        expected.add("   thar an madra leisciúil                           teacht i gcabhair ar a dtír");
        expected.add("");

        TableDefinition table = TableDefinition.from("Common Phrases", styles, Arrays.asList(headers), rows);
        sb.setLength(0);
        underTest.setMaxWidth(80);
        underTest.appendTable(table);
        List<String> actual = IOUtils.readLines(new StringReader(sb.toString()));
        assertEquals(expected, actual, "full table failed");

        table = TableDefinition.from(null, styles, Arrays.asList(headers), rows);
        expected.remove(1);
        expected.remove(0);
        sb.setLength(0);
        underTest.appendTable(table);
        actual = IOUtils.readLines(new StringReader(sb.toString()));
        assertEquals(expected, actual);

        table = TableDefinition.from(null, styles, Arrays.asList(headers), Collections.emptyList());
        expected = new ArrayList<>();
        expected.add(" fox     time");
        expected.add("");
        sb.setLength(0);
        underTest.appendTable(table);
        actual = IOUtils.readLines(new StringReader(sb.toString()));
        assertEquals(expected, actual, "no rows test failed");
    }}

    @Test
    void testResizeTableFormat() {{
        underTest.setMaxWidth(150);
        final TableDefinition tableDefinition = TableDefinition.from("Caption",
                Collections.singletonList(TextStyle.builder().setMinWidth(20).setMaxWidth(100).get()), Collections.singletonList("header"),
                Collections.singletonList(Collections.singletonList("one")));
        final TableDefinition result = underTest.adjustTableFormat(tableDefinition);
        assertEquals(20, result.columnTextStyles().get(0).getMinWidth(), "Minimum width should not be reset");
        assertEquals(100, result.columnTextStyles().get(0).getMaxWidth(), "Maximum width should not be reset");
    }}
}}
  </INPUT>

  <IMPORTANT>As a reminder, Please DO NOT INCLUDE ANY COMMENTS IN THE CODE OR POINT OUT THE BUG IN ANY WAY.</IMPORTANT>

  OUTPUT:
    """
    print(prompt)
    return prompt


system_prompt_rewrite = """
You are a software developer and you have been asked to implement a function.

You will be given the contents of an entire file, with one or more functions defined in it.
Please implement the function(s) that are missing.
Do NOT modify the function signature, including the function name, parameters, return types, or docstring if provided.
Do NOT change any other code in the file.
You should not use any external libraries.
"""

test_file = """
package org.apache.commons.cli.help;

import java.util.function.Supplier;

/**
 * The definition for styling recommendations blocks of text. Most common usage is to style columns in a table, but may also be used to specify default styling
 * for a {@link HelpAppendable}. HelpWriters are free to ignore the TextStyle recommendations particularly where they are not supported or contradict common
 * usage.
 *
 * @since 1.10.0
 */
public final class TextStyle {

    /**
     * The alignment possibilities.
      */
    public enum Alignment {

        /**
         * Left justifies the text.
         */
        LEFT,

        /**
         * Centers the text.
         */
        CENTER,

        /**
         * Right justifies the text.
         */
        RIGHT
    }

    /**
     * The builder for the TextStyle. The default values are:
     * <ul>
     * <li>alignment = LEFT</li>
     * <li>leftPad = 0</li>
     * <li>scaling = VARIABLE</li>
     * <li>minWidth = 0</li>
     * <li>maxWidth = UNSET_MAX_WIDTH</li>
     * </ul>
     */
    public static final class Builder implements Supplier<TextStyle> {

        /** The alignment. */
        private Alignment alignment = Alignment.LEFT;

        /** The left padding. */
        private int leftPad;

        /** The subsequent line indentation. */
        private int indent;

        /** The scalable flag. Identifies text blocks that can be made narrower or wider as needed by the HelpAppendable. */
        private boolean scalable = true;

        /** The minimum width. */
        private int minWidth;

        /** The maximum width. */
        private int maxWidth = UNSET_MAX_WIDTH;

        /**
         * Constructs a new instance. The default values are:
         * <ul>
         * <li>alignment = LEFT</li>
         * <li>leftPad = 0</li>
         * <li>scaling = VARIABLE</li>
         * <li>minWidth = 0</li>
         * <li>maxWidth = UNSET_MAX_WIDTH</li>
         * </ul>
         */
        private Builder() {
        }

        @Override
        public TextStyle get() {
            return new TextStyle(this);
        }

        /**
         * Gets the currently specified indent value.
         *
         * @return The currently specified indent value.
         */
        public int getIndent() {
            return indent;
        }

        /**
         * Gets the currently specified leftPad.
         *
         * @return The currently specified leftPad.
         */
        public int getLeftPad() {
            return leftPad;
        }

        /**
         * Gets the currently specified maximum width value.
         *
         * @return The currently specified maximum width value.
         */
        public int getMaxWidth() {
            return maxWidth;
        }

        /**
         * Gets the currently specified minimum width value.
         *
         * @return The currently specified minimum width value.
         */
        public int getMinWidth() {
            return minWidth;
        }

        /**
         * Specifies if the column can be made wider or to narrower width to fit constraints of the HelpAppendable and formatting.
         *
         * @return The currently specified scaling value.
         */
        public boolean isScalable() {
            return scalable;
        }

        /**
         * Sets the alignment.
         *
         * @param alignment the desired alignment.
         * @return {@code this} instance.
         */
        public Builder setAlignment(final Alignment alignment) {
            this.alignment = alignment;
            return this;
        }

        /**
         * Sets the indent value.
         *
         * @param indent the new indent value.
         * @return {@code this} instance.
         */
        public Builder setIndent(final int indent) {
            this.indent = indent;
            return this;
        }

        /**
         * Sets the left padding.
         *
         * @param leftPad the new left padding.
         * @return {@code this} instance.
         */
        public Builder setLeftPad(final int leftPad) {
            this.leftPad = leftPad;
            return this;
        }

        /**
         * Sets the currently specified minimum width.
         *
         * @param maxWidth The currently specified maximum width.
         * @return {@code this} instance.
         */
        public Builder setMaxWidth(final int maxWidth) {
            this.maxWidth = maxWidth;
            return this;
        }

        /**
         * Sets the currently specified minimum width.
         *
         * @param minWidth The currently specified minimum width.
         * @return {@code this} instance.
         */
        public Builder setMinWidth(final int minWidth) {
            this.minWidth = minWidth;
            return this;
        }

        /**
         * Sets whether the column can be made wider or to narrower width to fit constraints of the HelpAppendable and formatting.
         *
         * @param scalable Whether the text width can be adjusted.
         * @return {@code this} instance.
         */
        public Builder setScalable(final boolean scalable) {
            this.scalable = scalable;
            return this;
        }

        /**
         * Sets all properties from the given text style.
         *
         * @param style the source text style.
         * @return {@code this} instance.
         */
        public Builder setTextStyle(final TextStyle style) {
            this.alignment = style.alignment;
            this.leftPad = style.leftPad;
            this.indent = style.indent;
            this.scalable = style.scalable;
            this.minWidth = style.minWidth;
            this.maxWidth = style.maxWidth;
            return this;
        }

    }

    /**
     * The unset value for maxWidth: {@value}.
     */
    public static final int UNSET_MAX_WIDTH = Integer.MAX_VALUE;

    /**
     * The default style as generated by the default Builder.
     */
    public static final TextStyle DEFAULT = builder().get();

    /**
     * Creates a new builder.
     *
     * @return a new builder.
     */
    public static Builder builder() {
        return new Builder();
    }

    /** The alignment. */
    private final Alignment alignment;

    /** The size of the left pad. This is placed before each line of text. */
    private final int leftPad;

    /** The size of the indent on the second and any subsequent lines of text. */
    private final int indent;

    /** The scaling allowed for the block. */
    private final boolean scalable;

    /** The minimum size of the text. */
    private final int minWidth;

    /** The maximum size of the text. */
    private final int maxWidth;

    /**
     * Constructs a new instance.
     *
     * @param builder the builder to build the text style from.
     */
    private TextStyle(final Builder builder) {
        this.alignment = builder.alignment;
        this.leftPad = builder.leftPad;
        this.indent = builder.indent;
        this.scalable = builder.scalable;
        this.minWidth = builder.minWidth;
        this.maxWidth = builder.maxWidth;
    }

    /**
     * Gets the alignment.
     *
     * @return the alignment.
     */
    public Alignment getAlignment() {
        return alignment;
    }

    /**
     * Gets the indent value.
     *
     * @return the indent value.
     */
    public int getIndent() {
        return indent;
    }

    /**
     * Gets the left padding.
     *
     * @return the left padding.
     */
    public int getLeftPad() {
        return leftPad;
    }

    /**
     * gets the maximum width.
     *
     * @return The maximum width.
     */
    public int getMaxWidth() {
        return maxWidth;
    }

    /**
     * gets the minimum width.
     *
     * @return The minimum width.
     */
    public int getMinWidth() {
        return minWidth;
    }

    /**
     * Specifies if the column can be made wider or to narrower width to fit constraints of the HelpAppendable and formatting.
     *
     * @return the scaling value.
     */
    public boolean isScalable() {
        return scalable;
    }

    
    public CharSequence pad(final boolean addIndent, final CharSequence text) {
        ```
        Functional Description: Pads a given text with spaces to fit within a specified maximum width, applying optional indentation and alignment (center, left, or right). If the text length exceeds the maximum width, it returns the original text unchanged. The method constructs a new string with the appropriate padding based on the alignment and indentation settings.\n\nArgs:\naddIndent: boolean - Indicates whether to add indentation spaces before the text.\ntext: CharSequence - The text to be padded with spaces.\n\nReturns: CharSequence - A padded string that fits within the specified maximum width, maintaining the specified alignment and indentation.\n\nPreconditions:\n1. The alignment must be set to a valid value (CENTER, LEFT, or RIGHT).\n2. maxWidth must be defined and should not be less than zero.\n3. The text parameter must not be null.\n\nPostconditions:\n1. If the text length is greater than or equal to maxWidth, the original text is returned unchanged.\n2. A new padded string is returned if the text length is less than maxWidth.\n3. The input parameters remain unchanged.\n\nInvariants:\n1. The method always returns a string representation of the padded text.\n2. The padding is determined based on the alignment and indentation settings.\n3. The method does not modify any class fields or static constants.\n\nException:\nNone - The method does not explicitly throw exceptions, but it assumes valid input as per the preconditions.
        ```
        pass;
    }

    @Override
    public String toString() {
        return String.format("TextStyle{%s, l:%s, i:%s, %s, min:%s, max:%s}", alignment, leftPad, indent, scalable, minWidth,
                maxWidth == UNSET_MAX_WIDTH ? "unset" : maxWidth);
    }
}
"""

user_prompt_rewrite = f"""
Please implement the function `public CharSequence pad(final boolean addIndent, final CharSequence text)` in the following code:

  ```
  {test_file}
  ```

  Remember, you should not modify the function signature, including the function name, parameters, return types, or docstring if provided.
  Do NOT change any other code in the file.
  Format your output as:

  Explanation:
  <explanation>

  ```java
  <func_to_write>
  ```
"""

def extract_code_block(text: str) -> str:
    pattern = r"```(?:\w+)?\n(.*?)```"
    match = re.search(pattern, text, re.DOTALL)
    return match.group(1).strip() if match else ""

def call_llm(system_prompt, prompt: str, max_K: int = 3) -> str:
        """
        调用大模型API生成测试代码

        Args:
            system_prompt: 系统提示文本
            prompt: 提示文本
            max_K: 最多生成测试用例数量

        Returns:
            生成的测试代码
        """
        message = [{"role": "system",
                    "content": system_prompt},
                   {"role": "user", "content": prompt}
                   ]
        tests = []
        client = OpenAI(api_key="sk-k9b2PKFt5xUXsYXHKikYHvFRg5fz7rSJCQcOie2pdHQUj5hZ", 
                        base_url="https://api.agicto.cn/v1")
        # print(self.model)
        mu = None
        for k in range(max_K):
            try:
                response = client.chat.completions.create(
                    model="gpt-5",
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
                        mu = json.loads(message_content)
                        # explanation = (
                        #     message_content.split("Explanation:")[-1].strip()
                        #     if "Explanation" in message_content
                        #     else message_content.split("```")[-1].strip()
                        # )
                        # bugged_code = extract_code_block(message_content)

                        # with open("bug.json", 'w', encoding='utf-8') as f:
                        #     json.dump(mu, f, indent=2, ensure_ascii=False)
                        # print(mu)
                        
                        
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

def gen_bug_modify(data_file) -> str:
    with open(data_file, 'r', encoding='utf-8') as f:
        function_info = json.load(f)

    results = []
    for func in function_info:
        # print(func)
        prompt = gen_prompt_modify(func)
        mu = call_llm(system_prompt_modify, prompt)

        result = {
            "src_code": func['code'],
            "mutations": mu
        }
        results.append(result)
    
    with open("dataset/gen_bug_modify.json", 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

def gen_bug_rewrite() -> str:
    function_info = []
    with open("dataset/gen_bug_rewrite.json", 'r', encoding='utf-8') as f:
        function_info = json.load(f)

    # results = []
    # for func in function_info:
    #     explanation, bugged_code = call_llm(system_prompt_rewrite, user_prompt_rewrite)

    #     result = {
    #         "src_code": func['code'],
    #         "explanation": explanation,
    #         "bugged_code": bugged_code
    #     }
    #     results.append(result)
    mu = call_llm(system_prompt_rewrite, user_prompt_rewrite)
    result = {
            "src_code": "public CharSequence pad(final boolean addIndent, final CharSequence text) {\n        if (text.length() >= maxWidth) {\n            return text;\n        }\n        String indentPad;\n        String rest;\n        final StringBuilder sb = new StringBuilder();\n        switch (alignment) {\n        case CENTER:\n            int padLen;\n            if (maxWidth == UNSET_MAX_WIDTH) {\n                padLen = addIndent ? indent : 0;\n            } else {\n                padLen = maxWidth - text.length();\n            }\n            final int left = padLen / 2;\n            indentPad = Util.repeatSpace(left);\n            rest = Util.repeatSpace(padLen - left);\n            sb.append(indentPad).append(text).append(rest);\n            break;\n        case LEFT:\n        case RIGHT:\n        default: \n            if (maxWidth == UNSET_MAX_WIDTH) {\n                indentPad = addIndent ? Util.repeatSpace(indent) : \"\";\n                rest = \"\";\n            } else {\n                int restLen = maxWidth - text.length();\n                if (addIndent && restLen > indent) {\n                    indentPad = Util.repeatSpace(indent);\n                    restLen -= indent;\n                } else {\n                    indentPad = \"\";\n                }\n                rest = Util.repeatSpace(restLen);\n            }\n\n            if (alignment == Alignment.LEFT) {\n                sb.append(indentPad).append(text).append(rest);\n            } else {\n                sb.append(indentPad).append(rest).append(text);\n            }\n            break;\n        }\n        return sb.toString();\n    }",
            "mutation": mu,
        }
    function_info.append(result)
    with open("dataset/gen_bug_rewrite.json", 'w', encoding='utf-8') as f:
        json.dump(function_info, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    gen_bug_modify("dataset/tem.json")
