# -*- coding: utf-8 -*-
from google import genai

import config

client = genai.Client(api_key=config.gemini_key())

response = client.models.generate_content(
    model="gemini-3-flash-preview", contents="Spain-LaLiga 这个联赛下 Espanyol 与 Real Oviedo 战力分析 请使用最新的数据分析，回答时给出分析的数据的时间"
)
print(response.text)
