#!/usr/bin/env python3
"""
ConditionNode 示例

演示条件分支路由
"""
import sys
from pathlib import Path


from auto_agent import WorkflowRunner

def main():
    config = {
        "workflow": {"name": "condition-demo"},
        "nodes": [
            {
                "id": "greet",
                "type": "LLMNode",
                "config": {
                    "model": "openai",
                    "model_name": "gpt-4o",
                    "system_prompt": "你是一个友好的助手，回答用户的问题。",
                    "user_prompt": "${data.question}",
                    "output_key": "data.score",
                    "temperature": 0.7,
                    "base_url": "",
                    "api_key": ""
                }
            },
            {
                "id": "check_grade",
                "type": "ConditionNode",
                "config": {
                    "branches": [
                        {"condition": "data.score >= 90", "target": "excellent"},
                        {"condition": "data.score >= 80", "target": "good"},
                        {"condition": "data.score >= 60", "target": "pass"},
                        {"condition": "default", "target": "fail"}
                    ]
                }
            },
            {
                "id": "excellent",
                "type": "TransformNode",
                "config": {
                    "transforms": [
                        {"action": "set", "key": "data.grade", "value": "优秀"},
                        {"action": "set", "key": "data.message", "value": "太棒了！继续保持！"}
                    ]
                }
            },
            {
                "id": "good",
                "type": "TransformNode",
                "config": {
                    "transforms": [
                        {"action": "set", "key": "data.grade", "value": "良好"},
                        {"action": "set", "key": "data.message", "value": "做得不错！"}
                    ]
                }
            },
            {
                "id": "pass",
                "type": "TransformNode",
                "config": {
                    "transforms": [
                        {"action": "set", "key": "data.grade", "value": "及格"},
                        {"action": "set", "key": "data.message", "value": "还需要努力！"}
                    ]
                }
            },
            {
                "id": "fail",
                "type": "TransformNode",
                "config": {
                    "transforms": [
                        {"action": "set", "key": "data.grade", "value": "不及格"},
                        {"action": "set", "key": "data.message", "value": "要加油了！"}
                    ]
                }
            }
        ],
        "edges": [
            {"from": "START", "to": "greet"},
            {"from": "greet", "to": "check_grade"},
            {
                "from": "check_grade",
                "condition_map": {
                    "excellent": "excellent",
                    "good": "good",
                    "pass": "pass",
                    "fail": "fail"
                }
            },
            {"from": "excellent", "to": "END"},
            {"from": "good", "to": "END"},
            {"from": "pass", "to": "END"},
            {"from": "fail", "to": "END"}
        ]
    }

    print("=" * 50)
    print("ConditionNode 示例：条件分支路由")
    print("=" * 50)

    runner = WorkflowRunner(config_dict=config)
    result = runner.invoke({
        "data": {"question": "69+1等于几, 只输出结果"}
    })

    data = result.get("data", {})
    print(f"分数: {data.get('score')}")
    print(f"等级: {data.get('grade')}")
    print(f"评语: {data.get('message')}")
    print("=" * 50)

if __name__ == "__main__":
    main()
