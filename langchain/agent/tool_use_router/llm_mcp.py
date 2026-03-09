# -*- coding: utf-8 -*-
import asyncio
import os
from typing import Any, cast

from langchain.agents import create_agent
from langchain_core.globals import set_debug, set_verbose
from langchain_core.messages import HumanMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

import config

# 开启详细日志
set_debug(True)
set_verbose(True)

llm = ChatOllama(
    model=config.OLLAMA_MODEL,
)


# llm = ChatOpenAI(
#     model=config.OPENAI_MODEL,
#     api_key=SecretStr(config.openai_key())
# )


def get_abs_path(relative_path):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), relative_path))


async def run(prompt):
    # 1. 结构化配置 MCP 服务器
    mcp_configs = {
        "weather_service": {
            "transport": "stdio",
            "command": "python",
            "args": [get_abs_path("../../../mcp/weather.py")]
        },
        "calc_service": {
            "transport": "stdio",
            "command": "python",
            "args": [get_abs_path("../../../mcp/calculator.py")]
        }
    }

    # 2. 初始化模型

    # 3. 初始化客户端
    client = MultiServerMCPClient(mcp_configs)

    try:
        # 提取工具
        print(">> 正在连接 MCP 服务器并加载工具...")
        tools = await client.get_tools()
        print(f">> 成功加载工具: {[t.name for t in tools]}")

        # 4. 创建 Agent
        agent = create_agent(
            llm,
            tools,
            system_prompt=config.SYS_PROMPT
        )

        print(f"Q: {prompt}")

        result = await agent.ainvoke(
            cast(Any, {"messages": [HumanMessage(content=prompt)]})
        )

        messages = result["messages"]
        for message in messages:
            message.pretty_print()

        # 5. 安全地获取回复内容
        if result.get("messages"):
            print(f"\nAI: {result['messages'][-1].content}")
        else:
            print("\nAI: 未生成回复。")

    except Exception as e:
        print(f"\n运行中出现异常: {e}")


if __name__ == "__main__":
    prompt = "北京和伦敦昨天的天气如何，顺便计算18.23加12.3等于多少"
    asyncio.run(run(prompt))
