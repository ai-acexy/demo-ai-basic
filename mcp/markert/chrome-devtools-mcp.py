# -*- coding: utf-8 -*-
import asyncio
import json

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import OpenAI
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionToolParam,
    ChatCompletionToolMessageParam, ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam
)

import config

MODEL_NAME = config.OPENAI_MODEL
openai_client = OpenAI(api_key=config.openai_key())


async def run(user_prompt: str):
    server_params = StdioServerParameters(
        command="npx",
        args=["chrome-devtools-mcp@latest", "--no-performance-crux", "--no-usage-statistics"]
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as mcp_session:
            await mcp_session.initialize()
            mcp_tools_resp = await mcp_session.list_tools()

            # 2. 准备工具列表
            tools: list[ChatCompletionToolParam] = []
            for tool in mcp_tools_resp.tools:
                tools.append({
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.inputSchema
                    }
                })

            # 3. 初始化对话历史
            messages: list[ChatCompletionMessageParam] = [
                ChatCompletionSystemMessageParam(role="system",
                                                 content="你是一个浏览器助手。你可以分多步操作：先导航到网页，查看内容，再提取信息。如果信息不足，请继续调用工具。"),
                ChatCompletionUserMessageParam(role="user", content=user_prompt)
            ]

            max_steps = 10  # 限制推理步数，防止死循环

            # --- 核心 ReAct 循环开始 ---
            for step in range(max_steps):
                print(f"\n[第 {step + 1} 轮推理开始...]")

                response = openai_client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=messages,
                    tools=tools
                )

                response_message = response.choices[0].message
                tool_calls = response_message.tool_calls

                if not tool_calls:
                    print(">> LLM 认为任务已完成，输出最终回复。")
                    return response_message.content

                messages.append(response_message.model_dump(exclude_none=True))
                print(f">> LLM 计划执行: {[tc.function.name for tc in tool_calls]}")

                for tool_call in tool_calls:
                    func_name = tool_call.function.name
                    func_args = json.loads(tool_call.function.arguments)
                    print(f">> 正在执行本地调用: {func_name}({func_args})")
                    try:
                        mcp_result = await mcp_session.call_tool(func_name, arguments=func_args)
                        print(f">> MCP 返回: {mcp_result}")
                        # 处理 MCP 返回的内容块
                        # 注意：chrome-devtools-mcp 有时返回 content[0].text，有时可能为空
                        obs_content = ""
                        if mcp_result.content:
                            obs_content = mcp_result.content[0].text

                        # 构造回复给大模型的消息
                        tool_msg: ChatCompletionToolMessageParam = {
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "content": obs_content if obs_content else "操作已完成，请检查页面当前状态。",
                        }
                        messages.append(tool_msg)

                    except Exception as e:
                        print(f">> 工具执行出错: {e}")
                        messages.append(ChatCompletionToolMessageParam(
                            role="tool",
                            tool_call_id=tool_call.id,
                            content=f"Error: {str(e)}"
                        ))

                # 循环会继续回到顶部，将最新的历史发给大模型，让它“思考”下一步
                print(">> 观察结果已收录，等待大模型下一步决策...")

            return "已达到最大步数限制，任务未完成。"


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(run("打开google.com 搜索关于最近美国以色列与伊朗战争的信息，然后汇总一下给我"))
        print(f"\nAI: {result}")
    finally:
        # 显式关闭循环前，先处理所有待处理的任务
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
