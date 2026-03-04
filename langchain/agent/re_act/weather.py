# -*- coding: utf-8 -*-
import json
from typing import Annotated

# 导入 LangChain 核心组件
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage, BaseMessage
from pydantic import SecretStr

import config


# 1. 定义工具 (使用 @tool 装饰器)
# LangChain 会自动解析函数名、注释和参数类型作为 LLM 的 Tool Schema
@tool
def get_current_weather(location: Annotated[str, "城市英文名，例如 'Beijing' 或 'London'"]):
    # 下面这段代码是tool的描述，不可以删除。langchain底层通过反射获取装配tool的描述
    """获取指定地点的实时天气情况。"""
    print(f"--- [本地系统] 正在调用天气接口查询: {location} ---")
    raw_data = {
        "London": {"temp": 15, "unit": "celsius", "humidity": "80%", "wind": "5km/h"},
        "Beijing": {"temp": 28, "unit": "celsius", "humidity": "40%", "wind": "2km/h"},
    }
    info = raw_data.get(location, {"temp": "未知", "condition": "无数据"})
    print(f"--- [本地系统] 天气信息: {info} ---")
    return json.dumps(info)


# 定义工具列表
tools = [get_current_weather]

# 2. 初始化模型并绑定工具
# 这里依然对接你的本地 Ollama
llm = ChatOpenAI(
    model="qwen2.5:7b",
    base_url="http://127.0.0.1:11434/v1",
    api_key=SecretStr("ollama"),
)

# 关键步骤：将工具绑定到 LLM 实例
llm_with_tools = llm.bind_tools(tools)


# 3. Agent 主逻辑
def run_langchain_agent(user_prompt: str):
    print(f"用户提问: {user_prompt}")

    # 使用 LangChain 的 Message 对象
    messages: list[BaseMessage] = [
        SystemMessage(content="一个助手，简洁明了的回复，可提供适量建议，但是不反问用户问题"),
        HumanMessage(content=user_prompt)
    ]

    # 第一轮请求：LLM 决定是否调用工具
    ai_msg = llm_with_tools.invoke(messages)
    messages.append(ai_msg)

    # 检查是否有 tool_calls
    if ai_msg.tool_calls:
        print(">> LLM 决定发起 Tool Call...")

        for tool_call in ai_msg.tool_calls:
            # 找到对应的工具函数并执行
            # LangChain 已经解析好了 tool_call['args']，通常不会出现嵌套字典报错
            tool_name = tool_call["name"].lower()
            tool_map = {tool.name.lower(): tool for tool in tools}

            selected_tool = tool_map[tool_name]

            # 调用工具并获得结果
            # invoke 会自动返回一个 ToolMessage 对象
            tool_output_msg = selected_tool.invoke(tool_call)

            print(f">> 工具执行结果: {tool_output_msg.content}")
            messages.append(tool_output_msg)

        # 第三步：将工具结果喂回 LLM，获取最终总结
        print(">> 结果已返回，LLM 正在组织语言...")
        final_response = llm_with_tools.invoke(messages)
        return final_response.content

    return ai_msg.content


# 测试执行
if __name__ == "__main__":
    try:
        # answer = run_langchain_agent("世界上最大的国家？")
        answer = run_langchain_agent("北京现在天气怎么样？")
        print(f"\nAI: {answer}")
    except Exception as e:
        print(f"\n运行出错: {e}")
