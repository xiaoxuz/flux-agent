#!/usr/bin/env python3
"""
SubgraphNode 示例

演示子图嵌套

注意: SubgraphNode 需要 JSON 配置文件路径，
这里展示如何通过代码模拟子图的效果。
"""
import sys
from pathlib import Path


from flux_agent import WorkflowRunner


sub_workflow_config = {
    "workflow": {"name": "sub-validation"},
    "nodes": [
        {
            "id": "check_input",
            "type": "TransformNode",
            "config": {
                "transforms": [
                    {"action": "set", "key": "data.valid", "value": True}
                ]
            }
        },
        {
            "id": "validate",
            "type": "TransformNode",
            "config": {
                "transforms": [
                    {"action": "set", "key": "data.validation_result", "value": "验证通过"},
                    {"action": "set", "key": "data.validation_score", "value": 95}
                ]
            }
        }
    ],
    "edges": [
        {"from": "START", "to": "check_input"},
        {"from": "check_input", "to": "validate"},
        {"from": "validate", "to": "END"}
    ]
}


def main():
    config = {
        "workflow": {"name": "subgraph-demo"},
        "nodes": [
            {
                "id": "prepare_data",
                "type": "TransformNode",
                "config": {
                    "transforms": [
                        {"action": "set", "key": "data.input", "value": "测试数据"}
                    ]
                }
            },
            {
                "id": "sub_process",
                "type": "TransformNode",
                "config": {
                    "transforms": [
                        {"action": "set", "key": "data.valid", "value": True},
                        {"action": "set", "key": "data.validation_result", "value": "验证通过"},
                        {"action": "set", "key": "data.validation_score", "value": 95}
                    ]
                }
            },
            {
                "id": "finalize",
                "type": "TransformNode",
                "config": {
                    "transforms": [
                        {"action": "set", "key": "data.status", "value": "completed"}
                    ]
                }
            }
        ],
        "edges": [
            {"from": "START", "to": "prepare_data"},
            {"from": "prepare_data", "to": "sub_process"},
            {"from": "sub_process", "to": "finalize"},
            {"from": "finalize", "to": "END"}
        ]
    }

    print("=" * 50)
    print("SubgraphNode 示例：子图嵌套")
    print("(这里用 TransformNode 模拟子图处理逻辑)")
    print("=" * 50)

    runner = WorkflowRunner(config_dict=config)
    result = runner.invoke({"data": {}})

    data = result.get("data", {})
    print(f"输入: {data.get('input')}")
    print(f"验证结果: {data.get('validation_result')}")
    print(f"验证分数: {data.get('validation_score')}")
    print(f"状态: {data.get('status')}")
    print("=" * 50)

if __name__ == "__main__":
    main()
