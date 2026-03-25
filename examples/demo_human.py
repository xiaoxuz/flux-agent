#!/usr/bin/env python3
"""
HumanInputNode 示例

演示人工介入节点

注意: 框架默认使用内存模式 checkpointer，HumanInputNode 可正常工作
运行后会在需要人工输入时暂停，可通过 resume() 方法恢复
"""

import sys
from pathlib import Path


from auto_agent import WorkflowRunner


def main():
    config = {
        "workflow": {"name": "human-input-demo"},
        "nodes": [
            {
                "id": "prepare",
                "type": "TransformNode",
                "config": {
                    "transforms": [
                        {"action": "set", "key": "data.draft", "value": "这是一个待审核的内容..."},
                        {"action": "set", "key": "data.status", "value": "pending_review"},
                    ]
                },
            },
            {
                "id": "review",
                "type": "HumanInputNode",
                "config": {
                    "prompt": "请审核以下内容：\n\n${data.draft}\n\n请输入 'approved' 或 'rejected'",
                    "output_key": "data.review_decision",
                    "options": ["approved", "rejected"],
                    "default_value": "approved",
                },
            },
            {
                "id": "process_result",
                "type": "TransformNode",
                "config": {
                    "transforms": [
                        {"action": "set", "key": "data.status", "value": "${data.review_decision}"}
                    ]
                },
            },
        ],
        "edges": [
            {"from": "START", "to": "prepare"},
            {"from": "prepare", "to": "review"},
            {"from": "review", "to": "process_result"},
            {"from": "process_result", "to": "END"},
        ],
    }

    print("=" * 50)
    print("HumanInputNode 示例：人工介入")
    print("=" * 50)

    runner = WorkflowRunner(config_dict=config)

    # 第一次执行，会在 HumanInputNode 处暂停
    result = runner.invoke({"data": {}}, thread_id="human-demo-1")

    # 检查是否有中断
    if "__interrupt__" in result:
        print("工作流已暂停，等待人工输入...")
        print("-" * 50)

        interrupt_info = result["__interrupt__"][0]
        interrupt_value = (
            interrupt_info.value if hasattr(interrupt_info, "value") else interrupt_info
        )

        if isinstance(interrupt_value, dict):
            prompt = interrupt_value.get("prompt", "")
            options = interrupt_value.get("options", [])
            print(f"\n{prompt}")
            if options:
                print(f"可选选项: {options}")
        else:
            print(f"\n{str(interrupt_value)}")

        print()

        # 真实控制台输入
        while True:
            user_input = input("请输入您的决定: ").strip()
            if user_input:
                break
            print("输入不能为空，请重新输入")

        # 恢复执行
        result = runner.resume("human-demo-1", user_input)

    print("-" * 50)
    print("执行完成!")

    data = result.get("data", {})
    print(f"\n草稿: {data.get('draft')}")
    print(f"审核决定: {data.get('review_decision')}")
    print(f"状态: {data.get('status')}")
    print("=" * 50)


if __name__ == "__main__":
    main()
