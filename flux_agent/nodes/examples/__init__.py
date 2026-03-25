# nodes/examples/__init__.py
"""
示例业务节点

演示如何开发自定义业务节点。
"""

from .simple_node import SimpleDataNode, SimpleDataNodeConfig
from .advanced_node import AdvancedProcessNode, AdvancedProcessNodeConfig


EXAMPLE_NODES = {
    "simple_data": SimpleDataNode,
    "advanced_process": AdvancedProcessNode,
}


__all__ = [
    "SimpleDataNode",
    "SimpleDataNodeConfig",
    "AdvancedProcessNode",
    "AdvancedProcessNodeConfig",
    "EXAMPLE_NODES",
]
