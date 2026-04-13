#!/usr/bin/env python3
"""
Agent + MCP Server 示例

演示四种 Agent 模式如何接入 MCP（Model Context Protocol）工具：
1. ReAct - 使用 MCP 工具进行问答
2. Plan-Execute - 使用 MCP 工具规划执行
3. Reflexion - 使用 MCP 工具反思改进

MCP Server 支持三种传输方式：stdio / http (SSE) / streamable_http

需要设置环境变量: OPENAI_API_KEY

用法:
  python examples/agents/demo_mcp_agent.py              # 运行所有示例
  python examples/agents/demo_mcp_agent.py --mode react # 只运行 ReAct 示例
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from langchain_openai import ChatOpenAI
from flux_agent.agents import create_agent, AgentConfig
from dotenv import load_dotenv
load_dotenv()

DEFAULT_BASE_URL = os.getenv("OPENAI_BASE_URL")
DEFAULT_API_KEY = os.getenv("OPENAI_API_KEY")

# ============================================================
# MCP Server 配置
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
        "args": [os.path.join(os.path.dirname(__file__), "mcp_math_server.py"),],
        "tool_name_prefix": "math_",
    },
    # {
    #     "name": "filesystem",
    #     "transport": "stdio",
    #     "command": "npx",
    #     "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
    #     "tool_name_prefix": "fs_",
    # },

    # ─────────────────────────────────────────────
    # 2. Streamable HTTP 方式
    #    MCP 协议最新推荐方式，URL 以 /mcp 结尾
    # ─────────────────────────────────────────────
    # {
    #     "name": "mcp-gateway",
    #     "transport": "streamable_http",
    #     "url": "http://mcp-gateway/mcp",
    #     "headers": {"Cookie": f"="},
    #     "tool_name_prefix": "gw_",
    # },
]

llm = ChatOpenAI(
    model="gemini-3.1-flash-lite-preview",
    base_url=DEFAULT_BASE_URL,
    api_key=DEFAULT_API_KEY,
)


def demo_react_mcp():
    """ReAct 模式 + MCP 工具"""
    print("=" * 60)
    print("ReAct 模式 + MCP 工具")
    print("=" * 60)

    agent = create_agent(
        "react",
        llm=llm,
        mcp_servers=MCP_SERVERS,
        config=AgentConfig(verbose=True),
    )

    result = agent.invoke("计算 (15 + 27) * 3 的结果")

    print(f"\n回答: {result.answer[:300]}")
    print(f"状态: {result.status.value}")
    print(f"步数: {result.total_steps}")
    print()


def demo_plan_execute_mcp():
    """Plan-Execute 模式 + MCP 工具"""
    print("=" * 60)
    print("Plan-Execute 模式 + MCP 工具")
    print("=" * 60)

    agent = create_agent(
        "plan_execute",
        llm=llm,
        mcp_servers=MCP_SERVERS,
        enable_replan=True,
        config=AgentConfig(verbose=True),
    )

    result = agent.invoke("帮我分析 2024 年 AI 行业的发展趋势")

    print(f"\n回答: {result.answer[:300]}")
    print(f"状态: {result.status.value}")
    print(f"计划步数: {len(result.metadata.get('plan', []))}")
    print()


def demo_reflexion_mcp():
    """Reflexion 模式 + MCP 工具"""
    print("=" * 60)
    print("Reflexion 模式 + MCP 工具")
    print("=" * 60)

    agent = create_agent(
        "reflexion",
        llm=llm,
        mcp_servers=MCP_SERVERS,
        max_iterations=2,
        quality_threshold=8.0,
        config=AgentConfig(verbose=True),
    )

    result = agent.invoke("写一个 Python 函数实现快速排序算法")

    print(f"\n回答: {result.answer[:300]}")
    print(f"状态: {result.status.value}")
    print(f"反思轮数: {result.metadata.get('total_reflections', 0)}")
    print()


def demo_mixed_tools():
    """MCP 工具 + 代码工具混合使用"""
    print("=" * 60)
    print("MCP 工具 + 代码工具混合")
    print("=" * 60)

    def greet(name: str) -> str:
        """生成问候语"""
        return f"你好, {name}! 很高兴为你服务。"

    def get_timestamp() -> int:
        """获取当前时间戳"""
        import time
        return int(time.time())

    agent = create_agent(
        "react",
        llm=llm,
        tools=[greet, get_timestamp],  # 代码注册的工具
        mcp_servers=MCP_SERVERS,  # MCP Server 的工具
        config=AgentConfig(verbose=True),
    )

    result = agent.invoke("请先问候张三, 然后 查看下业务线：tiku 服务单元：gvideo-hub近半个小时的错误日志")

    print(f"\n回答: {result.answer[:300]}")
    print(f"状态: {result.status.value}")
    print()


def main():
    print("\n" + "=" * 60)
    print("  Flux-Agent MCP 示例 - Agent 模式")
    print("=" * 60 + "\n")

    if not os.environ.get("OPENAI_API_KEY"):
        print("请设置环境变量 OPENAI_API_KEY")
        return

    # 默认只运行 ReAct，取消注释以运行更多
    try:
        # demo_react_mcp()
        # demo_plan_execute_mcp()
        demo_reflexion_mcp()
        # demo_mixed_tools()
    except Exception as e:
        print(f"运行示例时出错: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)
    print("  演示完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
