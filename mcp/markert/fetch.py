# -*- coding: utf-8 -*-
import asyncio

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "mcp-fetch-server"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            mcp_tools = await session.list_tools()
            print(f"MCP Server 列表: {mcp_tools.tools}")
            result = await session.call_tool("fetch_html", arguments={
                "url": "https://www.news.cn/world/20260309/21be941e49884795a80dd33f3e3d71a3/c.html",
                "proxy": "http://localhost:7890"
            })

            for content in result.content:
                print(f"搜索结果: {content.text}")


if __name__ == "__main__":
    asyncio.run(main())
