# -*- coding: utf-8 -*-
import asyncio
import json
from contextlib import AsyncExitStack
from typing import Dict, List
from openai import OpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionToolParam, ChatCompletionUserMessageParam, \
    ChatCompletionToolMessageParam, ChatCompletionSystemMessageParam

import config

# 展示mcp聚合
# 模式 单轮并行调用 (Parallel Tool Calling) 或者 单次决策模式

MCP_CONFIGS = [
    {"name": "weather", "command": "python", "args": ["../weather.py"]},
    {"name": "calculator", "command": "python", "args": ["../calculator.py"]},
]

MODEL_NAME = config.OLLAMA_MODEL
openai_client = OpenAI(base_url="http://127.0.0.1:11434/v1", api_key="ollama")


# MODEL_NAME = "gpt-5-nano-2025-08-07"
# openai_client = OpenAI(api_key=config.get_env("OPEN_AI_API_KEY"))


async def run(user_prompt: str):
    async with AsyncExitStack() as stack:
        tool_to_session: Dict[str, ClientSession] = {}
        all_openai_tools: List[ChatCompletionToolParam] = []

        for c in MCP_CONFIGS:
            params = StdioServerParameters(command=c["command"], args=c["args"])

            # 启动并注册到 stack，确保退出时自动关闭进程
            read, write = await stack.enter_async_context(stdio_client(params))
            session = await stack.enter_async_context(ClientSession(read, write))
            await session.initialize()

            # 注册工具
            mcp_tools = await session.list_tools()
            for tool in mcp_tools.tools:
                tool_to_session[tool.name] = session
                all_openai_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.inputSchema
                    }
                })

        print(f">> 已加载 {len(all_openai_tools)} 个工具。")

        messages: List[ChatCompletionMessageParam] = [
            ChatCompletionSystemMessageParam(role="system", content=config.SYS_PROMPT),
            ChatCompletionUserMessageParam(role="user", content=user_prompt)
        ]

        response = openai_client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            tools=all_openai_tools
        )

        response_message = response.choices[0].message
        if response_message.tool_calls:
            messages.append(response_message.model_dump(exclude_none=True))

            for tool_call in response_message.tool_calls:
                func_name = tool_call.function.name
                target_session = tool_to_session.get(func_name)

                if target_session:
                    print(f">> 路由：正在调用 {func_name}...")
                    # 执行 MCP 调用
                    mcp_result = await target_session.call_tool(
                        func_name,
                        arguments=json.loads(tool_call.function.arguments)
                    )

                    # 提取结果（处理 TextContent 列表）
                    mcp_msg: ChatCompletionToolMessageParam = {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "content": mcp_result.content[0].text,
                    }
                    messages.append(mcp_msg)

            # 最终汇总回复
            final_resp = openai_client.chat.completions.create(model=MODEL_NAME, messages=messages)
            return final_resp.choices[0].message.content

        return response_message.content


if __name__ == "__main__":
    try:
        ans = asyncio.run(run("北京天气如何？顺便告诉我 23+46=多少"))
        print(f"\nAI: {ans}")
    except Exception as e:
        print(f"\n运行异常: {e}")
