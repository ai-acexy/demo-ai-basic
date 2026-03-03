# -*- coding: utf-8 -*-
from openai import OpenAI
from openai.types.chat import ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam

# 指向 Ollama 的 OpenAI 兼容接口
client = OpenAI(
    base_url="http://127.0.0.1:11434/v1",
    api_key="ollama",
)

response = client.chat.completions.create(
    model="deepseek-r1",
    stream=True,
    messages=[
        ChatCompletionSystemMessageParam(
            role="system",
            content="你是一个中国古诗辞库"
        ),
        ChatCompletionUserMessageParam(
            role="user",
            content="给我来一首冷门的古诗呢"
        )
    ]
)

print("-------- 开始回复 --------")

for chunk in response:
    # 获取正式回复内容
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)

print("\n-------- 回复结束 --------")
