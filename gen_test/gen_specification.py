import json
import openai
from openai import OpenAI
import os
import time
from typing import List, Dict, Any
import logging
import glob
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed

# system_prompt = """You are an expert software engineer and technical documentation specialist. Your task is to generate detailed technical specifications for Python methods based on provided code and context.

# You will receive:
# 1. Method information (name, full code)
# 2. If it is a class method, it will provide the Class information (name, constructor, fields)


# Your response MUST follow this exact format:

# Functional Description: <Provide a 2-3 sentence description of the method's purpose, algorithm, and role in the system.>

# Args:
# <parameter_name>: <type> - <detailed_description>

# Returns: <return_type> - <description_of_return_value_meaning>

# Preconditions:
# <condition>

# Postconditions:
# <condition>

# Invariants:
# <invariant>

# Exception:
# <exception_type> - <trigger_condition>

# IMPORTANT RULES:
# 1. Keep each section concise but comprehensive
# 2. Use bullet points or numbered lists within sections
# 3. For helper functions mentioned in code, infer their purpose from names and context
# 4. Focus on practical information useful for developers
# 5. Do not include any additional explanations, headers, or formatting beyond the specified structure
# 6. If information is missing from the input, state "None" or make reasonable inferences


# ### Example 1:
# Input:
# def default_format(val):
#     # Create numpy dtype so that numpy formatting will work.
#     components = val.components
#     values = tuple(getattr(val, component).value for component in components)
#     a = np.empty(
#         getattr(val, "shape", ()),
#         [(component, value.dtype) for component, value in zip(components, values)],
#     )
#     for component, value in zip(components, values):
#         a[component] = value
#     return str(a)

# Output:
# Functional Description: Converts a structured data object into a formatted string representation using numpy array formatting. Extracts components and their values from the input object, creates a structured numpy array with matching dtypes, and returns the string representation of the array.

# Args:
# val: object - A structured data object that must have a 'components' attribute (iterable of component names) and each component must have a 'value' attribute with a 'dtype' property; optionally may have a 'shape' attribute

# Returns: str - String representation of a numpy structured array containing the values from each component of the input object

# Preconditions:
# 1. val must have a 'components' attribute that is iterable and returns component names
# 2. For each component name in val.components, getattr(val, component) must return an object with a 'value' attribute
# 3. Each component's value must have a 'dtype' attribute compatible with numpy dtype specification
# 4. numpy module must be available as 'np'
# 5. val may optionally have a 'shape' attribute, which will be used for the array shape

# Postconditions:
# 1. Returns a string representation of a numpy structured array
# 2. The output string contains all component values from the input object
# 3. The numpy array is created but not stored or returned (only its string representation)
# 4. Original val object remains unchanged

# Invariants:
# 1. Number of array fields equals number of components in val.components
# 2. Array field names match component names
# 3. Each field's dtype matches the corresponding component's value.dtype
# 4. If val has shape attribute, array shape matches val.shape; otherwise shape is ()
# 5. The method does not modify any class or instance state (static method)

# Exception:
# AttributeError - If val lacks 'components' attribute or any component lacks 'value' attribute
# TypeError - If components is not iterable, or if value.dtype is not a valid dtype
# ValueError - If creating numpy array with given dtypes fails
# KeyError - If component name is invalid for numpy field naming


# ### Example 2:
# Input:
# class RGBImageMapping:
#     def __init__(
#         self, interval=ManualInterval(vmin=0, vmax=None), stretch=LinearStretch()
#     ):
#         try:
#             len(interval)
#         except TypeError:
#             interval = 3 * [interval]
#         if len(interval) != 3:
#             raise ValueError("please provide 1 or 3 instances for interval.")

#         self.intervals = interval
#         self.stretch = stretch

#     def make_rgb_image(self, image_r, image_g, image_b, output_dtype=np.uint8):
#         if output_dtype not in _OUTPUT_IMAGE_FORMATS:
#             raise ValueError(f"'output_dtype' must be one of {_OUTPUT_IMAGE_FORMATS}!")

#         image_r = np.asarray(image_r)
#         image_g = np.asarray(image_g)
#         image_b = np.asarray(image_b)

