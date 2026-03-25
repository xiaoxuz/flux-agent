# nodes/base/__init__.py
"""
节点基类模块

提供节点开发所需的基础类和接口。
"""

from .node import BaseNode
from .config import NodeConfig, RetryPolicy, CachePolicy
from .interfaces import (
    INode,
    IConfigurable,
    IValidatable,
    NodeResult,
    ConditionResult,
    RouteResult,
)


__all__ = [
    # 核心基类
    "BaseNode",
    "NodeConfig",
    # 策略配置
    "RetryPolicy",
    "CachePolicy",
    # 接口协议
    "INode",
    "IConfigurable",
    "IValidatable",
    # 类型定义
    "NodeResult",
    "ConditionResult",
    "RouteResult",
]
