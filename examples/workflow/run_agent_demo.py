#!/usr/bin/env python3
"""
AgentNode 工作流示例

演示如何在工作流中使用 AgentNode
"""
import sys
import os
from flux_agent import WorkflowRunner
from dotenv import load_dotenv
load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

workflow_config = {
    "workflow": {
        "name": "agent-demo",
        "description": "AgentNode 工作流示例",
        "version": "1.0.0"
    },
    "tools": [
        {
            "name": "mock_search",
            "implementation": "examples.tools:mock_search"
        }
    ],
    "nodes": [
        {
            "id": "agent_react",
            "type": "AgentNode",
            "config": {
                "mode": "plan_execute",
                "input_key": "data.question",
                "output_key": "data.answer",
                "tools": ["mock_search"],
                "max_steps": 5,
                "base_url": os.getenv("OPENAI_BASE_URL"),
                "api_key": os.getenv("OPENAI_API_KEY"),
                "model_name": "gpt-4.1",
                "verbose":True
            }
        }
    ],
    "edges": [
        {"from": "START", "to": "agent_react"},
        {"from": "agent_react", "to": "END"}
    ]
}


def main():
    print("=" * 60)
    print("AgentNode 工作流示例")
    print("=" * 60)

    runner = WorkflowRunner(config_dict=workflow_config)

    result = runner.invoke({"data":{"question": "今天北京天气怎么样？"}})
    print(result)

    print(f"\n问题: {result['data']['question']}")
    print(f"回答: {result['data']['answer']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