#         if (image_r.shape != image_g.shape) or (image_g.shape != image_b.shape):
#             msg = "The image shapes must match. r: {}, g: {} b: {}"
#             raise ValueError(msg.format(image_r.shape, image_g.shape, image_b.shape))

#         image_rgb = self.apply_mappings(image_r, image_g, image_b)
#         if np.issubdtype(output_dtype, float):
#             conv_images = self._convert_images_to_float(image_rgb, output_dtype)
#         elif np.issubdtype(output_dtype, np.unsignedinteger):
#             conv_images = self._convert_images_to_uint(image_rgb, output_dtype)

#         return np.dstack(conv_images)

# Output:
# Functional Description: Converts three separate grayscale image arrays (red, green, blue channels) into a single RGB image array with specified output data type. Applies interval mapping and stretching transformations to each channel, validates input shapes and output format, and stacks the processed channels along the depth axis.

# Args:
# self: RGBImageMapping - Instance with intervals and stretch attributes for channel mapping
# image_r: array-like - Input data for red channel, will be converted to numpy array
# image_g: array-like - Input data for green channel, will be converted to numpy array
# image_b: array-like - Input data for blue channel, will be converted to numpy array
# output_dtype: dtype, optional (default=np.uint8) - Desired data type for output image; must be in _OUTPUT_IMAGE_FORMATS

# Returns: numpy.ndarray - 3D array with shape (height, width, 3) containing the stacked RGB channels in the specified output data type

# Preconditions:
# 1. self.intervals must be properly initialized (list of 3 interval objects)
# 2. self.stretch must be properly initialized
# 3. image_r, image_g, image_b must be convertible to numpy arrays
# 4. All three input images must have identical shapes after conversion
# 5. output_dtype must be a valid numpy dtype and present in _OUTPUT_IMAGE_FORMATS
# 6. Helper methods (apply_mappings, _convert_images_to_float, _convert_images_to_uint) must be defined
# 7. numpy must be available as 'np'

# Postconditions:
# 1. Returns a 3D numpy array with shape (height, width, 3) where the third dimension represents RGB channels
# 2. Output array has the specified output_dtype (float or unsigned integer)
# 3. Input arrays are not modified (converted to numpy arrays if needed)
# 4. self instance state remains unchanged
# 5. Each channel has had interval mapping and stretching applied via apply_mappings

# Invariants:
# 1. Output array always has 3 channels (R, G, B) in that order
# 2. Output shape preserves the spatial dimensions of input images
# 3. All three input arrays undergo identical processing steps
# 4. The method only supports float and unsigned integer output types (per np.issubdtype checks)
# 5. Channel ordering in output matches input parameter ordering (R, G, B)

# Exception:
# ValueError - If output_dtype is not in _OUTPUT_IMAGE_FORMATS
# ValueError - If input images have mismatching shapes after conversion to arrays
# TypeError - If inputs cannot be converted to numpy arrays
# AttributeError - If required helper methods are not defined
# ValueError - If apply_mappings or conversion methods fail internally
# NotImplementedError - If output_dtype is neither float nor unsigned integer (though code doesn't explicitly handle this case)
# """


# system_prompt = """You are an expert software engineer and technical documentation specialist. Your task is to generate detailed technical specifications for Java methods based on provided code and context.

# You will receive:
# 1. Method information (name, full code)
# 2. If it is a class method, it will provide the Class information (name, constructor, fields)


# Your response MUST follow this exact format:

# Functional Description: <Provide a 2-3 sentence description of the method's purpose, algorithm, and role in the system.>

# Args:
# <parameter_name>: <type> - <detailed_description>

# Returns: <return_type> - <description_of_return_value_meaning>

# Preconditions:
# <condition>

# Postconditions:
# <condition>

# Invariants:
# <invariant>

# Exception:
# <exception_type> - <trigger_condition>

# IMPORTANT RULES:
# 1. Keep each section concise but comprehensive
# 2. Use bullet points or numbered lists within sections
# 3. For helper functions mentioned in code, infer their purpose from names and context
# 4. Focus on practical information useful for developers
# 5. Do not include any additional explanations, headers, or formatting beyond the specified structure
# 6. If information is missing from the input, state "None" or make reasonable inferences


