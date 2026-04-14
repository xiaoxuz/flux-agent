"""
flux_agent/agents/registry.py
Agent 注册中心 — 管理所有可用的 Agent 模式
"""
from __future__ import annotations

from typing import Type

from .base import BaseAgent, AgentMode


class AgentRegistry:
    """
    Agent 模式注册中心
    """
    
    _registry: dict[str, Type[BaseAgent]] = {}
    
    @classmethod
    def register(cls, mode: str | AgentMode):
        """装饰器：注册一个 Agent 类"""
        mode_key = mode.value if isinstance(mode, AgentMode) else mode
        
        def decorator(agent_class: Type[BaseAgent]):
            if not issubclass(agent_class, BaseAgent):
                raise TypeError(f"{agent_class.__name__} 必须继承 BaseAgent")
            cls._registry[mode_key] = agent_class
            return agent_class
        
        return decorator
    
    @classmethod
    def register_class(cls, mode: str | AgentMode, agent_class: Type[BaseAgent]):
        """命令式注册"""
        mode_key = mode.value if isinstance(mode, AgentMode) else mode
        if not issubclass(agent_class, BaseAgent):
            raise TypeError(f"{agent_class.__name__} 必须继承 BaseAgent")
        cls._registry[mode_key] = agent_class
    
    @classmethod
    def get(cls, mode: str | AgentMode) -> Type[BaseAgent]:
        """获取 Agent 类"""
        mode_key = mode.value if isinstance(mode, AgentMode) else mode
        if mode_key not in cls._registry:
            available = ", ".join(cls._registry.keys())
            raise KeyError(f"未注册的 Agent 模式: '{mode_key}'。可用模式: [{available}]")
        return cls._registry[mode_key]
    
    @classmethod
    def list_modes(cls) -> list[str]:
        """列出所有已注册的模式"""
        return list(cls._registry.keys())
    
    @classmethod
    def has(cls, mode: str | AgentMode) -> bool:
        """检查模式是否已注册"""
        mode_key = mode.value if isinstance(mode, AgentMode) else mode
        return mode_key in cls._registry
    
    @classmethod
    def unregister(cls, mode: str | AgentMode):
        """取消注册"""
        mode_key = mode.value if isinstance(mode, AgentMode) else mode
        cls._registry.pop(mode_key, None)
    
    @classmethod
    def clear(cls):
        """清空所有注册"""
        cls._registry.clear()


def _register_builtin_agents():
    """注册内置的 Agent 模式"""
    from .react_agent import ReactAgent
    from .deep_agent import DeepAgent
    from .plan_execute_agent import PlanExecuteAgent
    from .reflexion_agent import ReflexionAgent
    from .supervisor_agent import SupervisorAgent

    AgentRegistry.register_class(AgentMode.REACT, ReactAgent)
    AgentRegistry.register_class(AgentMode.DEEP, DeepAgent)
    AgentRegistry.register_class(AgentMode.PLAN_EXECUTE, PlanExecuteAgent)
    AgentRegistry.register_class(AgentMode.REFLEXION, ReflexionAgent)
    AgentRegistry.register_class(AgentMode.SUPERVISOR, SupervisorAgent)


_register_builtin_agents()
