"""
flux_agent/agents/deep_agent.py
Deep 模式 Agent - 包装 deepagents.create_deep_agent
"""

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langchain_core.messages import AIMessage

from .base import (
    BaseAgent, AgentMode, AgentInput, AgentOutput,
    AgentStep, AgentConfig, AgentStatus, StepType,
)


class DeepAgent(BaseAgent):
    """
    Deep 模式 Agent
    
    包装 deepagents.create_deep_agent，提供统一的输入输出接口
    如果 deepagents 未安装，降级到 ReactAgent
    
    Usage:
        from langchain_openai import ChatOpenAI
        
        llm = ChatOpenAI(model="gpt-4o")
        
        agent = DeepAgent(llm=llm, tools=[search])
        result = agent.invoke("分析2024年AI领域的重要突破")
        
        print(result.answer)
    """
    
    def __init__(
        self,
        llm: BaseChatModel,
        tools: list[BaseTool] | None = None,
        system_prompt: str | None = None,
        config: AgentConfig | None = None,
    ):
        self._fallback_agent = None
        super().__init__(llm=llm, tools=tools, system_prompt=system_prompt, config=config)
    
    @property
    def mode(self) -> AgentMode:
        return AgentMode.DEEP
    
    def _build(self) -> None:
        """构建 Deep agent"""
        try:
            from deepagents import create_deep_agent
            self._agent = create_deep_agent(
                tools=self.tools,
                system_prompt=self.system_prompt or "You are a helpful assistant.",
            )
            self._use_fallback = False
        except ImportError as e:
            # 降级到 ReactAgent
            self._use_fallback = True
            from .react_agent import ReactAgent
            self._fallback_agent = ReactAgent(
                llm=self.llm,
                tools=self.tools,
                system_prompt=self.system_prompt,
                config=self.config,
            )
    
    def _run(self, agent_input: AgentInput) -> AgentOutput:
        """执行 Deep 流程"""
        if self._use_fallback and self._fallback_agent:
            result = self._fallback_agent._run(agent_input)
            result.agent_mode = self.mode
            result.metadata["fallback"] = True
            return result
        
        messages = agent_input.to_messages()
        
        try:
            result = self._agent.invoke({"messages": messages})
        except Exception as e:
            return AgentOutput(
                answer=f"Deep Agent 执行失败: {str(e)}",
                status=AgentStatus.FAILED,
                agent_mode=self.mode,
                error=str(e),
            )
        
        # 提取结果
        steps = []
        step_index = 0
        final_answer = ""
        
        result_messages = result.get("messages", [])
        
        for msg in result_messages:
            if isinstance(msg, AIMessage):
                if msg.tool_calls:
                    for tc in msg.tool_calls:
                        steps.append(AgentStep(
                            step_index=step_index,
                            step_type=StepType.ACTION,
                            content=f"调用工具: {tc.get('name', 'unknown')}",
                            tool_name=tc.get("name"),
                            tool_input=tc.get("args"),
                        ))
                        step_index += 1
                elif msg.content and not msg.tool_calls:
                    final_answer = msg.content
                    steps.append(AgentStep(
                        step_index=step_index,
                        step_type=StepType.FINAL_ANSWER,
                        content=msg.content,
                    ))
                    step_index += 1
            elif hasattr(msg, 'name') and hasattr(msg, 'content'):
                steps.append(AgentStep(
                    step_index=step_index,
                    step_type=StepType.OBSERVATION,
                    content=msg.content[:500] if len(msg.content) > 500 else msg.content,
                    tool_name=getattr(msg, 'name', None),
                    tool_output=msg.content[:500] if len(msg.content) > 500 else msg.content,
                ))
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
            metadata={"fallback": False},
        )
