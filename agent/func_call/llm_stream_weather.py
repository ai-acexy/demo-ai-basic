# -*- coding: utf-8 -*-
import json

from openai.types.shared_params import FunctionDefinition

import config
from openai import OpenAI
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionUserMessageParam, ChatCompletionSystemMessageParam,
    ChatCompletionToolParam, ChatCompletionToolMessageParam,
)

# MODEL_NAME = "gpt-5-nano-2025-08-07"
# client = OpenAI(
#     api_key=config.get_env("OPEN_AI_API_KEY"),
# )

MODEL_NAME = config.OLLAMA_MODEL
client = OpenAI(
    base_url="http://127.0.0.1:11434/v1",
    api_key="ollama"
)

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


def run_agent_stream(user_prompt: str):
    print(f"Q: {user_prompt}")

    messages: list[ChatCompletionMessageParam] = [
        ChatCompletionSystemMessageParam(role="system", content=config.SYS_PROMPT),
        ChatCompletionUserMessageParam(role="user", content=user_prompt)
    ]

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        tools=tools,
        tool_choice="auto",
        stream=False
    )

    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls

    if tool_calls:
        print(">> LLM 决定发起 Tool Call...")
        messages.append(response_message.model_dump(exclude_none=True))

        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)

            # 动态调用函数逻辑
            if function_name == "get_current_weather":
                obs_content = get_current_weather(location=function_args.get("location"))
            elif function_name == "get_last_day_weather":
                obs_content = get_last_day_weather(location=function_args.get("location"))
            else:
                obs_content = "未找到对应工具"

            tool_msg: ChatCompletionToolMessageParam = {
                "tool_call_id": tool_call.id,
                "role": "tool",
                "content": obs_content,
            }
            messages.append(tool_msg)

        print(">> Tool Call Finish，正在生成最终回答...\nAI: ", end="", flush=True)

        stream_response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            stream=True  # 开启流式
        )

        full_answer = ""
        for chunk in stream_response:
            # 提取流式块中的内容
            content = chunk.choices[0].delta.content
            if content:
                print(content, end="", flush=True)  # 实时打印到控制台
                full_answer += content

        print()  # 换行
        return full_answer
    else:
        # 如果不需要工具调用，直接普通返回
        return response_message.content


# 测试执行
if __name__ == "__main__":
    run_agent_stream("北京昨天和今天的天气各是怎么样？")
