#!/usr/bin/env python3
"""
示例：运行简单工作流

使用方法：
    ./venv/bin/python examples/run_example.py
"""

import sys
from pathlib import Path


from flux_agent import WorkflowRunner
from flux_agent.utils import pretty_state

def example_input_hook(node_id, state):
    print(f"[IN]>>>>>>>>>>>>>> {node_id}: {state.get('data', {})}")
    # pass
    # return state  # 可修改后返回

def example_output_hook(node_id, state, output):
    print(f"[OUT]<<<<<<<<<<<<< {node_id}: {output}")
    # pass

def main():
    import logging

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S"
    )
    example_dir = Path(__file__).parent

    runner = WorkflowRunner(
        config_path=str(example_dir / "question_script_config.json"), 
        # on_node_input=example_input_hook,
        # on_node_output=example_output_hook,
    )

    result = runner.invoke(
        {"data": {"tid": 1604096837}}
    )

    print("工作流执行完成！")
    print("-" * 50)
    print(result.get("data", {}).get("script_result", {}))
    # print(pretty_state(result.get("data", {}).get("script_raw", {})))
    print("-" * 50)


if __name__ == "__main__":
    main()
