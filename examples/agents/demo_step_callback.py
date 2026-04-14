#!/usr/bin/env python3
"""
Flux-Agent 步骤级实时回调演示

演示 AgentConfig.on_step 回调功能：
每完成一个步骤就实时获取中间进度，而非等所有步骤完成后才返回结果。
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dotenv import load_dotenv
load_dotenv()

from langchain_openai import ChatOpenAI
from flux_agent.agents import (
    create_agent,
    AgentConfig,
    StepType,
)
from examples.tools import mock_search


llm = ChatOpenAI(
    model="gpt-4.1",
    temperature=1,
    base_url=os.getenv("OPENAI_BASE_URL"),
    api_key=os.getenv("OPENAI_API_KEY"),
)


def make_callback(prefix: str):
    """创建带时间戳和格式的 step 回调"""
    start = time.time()

    def on_step(step):
        elapsed = time.time() - start
        print(f"分步骤输出：[{elapsed:.2f}s] {prefix} | {step.step_type.value}: {step.content[:80]}")

    return on_step


def demo_react_callback():
    """演示 ReAct 模式 on_step 实时回调"""
    print("=" * 60)
    print("示例1: ReAct - 步骤级实时回调")
    print("=" * 60)

    agent = create_agent(
        "react",
        llm=llm,
        config=AgentConfig(
            verbose=False,
            on_step=make_callback("ReAct"),
        ),
        tools=[mock_search],
    )

    print("\n执行中...\n")
    result = agent.invoke("2024年 AI 领域有什么重大突破？北京天气怎么样")

    print(f"\n最终回答: {result.answer[:200]}...")
    print(f"总步数: {result.total_steps} | 耗时: {result.elapsed_time:.2f}s\n")


def demo_plan_execute_callback():
    """演示 Plan-Execute 模式 on_step 实时回调"""
    print("=" * 60)
    print("示例2: Plan-Execute - 步骤级实时回调")
    print("=" * 60)

    agent = create_agent(
        "plan_execute",
        llm=ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            base_url=os.getenv("OPENAI_BASE_URL"),
            api_key=os.getenv("OPENAI_API_KEY"),
        ),
        enable_replan=True,
        config=AgentConfig(
            verbose=False,
            on_step=make_callback("PlanExecute"),
        ),
    )

    print("\n执行中...\n")
    result = agent.invoke("分析 Python 和 JavaScript 的优缺点，并给出选择建议")

    print(f"\n最终回答: {result.answer[:200]}...")
    print(f"总步数: {result.total_steps} | 耗时: {result.elapsed_time:.2f}s\n")


def demo_reflexion_callback():
    """演示 Reflexion 模式 on_step 实时回调"""
    print("=" * 60)
    print("示例3: Reflexion - 步骤级实时回调")
    print("=" * 60)

    agent = create_agent(
        "reflexion",
        llm=ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            base_url=os.getenv("OPENAI_BASE_URL"),
            api_key=os.getenv("OPENAI_API_KEY"),
        ),
        max_iterations=2,
        quality_threshold=8.0,
        config=AgentConfig(
            verbose=False,
            on_step=make_callback("Reflexion"),
        ),
    )

    print("\n执行中...\n")
    result = agent.invoke("写一个 Python 函数，计算斐波那契数列")

    print(f"\n最终回答: {result.answer[:200]}...")
    print(f"总步数: {result.total_steps} | 耗时: {result.elapsed_time:.2f}s\n")


def demo_no_callback_still_works():
    """验证无回调时行为不变"""
    print("=" * 60)
    print("示例4: 无回调 - 行为验证（一次性返回）")
    print("=" * 60)

    agent = create_agent(
        "plan_execute",
        llm=ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            base_url=os.getenv("OPENAI_BASE_URL"),
            api_key=os.getenv("OPENAI_API_KEY"),
        ),
        config=AgentConfig(verbose=False),  # 无 on_step
    )

    result = agent.invoke("1+1等于几？")
    print(f"一次性返回结果: {result.answer[:100]}...")
    print(f"总步数: {result.total_steps} | 耗时: {result.elapsed_time:.2f}s\n")


def main():
    print("\n" + "=" * 60)
    print("  Flux-Agent 步骤级实时回调演示")
    print("=" * 60 + "\n")

    try:
        demo_react_callback()
        # demo_plan_execute_callback()
        # demo_reflexion_callback()
        # demo_no_callback_still_works()
    except Exception as e:
        print(f"运行需要配置 OPENAI_API_KEY: {e}")
        import traceback
        traceback.print_exc()

    print("=" * 60)
    print("  演示完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
