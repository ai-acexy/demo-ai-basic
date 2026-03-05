# -*- coding: utf-8 -*-

# pip install "mcp[cli]" 安装mcp开发框架

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Calculator", json_response=True)


@mcp.tool()
def add_numbers(a: float, b: float) -> float:
    """
    将两个数字相加并返回结果。
    参数:
        a: 第一个加数
        b: 第二个加数
    """
    result = a + b
    print(f"--- 触发计算: {a} + {b} = {result} ---")  # 这会在服务器终端显示
    return result


@mcp.tool()
def multiply_numbers(a: float, b: float) -> float:
    """
    将两个数字相乘并返回结果。
    参数:
        a: 第一个加数
        b: 第二个加数
    """
    result = a * b
    print(f"--- 触发计算: {a} * {b} = {result} ---")  # 这会在服务器终端显示
    return result


if __name__ == "__main__":
    # "stdio":
    #   (Standard Input/Output)
    #   作用：通过程序的**标准输入（stdin）和标准输出（stdout）**进行通信。
    #   原理：客户端启动服务器作为一个子进程，然后像你在命令行打字一样发送 JSON 指令，服务器处理完后把结果“打印”出来，客户端再读取这些打印内容。
    #   场景：本地开发和私有化工具。比如 Claude Desktop 调用你电脑本地的 MySQL 或文件系统。
    #   优点：简单、极其安全（不需要联网，进程间直接通信），几乎不需要配置网络环境。

    # "sse":
    #   这是一种基于 HTTP 的单向推送技术。
    #   作用：允许服务器向客户端发送实时更新，通常与 HTTP POST 配合实现双向通信。
    #   原理：客户端维持一个 HTTP 连接，服务器可以持续地将新数据推送到这个连接上。在 MCP 中，它通常用于处理需要较长时间运行的任务或需要流式返回结果的场景。
    #   场景：远程服务器或云端服务。    #   优点：比传统的 HTTP 请求响应模式更轻量，非常适合实时状态更新。

    # "streamable-http":
    #   这与 "sse" 类似，但更适合处理大文件传输。
    #   作用：允许服务器向客户端发送大文件，通常与 HTTP POST 配合实现双向通信。
    #   原理：服务器将文件数据分块发送给客户端，客户端可以逐块接收并保存。
    #   场景：远程服务器或云端服务。让全球各地的 Agent 都能调用。
    #   优点：适合处理大文件传输，如文件下载。
    mcp.run(transport="stdio")
