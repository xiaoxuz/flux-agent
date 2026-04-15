"""
flux_agent/agents/plan_execute_agent.py
Plan-and-Execute 模式：先规划完整计划，再逐步执行
"""
import re

from typing import List

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langchain_core.messages import HumanMessage, SystemMessage

from .base import (
    BaseAgent, AgentMode, AgentInput, AgentOutput,
    AgentStep, AgentConfig, AgentStatus, StepType,
    TokenUsageSummary,
)
from .skill import Skill
from .utils.prompts import PromptLibrary
from .utils.token_usage import extract_usage_from_message, aggregate_details_to_summary


class PlanExecuteAgent(BaseAgent):
    """
    Plan-and-Execute 模式 Agent

    工作流程：
    1. Planner: LLM 分析任务，生成完整的分步计划
    2. Executor: 逐步执行计划（每步可调用工具）
    3. Replanner(可选): 根据执行结果动态调整后续计划

    Usage:
        agent = PlanExecuteAgent(
            llm=llm,
            tools=[search_tool],
            enable_replan=True,
        )
        result = agent.invoke("分析2024年中国新能源汽车市场趋势并给出投资建议")
    """

    def __init__(
        self,
        llm: BaseChatModel,
        tools: list[BaseTool] | None = None,
        system_prompt: str | None = None,
        config: AgentConfig | None = None,
        enable_replan: bool = True,
        skills: List[Skill] | None = None,
        skills_dir: str = "skills",
        mcp_servers: List[dict] | None = None,
    ):
        self.enable_replan = enable_replan
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
        return AgentMode.PLAN_EXECUTE
    
    def _build(self) -> None:
        """构建执行器"""
        all_tools = self._get_all_tools()
        if all_tools:
            from langgraph.prebuilt import create_react_agent
            self._executor = create_react_agent(
                model=self.llm,
                tools=all_tools,
            )
        else:
            self._executor = None

    def _run(self, agent_input: AgentInput) -> AgentOutput:
        """执行 Plan-and-Execute 流程"""
        task = agent_input.query

        # Skill 选择逻辑
        self._selected_skills = self._resolve_active_skills(agent_input)
        if self._selected_skills:
            self._logger.info(f"使用 Skills: {[s.name for s in self._selected_skills]}")

        steps = []
        step_index = 0
        details = []

        # 1. 生成计划
        plan = self._generate_plan(task, details)
        
        self._logger.info(f"\n生成计划 ({len(plan)} 步):")
        for i, p in enumerate(plan):
            self._logger.info(f"  {i+1}. {p}")
        
        for i, p in enumerate(plan):
            step = AgentStep(
                step_index=step_index,
                step_type=StepType.PLAN,
                content=f"计划第{i+1}步: {p}",
            )
            steps.append(step)
            self._emit_step(step)
            step_index += 1

        # 2. 执行计划
        step_results = []
        current_plan = plan

        for i, plan_step in enumerate(current_plan):
            self._logger.info(f"\n执行 Step {i+1}/{len(current_plan)}: {plan_step}")

            result = self._execute_step(
                task=task,
                plan=current_plan,
                previous_results=step_results,
                current_step=plan_step,
                step_index=step_index,
                details=details,
            )

            step_results.append(result)

            obs_step = AgentStep(
                step_index=step_index,
                step_type=StepType.OBSERVATION,
                content=result[:500] if len(result) > 500 else result,
                metadata={"plan_step_index": i},
            )
            steps.append(obs_step)
            self._emit_step(obs_step)
            step_index += 1
            
            # 3. 检查是否需要重规划
            if self.enable_replan and i < len(current_plan) - 1:
                should_continue, new_plan = self._replan(
                    task=task,
                    original_plan=current_plan,
                    completed_steps=current_plan[:i+1],
                    completed_results=step_results,
                    step_index=step_index,
                    details=details,
                )
                
                if not should_continue:
                    break
                
                if new_plan:
                    current_plan = current_plan[:i+1] + new_plan
                    self._logger.info(f"\n调整计划，剩余 {len(new_plan)} 步")
        
        # 4. 生成最终答案
        final_answer = step_results[-1] if step_results else "未能生成回答"
        
        answer_step = AgentStep(
            step_index=step_index,
            step_type=StepType.FINAL_ANSWER,
            content=final_answer[:500] if len(final_answer) > 500 else final_answer,
        )
        steps.append(answer_step)
        self._emit_step(answer_step)
        
        token_summary = aggregate_details_to_summary(details)

        return AgentOutput(
            answer=final_answer,
            status=AgentStatus.SUCCESS,
            steps=steps,
            agent_mode=self.mode,
            total_steps=len(steps),
            total_tokens=token_summary.total_tokens or None,
            token_usage=token_summary,
            metadata={
                "plan": current_plan,
                "enable_replan": self.enable_replan,
            },
        )
    
    def _generate_plan(self, task: str, details: list) -> list[str]:
        """生成执行计划"""
        prompt_template = PromptLibrary.get("plan_execute.planner")
        prompt = prompt_template.format(task=task)

        # 构建 system prompt — 包含 skill catalog + 已强制激活的 skills
        base_system = "你是一个任务规划专家。"
        system_content = self._build_system_prompt_with_skills(
            getattr(self, '_selected_skills', []),
            base_system,
            include_catalog=True,
        )

        response = self.llm.invoke([
            SystemMessage(content=system_content),
            HumanMessage(content=prompt),
        ])

        if usage := extract_usage_from_message(response, operation="generate_plan"):
            details.append(usage)

        return self._parse_plan(response.content)
    
    def _execute_step(
        self,
        task: str,
        plan: list[str],
        previous_results: list[str],
        current_step: str,
        step_index: int,
        details: list,
    ) -> str:
        """执行单步"""
        plan_text = "\n".join([f"Step {i+1}: {s}" for i, s in enumerate(plan)])
        prev_text = "\n".join([
            f"Step {i+1} 结果: {r}" for i, r in enumerate(previous_results)
        ]) if previous_results else "无"

        prompt_template = PromptLibrary.get("plan_execute.executor")
        exec_prompt = prompt_template.format(
            plan=plan_text,
            previous_results=prev_text,
            current_step=current_step,
        )

        if self._executor and self.tools:
            exec_result = self._executor.invoke({
                "messages": [HumanMessage(content=exec_prompt)]
            })

            result_text = ""
            for msg in reversed(exec_result.get("messages", [])):
                if hasattr(msg, 'content') and msg.type == "ai" and not getattr(msg, "tool_calls", None):
                    result_text = msg.content
                    if usage := extract_usage_from_message(msg, step_index=step_index, operation="execute_step"):
                        details.append(usage)
                    break

            return result_text or "执行完成"
        else:
            response = self.llm.invoke([HumanMessage(content=exec_prompt)])
            if usage := extract_usage_from_message(response, step_index=step_index, operation="execute_step"):
                details.append(usage)
            return response.content
    
    def _replan(
        self,
        task: str,
        original_plan: list[str],
        completed_steps: list[str],
        completed_results: list[str],
        step_index: int,
        details: list,
    ) -> tuple[bool, list[str] | None]:
        """重规划，返回 (是否继续, 新计划)"""
        plan_text = "\n".join([f"Step {i+1}: {s}" for i, s in enumerate(original_plan)])
        results_text = "\n".join([
            f"Step {i+1} 结果: {r}" for i, r in enumerate(completed_results)
        ])

        prompt_template = PromptLibrary.get("plan_execute.replanner")
        prompt = prompt_template.format(
            task=task,
            plan=plan_text,
            completed_results=results_text,
        )

        response = self.llm.invoke([HumanMessage(content=prompt)])
        if usage := extract_usage_from_message(response, step_index=step_index, operation="replan"):
            details.append(usage)
        content = response.content

        if "FINAL_ANSWER:" in content.upper():
            return False, None
        
        new_plan = self._parse_plan(content)
        return True, new_plan if new_plan else None
    
    def _parse_plan(self, text: str) -> list[str]:
        """从 LLM 输出中解析步骤列表"""
        lines = text.strip().split("\n")
        steps = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            match = re.match(
                r"^(?:Step\s*\d+[:.)]?\s*|[\d]+[.)]\s*|-\s*)(.*)",
                line,
                re.IGNORECASE
            )
            if match:
                step_content = match.group(1).strip()
                if step_content:
                    steps.append(step_content)
        
        if not steps and text.strip():
            steps = [text.strip()]
        
        return steps
