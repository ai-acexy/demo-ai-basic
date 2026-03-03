# -*- coding: utf-8 -*-
from openai import OpenAI
import json

from openai.types.chat import ChatCompletionUserMessageParam, ChatCompletionToolParam
from openai.types.shared_params import FunctionDefinition

# 1. 初始化客户端 (对接本地 Ollama 或 OpenAI 官方)
client = OpenAI(
    base_url="http://127.0.0.1:11434/v1",  # 假设你还在用 Ollama
    api_key="ollama"
)


# 2. 定义我们的“工具”函数（这就是模拟的执行层）
def get_current_weather(location):
    """获取指定城市的模拟天气数据"""
    # 这里的数据通常来自真实的 API (如 OpenWeather)
    # 模拟一个原始的、杂乱的数据源
    raw_data = {
        "London": {"temp": 15, "unit": "celsius", "humidity": "80%", "wind": "5km/h"},
        "Beijing": {"temp": 28, "unit": "celsius", "humidity": "40%", "wind": "2km/h"},
    }

    # --- Map 概念的应用 ---
    # 我们将原始数据 Map (映射) 为更简洁的结构，过滤掉不需要的信息
    weather_info = raw_data.get(location, {"temp": "unknown", "condition": "no data"})
    return json.dumps(weather_info)


weather_function = FunctionDefinition(
    name="get_current_weather",
    description="获取指定地点的实时天气情况",
    parameters={
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "城市名，例如：London"
            }
        },
        "required": ["location"],
        "additionalProperties": False,
    },
    strict=True
)

tools: list[ChatCompletionToolParam] = [
    {
        "type": "function",
        "function": weather_function
    }
]


def run_agent(user_prompt):
    print(f"用户提问: {user_prompt}")

    # 第一步：把问题和工具表交给 LLM
    messages = [{"role": "user", "content": user_prompt}]
    response = client.chat.completions.create(
        model="qwen2.5:7b",  # 确保你的模型支持 tool calling
        messages=[
            ChatCompletionUserMessageParam(
                role="user",
                content=user_prompt
            )
        ],
        tools=tools,
        tool_choice="auto"
    )

    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls

    # 第二步：判断 LLM 是否决定调用工具
    if tool_calls:
        print(">> LLM 决定调用工具...")

        # 我们可以支持多个工具调用，所以这里用循环
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)

            # 动态执行函数
            if function_name == "get_current_weather":
                function_response = get_current_weather(
                    location=function_args.get("location")
                )

                # 第三步：将工具执行结果塞回给 LLM
                messages.append(response_message)  # 把 AI 的决策存入历史
                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": function_response,
                })

        # 第四步：让 LLM 根据拿到的“天气 Content”说人话
        second_response = client.chat.completions.create(
            model="qwen2.5:7b",
            messages=messages,
        )
        return second_response.choices[0].message.content
    else:
        return response_message.content


# 测试
print("--- Agent 思考中 ---")
result = run_agent("伦敦现在天气怎么样？")
print(f"AI 回复: {result}")
