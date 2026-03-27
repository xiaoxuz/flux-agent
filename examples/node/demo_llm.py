#!/usr/bin/env python3
"""
LLMNode 示例

需要设置环境变量: OPENAI_API_KEY
"""

import sys
import os
from pathlib import Path
import json

from flux_agent import WorkflowRunner
from flux_agent import tools

def greet(name: str) -> str:
    """生成问候语"""
    return f"Hello, {name}!"

def get_city() -> str:
    return "凤城"

def get_weather(city: str) -> str:
    """获取城市天气（模拟）"""
    return f"{city}今天天气晴朗，温度25℃"

def main():
    # if not os.environ.get("OPENAI_API_KEY"):
    #     print("请设置环境变量 OPENAI_API_KEY")
    #     print("示例: export OPENAI_API_KEY=sk-xxx")
    #     return
    config = {
        "workflow": {"name": "llm-demo"},
        "nodes": [
            {
                "id": "text_answer",
                "type": "LLMNode",
                "config": {
                    "model": "openai",
                    "model_name": "gpt-4o",
                    "system_prompt": "你是一个友好的助手，回答要简洁",
                    "user_prompt": "${data.question}",
                    "output_key": "data.response.text",
                    "temperature": 0.7,
                    "base_url": "",
                    "api_key": "",
                    "save_to_messages":True
                },
            },
            {
                "id": "img_desc",
                "type": "LLMNode",
                "config": {
                    "model": "openai",
                    "model_name": "gpt-4o",
                    "system_prompt": "你是一个视觉大师",
                    "user_prompt": "这个图片中有什么",
                    "output_key": "data.response.image",
                    "image_list":["${data.image_path}"],
                    "temperature": 0.7,
                    "base_url": "",
                    "api_key": "",
                    "save_to_messages":False
                },
            },  
            {
                "id": "tool_use",
                "type": "LLMNode",
                "config": {
                    "model_name": "gpt-4o",
                    "system_prompt": "你是一个助手，可以使用工具来帮助用户。",
                    "user_prompt": "请帮我问候王五，然后查看下当前城市是哪里，然后告诉我这个城市今天的天气",
                    "tools": ["greet", "get_city", "get_weather"],  # LLM 可用的工具列表
                    "output_key": "data.response.tool",
                    "base_url": "",
                    "api_key": "",
                    "save_to_messages":True
                },
            }
        ],
        "edges": [{"from": "START", "to": "text_answer"}, {"from": "text_answer", "to": "img_desc"}, {"from": "img_desc", "to": "tool_use"}, {"from": "tool_use", "to": "END"}],
    }

    print("=" * 50)
    print("LLMNode 示例：调用大语言模型")
    print("=" * 50)

    runner = WorkflowRunner(config_dict=config, tools={"greet":greet, "get_city":get_city, "get_weather":get_weather})
    result = runner.invoke({"data": {"question": " 你是什么模型", "image_path": "https://img.com/f8b863843d0af65ee5d72f7d70bb86b8.jpg"}})

    print(f"回答: {result.get('data', {}).get('response', {})}")
    print("=" * 50)
    # print(dumps(result, pretty=True))
    print(tools.pretty_state(result))


if __name__ == "__main__":
    main()
