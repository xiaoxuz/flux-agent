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
from .skill import Skill, SkillLoader, SkillSelector, SkillRegistry, SkillExecutor, build_skill_tools

from .react_agent import ReactAgent
from .deep_agent import DeepAgent
from .plan_execute_agent import PlanExecuteAgent
from .reflexion_agent import ReflexionAgent
from .supervisor_agent import SupervisorAgent
from .factory import WorkerConfig
from .multi.mailbox import Mailbox, MailboxMessage, InMemoryMailbox, FileMailbox

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

    "Skill",
    "SkillLoader",
    "SkillSelector",
    "SkillRegistry",
    "SkillExecutor",
    "build_skill_tools",

    "ReactAgent",
    "DeepAgent",
    "PlanExecuteAgent",
    "ReflexionAgent",
    "SupervisorAgent",
    "WorkerConfig",

    "Mailbox",
    "MailboxMessage",
    "InMemoryMailbox",
    "FileMailbox",
]
