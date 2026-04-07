"""
flux_agent/agents/__init__.py
Agent 模块 — 开箱即用的多模式 Agent 能力
"""
from .base import (
    BaseAgent,
    AgentInput,
    AgentOutput,
    AgentStep,
    AgentConfig,
    AgentMode,
    AgentStatus,
    StepType,
)
from .registry import AgentRegistry
from .factory import create_agent, list_available_modes

from .react_agent import ReactAgent
from .deep_agent import DeepAgent
from .plan_execute_agent import PlanExecuteAgent
from .reflexion_agent import ReflexionAgent

__all__ = [
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
