# -*- coding: utf-8 -*-
import ollama

# 使用模型将文本向量化

# 输入你想转换的文本
text = "人工智能正在改变我们的工作方式"

# 调用本地模型生成向量
response = ollama.embed(
    model='qwen3-embedding:0.6b',
    input=text
)

# 提取向量 (Embedding)
embedding = response['embeddings'][0]

print(f"向量维度: {len(embedding)}")
print(f"向量前5位: {embedding[:5]}")
