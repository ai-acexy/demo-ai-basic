# -*- coding: utf-8 -*-
import asyncio
import os
from typing import Any, cast

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

import config


# 建议使用绝对路径防止子进程启动失败
def get_abs_path(relative_path):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), relative_path))


async def run_langchain_mcp_react():
    # 1. MCP 服务器配置 (对应你手动代码里的 MCP_CONFIGS)
    mcp_configs = {
        "weather": {
            "transport": "stdio",
            "command": "python",
            "args": [get_abs_path("../../../mcp/weather.py")]
        },
        "calculator": {
            "transport": "stdio",
            "command": "python",
            "args": [get_abs_path("../../../mcp/calculator.py")]
        }
    }

    # 2. 初始化 LLM
    llm = ChatOpenAI(
        model=config.OLLAMA_MODEL,
        base_url="http://localhost:11434/v1",
        api_key=SecretStr("ollama"),
        temperature=0  # ReAct 模式建议设为 0，增加推理稳定性
    )

    # 3. 使用适配器管理 MCP 连接
    # 它替代了你手动写的 AsyncExitStack 和 ClientSession 初始化逻辑
    client = MultiServerMCPClient(mcp_configs)

    try:
        # 加载并自动转换 MCP 工具为 LangChain Tools
        print(">> 正在自动连接 MCP 并转换工具...")
        tools = await client.get_tools()

        # 4. 创建 Agent (核心 ReAct 引擎)
        # create_agent 内部自带了类似你手动写的 while 循环逻辑
        # 它会反复询问 LLM 是否需要调用工具，直到问题解决或达到最大步数
        agent = create_agent(
            llm,
            tools,
            system_prompt=config.SYS_PROMPT
        )

        query = "北京和伦敦现在的温度总和是多少？昨天的温度相加是多少，另外把这个昨天的温度总和乘以今天的温度总和"
        print(f"\nQ: {query}")

        # 5. 执行推理循环
        # 注意：这里我们使用 astream 模式，这样你可以看到类似你手动代码里的 Step 过程
        inputs = {"messages": [HumanMessage(content=query)]}

        # 使用 cast(Any, ...) 解决 PyCharm 警告
        async for chunk in agent.astream(cast(Any, inputs), stream_mode="values"):
            latest_message = chunk["messages"][-1]
            # 漂亮的打印出每一轮的思考或工具执行结果
            latest_message.pretty_print()

    except Exception as e:
        print(f"\n运行异常: {e}")


if __name__ == "__main__":
    asyncio.run(run_langchain_mcp_react())
