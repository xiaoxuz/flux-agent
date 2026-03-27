"""
RAG 模块

提供知识库管理和检索能力。
"""

from .knowledge_base import KnowledgeBase, KnowledgeBaseConfig, KnowledgeChunkConfig, KnowledgeEmbeddingConfig
from .storage import (
    add_knowledge_base,
    get_knowledge_base,
    list_knowledge_bases,
    clear_knowledge_bases,
)

__all__ = [
    "KnowledgeBase",
    "KnowledgeBaseConfig",
    "KnowledgeChunkConfig",
    "KnowledgeEmbeddingConfig",
    "add_knowledge_base",
    "get_knowledge_base",
    "list_knowledge_bases",
    "clear_knowledge_bases",
]
