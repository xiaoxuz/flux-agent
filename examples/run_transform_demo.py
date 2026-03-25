#!/usr/bin/env python3
"""
示例：数据转换工作流（无需 API Key）

使用方法：
    ./venv/bin/python examples/run_transform_demo.py
"""

import sys
from pathlib import Path


from auto_agent import WorkflowRunner


def main():
    example_dir = Path(__file__).parent

    runner = WorkflowRunner(config_path=str(example_dir / "transform_demo.json"))

    print("=" * 50)
    print("开始执行工作流...")
    print("=" * 50)

    result = runner.invoke({"data": {}})

    print("\n工作流执行完成！")
    print("=" * 50)
    print(f"消息: {result.get('data', {}).get('message')}")
    print(f"计数: {result.get('data', {}).get('count')}")
    print(f"日志: {result.get('data', {}).get('logs')}")
    print(f"状态: {result.get('data', {}).get('status')}")
    print(f"最终消息: {result.get('data', {}).get('final_message')}")
    print("=" * 50)


if __name__ == "__main__":
    main()
