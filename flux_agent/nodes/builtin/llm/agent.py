"""
flux_agent/nodes/builtin/control/agent.py
AgentNode - 在工作流中调用智能 Agent 模块
"""
from __future__ import annotations

from typing import Any, Dict, List
from dataclasses import dataclass, field

from flux_agent.nodes.base import BaseNode, NodeConfig


@dataclass
class AgentNodeConfig(NodeConfig):
    """Agent 节点配置"""

    mode: str = "react"
    tools: List[str] = field(default_factory=list)
    system_prompt: str = ""
    input_key: str = "data.query"
    output_key: str = "data.result"

    base_url: str = ""
    api_key: str = ""
    model_name: str = "gpt-4.1"

    max_steps: int = 10
    verbose: bool = False

    extra_config: Dict[str, Any] = field(default_factory=dict)


class AgentNode(BaseNode):
    """
    Agent 节点 - 在工作流中调用智能 Agent 模块
    
    支持的模式：
    - react: ReAct 模式
    - deep: Deep 模式
    - plan_execute: Plan-Execute 模式
    - reflexion: Reflexion 模式
    
    Usage:
        {
            "id": "agent",
            "type": "agent",
            "config": {
                "mode": "react",
                "tools": ["search", "calculator"],
                "input_key": "data.query",
                "output_key": "data.answer"
            }
        }
    """

    node_type = "agent"
    config_class = AgentNodeConfig

    def __init__(self, config: Dict[str, Any], **kwargs):
        super().__init__(config, **kwargs)
        self._parent_tools = kwargs.get("tools", {})

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        from flux_agent.agents import create_agent, AgentConfig

        llm = self._get_llm()
        tools = self._resolve_tools()
        
        agent_config = AgentConfig(
            verbose=self.config.verbose,
            max_steps=self.config.max_steps,
            extra=self.config.extra_config,
        )

        agent = create_agent(
            mode=self.config.mode,
            llm=llm,
            tools=tools if tools else None,
            system_prompt=self.config.system_prompt or None,
            config=agent_config,
        )

        query = self._get_nested(state, self.config.input_key, "")
        
        if not query:
            return self._set_nested({}, self.config.output_key, "")

        result = agent.invoke(query)

        output = self._set_nested({}, self.config.output_key, result.answer)

        if self.config.verbose:
            output["data"] = output.get("data", {})
            output["data"]["agent_steps"] = len(result.steps)
            output["data"]["agent_status"] = result.status.value

        return output

    def _get_llm(self):
        from langchain_openai import ChatOpenAI

        llm_params = {
            "model": self.config.model_name,
            "temperature": 1,
        }

        if self.config.api_key:
            llm_params["api_key"] = self.config.api_key
        if self.config.base_url:
            llm_params["base_url"] = self.config.base_url

        return ChatOpenAI(**llm_params)

    def _resolve_tools(self) -> List:
        tools = []
        for tool_name in self.config.tools:
            if tool_name in self._parent_tools:
                tools.append(self._parent_tools[tool_name])
        return tools
