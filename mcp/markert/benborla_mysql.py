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

# MODEL_NAME = config.OPENAI_MODEL
# openai_client = OpenAI(api_key=config.openai_key())
MODEL_NAME = config.OLLAMA_MODEL
openai_client = OpenAI(base_url="http://localhost:11434/v1", api_key="")


async def run(user_prompt: str):
    settings: dict[str, str] = {
        "MYSQL_HOST": config.get_env("MYSQL_HOST"),
        "MYSQL_PORT": config.get_env("MYSQL_PORT"),
        "MYSQL_USER": config.get_env("MYSQL_USER"),
        "MYSQL_PASS": config.get_env("MYSQL_PASS"),
        "MYSQL_DB": config.get_env("MYSQL_DB"),
    }
    server_params = StdioServerParameters(
        command="npx",
        args=["@benborla29/mcp-server-mysql@latest"],
        env=settings
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

            prompt = """
            你是一个数据库管理员，通过理解用户输入，自动查询相关表的数据返回给用户,如果用户的要求和操作数据库无关，则直接拒绝。注意你永远只允许执行select查询相关的权限不允许做任何修改，一旦你发现包含修改要求，你需要直接拒绝。
            
            当前表结构
            create table user
(
    id          bigint unsigned auto_increment
        primary key,
    created_at  datetime     default CURRENT_TIMESTAMP not null,
    modified_at datetime     default CURRENT_TIMESTAMP not null on update CURRENT_TIMESTAMP,
    email       varchar(200)                           null comment '邮箱',
    shop_email  varchar(200)                           null comment '购物邮箱',
    nickname    varchar(255)                           null comment '昵称',
    avatar      varchar(255)                           null comment '头像',
    followers   int unsigned default '0'               null comment '粉丝数',
    following   int unsigned default '0'               null comment '关注数',
    likes       int unsigned default '0'               null comment '全站发布内容被点赞数',
    bio         varchar(255)                           null comment '个人介绍',
    cover       varchar(255)                           null comment '个人背景封面',
    password    varchar(255)                           null comment '密码',
    channel     varchar(10)  default 'email'           null comment '账户创建渠道',
    status      int          default 1                 null comment '账号状态 1正常 2-禁用',
    constraint uk_email
        unique (email),
    constraint check_followers
        check (`followers` >= 0),
    constraint check_following
        check (`following` >= 0),
    constraint check_likes
        check (`likes` >= 0)
)
    comment '用户表';
            """

            # 3. 初始化对话历史
            messages: list[ChatCompletionMessageParam] = [
                ChatCompletionSystemMessageParam(role="system",
                                                 content=prompt),
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
                        obs_content = ""
                        if mcp_result.content:
                            obs_content = mcp_result.content[0].text

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


if __name__ == "__main__":
    try:
        result = asyncio.run(run("帮我查看用户表的最新一条数据"))
        print(f"\nAI: {result}")
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"发生意外错误: {e}")
