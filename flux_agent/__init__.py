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
    AgentNode,
)
from .utils import evaluate_condition, ExpressionEvaluator
from .rag import (
    KnowledgeBase,
    add_knowledge_base,
    get_knowledge_base,
    list_knowledge_bases,
    clear_knowledge_bases,
)
from .agents import (
    create_agent,
    list_available_modes,
    BaseAgent,
    AgentInput,
    AgentOutput,
    AgentStep,
    AgentConfig,
    AgentMode,
    AgentStatus,
    StepType,
    AgentRegistry,
    ReactAgent,
    DeepAgent,
    PlanExecuteAgent,
    ReflexionAgent,
)


__version__ = "0.2.7"

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
    "AgentNode",
    "evaluate_condition",
    "ExpressionEvaluator",
    "KnowledgeBase",
    "add_knowledge_base",
    "get_knowledge_base",
    "list_knowledge_bases",
    "clear_knowledge_bases",
    "create_agent",
    "list_available_modes",
    "BaseAgent",
    "AgentInput",
    "AgentOutput",
    "AgentStep",
    "AgentConfig",
    "AgentMode",
    "AgentStatus",
    "StepType",
    "AgentRegistry",
    "ReactAgent",
    "DeepAgent",
    "PlanExecuteAgent",
    "ReflexionAgent",
]
