# # -*- coding: utf-8 -*-
# import asyncio
# import os
# from langchain_openai import ChatOpenAI
# from langchain_mcp_adapters.client import MultiServerMCPClient
# from langgraph.prebuilt import create_react_agent
# from pydantic import SecretStr
#
#
# # 建议：使用绝对路径，避免 Agent 找不到脚本
# def get_abs_path(relative_path):
#     return os.path.abspath(os.path.join(os.path.dirname(__file__), relative_path))
#
#
# # --- 1. 核心修复：添加 'transport' 键并结构化配置 ---
# MCP_CONFIGS = {
#     "weather": {
#         "transport": "stdio",  # 必须明确指定传输方式
#         "command": "python",
#         "args": [get_abs_path("../../../mcp/weather.py")],
#     },
#     "calculator": {
#         "transport": "stdio",
#         "command": "python",
#         "args": [get_abs_path("../../../mcp/calculator.py")],
#     },
# }
#
# llm = ChatOpenAI(
#     model="qwen3.5:2b",
#     base_url="http://127.0.0.1:11434/v1",
#     api_key=SecretStr("ollama"),
# )
#
#
# async def run_langchain_mcp_agent(user_prompt: str):
#     # 2. 初始化客户端 (v0.1.0 标准)
#     client = MultiServerMCPClient(MCP_CONFIGS)
#
#     try:
#         # 3. 提取工具
#         print(">> 正在通过 stdio 协议连接服务器...")
#         tools = await client.get_tools()
#         print(f">> 成功加载工具: {[t.name for t in tools]}")
#
#         # 4. 创建 Agent
#         agent_executor = create_react_agent(llm, tools)
#
#         # 5. 执行任务并流式输出思考过程 (推荐做法)
#         print(f">> 任务启动: {user_prompt}")
#         inputs = {"messages": [("user", user_prompt)]}
#
#         # 使用 astream 可以看到 Agent 是一步步如何调用工具的
#         final_content = ""
#         async for chunk in agent_executor.astream(inputs, stream_mode="values"):
#             message = chunk["messages"][-1]
#             if message.content:
#                 final_content = message.content
#                 # 打印中间思考，方便调试
#                 print(f"DEBUG [Agent]: {message.content[:50]}...")
#
#         return final_content
#
#     finally:
#         # 0.1.0 建议手动关闭以释放子进程
#         # 如果 client 有 close 方法可以调用，或者等待进程自动结束
#         pass
#
#
# if __name__ == "__main__":
#     query = "北京和伦敦现在的温度总和是多少？"
#     try:
#         ans = asyncio.run(run_langchain_mcp_agent(query))
#         print(f"\nAI 最终回复: {ans}")
#     except Exception as e:
#         import traceback
#
#         print(f"\n配置或运行异常: {e}")
#         traceback.print_exc()