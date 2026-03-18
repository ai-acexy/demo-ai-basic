# -*- coding: utf-8 -*-

from browser_use import Agent, Browser
from browser_use import ChatOpenAI
import asyncio

import config


async def main():
    browser = Browser(
        # use_cloud=True,  # Use a stealth browser on Browser Use Cloud
    )

    agent = Agent(
        task="打开这个网址https://scores24.live/en/soccer/2026-03-21 找到比赛 Kitchee vs Eastern 进入详情，查看 overview输出的内容",
        llm=ChatOpenAI(model=config.OPENAI_MODEL, api_key=config.openai_key()),
        browser=browser,
    )
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
