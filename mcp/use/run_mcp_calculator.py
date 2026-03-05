import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def run_calculator_agent():
    server_params = StdioServerParameters(
        command="python",
        args=["../calculator.py"]
    )

    # 2. 建立 stdio 管道连接
    # 这步会自动在后台拉起一个新的 python 进程运行你的 calculator.py
    async with stdio_client(server_params) as (read, write):
        # 3. 初始化会话
        async with ClientSession(read, write) as session:
            await session.initialize()

            # -------------------------------------------------------
            # 步骤 A: 发现阶段 (大模型会先看你有什么本事)
            # -------------------------------------------------------
            tools = await session.list_tools()
            print(f"--- Agent 扫描到的工具列表 ---")
            for tool in tools.tools:
                print(f"发现工具: {tool.name}")
                print(f"    作用: {tool.description}")

            # -------------------------------------------------------
            # 步骤 B: 调用阶段 (大模型根据需求决定使用哪个工具)
            # -------------------------------------------------------
            print(f"\n--- Agent 正在执行加法指令 ---")

            # 模拟大模型提取了用户需求（比如 10 + 20）并封装成 JSON 发送
            result = await session.call_tool(
                "add_numbers",
                arguments={"a": 1.33, "b": 21.1}
            )

            # -------------------------------------------------------
            # 步骤 C: 结果解析
            # -------------------------------------------------------
            # MCP 结果通常放在 content 列表里
            answer = result.content[0].text
            print(f"最终结果: {answer}")


if __name__ == "__main__":
    asyncio.run(run_calculator_agent())
