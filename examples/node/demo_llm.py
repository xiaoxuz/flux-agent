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
from flux_agent import utils

from dotenv import load_dotenv
load_dotenv()
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def greet(name: str) -> str:
    """生成问候语"""
    return f"Hello, {name}!"

def get_city() -> str:
    return "凤城"

def get_weather(city: str) -> str:
    """获取城市天气（模拟）"""
    return f"{city}今天天气晴朗，温度25℃"

DEFAULT_BASE_URL = os.getenv("OPENAI_BASE_URL")
DEFAULT_API_KEY = os.getenv("OPENAI_API_KEY")

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
                    "base_url": DEFAULT_BASE_URL,
                    "api_key": DEFAULT_API_KEY,
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
                    "user_prompt": "这个图片中有什么, 请返回json 数据 {\"desc\":\"图片描述\"}",
                    "output_key": "data.response.image",
                    "image_list":["${data.image_path}"],
                    "temperature": 0.7,
                          "base_url": DEFAULT_BASE_URL,
                    "api_key": DEFAULT_API_KEY,
                    "save_to_messages":False,
                    "response_format": {
                        "type": "json_object"
                    },
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
                    "base_url": DEFAULT_BASE_URL,
                    "api_key": DEFAULT_API_KEY,
                    "save_to_messages":True,
                    "json_schema": {
                        "required": ["contacts"],
                        "type": "object",
                        "properties": {
                            "greet": {"type": "string", "description": "问候内容"},
                            "city": {"type": "string", "description": "当前城市"},
                            "weather": {"type": "string", "description": "城市天气"},
                        },
                        "required": ["greet", "city", "weather"],
                    },
                },
            }
        ],
        "edges": [{"from": "START", "to": "text_answer"}, {"from": "text_answer", "to": "img_desc"}, {"from": "img_desc", "to": "tool_use"}, {"from": "tool_use", "to": "END"}],
    }

    print("=" * 50)
    print("LLMNode 示例：调用大语言模型")
    print("=" * 50)

    runner = WorkflowRunner(config_dict=config, tools={"greet":greet, "get_city":get_city, "get_weather":get_weather})
    result = runner.invoke({"data": {"question": " 你是什么模型", "image_path": "https://img.x.cc/cff03c74a7cf7262cbd99fe16f932772.jpg"}})

    print(f"回答: {result.get('data', {}).get('response', {})}")
    print("=" * 50)
    # print(dumps(result, pretty=True))
    print(utils.pretty_state(result))


if __name__ == "__main__":
    main()
