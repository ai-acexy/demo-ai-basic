# -*- coding: utf-8 -*-
import json
from typing import Annotated

from langchain.agents import create_agent
from langchain_core.globals import set_debug, set_verbose
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

import config

# Tool-Use Router —— 工具路由
# 最轻量级的结构，LLM 仅作为“智能分流器”。
#
# * 核心逻辑：输入 -> LLM 路由判断 -> 命中对应函数/API -> 直接输出。
# * 适用场景：功能明确的助手、简单的 API 调度中心、低延迟业务。
# * 特点：响应速度最快，成本最低，不支持复杂的多步推理。

# 开启详细日志
set_debug(True)
set_verbose(True)


@tool
def get_current_weather(location: Annotated[str, "城市英文名，例如 'Beijing'"]):
    """获取指定地点的实时天气情况。"""
    raw_data = {
        "London": {"temp": 15, "unit": "celsius", "humidity": "80%", "wind": "5km/h"},
        "Beijing": {"temp": 28, "unit": "celsius", "humidity": "40%", "wind": "2km/h"},
    }
    return json.dumps(raw_data.get(location, {"temp": "未知"}))


@tool
def get_last_day_weather(location: Annotated[str, "城市英文名，例如 'Beijing'"]):
    """获取指定地点的昨天天气情况。"""
    raw_data = {
        "London": {"temp": 11, "unit": "celsius", "humidity": "84%", "wind": "35km/h"},
        "Beijing": {"temp": 23, "unit": "celsius", "humidity": "10%", "wind": "21km/h"},
    }
    return json.dumps(raw_data.get(location, {"temp": "未知"}))


tools = [get_current_weather, get_last_day_weather]

llm = ChatOpenAI(
    model=config.OLLAMA_MODEL,
    base_url="http://127.0.0.1:11434/v1",
    api_key=SecretStr("ollama"),
)

agent = create_agent(
    llm,
    tools,
    system_prompt=config.SYS_PROMPT
)

user_prompt = "伦敦昨天和现在天气怎么样？"
print(f"Q: {user_prompt}")
result = agent.invoke({"messages": [HumanMessage(content=user_prompt)]})  # type: ignore

messages = result["messages"]
for message in messages:
    message.pretty_print()

print(f"\n\nAI: {result['messages'][-1].content}")
