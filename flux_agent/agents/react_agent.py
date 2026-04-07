"""
flux_agent/agents/react_agent.py
ReAct 模式 Agent - 包装 langgraph.prebuilt.create_react_agent
"""

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langchain_core.messages import AIMessage

from .base import (
    BaseAgent, AgentMode, AgentInput, AgentOutput,
    AgentStep, AgentConfig, AgentStatus, StepType,
)


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
    ):
        super().__init__(llm=llm, tools=tools, system_prompt=system_prompt, config=config)
    
    @property
    def mode(self) -> AgentMode:
        return AgentMode.REACT
    
    def _build(self) -> None:
        """构建 ReAct agent"""
        from langgraph.prebuilt import create_react_agent
        
        self._agent = create_react_agent(
            model=self.llm,
            tools=self.tools,
            prompt=self.system_prompt,
        )
    
    def _run(self, agent_input: AgentInput) -> AgentOutput:
        """执行 ReAct 流程"""
        messages = agent_input.to_messages()
        
        try:
            result = self._agent.invoke(
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
                step = AgentStep(
                    step_index=step_index,
                    step_type=StepType.OBSERVATION,
                    content=msg.content[:500] if len(msg.content) > 500 else msg.content,
                    tool_name=msg.name if hasattr(msg, 'name') else None,
                    tool_output=msg.content[:500] if len(msg.content) > 500 else msg.content,
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
