#!/usr/bin/env python3
"""
示例：运行简单工作流

使用方法：
    ./venv/bin/python examples/run_example.py
"""

import sys
from pathlib import Path


from auto_agent import WorkflowRunner

def example_input_hook(node_id, state):
    print(f"[IN]>>>>>>>>>>>>>> {node_id}: {state.get('data', {})}")
    # pass
    # return state  # 可修改后返回

def example_output_hook(node_id, state, output):
    print(f"[OUT]<<<<<<<<<<<<< {node_id}: {output}")
    # pass

def greet(name: str, taskID: str) -> str:
    """生成问候语"""
    return f"【当前任务 ID】:{taskID} - Hello, {name}!"

def get_weather(city: str) -> str:
    """获取城市天气（模拟）"""
    return f"{city}今天天气晴朗，温度255555℃"

def get_city(greet: str) -> str:
    return "北京"

def main():
    import logging

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S"
    )
    example_dir = Path(__file__).parent

    runner = WorkflowRunner(
        config_path=str(example_dir / "simple_chain.json"), 
        on_node_input=example_input_hook,
        on_node_output=example_output_hook,
        tools={"greet": greet, "get_weather": get_weather, "get_city": get_city}
    )

    result = runner.invoke(
        {"data": {"user_input": "你好，请用一句话介绍你自己"}, "context":{"task_id":"17441004694569588072"}}
    )

    print("工作流执行完成！")
    print("-" * 50)
    print(result)
    print("-" * 50)


if __name__ == "__main__":
    main()
