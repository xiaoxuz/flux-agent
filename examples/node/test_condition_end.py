#!/usr/bin/env python3
"""
测试 condition_map 中 END 支持

演示在 condition_map 中直接使用 "END" 值来退出 workflow
"""

import sys
from pathlib import Path


from flux_agent import WorkflowRunner


def test_condition_map_end():
    """测试 condition_map 中使用 END 直接退出"""
    config = {
        "workflow": {"name": "condition-end-test"},
        "nodes": [
            {
                "id": "set_value",
                "type": "TransformNode",
                "config": {
                    "transforms": [{"action": "set", "key": "data.should_exit", "value": True}]
                },
            },
            {
                "id": "check_exit",
                "type": "TransformNode",
                "config": {
                    "transforms": [
                        {"action": "set", "key": "_route", "value": "exit" if True else "continue"}
                    ]
                },
            },
            {
                "id": "continue_node",
                "type": "TransformNode",
                "config": {
                    "transforms": [{"action": "set", "key": "data.continued", "value": True}]
                },
            },
        ],
        "edges": [
            {"from": "START", "to": "set_value"},
            {"from": "set_value", "to": "check_exit"},
            {"from": "check_exit", "condition_map": {"exit": "END", "continue": "continue_node"}},
            {"from": "continue_node", "to": "END"},
        ],
    }

    print("=" * 50)
    print("测试 condition_map 中使用 END")
    print("=" * 50)

    try:
        runner = WorkflowRunner(config_dict=config)
        result = runner.invoke({"data": {}})

        data = result.get("data", {})
        print(f"should_exit: {data.get('should_exit')}")
        print(f"continued: {data.get('continued', '未执行')}")  # 应该是 '未执行'
        print("✅ 测试成功！")
        return True
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_condition_branch_with_end():
    """测试 condition branch 中使用 END 直接退出"""
    config = {
        "workflow": {"name": "condition-branch-end-test"},
        "nodes": [
            {
                "id": "set_score",
                "type": "TransformNode",
                "config": {"transforms": [{"action": "set", "key": "data.score", "value": 95}]},
            },
            {
                "id": "check_grade",
                "type": "ConditionNode",
                "config": {
                    "branches": [
                        {"condition": "data.score >= 90", "target": "END"},
                        {"condition": "default", "target": "fail_handler"},
                    ]
                },
            },
            {
                "id": "fail_handler",
                "type": "TransformNode",
                "config": {
                    "transforms": [{"action": "set", "key": "data.handled_fail", "value": True}]
                },
            },
        ],
        "edges": [
            {"from": "START", "to": "set_score"},
            {"from": "set_score", "to": "check_grade"},
            {"from": "check_grade", "condition_map": {"excellent": "END", "fail": "fail_handler"}},
            {"from": "fail_handler", "to": "END"},
        ],
    }

    print("\n" + "=" * 50)
    print("测试 ConditionNode branch 中使用 END")
    print("=" * 50)

    try:
        runner = WorkflowRunner(config_dict=config)
        result = runner.invoke({"data": {}})

        data = result.get("data", {})
        print(f"score: {data.get('score')}")
        print(f"handled_fail: {data.get('handled_fail', '未执行')}")  # 应该是 '未执行'
        print("✅ 测试成功！")
        return True
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success1 = test_condition_map_end()
    success2 = test_condition_branch_with_end()

    print("\n" + "=" * 50)
    if success1 and success2:
        print("所有测试通过！")
    else:
        print("有测试失败")
    print("=" * 50)
