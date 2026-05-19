# -*- coding: utf-8 -*-
from openai import OpenAI
from openai.types.chat import ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam

import config

client = OpenAI(
    api_key=config.openai_key(),
)

response = client.chat.completions.create(
    model="gpt-5.4",
    stream=True,
    messages=[
        ChatCompletionSystemMessageParam(
            role="system",
            content="你是一个足球体育赛事分析师，专注于预测赛事相关的结果，可以使用额外的搜索工具来搜索最新的资料，每次回复时，你要提供基于当前预测的具体使用的数据的时间"
        ),
        ChatCompletionUserMessageParam(
            role="user",
            content="关于 Spain-LaLiga 这个联赛下 2026-03-10 Espanyol VS Real Oviedo"
        )
    ],
)


print("-------- 开始回复 --------")

for chunk in response:
    # 获取正式回复内容
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)

print("\n-------- 回复结束 --------")
