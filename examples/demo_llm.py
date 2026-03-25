#!/usr/bin/env python3
"""
LLMNode 示例

需要设置环境变量: OPENAI_API_KEY
"""

import sys
import os
from pathlib import Path


from flux_agent import WorkflowRunner


def main():
    # if not os.environ.get("OPENAI_API_KEY"):
    #     print("请设置环境变量 OPENAI_API_KEY")
    #     print("示例: export OPENAI_API_KEY=sk-xxx")
    #     return
    config = {
        "workflow": {"name": "llm-demo"},
        "nodes": [
            {
                "id": "greet",
                "type": "LLMNode",
                "config": {
                    "model": "openai",
                    "model_name": "MiniMax-M2.5",
                    "system_prompt": "你是一个友好的助手，回答要简洁",
                    "user_prompt": "${data.question}",
                    "output_key": "data.answer.test",
                    "temperature": 0.7,
                    "base_url": "",
                    "api_key": "",
                },
            }
        ],
        "edges": [{"from": "START", "to": "greet"}, {"from": "greet", "to": "END"}],
    }

    print("=" * 50)
    print("LLMNode 示例：调用大语言模型")
    print("=" * 50)

    runner = WorkflowRunner(config_dict=config)
    result = runner.invoke({"data": {"question": "用一句话介绍什么是 Agent"}})

    print(f"问题: 什么是 Agent?")
    print(f"回答: {result.get('data', {}).get('answer', {}).get('test')}")
    print("=" * 50)


if __name__ == "__main__":
    main()
