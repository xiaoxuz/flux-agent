# flux_agent/__init__.py
"""
Flux-Agent: 基于 LangGraph + LLM 的通用 Agent 编排框架

通过 JSON 配置文件即可启动多 Agent Node 工作流。
"""
from .core import (
    WorkflowRunner,
    NodeRegistry,
    register,
    get_registry,
    parse_workflow,
    load_workflow_from_file,
)
from .nodes import (
    BaseNode,
    NodeConfig,
    BUILTIN_NODES,
    LLMNode,
    ConditionNode,
    TransformNode,
    ToolNode,
    HTTPRequestNode,
    LoopNode,
    ParallelNode,
    SubgraphNode,
    HumanInputNode,
)
from .utils import evaluate_condition, ExpressionEvaluator


__version__ = "0.1.1"

__all__ = [
    "__version__",
    "WorkflowRunner",
    "NodeRegistry",
    "register",
    "get_registry",
    "parse_workflow",
    "load_workflow_from_file",
    "BaseNode",
    "NodeConfig",
    "BUILTIN_NODES",
    "LLMNode",
    "ConditionNode",
    "TransformNode",
    "ToolNode",
    "HTTPRequestNode",
    "LoopNode",
    "ParallelNode",
    "SubgraphNode",
    "HumanInputNode",
    "evaluate_condition",
    "ExpressionEvaluator",
]
