# -*- coding: utf-8 -*-
from openai import OpenAI

import config

client = OpenAI(
    api_key=config.openai_key()
)

resp = client.responses.create(
    model="gpt-5",
    tools=[{"type": "web_search", "external_web_access": True}],
    tool_choice="auto",
    input="现在足球比赛United States - MLS Next Pro联赛下Portland Timbers 2 vs Ventura County FC 比分是多少了",
    # input="https://scores24.live/en/soccer/m-21-03-2026-brighton-hove-albion-liverpool检查这个页面Prediction部分的内容 输出它原始的信息",
)
print(resp.output_text)
