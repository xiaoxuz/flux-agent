#!/usr/bin/env python3
"""
TransformNode 示例

演示各种数据转换操作
"""
import sys
from pathlib import Path


from flux_agent import WorkflowRunner

def main():
    config = {
        "workflow": {"name": "transform-demo"},
        "nodes": [
            {
                "id": "init",
                "type": "TransformNode",
                "config": {
                    "transforms": [
                        {"action": "set", "key": "data.name", "value": "Flux-Agent"},
                        {"action": "set", "key": "data.version", "value": "1.0.0"},
                        {"action": "set", "key": "data.count", "value": 0}
                    ]
                }
            },
            {
                "id": "increment",
                "type": "TransformNode",
                "config": {
                    "transforms": [
                        {"action": "increment", "key": "data.count"},
                        {"action": "increment", "key": "data.count"},
                        {"action": "increment", "key": "data.count"}
                    ]
                }
            },
            {
                "id": "list_ops",
                "type": "TransformNode",
                "config": {
                    "transforms": [
                        {"action": "set", "key": "data.tags", "value": ["python", "agent"]},
                        {"action": "append", "key": "data.tags", "value": "langgraph"},
                        {"action": "append", "key": "data.tags", "value": "llm"}
                    ]
                }
            },
            {
                "id": "merge_config",
                "type": "TransformNode",
                "config": {
                    "transforms": [
                        {"action": "set", "key": "data.config", "value": {"debug": False}},
                        {"action": "merge", "key": "data.config", "value": {"timeout": 30}},
                        {"action": "merge", "key": "data.config", "value": {"debug": True}},
                        {"action": "merge", "key": "data.config", "value": {"context": "${data.tags}"}}
                    ]
                }
            }
        ],
        "edges": [
            {"from": "START", "to": "init"},
            {"from": "init", "to": "increment"},
            {"from": "increment", "to": "list_ops"},
            {"from": "list_ops", "to": "merge_config"},
            {"from": "merge_config", "to": "END"}
        ]
    }

    print("=" * 50)
    print("TransformNode 示例：数据转换操作")
    print("=" * 50)

    runner = WorkflowRunner(config_dict=config)
    result = runner.invoke({"data": {}})

    data = result.get("data", {})
    print(f"名称: {data.get('name')}")
    print(f"版本: {data.get('version')}")
    print(f"计数: {data.get('count')}")
    print(f"标签: {data.get('tags')}")
    print(f"配置: {data.get('config')}")
    print("=" * 50)

if __name__ == "__main__":
    main()
