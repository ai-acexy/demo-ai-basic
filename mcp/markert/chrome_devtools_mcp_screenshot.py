# -*- coding: utf-8 -*-
import asyncio
import json
import os
import re
import sys
from datetime import datetime

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import OpenAI
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionToolParam,
    ChatCompletionToolMessageParam, ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam
)

import config

MODEL_NAME = 'deepseek-v4-pro'
openai_client = OpenAI(
    api_key=config.deepseek_key(),
    base_url="https://api.deepseek.com"
)

SCREENSHOT_DIR = os.path.abspath(os.path.join(os.getcwd(), "screenshots"))

SYSTEM_PROMPT = (
    "你是一个浏览器截图执行器."
    "根据用户的自然语言描述，先打开目标网站，再定位用户指定的页面元素，"
    "优先使用 take_screenshot_of_element 对元素区域截图。"
    "如果用户一次提供多个元素位置，请按顺序逐个处理，确保每个元素都独立截图且不遗漏。"
    "截图文件必须保存到当前工作目录下的 ./screenshots 目录"
    "如果用户只描述了页面局部区域，则合理推断并完成截图。"
)


def _inject_screenshot_filepath(func_args: dict):
    """为截图工具调用自动注入 filePath 参数。"""
    if "filePath" not in func_args:
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        func_args["filePath"] = os.path.join(SCREENSHOT_DIR, f"screenshot_{timestamp}.png")


def _split_multi_target_prompt(user_prompt: str) -> list[str]:
    """把显式列出的多个元素位置拆成多个子任务。"""
    prompt = user_prompt.strip()
    if not prompt:
        return [prompt]

    lines = [line.strip() for line in prompt.splitlines() if line.strip()]
    if len(lines) <= 1:
        return [prompt]

    item_pattern = re.compile(r"^(?:\d+[\.\)、:]|[-*•])\s*(.+)$")
    intro_lines: list[str] = []
    items: list[str] = []

    for line in lines:
        match = item_pattern.match(line)
        if match:
            items.append(match.group(1).strip())
        else:
            intro_lines.append(line)

    if len(items) < 2:
        return [prompt]

    intro = "\n".join(intro_lines).strip()
    if not intro:
        return items

    normalized_tasks = []
    for item in items:
        normalized_tasks.append(f"{intro}\n目标元素：{item}")
    return normalized_tasks


async def execute_task(mcp_session: ClientSession, tools: list[ChatCompletionToolParam], user_prompt: str):
    """执行单次截图任务，返回 LLM 的最终回复。"""
    messages: list[ChatCompletionMessageParam] = [
        ChatCompletionSystemMessageParam(role="system", content=SYSTEM_PROMPT),
        ChatCompletionUserMessageParam(role="user", content=user_prompt)
    ]

    for step in range(20):
        print(f"\n[第 {step + 1} 轮推理开始...]")

        response = openai_client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            tools=tools,
            extra_body={"thinking": {"type": "enabled"}},
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

            if "screenshot" in func_name.lower():
                _inject_screenshot_filepath(func_args)
                tool_call.function.arguments = json.dumps(func_args, ensure_ascii=False)

            print(f">> 正在执行调用: {func_name}({func_args})")
            try:
                mcp_result = await mcp_session.call_tool(func_name, arguments=func_args)
                obs_content = ""
                if mcp_result.content:
                    first_content = mcp_result.content[0]

                    if "screenshot" in func_name.lower():
                        obs_content = getattr(first_content, "text", "") or ""
                        screenshot_path = func_args.get("filePath", "")
                        if screenshot_path and os.path.isfile(screenshot_path):
                            print(f">> 截图已保存到: {screenshot_path}")
                            obs_content = f"截图已保存到文件: {screenshot_path}"
                        elif not screenshot_path:
                            print(">> 注意: 截图工具调用时未指定 filePath，无法确认文件位置")
                    else:
                        obs_content = getattr(first_content, "text", "") or ""

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

        print(">> 观察结果已收录，等待大模型下一步决策...")

    return "已达到最大步数限制，任务未完成。"


async def main(user_prompt: str):
    server_params = StdioServerParameters(
        command="npx",
        args=["chrome-devtools-mcp@latest", "--no-performance-crux", "--no-usage-statistics"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as mcp_session:
            await mcp_session.initialize()
            mcp_tools_resp = await mcp_session.list_tools()
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

            print("=" * 50)
            print(f"任务描述: {user_prompt}")
            print("=" * 50)
            task_prompts = _split_multi_target_prompt(user_prompt)
            if len(task_prompts) == 1:
                result = await execute_task(mcp_session, tools, user_prompt)
                print(f"\nAI: {result}")
            else:
                results = []
                for index, task_prompt in enumerate(task_prompts, start=1):
                    print(f"\n{'=' * 20} 子任务 {index}/{len(task_prompts)} {'=' * 20}")
                    print(task_prompt)
                    result = await execute_task(mcp_session, tools, task_prompt)
                    results.append(f"[子任务 {index}] {result}")
                print("\nAI: " + "\n".join(results))


if __name__ == "__main__":
    try:
        asyncio.run(main(
            '打https://www.allscores.io/match/5188760/lineups/lokomotiv-plovdiv-vs-cska-sofia 将class="bg-bg-color-2 border border-border-level-2 rounded-[var(--page-card-radius)] p-page-card-padding p-0! overflow-hidden" 这个区域截图下来'))
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"发生意外错误: {e}")
