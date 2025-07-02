import os
import openai
from typing import Optional

# 仍然建议使用环境变量来管理你的 API 密钥
# 在终端中运行: export OPENAI_API_KEY='your_aliyun_bailian_api_key'
ALIYUN_API_KEY = os.getenv("OPENAI_API_KEY")
ALIYUN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/" # 阿里云百炼的 Base URL

def get_llm_response(
    prompt: str,
    model_name: str,
    system_prompt: str = "你是一个乐于助人的AI助手。",
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    temperature: float = 0.7,
) -> Optional[str]:
    """
    使用兼容OpenAI接口的自定义模型服务（如阿里云百炼）进行通用问答。

    :param prompt: 您提供给模型的用户提示词（问题或指令）。
    :param model_name: 您在模型服务上部署的模型名称（例如 qwen-turbo）。
    :param system_prompt: 系统提示词，用于设定AI的角色和行为。
    :param api_key: 您的模型服务 API Key。如果为 None，则尝试从环境变量 'OPENAI_API_KEY' 读取。
    :param base_url: 您的模型服务 API 的 Base URL。如果为 None，则使用默认的阿里云百炼地址。
    :param temperature: 控制模型输出的随机性，0.0-2.0之间。值越高，回答越有创意。
    :return: 模型的文本响应，如果失败则返回 None。
    """
    # 优先使用函数传入的参数，否则使用全局或环境变量中的值
    key = api_key if api_key else ALIYUN_API_KEY
    url = base_url if base_url else ALIYUN_BASE_URL

    if not key:
        print("错误：API Key 未提供。请通过函数参数或设置 'OPENAI_API_KEY' 环境变量提供。")
        return None
    if not url:
        print("错误：Base URL 未提供。")
        return None

    try:
        # 1. 初始化客户端，并指定你的 key 和 base_url
        client = openai.OpenAI(
            api_key=key,
            base_url=url
        )

        # 2. 构建发送给API的消息体
        #    这里的 'user' 角色的内容就是您传入的 prompt
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]

        # 3. 调用 chat completions 接口
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=4096,  # 可根据需要调整
        )

        # 4. 提取并返回模型的回答
        answer = response.choices[0].message.content.strip()
        return answer

    except openai.APIConnectionError as e:
        print(f"API 连接错误：请检查 Base URL '{url}' 是否正确以及网络连接。")
        print(f"错误详情: {e.__cause__}")
    except openai.AuthenticationError:
        print("API 认证错误：请检查你的 API Key 是否正确或有效。")
    except openai.RateLimitError:
        print("请求频率超限：您向API发送请求的频率过快。")
    except Exception as e:
        print(f"发生未知错误: {e}")
        
    return None

# --- 使用示例 ---
if __name__ == '__main__':
    # --- 请在这里配置你的信息 ---
    # 你的阿里云百炼 API Key。强烈建议通过环境变量设置。
    my_api_key = "zxczc" 

    # 你在阿里云百炼上部署并开通公网访问的模型服务名称
    my_model_name = "qwen-turbo" # 例如 "qwen-turbo"

    # 阿里云百炼的 Base URL
    my_base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1/"
    
    # --- 示例 1: 提出一个开放性问题 ---
    print("--- 示例 1: 开放性问题 ---")
    my_prompt_1 = "请用通俗易懂的语言解释一下什么是“云计算”，并举一个生活中的例子。"
    
    response_1 = get_llm_response(
        prompt=my_prompt_1,
        model_name=my_model_name,
        api_key=my_api_key,
        base_url=my_base_url
    )

    if response_1:
        print(f"我的问题: {my_prompt_1}")
        print(f"AI的回答: \n{response_1}\n")
    else:
        print("获取回答失败。\n")

    # --- 示例 2: 扮演角色并完成任务 ---
    print("--- 示例 2: 扮演角色 ---")
    # 通过修改 system_prompt 来让AI扮演特定角色
    system_role_prompt = "你是一位资深的程序员和技术博主，你的回答专业、严谨且富有条理。"
    my_prompt_2 = "我想学习Python，请为我规划一个为期一个月的学习路线图，从入门到能够写一个简单的爬虫程序。"

    response_2 = get_llm_response(
        prompt=my_prompt_2,
        model_name=my_model_name,
        system_prompt=system_role_prompt, # 传入自定义的 system prompt
        api_key=my_api_key,
        base_url=my_base_url,
        temperature=0.5 # 对于规划类任务，可以稍微降低温度
    )

    if response_2:
        print(f"我的问题: {my_prompt_2}")
        print(f"AI的回答: \n{response_2}\n")
    else:
        print("获取回答失败。\n")