"""
flux_agent/agents/base.py
统一的 Agent 基类、输入输出定义
"""
from __future__ import annotations

import uuid
import time
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Optional, List

from pydantic import BaseModel, Field
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from .skill import Skill, SkillLoader, SkillSelector, SkillRegistry, SkillExecutor, build_skill_tools


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
    # Skill 相关字段
    skills: List[Skill] = Field(default_factory=list, description="可用的 skills 全集")
    active_skills: List[str] = Field(default_factory=list, description="本次强制激活的 skill 名称列表")
    auto_select_skills: bool = Field(default=True, description="是否由 Agent 自主选择 skills")

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
        skills: List[Skill] | None = None,
        skills_dir: str = "skills",
    ):
        self.llm = llm
        self.tools = tools or []
        self.system_prompt = system_prompt
        self.config = config or AgentConfig()

        # Skill 相关
        self._skill_loader = SkillLoader(skills_dir) if skills_dir else None
        self._skill_registry = SkillRegistry(self._skill_loader)
        self._skill_executor = SkillExecutor()

        # 注册传入的 skills
        if skills:
            self._skill_registry.register_all(skills)

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

    # ========== Skill 管理方法 ==========

    @property
    def skill_registry(self) -> SkillRegistry:
        return self._skill_registry

    def add_skill(self, skill: Skill) -> None:
        """动态添加 skill"""
        self._skill_registry.register(skill)

    def load_skill(self, name: str) -> None:
        """按名称加载 skill"""
        if not self._skill_loader:
            self._skill_loader = SkillLoader()
        skill = self._skill_loader.load(name)
        self.add_skill(skill)

    def load_all_skills(self) -> None:
        """从 skills 目录加载并注册所有 Skill"""
        self._skill_registry.load_and_register_all()

    def list_available_skills(self) -> list[str]:
        """列出所有可用的 skill 名称"""
        if self._skill_loader:
            return self._skill_loader.list_skills()
        return []

    def _resolve_active_skills(self, agent_input: AgentInput) -> List[Skill]:
        """
        解析本次调用应激活的 Skills

        优先级：
        1. active_skills — invoke 时强制指定的 skill 名称
        2. 显式引用 — query 中 "使用 xxx 技能" 格式
        3. auto_select_skills=True — 不做自动选择，而是注入 catalog 让 LLM 自行判断
        """
        registry = self._skill_registry
        resolved: List[Skill] = []

        # 1. 强制激活
        for name in agent_input.active_skills:
            skill = registry.get(name)
            if skill:
                resolved.append(skill)
            else:
                # 尝试从 loader 按需加载
                try:
                    if self._skill_loader:
                        s = self._skill_loader.load(name)
                        registry.register(s)
                        resolved.append(s)
                except ValueError:
                    pass

        if resolved:
            return resolved

        # 2. 显式引用
        skill_name = SkillSelector.parse_skill_reference(agent_input.query)
        if skill_name:
            skill = registry.get(skill_name)
            if skill:
                return [skill]
            try:
                if self._skill_loader:
                    s = self._skill_loader.load(skill_name)
                    registry.register(s)
                    return [s]
            except ValueError:
                pass

        # 3. 传入的 skills 列表中的非 disable_model_invocation 项（由 LLM 通过 catalog 自行选择）
        # 这里不做自动匹配，返回空列表表示"尚未激活"
        return []

    def _build_system_prompt_with_skills(
        self,
        active_skills: List[Skill],
        base_prompt: str = "",
        include_catalog: bool = True,
    ) -> str:
        """
        构建包含 Skill 的 system prompt

        三层注入：
        1. base_prompt — 原始 system prompt
        2. Skill 目录摘要 — 所有可用 Skill 的 name + description
        3. 已激活 Skill 的完整内容
        """
        parts = [base_prompt] if base_prompt else []

        # 第一层：注入 Skill 目录摘要（让 LLM 知道有哪些 Skill 可用）
        if include_catalog:
            catalog = self._skill_registry.build_skill_catalog_prompt()
            if catalog:
                parts.append("\n\n" + catalog)

        # 第二层：注入已激活 Skill 的完整内容
        if active_skills:
            parts.append("\n\n# Active Skills\n")
            parts.append("Follow the instructions in these skills:\n")
            for skill in active_skills:
                parts.append(f"\n---\n## Skill: {skill.name}\n")
                parts.append(skill.content)

        return "\n".join(parts)

    def _get_skill_tools(self) -> list[BaseTool]:
        """
        生成 Skill 操作的 LangChain Tools。

        有注册的 invocable skills 时返回 3 个 tool：
        - activate_skill: LLM 看到 catalog 后调用，获取 skill content
        - run_skill_script: LLM 根据 content 判断后调用，执行脚本
        - load_skill_reference: LLM 根据 content 判断后调用，加载参考资料

        无 skills 时返回空列表。
        """
        if not self._skill_registry.invocable_skills:
            return []
        if not hasattr(self, "_cached_skill_tools"):
            self._cached_skill_tools = build_skill_tools(
                self._skill_registry, self._skill_loader
            )
        return self._cached_skill_tools

    def _get_all_tools(self) -> list[BaseTool]:
        """获取用户 tools + skill tools 的合并列表"""
        return self.tools + self._get_skill_tools()
    
    def __repr__(self) -> str:
        tool_names = [t.name for t in self.tools] if self.tools else []
        return f"<{self.__class__.__name__} mode={self.mode.value} tools={tool_names}>"
