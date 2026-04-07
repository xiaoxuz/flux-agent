"""
flux_agent/agents/base.py
统一的 Agent 基类、输入输出定义
"""
from __future__ import annotations

import uuid
import time
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage


class AgentMode(str, Enum):
    """支持的 Agent 模式"""
    REACT = "react"
    DEEP = "deep"
    PLAN_EXECUTE = "plan_execute"
    REFLEXION = "reflexion"


class AgentStatus(str, Enum):
    """Agent 执行状态"""
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    INTERRUPTED = "interrupted"


class StepType(str, Enum):
    """执行步骤类型"""
    THOUGHT = "thought"
    ACTION = "action"
    OBSERVATION = "observation"
    PLAN = "plan"
    REFLECTION = "reflection"
    FINAL_ANSWER = "final_answer"


class AgentInput(BaseModel):
    """统一的 Agent 输入"""
    query: str = Field(..., description="用户的问题/任务描述")
    messages: Optional[list[dict]] = Field(default=None, description="对话历史")
    context: Optional[str] = Field(default=None, description="额外的上下文信息")
    system_prompt: Optional[str] = Field(default=None, description="覆盖默认的 system prompt")
    max_steps: int = Field(default=10, description="最大执行步数")
    config: dict[str, Any] = Field(default_factory=dict, description="模式特定的额外配置")

    def to_messages(self) -> list[BaseMessage]:
        """将输入转换为 LangChain 消息格式"""
        msgs = []
        if self.messages:
            for msg in self.messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "user":
                    msgs.append(HumanMessage(content=content))
                elif role == "assistant":
                    msgs.append(AIMessage(content=content))
        msgs.append(HumanMessage(content=self.query))
        return msgs


class AgentStep(BaseModel):
    """单个执行步骤"""
    step_index: int = Field(..., description="步骤序号")
    step_type: StepType = Field(..., description="步骤类型")
    content: str = Field(..., description="步骤内容")
    tool_name: Optional[str] = Field(default=None, description="使用的工具名")
    tool_input: Optional[dict] = Field(default=None, description="工具输入")
    tool_output: Optional[str] = Field(default=None, description="工具输出")
    timestamp: float = Field(default_factory=time.time)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentOutput(BaseModel):
    """统一的 Agent 输出"""
    answer: str = Field(..., description="最终回答")
    status: AgentStatus = Field(default=AgentStatus.SUCCESS, description="执行状态")
    steps: list[AgentStep] = Field(default_factory=list, description="执行过程中的所有步骤")
    agent_mode: AgentMode = Field(..., description="使用的 Agent 模式")
    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="本次运行ID")
    total_steps: int = Field(default=0, description="总步数")
    total_tokens: Optional[int] = Field(default=None, description="消耗的总 token 数")
    elapsed_time: Optional[float] = Field(default=None, description="耗时(秒)")
    error: Optional[str] = Field(default=None, description="错误信息")
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def is_success(self) -> bool:
        return self.status == AgentStatus.SUCCESS

    def get_steps_by_type(self, step_type: StepType) -> list[AgentStep]:
        """按类型筛选步骤"""
        return [s for s in self.steps if s.step_type == step_type]

    def summary(self) -> str:
        """生成执行摘要"""
        return (
            f"[{self.agent_mode.value}] Status: {self.status.value} | "
            f"Steps: {self.total_steps} | "
            f"Tokens: {self.total_tokens or 'N/A'} | "
            f"Time: {self.elapsed_time:.2f}s" if self.elapsed_time else "Time: N/A"
        )


class AgentConfig(BaseModel):
    """Agent 通用配置"""
    verbose: bool = Field(default=False, description="是否打印详细日志")
    max_steps: int = Field(default=10, description="默认最大步数")
    temperature: float = Field(default=0.0, description="LLM 温度")
    callbacks: Optional[list] = Field(default=None, description="回调列表")
    extra: dict[str, Any] = Field(default_factory=dict, description="额外配置")


class BaseAgent(ABC):
    """
    所有 Agent 模式的基类
    
    子类需实现：
        - mode: 返回 AgentMode
        - _build(): 构建内部 agent 实例
        - _run(): 执行具体逻辑
    """
    
    def __init__(
        self,
        llm: BaseChatModel,
        tools: list[BaseTool] | None = None,
        system_prompt: str | None = None,
        config: AgentConfig | None = None,
    ):
        self.llm = llm
        self.tools = tools or []
        self.system_prompt = system_prompt
        self.config = config or AgentConfig()
        
        self._agent = None
        self._is_built = False
        
        from .utils.logging import AgentLogger
        self._logger = AgentLogger(self.__class__.__name__, verbose=self.config.verbose)
        
        self._build()
        self._is_built = True
    
    @property
    @abstractmethod
    def mode(self) -> AgentMode:
        """返回当前 Agent 的模式类型"""
        ...
    
    @abstractmethod
    def _build(self) -> None:
        """构建内部 agent 实例"""
        ...
    
    @abstractmethod
    def _run(self, agent_input: AgentInput) -> AgentOutput:
        """执行具体的 agent 逻辑"""
        ...
    
    def invoke(self, input: str | dict | AgentInput, **kwargs) -> AgentOutput:
        """统一调用入口"""
        agent_input = self._normalize_input(input, **kwargs)
        
        start_time = time.time()
        self._logger.start(agent_input.query)
        
        try:
            output = self._run(agent_input)
            output.elapsed_time = time.time() - start_time
            output.agent_mode = self.mode
            
            self._logger.end(output.answer, output.total_steps, output.elapsed_time)
            
            return output
            
        except Exception as e:
            elapsed = time.time() - start_time
            self._logger.error(str(e))
            return AgentOutput(
                answer=f"Agent 执行失败: {str(e)}",
                status=AgentStatus.FAILED,
                agent_mode=self.mode,
                elapsed_time=elapsed,
                error=str(e),
            )
    
    async def ainvoke(self, input: str | dict | AgentInput, **kwargs) -> AgentOutput:
        """异步调用入口"""
        return self.invoke(input, **kwargs)
    
    def stream(self, input: str | dict | AgentInput, **kwargs):
        """流式调用入口"""
        output = self.invoke(input, **kwargs)
        yield output
    
    def _normalize_input(self, input: str | dict | AgentInput, **kwargs) -> AgentInput:
        """将各种输入格式统一转换为 AgentInput"""
        if isinstance(input, AgentInput):
            return input
        elif isinstance(input, str):
            return AgentInput(query=input, **kwargs)
        elif isinstance(input, dict):
            input_copy = dict(input)
            input_copy.update(kwargs)
            return AgentInput(**input_copy)
        else:
            raise ValueError(f"不支持的输入类型: {type(input)}")
    
    def __repr__(self) -> str:
        tool_names = [t.name for t in self.tools] if self.tools else []
        return f"<{self.__class__.__name__} mode={self.mode.value} tools={tool_names}>"
