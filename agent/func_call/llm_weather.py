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

MODEL_NAME = "qwen3.5:2b"
client = OpenAI(
    base_url="http://127.0.0.1:11434/v1",
    api_key="ollama"
)

# MODEL_NAME = "gpt-5-nano-2025-08-07"
# client = OpenAI(
#     api_key=config.get_env("OPEN_AI_API_KEY"),
# )

# 2. 定义 Tools 能力 (严格遵循源码结构)
get_current_weather: FunctionDefinition = {
    "name": "get_current_weather",
    "description": "获取指定地点实时天气情况",
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

get_last_day_weather: FunctionDefinition = {
    "name": "get_last_day_weather",
    "description": "获取指定地点昨天天气情况",
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
        "function": get_current_weather
    },
    {
        "type": "function",
        "function": get_last_day_weather
    }
]


def get_current_weather(location: str):
    print(f"--- [本地系统] 正在调用当前天气接口查询: {location} ---")
    raw_data = {
        "London": {"temp": 15, "unit": "celsius", "humidity": "80%", "wind": "5km/h"},
        "Beijing": {"temp": 28, "unit": "celsius", "humidity": "40%", "wind": "2km/h"},
    }
    # 模拟 Map 处理：过滤出核心信息
    info = raw_data.get(location, {"temp": "未知", "condition": "无数据"})
    print(f"--- [本地系统] 天气信息: {info} ---")
    return json.dumps(info)


def get_last_day_weather(location: str):
    print(f"--- [本地系统] 正在调用昨天天气接口查询: {location} ---")
    raw_data = {
        "London": {"temp": -14, "unit": "celsius", "humidity": "80%", "wind": "5km/h"},
        "Beijing": {"temp": 26, "unit": "celsius", "humidity": "30%", "wind": "2km/h"},
    }
    # 模拟 Map 处理：过滤出核心信息
    info = raw_data.get(location, {"temp": "未知", "condition": "无数据"})
    print(f"--- [本地系统] 天气信息: {info} ---")
    return json.dumps(info)


def run_agent(user_prompt: str):
    print(f"Q: {user_prompt}")

    messages: list[ChatCompletionMessageParam] = [
        ChatCompletionSystemMessageParam(
            role="system",
            content="一个助手，简洁明了的回复，可提供适量建议，但是不反问用户问题"
        ),
        ChatCompletionUserMessageParam(role="user", content=user_prompt)
    ]

    print(f"已注入所有tools {json.dumps(tools)}")
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )

    print(f">> LLM 响应: {response}")
    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls

    # 第二步：检查是否需要调用工具
    if tool_calls:
        print(">> LLM 决定发起 Tool Call...")
        # 把 AI 产生的包含 tool_calls 的 message 放入历史
        messages.append(response_message.model_dump(exclude_none=True))

        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)

            if function_name == "get_current_weather":
                # 执行真实函数
                obs_content = get_current_weather(location=function_args.get("location"))
                print(f">> 函数执行结果: {obs_content}")

                # 构造 Tool 角色消息并标注类型
                tool_msg: ChatCompletionToolMessageParam = {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "content": obs_content,
                }
                messages.append(tool_msg)
            elif function_name == "get_last_day_weather":
                # 执行真实函数
                obs_content = get_last_day_weather(location=function_args.get("location"))
                print(f">> 函数执行结果: {obs_content}")

                # 构造 Tool 角色消息并标注类型
                tool_msg: ChatCompletionToolMessageParam = {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "content": obs_content,
                }
                messages.append(tool_msg)

        # 第三步：把执行结果塞回给 LLM，获取最终回复
        print(">> Tool Call Finish，LLM 正在组织语言...")
        second_response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
        )
        print(f">> LLM 响应: {second_response}")
        return second_response.choices[0].message.content
    else:
        # 如果不需要工具调用3，直接返回文本
        return response_message.content


# 测试执行
if __name__ == "__main__":
    try:
        # final_answer = run_agent("北京现在天气怎么样？")
        # final_answer = run_agent("北京昨天天气怎么样？")
        final_answer = run_agent("北京昨天和今天的天气各是怎么样？")
        # final_answer = run_agent("中国国土面积多大？")
        print(f"\nAI: {final_answer}")
    except Exception as e:
        print(f"\n运行出错: {e}")
