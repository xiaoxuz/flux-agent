# core/__init__.py
"""
核心模块
"""

from .state import (
    BaseWorkflowState,
    get_nested_value,
    set_nested_value,
    delete_nested_value,
)
from .registry import NodeRegistry, register, get_registry, load_node_class
from .parser import WorkflowParser, parse_workflow, load_workflow_from_file
from .executor import WorkflowRunner


__all__ = [
    "BaseWorkflowState",
    "get_nested_value",
    "set_nested_value",
    "delete_nested_value",
    "NodeRegistry",
    "register",
    "get_registry",
    "load_node_class",
    "WorkflowParser",
    "parse_workflow",
    "load_workflow_from_file",
    "WorkflowRunner",
]
