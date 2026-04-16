"""
flux_agent/agents/supervisor_agent.py
Supervisor 模式 — Agent 内部自动编排：任务分解 -> 分发执行 -> 结果合成
"""
from __future__ import annotations

import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Dict, List

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool

from .base import (
    BaseAgent, AgentMode, AgentInput, AgentOutput,
    AgentConfig, AgentStatus, StepType, AgentStep,
    TokenUsageSummary,
)
from .factory import create_agent, WorkerConfig
from .skill import Skill
from .utils.prompts import PromptLibrary
from .utils.token_usage import extract_usage_from_message, aggregate_details_to_summary, merge_usage_summaries

logger = logging.getLogger(__name__)


@dataclass
class _WorkerInstance:
    """运行时 worker 实例"""
    config: WorkerConfig
    agent: BaseAgent


class SupervisorAgent(BaseAgent):
    """
    Supervisor 模式 Agent

    invoke() 时内部执行三阶段：
    1. 任务分解 — LLM 将 query 拆为子任务
    2. 分发执行 — 并行或串行调用 worker agent
    3. 结果合成 — LLM 汇总所有 worker 结果

    Usage:
        supervisor = create_agent(
            mode="supervisor",
            llm=ChatOpenAI(),
            workers={
                "researcher": WorkerConfig(
                    mode="react", description="负责搜索和调研",
                    tools=["web_search"],
                ),
                "writer": WorkerConfig(
                    mode="plan_execute", description="负责撰写报告",
                    tools=["write_file"],
                ),
            }
        )
        result = supervisor.invoke("调研 AI 行业并写报告")
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
        workers: Dict[str, WorkerConfig] | None = None,
        parallel: bool = True,
    ):
        self._worker_configs = workers or {}
        self._parallel = parallel
        self._workers: Dict[str, _WorkerInstance] = {}
        self._auto_mode = workers is None  # 不传 workers 时启用自动模式

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
        return AgentMode.SUPERVISOR

    def _build(self) -> None:
        """实例化所有 worker agent（自动模式下初始时为空，由 _plan_workers 填充）"""
        # 使用完整工具池（user tools + skill tools + MCP tools）
        all_tools = self._get_all_tools()
        tool_map = {t.name: t for t in all_tools} if all_tools else {}
        # 准备 skills 传递给需要 skill 工具的 worker
        worker_skills = self._skill_registry.invocable_skills if self._skill_registry and self._skill_registry.invocable_skills else None

        for name, wcfg in self._worker_configs.items():
            # 按 worker 配置的 tools 字段筛选，只传对应的 BaseTool 实例
            worker_tools = [tool_map[n] for n in wcfg.tools if n in tool_map] if wcfg.tools else []
            worker_agent = create_agent(
                mode=wcfg.mode,
                llm=self.llm,
                tools=worker_tools,
                system_prompt=wcfg.system_prompt or None,
                config=self.config,
                skills=worker_skills,
            )
            self._workers[name] = _WorkerInstance(config=wcfg, agent=worker_agent)
            self._logger.info(f"SubAgent-显式模式：创建 Agent:[{name}] Tools:[{[t.name for t in worker_tools]}]")

    def _run(self, agent_input: AgentInput) -> AgentOutput:
        """三阶段：分解 -> 分发 -> 合成（自动模式下先规划 worker）"""
        query = agent_input.query
        details = []
        self._input_images = agent_input.image_list  # 保存完整图片列表用于 worker 分发

        # 自动模式：动态规划 worker
        if self._auto_mode and not self._workers:
            worker_plan = self._plan_workers(query, details, self._input_images)
            if not worker_plan:
                # LLM 判断单角色够用，用 ReactAgent 直接回复（带完整工具链）
                self._logger.info("SubAgent - 自动模式：LLM 判断无需多角色，创建 ReactAgent 直接回复")
                all_tools = self._get_all_tools()
                single_agent = create_agent(
                    mode="react",
                    llm=self.llm,
                    tools=all_tools,
                    config=self.config,
                    skills=self._skill_registry.invocable_skills if self._skill_registry and self._skill_registry.invocable_skills else None,
                )
                output = single_agent.invoke(agent_input)
                # 合并 ReactAgent 的 token usage
                if output.token_usage:
                    details.extend(output.token_usage.details)
                token_summary = aggregate_details_to_summary(details)
                return AgentOutput(
                    answer=output.answer,
                    status=output.status,
                    agent_mode=self.mode,
                    total_steps=output.total_steps,
                    total_tokens=token_summary.total_tokens or None,
                    token_usage=token_summary,
                )
            self._create_workers_from_plan(worker_plan)
            self._logger.info(f"SubAgent-自动模式：创建了 {len(self._workers)} 个 worker: {list(self._workers.keys())}")

        # Phase 1: 任务分解
        subtasks = self._decompose(query, details, self._input_images)
        if not subtasks:
            return AgentOutput(
                answer="无法分解任务，没有可用的 worker 能处理该请求",
                status=AgentStatus.FAILED,
                agent_mode=self.mode,
            )

        self._logger.info(f"分解为 {len(subtasks)} 个子任务: {subtasks}")
        self._emit_step(AgentStep(
            step_index=0,
            step_type=StepType.PLAN,
            content=f"任务分解为 {len(subtasks)} 个子任务",
            tool_output=json.dumps(subtasks, ensure_ascii=False),
        ))

        # Phase 2: 分发执行
        worker_results, worker_outputs = self._dispatch_with_output(subtasks)

        results_text = ""
        for i, (worker_name, result) in enumerate(worker_results.items()):
            results_text += f"\n--- {worker_name} ---\n{result}\n"
            self._emit_step(AgentStep(
                step_index=i + 1,
                step_type=StepType.OBSERVATION,
                content=f"Worker '{worker_name}' 完成",
                tool_name=worker_name,
                tool_output=result[:500] if len(result) > 500 else result,
            ))

        # Phase 3: 结果合成
        final_answer = self._synthesize(query, worker_results, details)

        # 聚合 token usage：orchestrator 自身 + 所有 worker
        token_summary = aggregate_details_to_summary(details)
        for w_out in worker_outputs.values():
            if w_out and w_out.token_usage:
                token_summary = merge_usage_summaries(token_summary, w_out.token_usage)

        return AgentOutput(
            answer=final_answer,
            status=AgentStatus.SUCCESS,
            agent_mode=self.mode,
            total_steps=len(worker_results) + 1,
            total_tokens=token_summary.total_tokens or None,
            token_usage=token_summary,
        )

    def _decompose(self, query: str, details: list, image_list: list[str] = None) -> list[dict]:
        """Phase 1: LLM 分解任务为子任务列表"""
        worker_desc = "\n".join(
            f"- {name}: {w.config.description} (可用工具: {[t.name for t in w.agent.tools]})"
            for name, w in self._workers.items()
        )
        if not worker_desc:
            worker_desc = "（无可用 worker）"

        prompt = PromptLibrary.get("supervisor.decompose").format(
            worker_descriptions=worker_desc,
            query=query,
        )

        # 构建多模态消息
        if image_list:
            image_blocks = [AgentInput._build_image_block(img) for img in image_list]
            user_content = [{"type": "text", "text": prompt}, *image_blocks]
        else:
            user_content = prompt

        resp = self.llm.invoke([("user", user_content)])
        if usage := extract_usage_from_message(resp, operation="decompose"):
            details.append(usage)
        raw = resp.content.strip()

        # 尝试提取 JSON
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

        try:
            tasks = json.loads(raw)
            if isinstance(tasks, list):
                # 过滤无效的 worker_name
                valid = set(self._workers.keys())
                result_tasks = []
                for t in tasks:
                    if not (isinstance(t, dict)
                            and t.get("worker_name") in valid
                            and t.get("task_description")):
                        continue
                    # 确保 depends_on 存在
                    if "depends_on" not in t:
                        t["depends_on"] = []
                    # 过滤无效的依赖
                    t["depends_on"] = [d for d in t["depends_on"] if d in valid]
                    result_tasks.append(t)
                return result_tasks
        except json.JSONDecodeError:
            pass

        self._logger.warning(f"任务分解失败，原始输出: {raw}")
        return []

    def _dispatch(self, subtasks: list[dict]) -> dict[str, str]:
        """Phase 2: 分发子任务到对应 worker 执行（向后兼容接口）"""
        results, _ = self._dispatch_with_output(subtasks)
        return results

    def _dispatch_with_output(self, subtasks: list[dict]) -> tuple[dict[str, str], dict[str, AgentOutput]]:
        """Phase 2: 分发子任务，返回 (string结果, AgentOutput结果)"""
        results: dict[str, str] = {}
        outputs: dict[str, AgentOutput] = {}

        # 检查是否有依赖关系
        has_deps = any(st.get("depends_on") for st in subtasks)

        if has_deps or not self._parallel:
            # 有依赖或串行模式：按顺序执行，传递前置结果
            for st in subtasks:
                wname = st["worker_name"]
                desc = st["task_description"]

                # 合并 WorkerConfig 中的依赖和子任务中的依赖
                worker_cfg = self._worker_configs.get(wname)
                cfg_deps = worker_cfg.depends_on if worker_cfg else []
                all_deps = list(dict.fromkeys(st.get("depends_on", []) + cfg_deps))

                # 将依赖结果拼入 task_description
                for dep in all_deps:
                    if dep in results:
                        desc += f"\n\n--- 来自 {dep} 的结果 ---\n{results[dep]}"

                try:
                    output = self._run_worker(wname, desc)
                    results[wname] = output.answer
                    outputs[wname] = output
                except Exception as e:
                    results[wname] = f"执行出错: {e}"
                if self._parallel is False:
                    time.sleep(0.1)
        else:
            # 并行执行：各 worker 独立
            with ThreadPoolExecutor(max_workers=len(subtasks)) as pool:
                futures = {}
                for st in subtasks:
                    wname = st["worker_name"]
                    desc = st["task_description"]
                    futures[pool.submit(self._run_worker, wname, desc)] = wname
                for fut in as_completed(futures):
                    wname = futures[fut]
                    try:
                        output = fut.result()
                        results[wname] = output.answer
                        outputs[wname] = output
                    except Exception as e:
                        results[wname] = f"执行出错: {e}"

        return results, outputs

    def _run_worker(self, worker_name: str, task_desc: str) -> AgentOutput:
        """调用单个 worker agent，返回完整 AgentOutput"""
        worker = self._workers.get(worker_name)
        if not worker:
            return AgentOutput(
                answer=f"Worker '{worker_name}' 不存在",
                status=AgentStatus.FAILED,
                agent_mode=self.mode,
            )

        self._logger.info(f"Dispatch to '{worker_name}': {task_desc}")

        # 根据 worker 的 image_indices 分发对应图片
        worker_images = []
        if worker.config.image_indices and hasattr(self, '_input_images') and self._input_images:
            worker_images = [
                self._input_images[i]
                for i in worker.config.image_indices
                if i < len(self._input_images)
            ]

        worker_input = AgentInput(query=task_desc, image_list=worker_images)
        return worker.agent.invoke(worker_input)

    def _synthesize(self, query: str, worker_results: dict[str, str], details: list) -> str:
        """Phase 3: LLM 合成最终回答"""
        results_text = "\n".join(
            f"**{name}**:\n{result}" for name, result in worker_results.items()
        )

        prompt = PromptLibrary.get("supervisor.synthesize").format(
            query=query,
            worker_results=results_text,
        )
        resp = self.llm.invoke([("user", prompt)])
        if usage := extract_usage_from_message(resp, operation="synthesize"):
            details.append(usage)
        return resp.content.strip()

    def _plan_workers(self, query: str, details: list, image_list: list[str] = None) -> list[dict]:
        """自动模式：LLM 规划需要哪些 worker 角色"""
        # 获取所有可用工具，注入到 prompt 中供 LLM 分配
        all_tools = self._get_all_tools()
        if all_tools:
            tools_desc = "\n".join(
                f'  - "{t.name}": {getattr(t, "description", "")}'
                for t in all_tools
            )
            available_tools_str = f"可用工具列表:\n{tools_desc}\n"
        else:
            available_tools_str = "可用工具列表:（无）\n"

        # 如果有 skills，注入 skill catalog 摘要
        if self._skill_registry and self._skill_registry.invocable_skills:
            skill_catalog = self._skill_registry.build_skill_catalog_prompt()
            if skill_catalog:
                available_tools_str += f"\n{skill_catalog}\n"

        # 如果有图片，注入图片说明
        image_instruction = ""
        if image_list:
            image_instruction = f"\n\n任务包含 {len(image_list)} 张图片（索引 0-{len(image_list)-1}）。"
            image_instruction += '如果任务包含多张图片，请在每个 worker 定义中添加 "image_indices": [0, 1] 字段来指定该 worker 需要查看的图片索引列表。'

        prompt = PromptLibrary.get("supervisor.plan_workers").format(
            query=query,
            available_tools=available_tools_str,
        ) + image_instruction

        # 构建多模态消息
        if image_list:
            image_blocks = [AgentInput._build_image_block(img) for img in image_list]
            user_content = [{"type": "text", "text": prompt}, *image_blocks]
        else:
            user_content = prompt

        resp = self.llm.invoke([("user", user_content)])
        if usage := extract_usage_from_message(resp, operation="plan_workers"):
            details.append(usage)
        raw = resp.content.strip()

        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

        try:
            plan = json.loads(raw)
            if isinstance(plan, list):
                # 验证每个 worker 定义
                valid = []
                for w in plan:
                    if (isinstance(w, dict)
                            and w.get("name")
                            and w.get("mode")
                            and w.get("description")):
                        valid.append(w)
                return valid
        except json.JSONDecodeError:
            pass

        self._logger.warning(f"Worker 规划失败，原始输出: {raw}")
        return []

    def _create_workers_from_plan(self, worker_defs: list[dict]) -> None:
        """根据 LLM 返回的 worker 定义创建 worker 实例"""
        # 使用完整工具池（user tools + skill tools + MCP tools）
        all_tools = self._get_all_tools()
        tool_map = {t.name: t for t in all_tools} if all_tools else {}
        # 准备 skills 传递给需要 skill 工具的 worker
        worker_skills = self._skill_registry.invocable_skills if self._skill_registry and self._skill_registry.invocable_skills else None

        for wdef in worker_defs:
            name = wdef["name"]
            wcfg = WorkerConfig(
                name=name,
                mode=wdef["mode"],
                description=wdef["description"],
                tools=wdef.get("tools", []),
                depends_on=wdef.get("depends_on", []),
                image_indices=wdef.get("image_indices", []),
            )
            # 按 LLM 指定的工具名筛选，只传对应的 BaseTool 实例
            worker_tools = [tool_map[n] for n in wdef.get("tools", []) if n in tool_map]
            worker_agent = create_agent(
                mode=wcfg.mode,
                llm=self.llm,
                tools=worker_tools,
                system_prompt=wcfg.system_prompt or None,
                config=self.config,
                skills=worker_skills,
            )
            self._workers[name] = _WorkerInstance(config=wcfg, agent=worker_agent)
            self._worker_configs[name] = wcfg
            self._logger.info(f"SubAgent-动态模式：创建 Agent:[{name}] Tools:[{[t.name for t in worker_tools]}] image_indices:[{wcfg.image_indices}]")

    def __repr__(self) -> str:
        worker_names = list(self._workers.keys())
        return (
            f"<SupervisorAgent workers={worker_names} "
            f"parallel={self._parallel}>"
        )