# ### Example 1:
# Input: 
# public class FlagValidatorClass implements ConstraintValidator<FlagValidator,Integer> {
#     @Override
#     public boolean isValid(Integer value, ConstraintValidatorContext constraintValidatorContext) {
#         boolean isValid = false;
#         if(value==null){
#             //当状态为空时使用默认值
#             return true;
#         }
#         for(int i=0;i<values.length;i++){
#             if(values[i].equals(String.valueOf(value))){
#                 isValid = true;
#                 break;
#             }
#         }
#         return isValid;
#     }
# }

# Output:
# Functional Description: Validates whether an Integer value is contained within the predefined list of allowed string values. Returns true for null values (treating them as valid default), otherwise checks if the string representation of the integer matches any value in the configured values array.

# Args:
# value: Integer - The integer value to validate; can be null
# constraintValidatorContext: ConstraintValidatorContext - The validation context providing contextual data and operations

# Returns: boolean - True if the value is null OR if its string representation matches any value in the values array; false otherwise

# Preconditions:
# 1. The validator must be properly initialized via initialize() method before calling isValid()
# 2. The values array must be populated from FlagValidator annotation configuration
# 3. FlagValidator annotation must define at least one value in its value() array
# 4. constraintValidatorContext must be a valid ConstraintValidatorContext instance

# Postconditions:
# 1. Returns a boolean validation result without modifying any state
# 2. Input parameters remain unchanged
# 3. Validator instance state (values array) remains unchanged
# 4. The validation context is not modified

# Invariants:
# 1. Null values always return true (treated as valid default)
# 2. Validation is case-sensitive (uses String.equals())
# 3. Only exact string matches are considered valid
# 4. The method is idempotent (same inputs produce same output)
# 5. values array length and content remain constant during validation

# Exception:
# NullPointerException - If values array is null when method is called (though initialize() should prevent this)
# NumberFormatException - If String.valueOf(value) fails (though Integer.toString() should not fail)
# IllegalStateException - If validator is not properly initialized before use


# ### Example 2:
# Input:
# public class JwtAuthenticationTokenFilter extends OncePerRequestFilter {
#     @Override
#     protected void doFilterInternal(HttpServletRequest request,
#                                     HttpServletResponse response,
#                                     FilterChain chain) throws ServletException, IOException {
#         String authHeader = request.getHeader(this.tokenHeader);
#         if (authHeader != null && authHeader.startsWith(this.tokenHead)) {
#             String authToken = authHeader.substring(this.tokenHead.length());// The part after "Bearer "
#             String username = jwtTokenUtil.getUserNameFromToken(authToken);
#             LOGGER.info("checking username:{}", username);
#             if (username != null && SecurityContextHolder.getContext().getAuthentication() == null) {
#                 UserDetails userDetails = this.userDetailsService.loadUserByUsername(username);
#                 if (jwtTokenUtil.validateToken(authToken, userDetails)) {
#                     UsernamePasswordAuthenticationToken authentication = new UsernamePasswordAuthenticationToken(userDetails, null, userDetails.getAuthorities());
#                     authentication.setDetails(new WebAuthenticationDetailsSource().buildDetails(request));
#                     LOGGER.info("authenticated user:{}", username);
#                     SecurityContextHolder.getContext().setAuthentication(authentication);
#                 }
#             }
#         }
#         chain.doFilter(request, response);
#     }
# }

# Output:
# Functional Description: Processes HTTP requests to extract and validate JWT authentication tokens from request headers. If a valid token is found, extracts username, loads user details, creates an authentication object, and sets it in Spring Security context. Always continues the filter chain regardless of authentication outcome.

# Args:
# request: HttpServletRequest - The HTTP request object containing headers including potential JWT token
# response: HttpServletResponse - The HTTP response object for potential response modification
# chain: FilterChain - The filter chain to continue processing after authentication logic

# Returns: void - Method does not return a value but may set authentication in SecurityContextHolder and always continues the filter chain

# Preconditions:
# 1. The filter must be properly configured with tokenHeader and tokenHead values (e.g., "Authorization" and "Bearer ")
# 2. jwtTokenUtil must be properly initialized and able to extract usernames and validate tokens
# 3. userDetailsService must be properly configured to load user details by username
# 4. SecurityContextHolder must be accessible and not already contain authentication for this request
# 5. HTTP request must contain the appropriate header if authentication is required

