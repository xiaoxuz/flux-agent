"""
flux_agent/agents/utils/logging.py
Agent 日志工具
"""

import logging
import sys
from typing import Optional

from ..base import AgentStep, StepType

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(funcName)s | %(filename)s:%(lineno)d | %(message)s',
    datefmt='%H:%M:%S',
    stream=sys.stdout,
)


class AgentLogger:
    """Agent 日志记录器"""
    
    def __init__(self, name: str, verbose: bool = False):
        self.logger = logging.getLogger(f"flux_agent.{name}")
        self.verbose = verbose
    
    def info(self, msg: str):
        if self.verbose:
            self.logger.info(msg)
    
    def debug(self, msg: str):
        if self.verbose:
            self.logger.debug(msg)
    
    def step(self, step: AgentStep):
        """打印步骤详情"""
        if not self.verbose:
            return
        
        icon = {
            StepType.THOUGHT: "💭",
            StepType.ACTION: "🔧",
            StepType.OBSERVATION: "👁",
            StepType.PLAN: "📋",
            StepType.REFLECTION: "🤔",
            StepType.FINAL_ANSWER: "✅",
        }.get(step.step_type, "•")
        
        content = step.content[:100] + "..." if len(step.content) > 100 else step.content
        
        if step.tool_name:
            self.logger.info(f"{icon} Step {step.step_index} [{step.step_type.value}] {step.tool_name}: {content}")
        else:
            self.logger.info(f"{icon} Step {step.step_index} [{step.step_type.value}] {content}")
    
    def start(self, query: str):
        """打印开始执行"""
        if self.verbose:
            q = query[:80] + "..." if len(query) > 80 else query
            self.logger.info(f"🚀 开始执行: {q}")
    
    def end(self, answer: str, total_steps: int, elapsed: float):
        """打印执行完成"""
        if self.verbose:
            a = answer[:100] + "..." if len(answer) > 100 else answer
            self.logger.info(f"🏁 完成 | 步数: {total_steps} | 耗时: {elapsed:.2f}s")
            self.logger.info(f"   回答: {a}")
    
    def error(self, msg: str):
        self.logger.error(f"❌ {msg}")