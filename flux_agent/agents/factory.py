"""
flux_agent/agents/factory.py
统一的 Agent 工厂函数 — 用户的主入口
"""
from __future__ import annotations

from typing import List

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool

from .base import BaseAgent, AgentMode, AgentConfig
from .registry import AgentRegistry
from .skill import Skill, SkillLoader


def create_agent(
    mode: str | AgentMode,
    llm: BaseChatModel,
    tools: list[BaseTool] | None = None,
    system_prompt: str | None = None,
    config: AgentConfig | dict | None = None,
    skills: List[Skill] | None = None,
    skills_dir: str = "skills",
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
        skills: Skill 列表（预加载的 skills）
        skills_dir: Skill 文件目录路径
        **kwargs: 传递给具体 Agent 类的额外参数

    Returns:
        BaseAgent 实例

    Usage:
        # 基本用法
        agent = create_agent("react", llm=llm, tools=[search])
        result = agent.invoke("今天天气怎么样？")

        # 使用 skills
        loader = SkillLoader("skills")
        agent = create_agent("react", llm=llm, skills=loader.load_all())
        result = agent.invoke("使用 langchain-architecture 技能，告诉我如何构建 RAG?")
    """
    if isinstance(config, dict):
        config = AgentConfig(**config)

    agent_cls = AgentRegistry.get(mode)

    return agent_cls(
        llm=llm,
        tools=tools,
        system_prompt=system_prompt,
        config=config,
        skills=skills,
        skills_dir=skills_dir,
        **kwargs,
    )


def list_available_modes() -> list[str]:
    """列出所有可用的 Agent 模式"""
    return AgentRegistry.list_modes()
