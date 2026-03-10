# -*- coding: utf-8 -*-
import asyncio
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

llm = ChatOllama(
    model="deepseek-r1:latest",
    reasoning=True,
)


async def run_langchain_translate():
    system_prompt = "你是一个翻译，你收到的内容都是博彩相关，你注重专用名词处理，跳过冗余的思考"
    user_content = """请提供合适的俄语翻译或音译。
要求：
按照顺序翻译每个文本，每行一个翻译结果，格式为：序号. 翻译结果 只返回俄语翻译，不要其他内容。如果某个文本无法翻译，返回空行待翻译文本：
1.Li, Bo 2.Osman, Ekber 3.Yufei, Jiang 请按以下格式返回（每行一个翻译结果）：
1. 翻译结果1
2. 翻译结果2 ..."""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_content)
    ]
    print("-------- 开始回复 --------")

    # 非流式回复
    response = await llm.ainvoke(messages)
    print(response.content)


if __name__ == "__main__":
    asyncio.run(run_langchain_translate())
