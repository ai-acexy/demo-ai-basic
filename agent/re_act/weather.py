# -*- coding: utf-8 -*-
import json
import config

from openai import OpenAI
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionToolParam,
    ChatCompletionToolMessageParam, ChatCompletionUserMessageParam, ChatCompletionSystemMessageParam,
)
from openai.types.shared_params import FunctionDefinition

MODEL_NAME = "qwen2.5:7b"
client = OpenAI(
    base_url="http://127.0.0.1:11434/v1",
    api_key="ollama"
)

# MODEL_NAME = "gpt-5-nano-2025-08-07"
# client = OpenAI(
#     api_key=config.get_env("OPEN_AI_API_KEY"),
# )

# 2. 定义 Tools 能力 (严格遵循源码结构)
weather_function: FunctionDefinition = {
    "name": "get_current_weather",
    "description": "获取指定地点的实时天气情况",
    "parameters": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "一个城市名称，如：Shanghai，首字母大写英文名"
            }
        },
        "required": ["location"],
        "additionalProperties": False,
    },
    "strict": True
}

tools: list[ChatCompletionToolParam] = [
    {
        "type": "function",
        "function": weather_function
    }
]


# 3. 定义模拟的外部工具执行逻辑
def get_current_weather(location: str):
    print(f"--- [本地系统] 正在调用天气接口查询: {location} ---")
    raw_data = {
        "London": {"temp": 15, "unit": "celsius", "humidity": "80%", "wind": "5km/h"},
        "Beijing": {"temp": 28, "unit": "celsius", "humidity": "40%", "wind": "2km/h"},
    }
    # 模拟 Map 处理：过滤出核心信息
    info = raw_data.get(location, {"temp": "未知", "condition": "无数据"})
    print(f"--- [本地系统] 天气信息: {info} ---")
    return json.dumps(info)


# 4. Agent 主逻辑
def run_agent(user_prompt: str):
    print(f"用户提问: {user_prompt}")

    # 显式标注类型，消除 PyCharm 对 messages 列表的黄色警告
    messages: list[ChatCompletionMessageParam] = [
        ChatCompletionSystemMessageParam(
            role="system",
            content="一个助手，简洁明了的回复，可提供适量建议，但是不反问用户问题"
        ),
        ChatCompletionUserMessageParam(role="user", content=user_prompt)
    ]
    # 第一步：初次请求，让 LLM 决定是否调用工具
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )

    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls

    # 第二步：检查是否需要调用工具
    if tool_calls:
        print(">> LLM 决定发起 Tool Call...")

        # 把 AI 产生的包含 tool_calls 的 message 放入历史
        print(response_message.model_dump(exclude_none=True))
        messages.append(response_message.model_dump(exclude_none=True))

        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)

            if function_name == "get_current_weather":
                # 执行真实函数
                obs_content = get_current_weather(location=function_args.get("location"))

                # 构造 Tool 角色消息并标注类型
                tool_msg: ChatCompletionToolMessageParam = {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "content": obs_content,
                }
                messages.append(tool_msg)

        # 第三步：把执行结果塞回给 LLM，获取最终回复
        print(">> 结果已返回，LLM 正在组织语言...")
        second_response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
        )
        return second_response.choices[0].message.content

    else:
        # 如果不需要工具调用3，直接返回文本
        return response_message.content


# 测试执行
if __name__ == "__main__":
    try:
        final_answer = run_agent("北京现在天气怎么样？")
        # final_answer = run_agent("中国国土面积多大？")
        print(f"\nAI: {final_answer}")
    except Exception as e:
        print(f"\n运行出错: {e}")