# Postconditions:
# 1. If valid JWT token is present and valid, SecurityContextHolder will contain authentication for the user
# 2. The filter chain will always be continued via chain.doFilter()
# 3. Request and response objects are passed unchanged to the next filter/servlet
# 4. Authentication details include user authorities and web authentication details from the request
# 5. Log entries are created for username checking and successful authentication

# Invariants:
# 1. Filter chain is always continued (chain.doFilter() is always called)
# 2. Existing authentication in SecurityContextHolder is never cleared by this filter
# 3. Token validation only occurs if header exists and starts with tokenHead
# 4. Authentication is only set if username is extracted and current context has no authentication
# 5. User details are loaded only after successful username extraction
# 6. Token is validated against loaded user details before setting authentication

# Exception:
# ServletException - If filter chain processing fails
# IOException - If I/O operations during filter chain processing fail
# NullPointerException - If dependencies (jwtTokenUtil, userDetailsService) are not properly injected
# IllegalArgumentException - If token extraction or validation fails internally
# AuthenticationException - If userDetailsService fails to load user or jwtTokenUtil fails validation (though these may be handled internally)
# """

system_prompt = """You are an expert software engineer and technical documentation specialist. Your task is to generate detailed technical specifications for JavaScript methods based on provided code and context.

You will receive:
1. Method information (name, full code)
2. If it is a class method, it will provide the Class information (name, constructor, fields)


Your response MUST follow this exact format:

Functional Description: <Provide a 2-3 sentence description of the method's purpose, algorithm, and role in the system.>

Args:
<parameter_name>: <type> - <detailed_description>

Returns: <return_type> - <description_of_return_value_meaning>

Preconditions:
<condition>

Postconditions:
<condition>

Invariants:
<invariant>

Exception:
<exception_type> - <trigger_condition>

IMPORTANT RULES:
1. Keep each section concise but comprehensive
2. Use bullet points or numbered lists within sections
3. For helper functions mentioned in code, infer their purpose from names and context
4. Focus on practical information useful for developers
5. Do not include any additional explanations, headers, or formatting beyond the specified structure
6. If information is missing from the input, state "None" or make reasonable inferences


### Example 1:
Input: 
function getWireframeVersion( geometry ) {

	return ( geometry.index !== null ) ? geometry.index.version : geometry.attributes.position.version;

}

Output:
Functional Description: Returns the wireframe version number of a geometry object. The version is used to detect changes in geometry data for cache invalidation. It determines whether to read the version from the geometry's index attribute (if present) or from the position attribute's version.

Args:
geometry: Object - A geometry object, typically a BufferGeometry instance, containing an index property (which may be null or a BufferAttribute) and an attributes object with a position property (a BufferAttribute).

Returns: number - The wireframe version. If geometry.index is not null, returns geometry.index.version; otherwise returns geometry.attributes.position.version.

Preconditions:
1. geometry must be a non-null object.
2. If geometry.index is not null, it must be an object with a version property.
3. If geometry.index is null, geometry.attributes must exist and geometry.attributes.position must be an object with a version property.

Postconditions:
1. The function does not modify any object state.
2. The returned version reflects the current data version of the geometry.

Invariants:
1. The version numbers are read-only and not altered by this function.
2. The logic follows the convention that wireframe version is tied to the index if present, otherwise to the position attribute.

Exception:
TypeError - If geometry is null or undefined; or if geometry.index is not null but geometry.index.version is undefined; or if geometry.index is null and geometry.attributes.position is missing or lacks a version property.



### Example 2:
Input:
class Ray {

	constructor( origin = new Vector3(), direction = new Vector3( 0, 0, - 1 ) ) {
		this.origin = origin;
		this.direction = direction;
	}

	distanceToPlane( plane ) {

		const denominator = plane.normal.dot( this.direction );

		if ( denominator === 0 ) {

			if ( plane.distanceToPoint( this.origin ) === 0 ) {

				return 0;

			}

			return null;

		}

		const t = - ( this.origin.dot( plane.normal ) + plane.constant ) / denominator;

		return t >= 0 ? t : null;

	}
}

Output:
Functional Description: Computes the distance from the ray's origin to the given plane. If the ray is parallel to the plane, returns 0 if the origin lies on the plane, otherwise returns null. Otherwise, calculates the intersection parameter t and returns t if t >= 0 (ray points toward the plane), else null. This method is used for ray-plane intersection tests.

Args:
plane: Plane - The plane to test against, expected to have normal (Vector3), constant (number) properties and a distanceToPoint method.

Returns: number|null - The distance from the ray origin to the intersection point if the ray intersects the plane in the forward direction; 0 if the origin is exactly on the plane; null if the ray is parallel and origin not on the plane, or if the intersection lies behind the ray (t < 0).

Preconditions:
1. The ray instance must have valid origin and direction properties (Vector3 instances). The direction should ideally be normalized, though the method does not enforce it.
2. The plane argument must be a valid Plane instance with normal, constant, and a distanceToPoint method.
3. The plane.normal should be normalized for accurate distance calculations, though the method does not enforce it.

Postconditions:
1. The ray and plane objects remain unchanged.
2. The returned value is based solely on the current state of the ray and plane.

Invariants:
1. The method does not modify any external state.
2. The ray's origin and direction are unchanged.
3. The plane's normal and constant are unchanged.

Exception:
TypeError - If plane is not an object; if plane.normal lacks a dot method; if plane.distanceToPoint is not a function; or if the ray's origin or direction do not have a dot method.
"""

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestCodeGenerator:
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        """
        初始化测试代码生成器

        Args:
            api_key: OpenAI API密钥
            model: 使用的模型名称
        """
        self.api_key = api_key
        self.model = model
        openai.api_key = api_key

    def generate_test_prompt(self, function_info: Dict[str, Any]) -> str:
        """
        为给定函数生成测试提示

        Args:
            function_info: 函数信息字典

        Returns:
            生成的提示字符串
        """
        function_name = function_info['name']
        function_code = function_info['code']
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

        file_path = function_info['src_file']
        test_path = function_info['test_file']

        prompt = f"""
    Please generate a technical specification for the following method.

    Method Information:
    - Name: {function_name}
    - Full Code:
    {function_code}

    Class Information:
    {class_info if class_name else 'Standalone function'}

    Please generate the specification according to the required format.
    """

        return prompt

    def call_llm(self, prompt: str, max_K: int = 1) -> str:
        """
        调用大模型API生成测试代码

        Args:
            prompt: 提示文本
            max_K: 最多生成测试用例数量

        Returns:
            生成的测试代码
        """
        message = [{"role": "system", "content": system_prompt},
                   {"role": "user", "content": prompt}
                   ]
        tests = []
        client = OpenAI(api_key=self.api_key, base_url="https://api.apiyi.com/v1")
                        # base_url="https://api.agicto.cn/v1")
        # print(self.model)
        for k in range(max_K):
            try:
                response = client.chat.completions.create(
                    model=self.model,
                    messages=message,
                    temperature=0.2,
                    max_tokens=4096
                )
                if response.choices and len(response.choices) > 0:
                    message_content = response.choices[0].message.content
                    if message_content:
                        test = self._extract_code(message_content)
                        tests.append(test)
                        message.append({"role": "assistant", "content": test})
                        message.append({"role": "user",
                                        "content": "Generate another test method for the function under test. Your answer must be different from previously-generated test cases and should cover different statements and branches."})

            except openai.RateLimitError:
                wait_time = 2 ** k  # 指数退避
                logger.warning(f"速率限制，等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)

            except openai.APIError as e:
                logger.error(f"API错误: {e}")
                if k >= 1:
                    raise
                time.sleep(1)

            except Exception as e:
                logger.error(f"未知错误: {e}")
                if k >= 1:
                    raise
                time.sleep(1)

        return tests

    def generate_test_for_function(self, function_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        为单个函数生成specification

        Args:
            function_info: 函数信息

        Returns:
            包含测试代码的增强函数信息
        """
        logger.info(f"为函数 {function_info['name']} 生成specification...")

        try:
            prompt = self.generate_test_prompt(function_info)
            specification = self.call_llm(prompt)
            result = function_info.copy()
            result['specification'] = specification

            logger.info(f"成功为 {function_info['name']} 生成specification")

        except Exception as e:
            logger.error(f"为 {function_info['name']} 生成specification失败: {e}")
            result = function_info.copy()
            result['specification'] = []

        return result

    def generate_tests_for_functions_parallel(self,
                                              functions: List[Dict[str, Any]],
                                              output_file: str = None,
                                              max_workers: int = 5,
                                              save_interval: int = 10) -> List[Dict[str, Any]]:
        """
        为函数列表批量生成specification（并行版本）

        Args:
            functions: 函数信息列表
            output_file: 输出文件路径（可选）
            max_workers: 最大并行工作线程数
            save_interval: 保存间隔（每处理多少个函数保存一次）

        Returns:
            包含测试代码的函数列表
        """
        results = []
        total = len(functions)

        # 创建线程池
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_function = {
                executor.submit(self.generate_test_for_function, func): func
                for func in functions
            }

            # 处理完成的任务
            completed_count = 0
            for future in as_completed(future_to_function):
                func = future_to_function[future]
                try:
                    result = future.result()
                    results.append(result)
                    completed_count += 1

                    # 更新进度
                    logger.info(f"处理进度: {completed_count}/{total} (完成 {func['name']})")

                    # 定期保存中间结果
                    if output_file and completed_count % save_interval == 0:
                        partial_file = f"{output_file}.partial_{completed_count}"
                        self.save_results(results, partial_file)
                        logger.info(f"已保存中间结果到: {partial_file}")

                except Exception as e:
                    logger.error(f"处理函数 {func['name']} 时发生错误: {e}")
                    # 创建错误结果
                    error_result = func.copy()
                    error_result['specification'] = []
                    results.append(error_result)
                    completed_count += 1

        # 保存最终结果
        if output_file:
            self.save_results(results, output_file)
            logger.info(f"最终结果已保存到: {output_file}")

            # 删除所有中间文件
            self._cleanup_partial_files(output_file)

        return results

    def generate_tests_for_functions_parallel_batch(self,
                                                    functions: List[Dict[str, Any]],
                                                    output_file: str = None,
                                                    max_workers: int = 5,
                                                    batch_size: int = 20,
                                                    batch_delay: int = 1) -> List[Dict[str, Any]]:
        """
        为函数列表批量生成测试代码（使用JSONL格式的中间文件）

        Args:
            functions: 函数信息列表
            output_file: 输出文件路径
            max_workers: 最大并行工作线程数
            batch_size: 每批次处理的函数数量
            batch_delay: 批次之间的延迟（秒）

        Returns:
            包含测试代码的函数列表
        """
        results = []
        total = len(functions)

        # 打开中间结果文件（JSONL格式）
        partial_file = None
        partial_fp = None

        try:
            if output_file:
                partial_file = f"{output_file}.partial.jsonl"
                # 打开文件，如果存在则覆盖
                partial_fp = open(partial_file, 'w', encoding='utf-8')
                logger.info(f"中间结果将保存到: {partial_file}")

            # 按批次处理
            for i in range(0, total, batch_size):
                batch = functions[i:i + batch_size]
                batch_num = i // batch_size + 1
                total_batches = (total + batch_size - 1) // batch_size

                logger.info(f"开始处理批次 {batch_num}/{total_batches} ({len(batch)} 个函数)")

                # 使用线程池并行处理当前批次
                batch_results = []
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    future_to_function = {
                        executor.submit(self.generate_test_for_function, func): func
                        for func in batch
                    }

                    # 处理完成的任务
                    for future in as_completed(future_to_function):
                        func = future_to_function[future]
                        try:
                            result = future.result()
                            batch_results.append(result)
                            results.append(result)

                            # 立即写入单行JSON（JSONL格式）
                            if partial_fp:
                                json_line = json.dumps(result, ensure_ascii=False)
                                partial_fp.write(json_line + '\n')
                                partial_fp.flush()  # 确保立即写入磁盘

                        except Exception as e:
                            logger.error(f"处理函数 {func['name']} 时发生错误: {e}")
                            error_result = func.copy()
                            error_result['specification'] = []
                            batch_results.append(error_result)
                            results.append(error_result)

                            if partial_fp:
                                json_line = json.dumps(error_result, ensure_ascii=False)
                                partial_fp.write(json_line + '\n')
                                partial_fp.flush()

                logger.info(f"批次 {batch_num} 处理完成，已追加到中间文件")

                # 如果不是最后一批，等待一段时间
                if i + batch_size < total and batch_delay > 0:
                    logger.info(f"等待 {batch_delay} 秒后处理下一批...")
                    time.sleep(batch_delay)

            # 保存最终结果
            if output_file:
                self.save_results(results, output_file)
                logger.info(f"最终结果已保存到: {output_file}")

                # 关闭并删除中间文件
                if partial_fp:
                    partial_fp.close()

                    # 删除中间文件
                    # self._cleanup_partial_files(partial_file)
                    os.remove(partial_file)

        except Exception as e:
            logger.error(f"处理过程中发生错误: {e}")
            if partial_fp:
                partial_fp.close()
            raise

        finally:
            # 确保文件被关闭
            if partial_fp:
                partial_fp.close()

        return results

    def _convert_jsonl_to_json(self, jsonl_file: str, json_file: str):
        """将JSONL文件转换为标准JSON文件"""
        try:
            results = []
            with open(jsonl_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        result = json.loads(line)
                        results.append(result)

            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)

            logger.info(f"已从JSONL转换到JSON: {json_file}")
        except Exception as e:
            logger.error(f"转换JSONL文件时出错: {e}")

    def _cleanup_partial_files(self, output_file: str):
        """
        清理中间结果文件

        Args:
            output_file: 最终输出文件路径
        """
        try:
            # 获取所有以output_file为前缀的中间文件
            base_name = os.path.basename(output_file)
            dir_name = os.path.dirname(output_file) or "."

            # 查找所有中间文件
            pattern = os.path.join(dir_name, f"{base_name}.partial*")
            partial_files = glob.glob(pattern)

            # 删除找到的文件
            deleted_count = 0
            for file_path in partial_files:
                try:
                    os.remove(file_path)
                    logger.info(f"已删除中间文件: {file_path}")
                    deleted_count += 1
                except Exception as e:
                    logger.warning(f"删除中间文件失败 {file_path}: {e}")

            logger.info(f"共删除 {deleted_count} 个中间文件")

        except Exception as e:
            logger.error(f"清理中间文件时出错: {e}")

    def _extract_code(self, s: str):
        # 使用 '```python' 和 '```' 来分割字符串
        parts = s.split('```')
        if len(parts) > 1:
            # 移除后面的 '```'
            code = parts[1].rsplit('```', 1)[0]
            return code.strip("\n").strip()
        return s.strip("\n").strip()

    def save_results(self, results: List[Dict[str, Any]], output_file: str):
        """
        保存结果到JSON文件

        Args:
            results: 结果列表
            output_file: 输出文件路径
        """
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            logger.info(f"结果已保存到: {output_file}")
        except Exception as e:
            logger.error(f"保存结果失败: {e}")


def main():
    # 从环境变量获取API密钥
    # api_key = "sk-Fxpi6k88q67K1Px71JKdRNFB1BvKMQpNOprjDowIFOtqQO6n"
    # api_key = "sk-WhZar4Km8tqMhzsRhzHn5oIvd6yzP7TZrMMGzkcgF4CDiTRJ"
    # api_key = "sk-BbMUtPcauaHedo7B8mv6wfT6VTwpmlSgoioVipdtbnB5cw9X"
    api_key = "sk-NEoXogd5Fg8bvg2b72702d183c1c4eFc9d9d6408B6D292D7"
    if not api_key:
        raise ValueError("请设置 OPENAI_API_KEY 环境变量")

    # 初始化生成器
    generator = TestCodeGenerator(api_key=api_key, model="gpt-4o-mini")

    # 加载函数数据
    input_file = "proton_lite.json"  # 替换为您的输入文件路径
    # input_file = "test_output.json"
    with open(input_file, 'r', encoding='utf-8') as f:
        functions_data = json.load(f)

    logger.info(f"找到 {len(functions_data)} 个需要生成测试的函数")

    # 生成测试代码 - 使用并行版本
    output_file = "proton_lite_specification_new.json"

    # 方法1: 完全并行处理
    # results = generator.generate_tests_for_functions_parallel(
    #     functions=functions_data,
    #     output_file=output_file,
    #     max_workers=5,  # 根据您的API限制调整这个值
    #     save_interval=10
    # )

    # 方法2: 批量并行处理（推荐，可控制速率）
    results = generator.generate_tests_for_functions_parallel_batch(
        functions=functions_data,
        output_file=output_file,
        max_workers=5,
        batch_size=20,
        batch_delay=2
    )


if __name__ == "__main__":
    main()