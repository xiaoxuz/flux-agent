"""
flux_agent/agents/reflexion_agent.py
Reflexion 模式：执行 → 评估 → 反思 → 改进重试
"""
import re

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langchain_core.messages import HumanMessage, SystemMessage

from .base import (
    BaseAgent, AgentMode, AgentInput, AgentOutput,
    AgentStep, AgentConfig, AgentStatus, StepType,
)
from .utils.prompts import PromptLibrary


class ReflexionAgent(BaseAgent):
    """
    Reflexion 自我反思模式 Agent
    
    工作流程：
    1. Generator: 生成初始回答
    2. Evaluator: 评估回答质量
    3. Reflector: 反思不足之处
    4. Generator: 基于反思改进回答
    5. 循环直到质量满意或达到最大轮次
    
    Usage:
        agent = ReflexionAgent(
            llm=llm,
            max_iterations=3,
            quality_threshold=8.0,
        )
        result = agent.invoke("写一个Python快速排序算法，要求有完整注释和测试")
    """
    
    def __init__(
        self,
        llm: BaseChatModel,
        tools: list[BaseTool] | None = None,
        system_prompt: str | None = None,
        config: AgentConfig | None = None,
        max_iterations: int = 3,
        quality_threshold: float = 8.0,
        evaluator_llm: BaseChatModel | None = None,
    ):
        self.max_iterations = max_iterations
        self.quality_threshold = quality_threshold
        self.evaluator_llm = evaluator_llm
        super().__init__(llm=llm, tools=tools, system_prompt=system_prompt, config=config)
    
    @property
    def mode(self) -> AgentMode:
        return AgentMode.REFLEXION
    
    def _get_evaluator_llm(self) -> BaseChatModel:
        """获取评估用的 LLM"""
        return self.evaluator_llm or self.llm
    
    def _build(self) -> None:
        """构建执行器"""
        if self.tools:
            from langgraph.prebuilt import create_react_agent
            self._executor = create_react_agent(
                model=self.llm,
                tools=self.tools,
            )
        else:
            self._executor = None
    
    def _run(self, agent_input: AgentInput) -> AgentOutput:
        """执行 Reflexion 流程"""
        task = agent_input.query
        
        steps = []
        step_index = 0
        attempts = []
        reflections = []
        current_answer = ""
        iteration = 0
        
        # 迭代循环
        while iteration < self.max_iterations:
            # 1. 生成/改进回答
            current_answer = self._generate(
                task=task,
                reflections=reflections,
            )
            attempts.append(current_answer)
            
            step = AgentStep(
                step_index=step_index,
                step_type=StepType.THOUGHT if iteration > 0 else StepType.ACTION,
                content=f"第{iteration+1}次尝试:\n{current_answer[:300]}...",
                metadata={"attempt_index": iteration},
            )
            steps.append(step)
            self._logger.step(step)
            step_index += 1
            
            label = "初始回答" if iteration == 0 else f"第{iteration+1}轮改进"
            self._logger.info(f"[{label}]: {current_answer[:200]}...")
            
            # 2. 评估
            score, needs_improvement, evaluation = self._evaluate(
                task=task,
                answer=current_answer,
            )
            
            self._logger.info(f"  评估分数: {score}/10 | 需要改进: {needs_improvement}")
            
            # 3. 判断是否满意
            is_satisfied = (score >= self.quality_threshold) or (not needs_improvement)
            
            if is_satisfied:
                break
            
            if iteration >= self.max_iterations - 1:
                self._logger.info(f"  达到最大迭代次数 ({self.max_iterations})，停止反思")
                break
            
            # 4. 反思
            reflection = self._reflect(
                task=task,
                answer=current_answer,
                evaluation=evaluation,
                previous_reflections=reflections,
            )
            reflections.append(reflection)
            
            step = AgentStep(
                step_index=step_index,
                step_type=StepType.REFLECTION,
                content=reflection,
                metadata={"reflection_index": iteration},
            )
            steps.append(step)
            self._logger.step(step)
            
            self._logger.info(f"  反思: {reflection[:200]}...")
            
            iteration += 1
        
        # 最终答案
        step = AgentStep(
            step_index=step_index,
            step_type=StepType.FINAL_ANSWER,
            content=current_answer,
        )
        steps.append(step)
        self._logger.step(step)
        
        return AgentOutput(
            answer=current_answer,
            status=AgentStatus.SUCCESS,
            steps=steps,
            agent_mode=self.mode,
            total_steps=len(steps),
            metadata={
                "total_iterations": iteration + 1,
                "total_reflections": len(reflections),
                "final_score": score if 'score' in dir() else None,
            },
        )
    
    def _generate(self, task: str, reflections: list[str]) -> str:
        """生成/改进回答"""
        if reflections:
            reflection_context = "基于以下反思进行改进:\n" + "\n".join([
                f"第{i+1}轮反思: {r}" for i, r in enumerate(reflections)
            ])
        else:
            reflection_context = ""
        
        system = self.system_prompt or "你是一个专业的助手，追求高质量输出。"
        
        prompt_template = PromptLibrary.get("reflexion.generator")
        prompt = prompt_template.format(
            task=task,
            reflection_context=reflection_context,
        )
        
        response = self.llm.invoke([
            SystemMessage(content=system),
            HumanMessage(content=prompt),
        ])

        if self._executor and self.tools:
            exec_result = self._executor.invoke({
                "messages": [SystemMessage(content=system), HumanMessage(content=prompt)]
            })
            
            result_text = ""
            for msg in reversed(exec_result.get("messages", [])):
                if hasattr(msg, 'content') and msg.type == "ai" and not getattr(msg, "tool_calls", None):
                    result_text = msg.content
                    break
            
            return result_text or "执行完成"
        else:
            response = self.llm.invoke([
                SystemMessage(content=system),
                HumanMessage(content=prompt),
            ])
            return response.content
    
    def _evaluate(self, task: str, answer: str) -> tuple[float, bool, str]:
        """评估当前回答质量，返回 (分数, 是否需要改进, 评估内容)"""
        prompt_template = PromptLibrary.get("reflexion.evaluator")
        prompt = prompt_template.format(task=task, answer=answer)
        
        evaluator_llm = self._get_evaluator_llm()
        response = evaluator_llm.invoke([
            SystemMessage(content="你是一个严格的质量评估专家。"),
            HumanMessage(content=prompt),
        ])
        
        evaluation = response.content
        
        score = self._parse_score(evaluation)
        needs_improvement = self._parse_needs_improvement(evaluation)
        
        return score, needs_improvement, evaluation
    
    def _reflect(
        self,
        task: str,
        answer: str,
        evaluation: str,
        previous_reflections: list[str],
    ) -> str:
        """反思并提出改进方向"""
        prev_text = "\n".join([
            f"第{i+1}轮: {r}" for i, r in enumerate(previous_reflections)
        ]) if previous_reflections else "无"
        
        prompt_template = PromptLibrary.get("reflexion.reflector")
        prompt = prompt_template.format(
            task=task,
            answer=answer,
            evaluation=evaluation,
            previous_reflections=prev_text,
        )
        
        response = self.llm.invoke([
            SystemMessage(content="你是一个善于自我反思和改进的专家。"),
            HumanMessage(content=prompt),
        ])
        
        return response.content
    
    def _parse_score(self, evaluation: str) -> float:
        """从评估文本中提取分数"""
        patterns = [
            r"综合评分[：:]\s*(\d+(?:\.\d+)?)",
            r"(\d+(?:\.\d+)?)\s*/\s*10",
            r"评分[：:]\s*(\d+(?:\.\d+)?)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, evaluation)
            if match:
                return float(match.group(1))
        
        return 5.0
    
    def _parse_needs_improvement(self, evaluation: str) -> bool:
        """解析是否需要改进"""
        lower = evaluation.lower()
        
        if "no" in lower or "否" in lower:
            no_idx = lower.find("no")
            否_idx = lower.find("否")
            if no_idx >= 0 or 否_idx >= 0:
                return False
        
        if "yes" in lower or "是" in lower:
            return True
        
        return True
