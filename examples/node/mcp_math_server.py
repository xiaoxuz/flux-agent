#!/usr/bin/env python3
"""
MCP Math Server — 一个简单的数学计算 MCP Server 示例

用于演示 flux-agent 的 MCP 集成能力。
传输方式: stdio
启动命令: python mcp_servers/math_server.py

本示例使用 mcp SDK 创建一个提供基础数学运算的 MCP Server。
"""

from mcp.server.fastmcp import FastMCP

# 创建 MCP Server
mcp = FastMCP("math-server")


@mcp.tool()
def add(a: float, b: float) -> float:
    """计算两个数的和"""
    return a + b


@mcp.tool()
def subtract(a: float, b: float) -> float:
    """计算两个数的差"""
    return a - b


@mcp.tool()
def multiply(a: float, b: float) -> float:
    """计算两个数的积"""
    return a * b


@mcp.tool()
def divide(a: float, b: float) -> float:
    """计算两个数的商，b 不能为 0"""
    if b == 0:
        raise ValueError("除数不能为 0")
    return a / b


@mcp.tool()
def power(base: float, exponent: float) -> float:
    """计算 base 的 exponent 次方"""
    return base ** exponent


if __name__ == "__main__":
    mcp.run()
