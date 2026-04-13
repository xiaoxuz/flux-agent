"""
flux_agent/agents/react_agent.py
ReAct 模式 Agent - 包装 langgraph.prebuilt.create_react_agent
"""

from typing import List

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langchain_core.messages import AIMessage

from .base import (
    BaseAgent, AgentMode, AgentInput, AgentOutput,
    AgentStep, AgentConfig, AgentStatus, StepType,
)
from .skill import Skill


class ReactAgent(BaseAgent):
    """
    ReAct 模式 Agent

    包装 langgraph.prebuilt.create_react_agent，提供统一的输入输出接口

    Usage:
        from langchain_openai import ChatOpenAI
        from langchain_community.tools import TavilySearchResults

        llm = ChatOpenAI(model="gpt-4o")
        search = TavilySearchResults()

        agent = ReactAgent(llm=llm, tools=[search])
        result = agent.invoke("今天北京天气怎么样？")

        print(result.answer)
    """

    def __init__(
        self,
        llm: BaseChatModel,
        tools: list[BaseTool] | None = None,
        system_prompt: str | None = None,
        config: AgentConfig | None = None,
        skills: List[Skill] | None = None,
        skills_dir: str = "skills",
        mcp_servers: List[dict] | None = None,
    ):
        super().__init__(
            llm=llm,
            tools=tools,
            system_prompt=system_prompt,
            config=config,
            skills=skills,
            skills_dir=skills_dir,
            mcp_servers=mcp_servers,
        )
    
    @property
    def mode(self) -> AgentMode:
        return AgentMode.REACT
    
    def _build(self) -> None:
        """构建 ReAct agent"""
        from langgraph.prebuilt import create_react_agent

        # 合并用户 tools + skill tools
        all_tools = self._get_all_tools()

        # 如果有 skills，注入 catalog 到 system prompt
        prompt = self.system_prompt
        if self._skill_registry.invocable_skills:
            prompt = self._build_system_prompt_with_skills(
                active_skills=[],
                base_prompt=self.system_prompt or "",
                include_catalog=True,
            )

        self._agent = create_react_agent(
            model=self.llm,
            tools=all_tools,
            prompt=prompt,
        )

    def _rebuild_agent_if_needed(self) -> None:
        """当 skill 注册表变化时重建 agent"""
        if not hasattr(self, "_last_skill_count"):
            self._last_skill_count = 0
        current_count = len(self._skill_registry.all_skills)
        if current_count != self._last_skill_count:
            self._last_skill_count = current_count
            # 清除缓存的 skill tools
            if hasattr(self, "_cached_skill_tools"):
                del self._cached_skill_tools
            self._build()

    def _run(self, agent_input: AgentInput) -> AgentOutput:
        """执行 ReAct 流程"""
        messages = agent_input.to_messages()

        # 如果有强制激活的 skills，把 content 直接注入到 user message 前面
        forced_skills = self._resolve_active_skills(agent_input)
        if forced_skills:
            self._logger.info(f"强制激活 Skills: {[s.name for s in forced_skills]}")
            skill_context = "\n\n".join(
                f"[Skill: {s.name}]\n{s.content}" for s in forced_skills
            )
            # 在 messages 最前面插入 skill context
            from langchain_core.messages import SystemMessage
            messages = [SystemMessage(content=f"# Active Skills\n{skill_context}")] + messages

        # 确保 agent 是最新的（动态添加 skill 后需要重建）
        self._rebuild_agent_if_needed()
        agent = self._agent

        try:
            result = agent.invoke(
                {"messages": messages},
                config={"recursion_limit": agent_input.max_steps * 3},
            )
        except Exception as e:
            self._logger.error(str(e))
            return AgentOutput(
                answer=f"ReAct 执行失败: {str(e)}",
                status=AgentStatus.FAILED,
                agent_mode=self.mode,
                error=str(e),
            )
        
        steps = []
        step_index = 0
        final_answer = ""
        
        result_messages = result.get("messages", [])
        
        for msg in result_messages:
            if isinstance(msg, AIMessage):
                if msg.tool_calls:
                    for tc in msg.tool_calls:
                        step = AgentStep(
                            step_index=step_index,
                            step_type=StepType.ACTION,
                            content=f"调用工具: {tc.get('name', 'unknown')}",
                            tool_name=tc.get("name"),
                            tool_input=tc.get("args"),
                        )
                        steps.append(step)
                        self._logger.step(step)
                        step_index += 1
                elif msg.content and not msg.tool_calls:
                    if steps:
                        step = AgentStep(
                            step_index=step_index,
                            step_type=StepType.FINAL_ANSWER,
                            content=msg.content,
                        )
                        steps.append(step)
                        self._logger.step(step)
                    final_answer = msg.content
                    step_index += 1
            elif hasattr(msg, 'name') and hasattr(msg, 'content'):
                content = msg.content
                if isinstance(content, list):
                    # MCP 工具返回格式: [{'type': 'text', 'text': '...'}]
                    content = " ".join(
                        item.get("text", "") for item in content if isinstance(item, dict) and item.get("type") == "text"
                    ) or str(content)
                step = AgentStep(
                    step_index=step_index,
                    step_type=StepType.OBSERVATION,
                    content=content[:500] if len(content) > 500 else content,
                    tool_name=msg.name if hasattr(msg, 'name') else None,
                    tool_output=content[:500] if len(content) > 500 else content,
                )
                steps.append(step)
                self._logger.step(step)
                step_index += 1
        
        if not final_answer and result_messages:
            for msg in reversed(result_messages):
                if isinstance(msg, AIMessage) and msg.content:
                    final_answer = msg.content
                    break
        
        return AgentOutput(
            answer=final_answer or "未能生成回答",
            status=AgentStatus.SUCCESS,
            steps=steps,
            agent_mode=self.mode,
            total_steps=len(steps),
        )
