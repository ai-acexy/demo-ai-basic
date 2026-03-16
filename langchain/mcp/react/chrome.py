import asyncio
from typing import cast, Any

from langchain.agents import create_agent
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

import config

llm = ChatOpenAI(
    model=config.OPENAI_MODEL,
    api_key=SecretStr(config.openai_key()),
)

client = MultiServerMCPClient(
    {
        "chrome": {
            "transport": "stdio",
            "command": "npx",
            "args": ["chrome-devtools-mcp@latest", "--no-performance-crux", "--no-usage-statistics"],
        },
    }
)


async def main():
    async with client.session("chrome") as session:
        tools = await load_mcp_tools(session)
        agent = create_agent(
            llm,
            tools
        )
        async for chunk in agent.astream(
                input=cast(Any, {
                    "messages": [
                        SystemMessage(
                            content="你是一个浏览器搜索工具，你分析用户的语义操作相关chrome tools完成用户的搜索要求"),
                        HumanMessage(content="打开特朗普真实社交网站， 找到他发的最新的贴文")]}),
                stream_mode="values"):
            latest_message = chunk["messages"][-1]
            latest_message.pretty_print()


if __name__ == "__main__":
    asyncio.run(main())
