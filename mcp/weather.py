# -*- coding: utf-8 -*-
from mcp.server.fastmcp import FastMCP
import json

# 1. 初始化 FastMCP
mcp = FastMCP("Weather")


# 2. 将原有的逻辑包装为 Tool
@mcp.tool()
def get_current_weather(location: str) -> str:
    """获取指定地点实时天气情况
    参数:
        location: 城市名称，如 Beijing, London"""
    print(f"--- [get_current_weather] 收到查询请求: {location} ---")
    raw_data = {
        "London": {"temp": 15, "unit": "celsius", "humidity": "80%", "wind": "5km/h"},
        "Beijing": {"temp": 28, "unit": "celsius", "humidity": "40%", "wind": "2km/h"},
    }
    info = raw_data.get(location, {"temp": "未知", "condition": "无数据"})
    return json.dumps(info)


# 2. 将原有的逻辑包装为 Tool
@mcp.tool()
def get_last_day_weather(location: str) -> str:
    """获取指定地点昨天天气情况
    参数:
        location: 城市名称，如 Beijing, London"""
    print(f"--- [get_current_weather] 收到查询请求: {location} ---")
    raw_data = {
        "London": {"temp": -15, "unit": "celsius", "humidity": "80%", "wind": "5km/h"},
        "Beijing": {"temp": -28, "unit": "celsius", "humidity": "40%", "wind": "2km/h"},
    }
    info = raw_data.get(location, {"temp": "未知", "condition": "无数据"})
    return json.dumps(info)


if __name__ == "__main__":
    mcp.run(transport="stdio")
