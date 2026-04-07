# nodes/builtin/__init__.py
"""
内置节点模块

包含框架提供的所有内置节点。
"""

from .control import ConditionNode, ConditionNodeConfig, LoopNode, LoopNodeConfig
from .llm import LLMNode, LLMNodeConfig, AgentNode, AgentNodeConfig
from .transform import TransformNode, TransformNodeConfig, JsonNode, JsonNodeConfig
from .io import (
    HTTPRequestNode,
    HTTPRequestNodeConfig,
    ToolNode,
    ToolNodeConfig,
    ParallelNode,
    ParallelNodeConfig,
    SubgraphNode,
    SubgraphNodeConfig,
    HumanInputNode,
    HumanInputNodeConfig,
)
from .rag import RagSearchNode, RagSearchNodeConfig


# 内置节点映射表
BUILTIN_NODES = {
    # 控制类
    "condition": ConditionNode,
    "ConditionNode": ConditionNode,
    "loop": LoopNode,
    "LoopNode": LoopNode,
    # LLM
    "llm": LLMNode,
    "LLMNode": LLMNode,
    "agent": AgentNode,
    "AgentNode": AgentNode,
    # 数据处理
    "transform": TransformNode,
    "TransformNode": TransformNode,
    "json": JsonNode,
    "JsonNode": JsonNode,
    # IO
    "http_request": HTTPRequestNode,
    "HTTPRequestNode": HTTPRequestNode,
    "tool": ToolNode,
    "ToolNode": ToolNode,
    "parallel": ParallelNode,
    "ParallelNode": ParallelNode,
    "subgraph": SubgraphNode,
    "SubgraphNode": SubgraphNode,
    "human_input": HumanInputNode,
    "HumanInputNode": HumanInputNode,
    # RAG
    "rag_search": RagSearchNode,
    "RagSearchNode": RagSearchNode,
}


__all__ = [
    # 控制类
    "ConditionNode",
    "ConditionNodeConfig",
    "LoopNode",
    "LoopNodeConfig",
    # LLM
    "LLMNode",
    "LLMNodeConfig",
    "AgentNode",
    "AgentNodeConfig",
    # 数据处理
    "TransformNode",
    "TransformNodeConfig",
    "JsonNode",
    "JsonNodeConfig",
    # IO
    "HTTPRequestNode",
    "HTTPRequestNodeConfig",
    "ToolNode",
    "ToolNodeConfig",
    "ParallelNode",
    "ParallelNodeConfig",
    "SubgraphNode",
    "SubgraphNodeConfig",
    "HumanInputNode",
    "HumanInputNodeConfig",
    # RAG
    "RagSearchNode",
    "RagSearchNodeConfig",
    # 映射表
    "BUILTIN_NODES",
]
