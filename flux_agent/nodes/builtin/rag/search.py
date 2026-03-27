"""
RAG 检索节点

从知识库检索相似文档。
"""

from __future__ import annotations
from typing import Any, Dict, List
from dataclasses import dataclass, field
import logging

from flux_agent.nodes.base import BaseNode, NodeConfig

logger = logging.getLogger(__name__)


@dataclass
class RagSearchNodeConfig(NodeConfig):
    """RAG 检索节点配置"""

    knowledge_base: str = ""
    query: str = ""
    top_k: int = 4
    output_key: str = "data.rag_docs"
    score_threshold: float = 0.0


class RagSearchNode(BaseNode):
    """
    RAG 检索节点

    从指定知识库检索相似文档，结果存入 state。

    输出格式:
    {
        "data": {
            "rag_docs": [
                {"page_content": "...", "metadata": {...}},
                {"page_content": "...", "metadata": {...}},
            ],
            "rag_count": 2
        }
    }
    """

    node_type = "rag_search"
    config_class = RagSearchNodeConfig

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        from flux_agent.rag import get_knowledge_base

        kb = get_knowledge_base(self.config.knowledge_base)
        if not kb:
            raise ValueError(f"知识库 {self.config.knowledge_base} 未找到")

        query = self._interpolate(self.config.query, state)

        if not query:
            logger.warning("查询文本为空，跳过检索")
            return self._set_nested({}, self.config.output_key, [])

        if self.config.score_threshold > 0:
            docs_with_score = kb.similarity_search_with_score(
                query=query,
                k=self.config.top_k,
            )
            docs = [doc for doc, score in docs_with_score if score <= self.config.score_threshold]
            logger.info(
                f"RAG 检索: 知识库={self.config.knowledge_base}, "
                f"查询={query[:50]}, 阈值={self.config.score_threshold}, 结果数={len(docs)}"
            )
        else:
            docs = kb.search(query=query, k=self.config.top_k)
            logger.info(
                f"RAG 检索: 知识库={self.config.knowledge_base}, "
                f"查询={query[:50]}, 结果数={len(docs)}"
            )

        output_docs = [{"page_content": doc.page_content, "metadata": doc.metadata} for doc in docs]

        output = self._set_nested({}, self.config.output_key, output_docs)

        count_key = self.config.output_key.rsplit(".", 1)[0] + ".rag_count"
        output = self._set_nested(output, count_key, len(output_docs))

        return output
