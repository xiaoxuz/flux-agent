"""
flux_agent/agents/factory.py
统一的 Agent 工厂函数 — 用户的主入口
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool

from .base import BaseAgent, AgentMode, AgentConfig
from .registry import AgentRegistry
from .skill import Skill, SkillLoader


@dataclass
class WorkerConfig:
    """Worker 配置 — 用于 SupervisorAgent"""
    name: str                     # worker 标识
    mode: str                     # react/deep/plan_execute/reflexion
    description: str              # 职责描述
    tools: List[str] = field(default_factory=list)
    system_prompt: str = ""
    skills: List[str] = field(default_factory=list)
    depends_on: List[str] = field(default_factory=list)  # 依赖的 worker 名称列表


def create_agent(
    mode: str | AgentMode,
    llm: BaseChatModel,
    tools: list[BaseTool] | None = None,
    system_prompt: str | None = None,
    config: AgentConfig | dict | None = None,
    skills: List[Skill] | None = None,
    skills_dir: str = "skills",
    mcp_servers: List[dict] | None = None,
    workers: dict[str, WorkerConfig] | None = None,
    parallel: bool = True,
    **kwargs,
) -> BaseAgent:
    """
    统一的 Agent 工厂函数

    Args:
        mode: Agent 模式 (react/deep/plan_execute/reflexion/supervisor)
        llm: LangChain ChatModel 实例
        tools: 工具列表
        system_prompt: 系统提示词
        config: Agent 配置
        skills: Skill 列表（预加载的 skills）
        skills_dir: Skill 文件目录路径
        mcp_servers: MCP Server 配置列表
        workers: SupervisorAgent 的 worker 池配置
        parallel: SupervisorAgent 是否并行执行子任务
        **kwargs: 传递给具体 Agent 类的额外参数

    Returns:
        BaseAgent 实例

    Usage:
        # 基本用法
        agent = create_agent("react", llm=llm, tools=[search])
        result = agent.invoke("今天天气怎么样？")

        # 使用 MCP Server
        agent = create_agent(
            "react", llm=llm,
            mcp_servers=[{
                "name": "filesystem",
                "transport": "stdio",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
            }]
        )

        # 使用 skills
        loader = SkillLoader("skills")
        agent = create_agent("react", llm=llm, skills=loader.load_all())
        result = agent.invoke("使用 langchain-architecture 技能，告诉我如何构建 RAG?")

        # 使用 SupervisorAgent
        supervisor = create_agent(
            "supervisor", llm=llm,
            workers={
                "researcher": WorkerConfig(
                    mode="react", description="负责搜索调研",
                ),
                "writer": WorkerConfig(
                    mode="plan_execute", description="负责撰写报告",
                ),
            }
        )
        result = supervisor.invoke("调研 AI 行业并写报告")
    """
    if isinstance(config, dict):
        config = AgentConfig(**config)

    agent_cls = AgentRegistry.get(mode)

    # 只有 supervisor 模式接受 workers 和 parallel 参数
    common_kwargs = {
        "llm": llm,
        "tools": tools,
        "system_prompt": system_prompt,
        "config": config,
        "skills": skills,
        "skills_dir": skills_dir,
        "mcp_servers": mcp_servers,
        **kwargs,
    }
    if mode == AgentMode.SUPERVISOR or mode == "supervisor":
        common_kwargs["workers"] = workers
        common_kwargs["parallel"] = parallel

    return agent_cls(**common_kwargs)


def list_available_modes() -> list[str]:
    """列出所有可用的 Agent 模式"""
    return AgentRegistry.list_modes()
