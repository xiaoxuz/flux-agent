"""
知识库存储

全局知识库存储，供 WorkflowRunner 和节点使用。
"""

from typing import Dict, Optional
from .knowledge_base import KnowledgeBase

_knowledge_bases: Dict[str, KnowledgeBase] = {}


def add_knowledge_base(name: str, kb: KnowledgeBase) -> None:
    """添加知识库到全局存储"""
    _knowledge_bases[name] = kb


def get_knowledge_base(name: str) -> Optional[KnowledgeBase]:
    """获取知识库"""
    return _knowledge_bases.get(name)


def list_knowledge_bases() -> list:
    """列出所有知识库"""
    return list(_knowledge_bases.keys())


def clear_knowledge_bases() -> None:
    """清空知识库"""
    _knowledge_bases.clear()
