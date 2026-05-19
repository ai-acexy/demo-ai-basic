# -*- coding: utf-8 -*-
from openai import OpenAI
from openai.types.chat import ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam

import config

client = OpenAI(
    api_key=config.deepseek_key(),
    base_url="https://api.deepseek.com"
)

# 非流式调用：删除 stream=True
response = client.chat.completions.create(
    extra_body={"thinking": {"type": "enabled"}},
    model="deepseek-v4-flash",
    stream=False,
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

# 非流式获取结果：直接从 message.content 读取
content = response.choices[0].message.content
print(content)

print("\n-------- 回复结束 --------")