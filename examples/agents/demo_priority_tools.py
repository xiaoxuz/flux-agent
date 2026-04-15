#!/usr/bin/env python3
"""
Flux-Agent 专用工具优先级系统演示

演示 Agent 同时拥有 Bash 工具和专用文件操作工具时，
优先选择专用工具而非通过 Bash 执行对应命令：
1. bash - 执行 shell 命令（附带"何时不用 Bash"的优先级指导）
2. glob_search - 文件路径模式搜索（替代 find/ls）
3. grep_search - 文件内容搜索（替代 grep/rg）
4. file_read - 读取文件（替代 cat/head/tail）
5. file_edit - 编辑文件（替代 sed/awk）
6. file_write - 写入文件（替代 echo>/cat<<EOF）

运行方式：
    python examples/agents/demo_priority_tools.py
"""

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from dotenv import load_dotenv
load_dotenv()

DEFAULT_BASE_URL = os.getenv("OPENAI_BASE_URL")
DEFAULT_API_KEY = os.getenv("OPENAI_API_KEY")

from langchain_openai import ChatOpenAI
from flux_agent.agents import ReactAgent, AgentConfig, create_agent

# ============================================================
# 1. 创建一个临时目录，放一些测试文件让 Agent 操作
# ============================================================
demo_dir = Path(tempfile.mkdtemp(prefix="flux_priority_demo_"))
print(f"测试目录: {demo_dir}\n")

# 创建示例 Python 文件
(demo_dir / "main.py").write_text("""\
import os

def greet(name: str) -> str:
    return f"Hello, {name}!"

def farewell(name: str) -> str:
    return f"Goodbye, {name}!"

if __name__ == "__main__":
    print(greet("World"))
""")

(demo_dir / "utils.py").write_text("""\
def add(a: int, b: int) -> int:
    return a + b

def multiply(a: int, b: int) -> int:
    return a * b
""")

(demo_dir / "README.md").write_text("""\
# Demo Project

This is a demo project for flux-agent priority tools.
""")


# ============================================================
# 2. 创建带 priority tools 的 ReactAgent
# ============================================================

llm = ChatOpenAI(
    model="gpt-4.1",
    base_url=DEFAULT_BASE_URL,
    api_key=DEFAULT_API_KEY,
)


config = AgentConfig(verbose=True)

# agent = ReactAgent(
#     llm=llm,
#     config=config,
# )
agent = create_agent(
    "supervisor",
    llm=llm,
    config=AgentConfig(verbose=True),
)

# 查看可用的工具
all_tools = agent._get_all_tools()
tool_names = [t.name for t in all_tools]
print(f"Agent 可用工具: {tool_names}")
print(f"其中优先级工具: bash, glob_search, grep_search, file_read, file_edit, file_write")
print()


# ============================================================
# 3. 演示任务：让 Agent 使用专用工具
# ============================================================

tasks = [
    f"请查看当前电脑 cpu 使用最高的5个进程",
    f"请在 {demo_dir} 目录下找到所有 .py 文件",
    f"请在 {demo_dir} 目录下搜索包含 'def' 的文件内容",
    f"请读取 {demo_dir / 'main.py'} 的内容",
    f"请将 {demo_dir / 'main.py'} 中的 'Hello' 替换为 'Hi'",
]

for i, task in enumerate(tasks, 1):
    print(f"\n{'='*60}")
    print(f"任务 {i}: {task}")
    print("="*60)

    result = agent.invoke(task)
    print(f"\n回答: {result.answer}")
    print(f"总步数: {result.total_steps}")
    print(f"token使用情况: {result.token_usage}")

    if result.steps:
        print("\n执行步骤:")
        for step in result.steps:
            if step.tool_name:
                print(f"  [{step.step_type.value}] 工具: {step.tool_name}")
