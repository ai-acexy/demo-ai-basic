# -*- coding: utf-8 -*-
import asyncio
import json

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    settings: dict[str, str] = {
        "SEARXNG_URL": "http://127.0.0.1:8080"
    }
    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "mcp-searxng"],
        env=settings
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            mcp_tools = await session.list_tools()
            print(f"MCP Server 列表: {mcp_tools.tools}")
            result = await session.call_tool("searxng_web_search", arguments={
                "query": "美国以色列与伊朗战争的最新情况 最新",
                "language": "en"
            })

            for content in result.content:
                print(f"搜索结果: {content.text}")


if __name__ == "__main__":
    asyncio.run(main())
