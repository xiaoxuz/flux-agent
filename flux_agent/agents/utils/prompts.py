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
