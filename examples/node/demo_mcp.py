#!/usr/bin/env python3
"""
LLMNode + MCP Server 示例

演示如何在工作流中使用 MCP（Model Context Protocol）工具。
MCP 工具与代码注册的工具在 LLMNode 中完全等价使用。

需要设置环境变量: OPENAI_API_KEY
可选: 配置 MCP_SERVERS 覆盖默认的 MCP Server 配置

用法:
  python examples/node/demo_mcp.py                  # 使用内置示例配置
  python examples/node/demo_mcp.py --server math    # 只运行 math server 示例
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from flux_agent import WorkflowRunner, utils
from dotenv import load_dotenv
load_dotenv()

DEFAULT_BASE_URL = os.getenv("OPENAI_BASE_URL")
DEFAULT_API_KEY = os.getenv("OPENAI_API_KEY")

# ============================================================
# MCP Server 配置（三种传输方式）
# ============================================================

MCP_SERVERS = [
    # ─────────────────────────────────────────────
    # 1. Stdio 方式：本地进程通信
    #    适用于本地工具、CLI 工具
    # ─────────────────────────────────────────────
    {
        "name": "math",
        "transport": "stdio",
        "command": "python",
        "args": [
            # 示例 MCP math server（提供加减乘除等基础运算）
            os.path.join(os.path.dirname(__file__), "mcp_math_server.py"),
        ],
        "tool_name_prefix": "math_",
    },

    # ─────────────────────────────────────────────
    # 2. Streamable HTTP 方式：无状态 HTTP 请求
    #    MCP 协议最新推荐方式
    # ─────────────────────────────────────────────
    {
        "name": "mcp-gateway",
        "transport": "streamable_http",
        "url": "http://xxxx/mcp",
        "headers": {
            "Cookie": f"aa:bb",
        },
        "tool_name_prefix": "gw_",
    },
]


def demo_mcp_workflow():
    """演示在 Workflow 中使用 MCP 工具"""
    print("=" * 60)
    print("LLMNode + MCP Server 示例")
    print("=" * 60)

    config = {
        "workflow": {"name": "mcp-demo", "version": "1.0.0"},

        # MCP Server 配置
        "mcp_servers": MCP_SERVERS,

        # 代码注册的工具（与 MCP 工具并存）
        "tools": [],

        "nodes": [
            {
                "id": "answer",
                "type": "LLMNode",
                "config": {
                    "model_name": "gpt-4o",
                    "system_prompt": (
                        "你是一个助手，必须使用 math 工具进行数学计算。"
                        "当用户提出数学问题时，使用 math_ 开头的工具来计算。"
                    ),
                    "user_prompt": "${data.question}",
                    "output_key": "data.answer",
                    "base_url": DEFAULT_BASE_URL,
                    "api_key": DEFAULT_API_KEY,
                    "max_tool_iterations": 10,
                },
            },
        ],
        "edges": [
            {"from": "START", "to": "answer"},
            {"from": "answer", "to": "END"},
        ],
    }

    runner = WorkflowRunner(
        config_dict=config,
        # 也可以在这里额外传 MCP Servers
        # mcp_servers=MCP_SERVERS,
    )

    result = runner.invoke({
        "data": {
            "question": "计算 (15 + 27) * 3 的结果是多少？",
        },
    })

    print(f"\n回答: {result.get('data', {}).get('answer', '')}")
    print("=" * 60)
    print(utils.pretty_state(result))


def demo_mcp_with_code_tools():
    """演示 MCP 工具与代码工具混合使用"""
    print("\n" + "=" * 60)
    print("MCP 工具 + 代码工具 混合示例")
    print("=" * 60)

    def greet(name: str) -> str:
        """生成问候语"""
        return f"你好呀呀, {name}!"

    config = {
        "workflow": {"name": "mcp-mixed-tools"},
        "mcp_servers": MCP_SERVERS,

        "nodes": [
            {
                "id": "assistant",
                "type": "LLMNode",
                "config": {
                    "model_name": "gpt-4o",
                    "system_prompt": "你是一个助手，可以使用工具帮助用户。",
                    "user_prompt": (
                        "请先使用工具问候张三，然后计算 100 除以 7 的结果。"
                    ),
                    "tools": ["greet"], 
                    "output_key": "data.result",
                    "base_url": DEFAULT_BASE_URL,
                    "api_key": DEFAULT_API_KEY,
                    "max_tool_iterations": 10,
                },
            },
        ],
        "edges": [
            {"from": "START", "to": "assistant"},
            {"from": "assistant", "to": "END"},
        ],
    }

    runner = WorkflowRunner(
        config_dict=config,
        tools={"greet": greet},
    )

    result = runner.invoke({"data": {}})

    print(f"\n回答: {result.get('data', {}).get('result', '')}")
    print("=" * 60)
    print(utils.pretty_state(result))
    

def demo_mcp_streamable_http_workflow():
    """演示在 Workflow 中使用 streamable_http 模式 MCP 工具"""
    print("=" * 60)
    print("LLMNode + MCP streamable_http Server 示例")
    print("=" * 60)

    config = {
        "workflow": {"name": "mcp-demo", "version": "1.0.0"},

        # MCP Server 配置
        "mcp_servers": MCP_SERVERS,

        # 代码注册的工具（与 MCP 工具并存）
        "tools": [],

        "nodes": [
            {
                "id": "answer",
                "type": "LLMNode",
                "config": {
                    "model_name": "gpt-4o",
                    "system_prompt": (
                        "你是一个助手"
                    ),
                    "user_prompt": "${data.question}",
                    "output_key": "data.answer",
                    "base_url": DEFAULT_BASE_URL,
                    "api_key": DEFAULT_API_KEY,
                    "max_tool_iterations": 10,
                },
            },
        ],
        "edges": [
            {"from": "START", "to": "answer"},
            {"from": "answer", "to": "END"},
        ],
    }

    runner = WorkflowRunner(
        config_dict=config,
        # 也可以在这里额外传 MCP Servers
        # mcp_servers=MCP_SERVERS,
    )

    result = runner.invoke({
        "data": {
            "question": "mcp 服务都提供了哪些工具",
        },
    })

    print(f"\n回答: {result.get('data', {}).get('answer', '')}")
    print("=" * 60)
    print(utils.pretty_state(result))


def main():
    print("\n" + "=" * 60)
    print("  Flux-Agent MCP 示例 - Workflow 模式")
    print("=" * 60 + "\n")

    if not os.environ.get("OPENAI_API_KEY"):
        print("请设置环境变量 OPENAI_API_KEY")
        return

    try:
        # demo_mcp_workflow()
        # demo_mcp_with_code_tools()
        demo_mcp_streamable_http_workflow()
    except Exception as e:
        print(f"运行示例时出错: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)
    print("  演示完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
