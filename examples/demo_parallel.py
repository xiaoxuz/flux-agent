#!/usr/bin/env python3
"""
ParallelNode 示例

演示并行执行多个分支
"""
import sys
from pathlib import Path


from auto_agent import WorkflowRunner

def main():
    config = {
        "workflow": {"name": "parallel-demo"},
        "nodes": [
            {
                "id": "init",
                "type": "TransformNode",
                "config": {
                    "transforms": [
                        {"action": "set", "key": "data.start_time", "value": "now"}
                    ]
                }
            },
            {
                "id": "branch_a",
                "type": "TransformNode",
                "config": {
                    "transforms": [
                        {"action": "set", "key": "data.task_a", "value": "任务A完成"},
                        {"action": "set", "key": "data.result_a", "value": 100}
                    ]
                }
            },
            {
                "id": "branch_b",
                "type": "TransformNode",
                "config": {
                    "transforms": [
                        {"action": "set", "key": "data.task_b", "value": "任务B完成"},
                        {"action": "set", "key": "data.result_b", "value": 200}
                    ]
                }
            },
            {
                "id": "branch_c",
                "type": "TransformNode",
                "config": {
                    "transforms": [
                        {"action": "set", "key": "data.task_c", "value": "任务C完成"},
                        {"action": "set", "key": "data.result_c", "value": 300}
                    ]
                }
            },
            {
                "id": "merge",
                "type": "TransformNode",
                "config": {
                    "transforms": [
                        {"action": "set", "key": "data.total", "value": 600}
                    ]
                }
            }
        ],
        "edges": [
            {"from": "START", "to": "init"},
            {"from": "init", "to": "branch_a"},
            {"from": "init", "to": "branch_b"},
            {"from": "init", "to": "branch_c"},
            {"from": "branch_a", "to": "merge"},
            {"from": "branch_b", "to": "merge"},
            {"from": "branch_c", "to": "merge"},
            {"from": "merge", "to": "END"}
        ]
    }

    print("=" * 50)
    print("ParallelNode 示例：并行执行")
    print("=" * 50)

    runner = WorkflowRunner(config_dict=config)
    result = runner.invoke({"data": {}})

    data = result.get("data", {})
    print(f"任务A: {data.get('task_a')}")
    print(f"任务B: {data.get('task_b')}")
    print(f"任务C: {data.get('task_c')}")
    print(f"总计: {data.get('total')}")
    print("=" * 50)

if __name__ == "__main__":
    main()
