"""
flux_agent/agents/utils/prompts.py
集中管理各模式的 Prompt 模板
"""
from __future__ import annotations


class PromptTemplate:
    """简单的 prompt 模板"""
    
    def __init__(self, template: str, name: str = ""):
        self.template = template
        self.name = name
    
    def format(self, **kwargs) -> str:
        return self.template.format(**kwargs)
    
    def __repr__(self):
        return f"<PromptTemplate name='{self.name}' len={len(self.template)}>"


class PromptLibrary:
    """Prompt 模板库"""
    
    _prompts: dict[str, PromptTemplate] = {}
    
    @classmethod
    def get(cls, key: str) -> PromptTemplate:
        if key not in cls._prompts:
            raise KeyError(f"未找到 prompt: '{key}'。可用: {list(cls._prompts.keys())}")
        return cls._prompts[key]
    
    @classmethod
    def set(cls, key: str, template: str):
        """覆盖或新增一个 prompt 模板"""
        cls._prompts[key] = PromptTemplate(template=template, name=key)
    
    @classmethod
    def list_keys(cls) -> list[str]:
        return list(cls._prompts.keys())


# Plan-Execute Prompts
PromptLibrary.set("plan_execute.planner", """你是一个任务规划专家。根据用户的任务，制定一个清晰的分步执行计划。

要求：
1. 每个步骤必须具体、可执行
2. 步骤之间有清晰的依赖关系
3. 最后一步必须是"汇总以上结果，给出最终回答"
4. 步骤数量控制在 3-7 步

请用以下格式输出计划：
Step 1: <具体步骤>
Step 2: <具体步骤>
...

用户任务: {task}""")

PromptLibrary.set("plan_execute.executor", """你正在执行一个多步计划中的某一步。

完整计划:
{plan}

之前步骤的结果:
{previous_results}

当前需要执行的步骤: {current_step}

请执行当前步骤，给出详细结果。""")

PromptLibrary.set("plan_execute.replanner", """你是一个任务规划专家。根据执行进度，判断是否需要调整计划。

原始任务: {task}
原始计划:
{plan}

已完成步骤及结果:
{completed_results}

请判断：
1. 如果已有足够信息回答原始任务，请直接输出: FINAL_ANSWER: <最终回答>
2. 如果需要继续执行或调整计划，请输出调整后的剩余步骤""")

# Reflexion Prompts
PromptLibrary.set("reflexion.generator", """你是一个专业的助手。请根据以下任务给出高质量的回答。

任务: {task}

{reflection_context}

请给出你的回答:""")

PromptLibrary.set("reflexion.evaluator", """你是一个严格的质量评估专家。请评估以下回答的质量。

原始任务: {task}
当前回答: {answer}

请从以下维度评分（1-10分）并给出评价：
1. 准确性：信息是否正确
2. 完整性：是否覆盖了所有要点
3. 逻辑性：推理是否清晰
4. 实用性：对用户是否有帮助

综合评分（1-10）：
评价：
是否需要改进（YES/NO）：""")

PromptLibrary.set("reflexion.reflector", """你是一个自我反思专家。根据评估反馈，分析当前回答的问题并提出改进方向。

原始任务: {task}
当前回答: {answer}
评估反馈: {evaluation}

历史反思:
{previous_reflections}

请进行深入反思：
1. 当前回答的主要问题是什么？
2. 具体哪些地方需要改进？
3. 改进的具体方向和策略是什么？

反思:""")

# Supervisor Prompts
PromptLibrary.set("supervisor.decompose", """你是一个任务分解专家。请将以下用户任务拆解为可由不同专业 Agent 完成的子任务。

可用 Worker 列表（仅能使用下方列出的 worker）:
{worker_descriptions}

用户任务: {query}

请将任务分解为若干子任务，每个子任务需要指定:
1. worker_name: 从上述列表中选择最合适的 worker
2. task_description: 给该 worker 的具体任务描述
3. depends_on: 依赖的 worker 名称列表（如该子任务需要等待其他 worker 的结果才能执行，则填入依赖 worker 的 name；如无依赖则为空数组）

请以 JSON 数组格式输出:
[
  {{"worker_name": "researcher", "task_description": "...", "depends_on": []}},
  {{"worker_name": "writer", "task_description": "...", "depends_on": ["researcher"]}}
]

注意:
- 每个子任务必须指定存在的 worker_name
- 如果子任务需要前置 worker 的结果（如写报告依赖搜索结果），必须在 depends_on 中声明
- 子任务按数组顺序执行，有依赖的子任务会自动收到依赖 worker 的结果作为上下文
- 如果单个 worker 能完成全部，只输出一个子任务
- **如果某个 worker 的可用工具中包含 activate_skill 和 run_skill_script，task_description 中必须明确指示该 worker 先调用 activate_skill 激活对应 skill，再通过 run_skill_script 执行分析**
- **如果某个 worker 的可用工具中包含普通工具（如 celsius_to_fahrenheit），task_description 中必须明确指示该 worker 使用这些工具**""")

PromptLibrary.set("supervisor.plan_workers", """你是一个任务规划专家。分析用户任务的复杂度，判断是否需要多角色协作。

用户任务: {query}

{available_tools}

请判断：
1. 如果该任务可以由一个通用助手直接回答，输出空数组 []
2. 如果需要多个专业角色协作，输出 worker 定义数组

输出 JSON 格式:
[]  // 单角色够用

或
[
  {{"name": "researcher", "mode": "react", "description": "负责搜索和信息收集", "tools": ["web_search"], "depends_on": []}},
  {{"name": "analyst", "mode": "plan_execute", "description": "负责数据分析和报告撰写", "tools": [], "depends_on": ["researcher"]}}
]

每个 worker:
- name: 唯一标识符（英文小写）
- mode: "react"（推理模式+工具交互式）/"plan_execute"（多步规划式）/"reflexion"（反思模式）, 优先：react模式
- description: 该 worker 的职责描述
- tools: 需要的工具名称列表（从上方可用工具列表中选择，如无工具则为空数组）
  - 普通工具：直接写工具名（如 "web_search"）
  - Skill 工具：如果需要某个 Skill 的功能，需要将 "activate_skill", "run_skill_script", "load_skill_reference" 添加到 tools 中，worker 会通过 activate_skill 激活 skill 后再执行脚本
- depends_on: 依赖的 worker 名称列表（如该 worker 需要等待其他 worker 的结果才能执行，则填入依赖 worker 的 name；如无依赖则为空数组）

注意:
- worker 数量控制在 2-5 个
- 每个 worker 职责清晰不重叠
- 有先后依赖关系的 worker 需要正确设置 depends_on
- 如果任务需要 skill 的功能，确保将 activate_skill 和 run_skill_script 添加到对应 worker 的 tools 中
- 选择合适的 mode 匹配任务性质""")

PromptLibrary.set("supervisor.synthesize", """你是一个信息整合专家。请综合以下各 worker 的返回结果，给出针对原始任务的最终回答。

原始任务: {query}

各 Worker 结果:
{worker_results}

请综合以上信息，给出清晰、完整的最终回答。""")
