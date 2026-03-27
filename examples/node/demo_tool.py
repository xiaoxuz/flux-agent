#!/usr/bin/env python3
"""
ToolNode 和 LLMNode 工具调用示例

演示三种工具使用方式：
1. config_dict 中定义 tools - 适合纯配置场景
2. WorkflowRunner(tools=...) 参数 - 适合 JSON 配置 + 代码混合场景
3. LLMNode + tools - LLM 自动调用工具
"""

import sys
from pathlib import Path


from flux_agent import WorkflowRunner


def calculate(expression: str) -> str:
    """计算数学表达式"""
    try:
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"错误: {e}"


def greet(name: str) -> str:
    """生成问候语"""
    return f"你好11111111111111111, {name}!"


def get_weather(city: str) -> str:
    """获取城市天气（模拟）"""
    return f"{city}今天天气晴朗，温度255555℃"


def main():
    print("=" * 60)
    print("Tool 示例：工具调用")
    print("=" * 60)

    # 方式1：config_dict 中定义 tools（纯配置方式）
    print("\n【方式1：config_dict 中定义 tools】\n")

    config_with_tools = {
        "workflow": {"name": "tool-demo"},
        "tools": [
            {
                "name": "greet",
                "implementation": greet,  # 直接引用 Python 函数
            },
            {
                "name": "calculate",
                "implementation": calculate,
            },
        ],
        "nodes": [
            {
                "id": "call_greet",
                "type": "ToolNode",
                "config": {
                    "tool_name": "greet",
                    "args": {"name": "张三"},
                    "output_key": "data.greeting",
                },
            },
            {
                "id": "call_calculate",
                "type": "ToolNode",
                "config": {
                    "tool_name": "calculate",
                    "args": {"expression": "2 ** 10 + 100"},
                    "output_key": "data.calc_result",
                },
            },
        ],
        "edges": [
            {"from": "START", "to": "call_greet"},
            {"from": "call_greet", "to": "call_calculate"},
            {"from": "call_calculate", "to": "END"},
        ],
    }

    runner1 = WorkflowRunner(config_dict=config_with_tools)
    result1 = runner1.invoke({"data": {}})
    data1 = result1.get("data", {})
    print(f"问候: {data1.get('greeting')}")
    print(f"计算: 2 ** 10 + 100 = {data1.get('calc_result')}")

    # 方式2：WorkflowRunner(tools=...) 参数（推荐，支持 JSON 配置文件）
    print("\n" + "=" * 60)
    print("【方式2：tools 参数注册工具】\n")
    print("适用场景：config_path='workflow.json' + tools={...}")
    print("优点：敏感工具不写进配置文件\n")

    config_simple = {
        "workflow": {"name": "tool-demo"},
        "nodes": [
            {
                "id": "call_tool",
                "type": "ToolNode",
                "config": {
                    "tool_name": "greet",
                    "args": {"name": "李四"},
                    "output_key": "data.greeting",
                },
            },
        ],
        "edges": [
            {"from": "START", "to": "call_tool"},
            {"from": "call_tool", "to": "END"},
        ],
    }

    # 工具通过参数传入，配置中不需要 tools 字段
    runner2 = WorkflowRunner(
        config_dict=config_simple, tools={"greet": greet, "calculate": calculate}
    )
    result2 = runner2.invoke({"data": {}})
    print(f"问候: {result2.get('data', {}).get('greeting')}")

    # 方式3：LLMNode + tools（LLM 自动决定调用哪个工具）
    print("\n" + "=" * 60)
    print("【方式3：LLMNode + tools（LLM 自动调用工具）】\n")

    llm_config = {
        "workflow": {"name": "llm-tool-demo"},
        "nodes": [
            {
                "id": "llm_agent",
                "type": "LLMNode",
                "config": {
                    "model_name": "MiniMax-M2.5",
                    "system_prompt": "你是一个助手，可以使用工具来帮助用户。",
                    "user_prompt": "请帮我问候王五，然后告诉他北京今天的天气",
                    "tools": ["greet", "get_weather"],  # LLM 可用的工具列表
                    "output_key": "data.response",
                    "base_url": "",
                    "api_key": "",
                },
            }
        ],
        "edges": [{"from": "START", "to": "llm_agent"}, {"from": "llm_agent", "to": "END"}],
    }

    llm_runner = WorkflowRunner(
        config_dict=llm_config, tools={"greet": greet, "get_weather": get_weather}
    )

    llm_result = llm_runner.invoke({"data": {}})
    print(f"LLM 响应: {llm_result.get('data', {}).get('response', '无')[:200]}...")

    print("\n" + "=" * 60)
    print("总结：")
    print("  - 方式1: config_dict['tools'] - 纯配置，适合简单场景")
    print("  - 方式2: tools 参数 - 推荐，支持 JSON 配置文件")
    print("  - 方式3: LLMNode + tools - LLM 自动调用工具")
    print("=" * 60)


if __name__ == "__main__":
    main()
