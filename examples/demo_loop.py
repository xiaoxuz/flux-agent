#!/usr/bin/env python3
"""
LoopNode 示例

演示循环执行（配合 ConditionNode 实现循环）
"""
import sys
from pathlib import Path


from auto_agent import WorkflowRunner

def main():
    config = {
        "workflow": {"name": "loop-demo"},
        "nodes": [
            {
                "id": "init",
                "type": "TransformNode",
                "config": {
                    "transforms": [
                        {"action": "set", "key": "data.counter", "value": 0},
                        {"action": "set", "key": "data.max", "value": 5},
                        {"action": "set", "key": "data.history", "value": []}
                    ]
                }
            },
            {
                "id": "process",
                "type": "TransformNode",
                "config": {
                    "transforms": [
                        {"action": "increment", "key": "data.counter"},
                        {"action": "append", "key": "data.history", "value": "处理中..."}
                    ]
                }
            },
            {
                "id": "check_loop",
                "type": "ConditionNode",
                "config": {
                    "branches": [
                        {"condition": "data.counter < data.max", "target": "process"},
                        {"condition": "default", "target": "done"}
                    ]
                }
            },
            {
                "id": "done",
                "type": "TransformNode",
                "config": {
                    "transforms": [
                        {"action": "set", "key": "data.status", "value": "completed"}
                    ]
                }
            }
        ],
        "edges": [
            {"from": "START", "to": "init"},
            {"from": "init", "to": "process"},
            {"from": "process", "to": "check_loop"},
            {
                "from": "check_loop",
                "condition_map": {
                    "process": "process",
                    "done": "done"
                }
            },
            {"from": "done", "to": "END"}
        ]
    }

    print("=" * 50)
    print("LoopNode 示例：循环执行（通过 ConditionNode 实现）")
    print("=" * 50)

    runner = WorkflowRunner(config_dict=config)
    result = runner.invoke({"data": {}})

    data = result.get("data", {})
    print(f"计数器: {data.get('counter')}")
    print(f"最大值: {data.get('max')}")
    print(f"状态: {data.get('status')}")
    print(f"历史记录: {len(data.get('history', []))} 条")
    print("=" * 50)

if __name__ == "__main__":
    main()
