#!/usr/bin/env python3
"""
Flux-Agent Supervisor Agent 演示

演示 Supervisor 模式的四种工作场景：
1. 手动模式：显式指定 researcher + writer worker，带 code tools + MCP servers
2. 自动模式：不传 workers，LLM 自动规划角色和工具
3. 简单 query：LLM 判断单角色够用，直接回复
4. 自动模式 + Skill + 工具：主 agent 配置 2 个工具 + 1 个 skill，LLM 动态规划两个 worker 分别使用
"""

import os
import sys
import logging
import tempfile
from pathlib import Path
from flux_agent.agents import create_agent, WorkerConfig, AgentConfig, SkillLoader, Skill, AgentInput


from dotenv import load_dotenv
load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
# ============================================================================
# 演示 1：手动模式 — 显式指定 worker
# ============================================================================
def demo_manual_mode():
    """手动模式：指定 researcher + writer worker，各取所需工具"""
   

    # 注意：这里只声明工具名，实际需要从 tool registry 获取 BaseTool 实例
    # 这里用纯配置演示接口用法
    supervisor = create_agent(
        "supervisor",
        llm=_get_llm(),
        workers={
            "researcher": WorkerConfig(
                name="researcher",
                mode="react",
                description="负责搜索和调研最新信息",
            ),
            "writer": WorkerConfig(
                name="writer",
                mode="react",
                description="负责撰写报告和总结",
            ),
        },
        parallel=True,
        config=AgentConfig(verbose=True),
    )

    print(f"\n{'='*60}")
    print("演示 1：手动模式")
    print(f"{'='*60}")
    print(f"Worker: {supervisor._workers.keys()}")
    print(f"Query: 调研 2024 年 AI 领域的重要突破并写一份总结报告")

    result = supervisor.invoke("调研 2024 年 AI 领域的重要突破并写一份总结报告")
    print(f"\n回答:\n{result.answer[:500]}...")
    print(f"状态: {result.status.value}, 步数: {result.total_steps}")
    print(f"token: {result.token_usage}")


# ============================================================================
# 演示 2：自动模式 — LLM 自动规划角色和工具
# ============================================================================
def demo_auto_mode():
    """自动模式：不传 workers，LLM 动态规划角色和工具分配"""
    from flux_agent.agents import create_agent

    supervisor = create_agent(
        "supervisor",
        llm=_get_llm(),
        config=AgentConfig(verbose=True),
    )

    print(f"\n{'='*60}")
    print("演示 2：自动模式")
    print(f"{'='*60}")
    print(f"Query: 分析 Python 3.13 的新特性，并写一份对比文档")

    result = supervisor.invoke("分析 Python 3.13 的新特性，并写一份对比文档,必须用多 agent处理, 然后agent是 react 模式, 然后模拟下生成(a/b/c)三个 agent, b依赖a的结果， c依赖 a和 b 的结果,  然后a输出111111  b输出2222 c输出3333")
    print(f"\n回答:\n{result.answer[:500]}...")
    print(f"状态: {result.status.value}, 步数: {result.total_steps}")
    print(f"token: {result.token_usage}")


# ============================================================================
# 演示 3：简单 query — LLM 判断单角色够用
# ============================================================================
def demo_simple_query():
    """简单 query：LLM 判断无需多角色，直接回复"""
    from flux_agent.agents import create_agent

    supervisor = create_agent(
        "supervisor",
        llm=_get_llm(),
        config=AgentConfig(verbose=True)
    )

    print(f"\n{'='*60}")
    print("演示 3：简单 query")
    print(f"{'='*60}")
    print(f"Query: 什么是 Python？")

    result = supervisor.invoke("什么是 Python？")
    print(f"\n回答:\n{result.answer[:500]}...")
    print(f"状态: {result.status.value}, 步数: {result.total_steps}")
    print(f"token: {result.token_usage}") 


# ============================================================================
# 演示 4：自动模式 + Skill + 工具
# ============================================================================
def _create_demo_skill_dir() -> str:
    """创建演示用的 skill 目录"""
    base = Path(tempfile.mkdtemp(prefix="flux_supervisor_skills_"))

    # Skill: data_analyzer — 数据分析 skill
    skill_dir = base / "data_analyzer"
    skill_dir.mkdir()
    scripts_dir = skill_dir / "scripts"
    scripts_dir.mkdir()

    (skill_dir / "SKILL.md").write_text("""\
---
name: data_analyzer
description: 数据统计分析工具，用于计算列表数据的总和、平均值、最大值、最小值
version: 1.0.0
---

# Data Analyzer

## 功能
对传入的数字列表进行统计分析，输出总和、平均值、最大值、最小值。

## 使用方法
使用 activate_skill 激活本 skill 后，可通过 run_skill_script 执行 analyze.py 脚本进行分析。

## 可用脚本
- `analyze.py`: 对 JSON 格式的数字列表进行统计分析，输出 count/sum/average/max/min
""")

    # 数据分析脚本
    (scripts_dir / "analyze.py").write_text("""\
import sys
import json

def main(data_json):
    data = json.loads(data_json)
    result = {
        "count": len(data),
        "sum": sum(data),
        "average": round(sum(data) / len(data), 2) if data else 0,
        "max": max(data) if data else None,
        "min": min(data) if data else None,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python analyze.py '[数字列表]'", file=sys.stderr)
        sys.exit(1)
    main(sys.argv[1])
""")

    return str(base)


