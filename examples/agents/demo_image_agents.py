#!/usr/bin/env python3
"""
Flux-Agent 智能 Agent 模块演示

演示 4 种 Agent 模式的使用：
1. ReAct - 简单问答
2. Deep - 深度研究（可选）
3. Plan-Execute - 复杂任务规划执行
4. Reflexion - 自我反思改进
"""

from langchain_openai import ChatOpenAI
from flux_agent.agents import (
    create_agent,
    list_available_modes,
    AgentMode,
    AgentConfig,
    AgentOutput,
    AgentInput,
    StepType,
)
from dotenv import load_dotenv
load_dotenv()
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from examples.tools import mock_search

import requests
import base64
from urllib.parse import urlparse


def image_url_to_base64(url: str, timeout: int = 10, with_prefix: bool = False) -> str:
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


def demo_available_modes():
    """演示查看所有可用模式"""
    print("=" * 60)
    print("可用的 Agent 模式:")
    print("=" * 60)
    
    for mode in list_available_modes():
        print(f"  - {mode}")
    print()
llm = ChatOpenAI(model="gpt-4.1", temperature=1, base_url=os.getenv("OPENAI_BASE_URL"), api_key=os.getenv("OPENAI_API_KEY"))
def demo_react_agent():
    """演示 ReAct 模式"""
    print("=" * 60)
    print("示例1: ReAct 模式 - 简单问答")
    print("=" * 60)
    agent = create_agent(
        "react",
        llm=llm,
        config=AgentConfig(verbose=True),
        tools=[mock_search]
    )
    input = AgentInput(
        query=" 告诉我你是谁? 描述下图片内容，然后再看下北京天气？",
        messages=[{"role": "user", "content": "你是AI 小弟"}],
        image_list=[
            image_url_to_base64(f"https://{os.getenv('TEST_IMAGE_HOST')}a78f8509db7dfcb55861757ae2bc9e4b.jpg"),
            image_url_to_base64(f"https://{os.getenv('TEST_IMAGE_HOST')}f3685cdf32f66ad60412b0a782fcd362.jpg"),
        ]
    )
    result = agent.invoke(input)
    
    print(f"\n回答: {result.answer[:200]}...")
    print(f"状态: {result.status.value}")
    print(f"步数: {result.total_steps}")
    print(f"token: {result.token_usage}")
    print()


def demo_plan_execute_agent():
    """演示 Plan-Execute 模式"""
    print("=" * 60)
    print("示例2: Plan-Execute 模式 - 复杂任务")
    print("=" * 60)
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    agent = create_agent(
        "plan_execute",
        llm=llm,
        enable_replan=True,
        config=AgentConfig(verbose=True),
    )

    input = AgentInput(
        query="找出两张图片相同点",
        image_list=[
            image_url_to_base64(f"https://{os.getenv('TEST_IMAGE_HOST')}a78f8509db7dfcb55861757ae2bc9e4b.jpg"),
            image_url_to_base64(f"https://{os.getenv('TEST_IMAGE_HOST')}f3685cdf32f66ad60412b0a782fcd362.jpg"),
        ]
    )
    
    result = agent.invoke(input)
    
    print(f"\n回答: {result.answer[:300]}...")
    print(f"状态: {result.status.value}")
    print(f"计划步数: {len(result.metadata.get('plan', []))}")
    print(f"token: {result.token_usage}")
    print()


def demo_reflexion_agent():
    """演示 Reflexion 模式"""
    print("=" * 60)
    print("示例3: Reflexion 模式 - 自我反思改进")
    print("=" * 60)
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    agent = create_agent(
        "reflexion",
        llm=llm,
        max_iterations=2,  # 最多反思 2 轮
        quality_threshold=10.0,
        config=AgentConfig(verbose=True),
    )
    input = AgentInput(
        query="描述图片内容",
        image_list=[
            image_url_to_base64(f"https://{os.getenv('TEST_IMAGE_HOST')}a78f8509db7dfcb55861757ae2bc9e4b.jpg"),
            image_url_to_base64(f"https://{os.getenv('TEST_IMAGE_HOST')}f3685cdf32f66ad60412b0a782fcd362.jpg"),
        ]
    )
    
    
    result = agent.invoke(input)
    
    
    print(f"\n回答: {result.answer[:800]}...")
    print(f"状态: {result.status.value}")
    print(f"总迭代: {result.metadata.get('total_iterations', 0)}")
    
    # 查看反思过程
    reflections = result.get_steps_by_type(StepType.REFLECTION)
    print(f"反思次数: {len(reflections)}")
    print(f"token: {result.token_usage}")
    print()


def demo_unified_output():
    """演示统一输出格式"""
    print("=" * 60)
    print("示例4: 统一输出格式")
    print("=" * 60)
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    for mode in ["react", "plan_execute"]:
        agent = create_agent(mode, llm=llm)
        result = agent.invoke("1+1等于几？")
        
        print(f"\n--- {mode} ---")
        print(f"  answer: {result.answer[:50]}...")
        print(f"  status: {result.status.value}")
        print(f"  steps: {result.total_steps}")
        print(f"  time: {result.elapsed_time:.2f}s" if result.elapsed_time else "  time: N/A")
    print()


def main():
    print("\n" + "=" * 60)
    print("  Flux-Agent 智能 Agent 模块演示")
    print("=" * 60 + "\n")
    
    demo_available_modes()
    
    # 简单演示（需要 API key）
    try:
        # demo_react_agent()
        demo_plan_execute_agent()
        # demo_reflexion_agent()
        # demo_unified_output()
    except Exception as e:
        print(f"运行示例需要配置 OPENAI_API_KEY: {e}")
    
    print("=" * 60)
    print("  演示完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
