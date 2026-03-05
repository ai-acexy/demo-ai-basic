# -*- coding: utf-8 -*-
import asyncio
import json
from openai import OpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionSystemMessageParam, \
    ChatCompletionUserMessageParam, ChatCompletionToolMessageParam, ChatCompletionToolParam

import config

MODEL_NAME = config.OLLAMA_MODEL
openai_client = OpenAI(base_url="http://127.0.0.1:11434/v1", api_key="ollama")


# MODEL_NAME = "gpt-5-nano-2025-08-07"
# openai_client = OpenAI(api_key=config.get_env("OPEN_AI_API_KEY"))


async def run_mcp_agent(user_prompt: str):
    # 1. 定义如何连接到你的 MCP Server
    server_params = StdioServerParameters(
        command="python",
        args=["../weather.py"]  # 确保路径正确
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as mcp_session:
            await mcp_session.initialize()
            mcp_tools_resp = await mcp_session.list_tools()
            print(f"MCP Server 列表: {mcp_tools_resp.tools}")

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

            messages: list[ChatCompletionMessageParam] = [
                ChatCompletionSystemMessageParam(role="system", content=config.SYS_PROMPT),
                ChatCompletionUserMessageParam(role="user", content=user_prompt)
            ]
            print(f"已注入所有tools {json.dumps(tools)}")

            response = openai_client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                tools=tools
            )

            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls

            if tool_calls:
                print(">> LLM 决定发起 Tool Call...")
                messages.append(response_message.model_dump(exclude_none=True))
                print(f"MCP Call: {response_message.model_dump(exclude_none=True)}")
                for tool_call in tool_calls:
                    # 5. 调用 MCP Server 执行逻辑 (选择与执行阶段)
                    # 注意：这里不再是 local_func()，而是 mcp_session.call_tool()
                    print(
                        f">> LLM 发起 MCP Call name: {tool_call.function.name} args: {tool_call.function.arguments} ... ")
                    mcp_result = await mcp_session.call_tool(
                        tool_call.function.name,
                        arguments=json.loads(tool_call.function.arguments)
                    )
                    print(f"MCP Resp: {mcp_result}")
                    mcp_msg: ChatCompletionToolMessageParam = {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "content": mcp_result.content[0].text,
                    }
                    messages.append(mcp_msg)

                final_response = openai_client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=messages
                )
                return final_response.choices[0].message.content

            return response_message.content


if __name__ == "__main__":
    # result = asyncio.run(run_mcp_agent("伦敦昨天天气怎么样？"))
    # result = asyncio.run(run_mcp_agent("北京当前天气怎么样？"))
    result = asyncio.run(run_mcp_agent("北京近昨天和现在的天气如何？"))
    # result = asyncio.run(run_mcp_agent("中国国土面积多大？"))

    print(f"\nAI: {result}")
