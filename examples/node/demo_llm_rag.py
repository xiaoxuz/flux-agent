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
from flux_agent.rag import KnowledgeBaseConfig, KnowledgeEmbeddingConfig
from flux_agent.tools import pretty_state
import logging
APIKEY = ""
BASEURL = ""
APIKEY_EMBEDDING = ""
BASEURL = ""
EMBEDDING_MODEL = "text-embedding-3-small"
EmbeddingConfig = KnowledgeEmbeddingConfig(model=EMBEDDING_MODEL, api_key=APIKEY_EMBEDDING, base_url=BASEURL)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S"
)

def main():
    config = {
        "workflow": {"name": "llm-demo"},
        "nodes": [
            {
                "id": "text_answer",
                "type": "LLMNode",
                "config": {
                    "model": "openai",
                    "model_name": "gpt-4o",
                    "system_prompt": "你是一个友好的助手，请回答用户的问题",
                    "user_prompt": "${data.question}",
                    "output_key": "data.response",
                    "temperature": 0.7,
                    "base_url": BASEURL,
                    "api_key": APIKEY,
                    "knowledge_base": "product_docs",
                    "rag_score_threshold": 0.5
                },
            }
        ],
        "edges": [{"from": "START", "to": "text_answer"},  {"from": "text_answer", "to": "END"}],
    }

    print("=" * 50)
    print("LLMNode 示例：调用大语言模型")
    print("=" * 50)
    rag_config = KnowledgeBaseConfig(
        persist_directory="./examples/rag/kb_data/product_docs",
        embedding_config=EmbeddingConfig
    )

    runner = WorkflowRunner(config_dict=config, knowledge_bases={"product_docs": rag_config})
    result = runner.invoke({"data": {"question": "LLMNode都有哪些配置"}})

    print(f"回答: {result.get('data', {}).get('response', {})}")
    print("=" * 50)
    print(pretty_state(result))


if __name__ == "__main__":
    main()
