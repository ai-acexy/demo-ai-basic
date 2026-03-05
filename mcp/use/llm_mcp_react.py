# -*- coding: utf-8 -*-
import asyncio
import json
from contextlib import AsyncExitStack
from typing import Dict, List
from openai import OpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionToolParam,
    ChatCompletionUserMessageParam,
    ChatCompletionToolMessageParam, ChatCompletionSystemMessageParam
)

import config

MCP_CONFIGS = [
    {"name": "weather", "command": "python", "args": ["../weather.py"]},
    {"name": "calculator", "command": "python", "args": ["../calculator.py"]},
]

MODEL_NAME = "qwen3.5:2b"
openai_client = OpenAI(base_url="http://127.0.0.1:11434/v1", api_key="ollama")


# MODEL_NAME = "gpt-5-nano-2025-08-07"
# openai_client = OpenAI(api_key=config.get_env("OPEN_AI_API_KEY"))

async def run_react_agent(user_prompt: str):
    async with AsyncExitStack() as stack:
        tool_to_session: Dict[str, ClientSession] = {}
        all_openai_tools: List[ChatCompletionToolParam] = []

        # --- 1. 初始化所有 MCP Servers ---
        for config in MCP_CONFIGS:
            params = StdioServerParameters(command=config["command"], args=config["args"])
            read, write = await stack.enter_async_context(stdio_client(params))
            session = await stack.enter_async_context(ClientSession(read, write))
            await session.initialize()

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

        # --- 2. 核心 ReAct 循环逻辑 ---
        messages: List[ChatCompletionMessageParam] = [
            ChatCompletionSystemMessageParam(
                role="system",
                content="你是一个助手，你需要根据用户的指令，调用工具来完成任务。"
            ),
            ChatCompletionUserMessageParam(role="user", content=user_prompt)
        ]

        max_steps = 10  # 防止死循环
        step = 0

        while step < max_steps:
            step += 1

            # 让大模型决策：是继续调工具，还是直接回答？
            response = openai_client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                tools=all_openai_tools
            )

            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls
            print(f">> LLM: {response}")
            if not tool_calls:
                print(f">> [Step {step}] LLM得出最后结论")
                return response_message.content

            print(f">> [Step {step}] LLM 准备调用工具: {[tc.function.name for tc in tool_calls]}")

            messages.append(response_message.model_dump(exclude_none=True))

            # 处理本轮所有的并行或顺序工具调用
            for tool_call in tool_calls:
                func_name = tool_call.function.name
                target_session = tool_to_session.get(func_name)
                if target_session:
                    print(f"   执行工具: {func_name} | 参数: {tool_call.function.arguments}")
                    mcp_result = await target_session.call_tool(
                        func_name,
                        arguments=json.loads(tool_call.function.arguments)
                    )

                    # 将执行结果存入历史
                    messages.append(ChatCompletionToolMessageParam(
                        role="tool",
                        tool_call_id=tool_call.id,
                        content=mcp_result.content[0].text)
                    )

            print(f">> [Step {step}] 结果已存入上下文，进行下一轮思考...")

        return "抱歉，任务超过最大步数限制，未能完成。"


if __name__ == "__main__":
    try:
        query = "北京和伦敦现在的温度总和是多少？昨天的温度相加是多少，另外把这个昨天的温度总和*今天的温度总和"
        ans = asyncio.run(run_react_agent(query))
        print(f"\nAI: {ans}")
    except Exception as e:
        print(f"\n运行异常: {e}")
