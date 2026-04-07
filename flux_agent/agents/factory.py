"""
flux_agent/agents/factory.py
统一的 Agent 工厂函数 — 用户的主入口
"""
from __future__ import annotations


from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool

from .base import BaseAgent, AgentMode, AgentConfig
from .registry import AgentRegistry


def create_agent(
    mode: str | AgentMode,
    llm: BaseChatModel,
    tools: list[BaseTool] | None = None,
    system_prompt: str | None = None,
    config: AgentConfig | dict | None = None,
    **kwargs,
) -> BaseAgent:
    """
    统一的 Agent 工厂函数
    
    Args:
        mode: Agent 模式 (react/deep/plan_execute/reflexion)
        llm: LangChain ChatModel 实例
        tools: 工具列表
        system_prompt: 系统提示词
        config: Agent 配置
        **kwargs: 传递给具体 Agent 类的额外参数
    
    Returns:
        BaseAgent 实例
    
    Usage:
        agent = create_agent("react", llm=llm, tools=[search])
        result = agent.invoke("今天天气怎么样？")
    """
    if isinstance(config, dict):
        config = AgentConfig(**config)
    
    agent_cls = AgentRegistry.get(mode)
    
    return agent_cls(
        llm=llm,
        tools=tools,
        system_prompt=system_prompt,
        config=config,
        **kwargs,
    )


def list_available_modes() -> list[str]:
    """列出所有可用的 Agent 模式"""
    return AgentRegistry.list_modes()