def _create_demo_tools():
    """创建 2 个演示工具"""
    from langchain_core.tools import tool

    @tool
    def get_current_time() -> str:
        """获取当前日期和时间，格式: YYYY-MM-DD HH:MM:SS"""
        import datetime
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @tool
    def celsius_to_fahrenheit(celsius: float) -> float:
        """将摄氏度转换为华氏度。参数 celsius 是摄氏度数值。"""
        return celsius * 9 / 5 + 32

    return [get_current_time, celsius_to_fahrenheit]


def demo_auto_with_skill_and_tools():
    """自动模式：主 agent 配置 2 个工具 + 1 个 skill，LLM 动态规划两个 worker 分别使用

    场景：天气数据分析 + 报告撰写
    - data_analyzer skill：统计分析温度数据
    - convert_units 工具：温度单位换算（摄氏度转华氏度）
    - get_current_time 工具：获取报告时间戳
    """
    # 创建 2 个工具
    user_tools = _create_demo_tools()

    # 创建 1 个 skill
    skill_dir = _create_demo_skill_dir()
    loader = SkillLoader(skill_dir)
    skills = loader.load_all()
    print(f"加载 Skill: {[s.name for s in skills]}")

    # 不传 workers，让 LLM 自动规划
    supervisor = create_agent(
        "supervisor",
        llm=_get_llm(),
        tools=user_tools,
        skills=skills,
        config=AgentConfig(verbose=True),
    )

    print(f"\n{'='*60}")
    print("演示 4：自动模式 + Skill + 工具")
    print(f"{'='*60}")
    print(f"配置: 2 个工具 (get_current_time, celsius_to_fahrenheit) + 1 个 Skill (data_analyzer)")
    print(f"Query: 我需要分析一周的气温数据并生成报告。气温数据(摄氏度): [18, 22, 15, 20, 25, 19, 23]。请先用数据分析工具统计分析气温（总和/平均值/最高/最低），然后把平均值从摄氏度换算为华氏度，最后生成带当前时间戳的专业气象分析报告。要求使用数据分析员和气象报告员两个角色协作完成，报告员需要依赖分析员的数据结果。")

    result = supervisor.invoke("我需要分析一周的气温数据并生成报告。气温数据(摄氏度): [18, 22, 15, 20, 25, 19, 23]。请先用数据分析工具统计分析气温（总和/平均值/最高/最低），然后把平均值从摄氏度换算为华氏度，最后生成带当前时间戳的专业气象分析报告。要求使用数据分析员和气象报告员两个角色协作完成，报告员需要依赖分析员的数据结果。")
    print(f"\n回答:\n{result.answer}")
    print(f"\n状态: {result.status.value}, 步数: {result.total_steps}")
    print(f"token: {result.token_usage}")

def image_url_to_base64(url: str, timeout: int = 10, with_prefix: bool = False) -> str:
    import requests
    import base64
    """
    将图片 URL 转换为 Base64 编码字符串

    Args:
        url: 图片的 URL 地址
        timeout: 请求超时时间（秒）
        with_prefix: 是否添加 data URI 前缀（如 data:image/png;base64,）

    Returns:
        Base64 编码的字符串
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                       'AppleWebKit/537.36 (KHTML, like Gecko) '
                       'Chrome/120.0.0.0 Safari/537.36'
    }

    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()

    # 获取图片的 MIME 类型
    content_type = response.headers.get('Content-Type', 'image/png')

    # 编码为 base64
    base64_str = base64.b64encode(response.content).decode('utf-8')

    if with_prefix:
        return f"data:{content_type};base64,{base64_str}"

    return base64_str

def demo_auto_image_test():
    # 不传 workers，让 LLM 自动规划
    supervisor = create_agent(
        "supervisor",
        llm=_get_llm(),
        config=AgentConfig(verbose=True),
    )

    input = AgentInput(
        query="描述图片内容, 要用2个 agent，分别描述一个图片",
        # query="找出两张图片相同点, 要用3个 agent，一个描述第一个图片，一个描述第二个图片，一个对比两个图片的描述",
        image_list=[
            image_url_to_base64(f"https://{os.getenv('TEST_IMAGE_HOST')}a78f8509db7dfcb55861757ae2bc9e4b.jpg"),
            image_url_to_base64(f"https://{os.getenv('TEST_IMAGE_HOST')}f3685cdf32f66ad60412b0a782fcd362.jpg"),
        ]
    )

    result = supervisor.invoke(input)
    print(f"\n回答:\n{result.answer}")
    print(f"\n状态: {result.status.value}, 步数: {result.total_steps}")
    print(f"token: {result.token_usage}")


def _get_llm():
    """获取 LLM 实例（从环境变量读取配置，默认使用通义千问）"""
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(model="gpt-4.1", temperature=1, base_url=os.getenv("OPENAI_BASE_URL"), api_key=os.getenv("OPENAI_API_KEY"))


if __name__ == "__main__":
    print("Flux-Agent Supervisor Agent 演示")
    print("请确保已设置 OPENAI_API_KEY 环境变量")

    # demo_manual_mode()
    # demo_auto_mode()
    # demo_simple_query()
    # demo_auto_with_skill_and_tools()
    demo_auto_image_test()

    print("\n演示完成")
