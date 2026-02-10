# -*- coding: utf-8 -*-
import openai

# 指向你本地的 Ollama
client = openai.OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="acexy"
)

response = client.chat.completions.create(
    model="deepseek-r1", # 或者你下载的模型名
    messages=[
        {"role": "system", "content": "你是一个严谨的后端专家。"},
        {"role": "user", "content": "分析一下在高并发场景下，用 Go 还是 Java 更有优势？"}
    ]
)

print(response.choices[0].message.content)