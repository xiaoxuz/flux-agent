# nodes/__init__.py
"""
节点模块

提供节点开发的基础类、内置节点和示例节点。

模块结构：
- base/: 基类和接口
- builtin/: 系统内置节点
- examples/: 示例业务节点
- business/: 项目业务节点

使用方式：
    # 方式1：从顶层导入
    from flux_agent.nodes import BaseNode, LLMNode, BUILTIN_NODES

    # 方式2：从子模块导入
    from flux_agent.nodes.base import BaseNode, NodeConfig
    from flux_agent.nodes.builtin import LLMNode, ConditionNode
    from flux_agent.nodes.business import BUSINESS_NODES
"""

from .base import (
    BaseNode,
    NodeConfig,
    RetryPolicy,
    CachePolicy,
    INode,
    NodeResult,
)
from .builtin import (
    BUILTIN_NODES,
    # 控制类
    ConditionNode,
    ConditionNodeConfig,
    LoopNode,
    LoopNodeConfig,
    # LLM
    LLMNode,
    LLMNodeConfig,
    # 数据处理
    TransformNode,
    TransformNodeConfig,
    # IO
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

try:
    from .business import BUSINESS_NODES
except ImportError:
    BUSINESS_NODES = {}


__all__ = [
    # 基类
    "BaseNode",
    "NodeConfig",
    "RetryPolicy",
    "CachePolicy",
    "INode",
    "NodeResult",
    # 控制类节点
    "ConditionNode",
    "ConditionNodeConfig",
    "LoopNode",
    "LoopNodeConfig",
    # LLM 节点
    "LLMNode",
    "LLMNodeConfig",
    # 数据处理节点
    "TransformNode",
    "TransformNodeConfig",
    # IO 节点
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
    # 内置节点映射
    "BUILTIN_NODES",
    # 业务节点映射
    "BUSINESS_NODES",
]
