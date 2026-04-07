"""
flux_agent/agents/utils/callbacks.py
统一的 Agent 事件回调系统
"""
from __future__ import annotations

from abc import ABC

from ..base import AgentInput, AgentOutput, AgentStep, AgentMode


class AgentCallback(ABC):
    """Agent 事件回调基类"""
    
    def on_agent_start(self, mode: AgentMode, input: AgentInput) -> None:
        """Agent 开始执行"""
        pass
    
    def on_agent_end(self, output: AgentOutput) -> None:
        """Agent 执行完成"""
        pass
    
    def on_agent_error(self, error: Exception) -> None:
        """Agent 执行出错"""
        pass
    
    def on_step(self, step: AgentStep) -> None:
        """每个步骤完成时"""
        pass
    
    def on_plan_created(self, plan: list[str]) -> None:
        """计划生成完成（Plan-Execute 模式）"""
        pass
    
    def on_reflection(self, reflection: str, iteration: int) -> None:
        """反思完成（Reflexion 模式）"""
        pass
    
    def on_tool_start(self, tool_name: str, tool_input: dict) -> None:
        """工具开始调用"""
        pass
    
    def on_tool_end(self, tool_name: str, tool_output: str) -> None:
        """工具调用完成"""
        pass


class PrintCallback(AgentCallback):
    """内置的打印回调 — 用于调试"""
    
    def on_agent_start(self, mode: AgentMode, input: AgentInput):
        print(f"\n{'='*60}")
        print(f"Agent 启动 | 模式: {mode.value}")
        print(f"输入: {input.query[:100]}...")
        print(f"{'='*60}")
    
    def on_agent_end(self, output: AgentOutput):
        print(f"\n{'='*60}")
        print(f"Agent 完成 | {output.summary()}")
        print(f"回答: {output.answer[:200]}...")
        print(f"{'='*60}")
    
    def on_agent_error(self, error: Exception):
        print(f"\nAgent 错误: {error}")
    
    def on_step(self, step: AgentStep):
        icons = {
            "thought": "🧠",
            "action": "🔧",
            "observation": "👁",
            "plan": "📋",
            "reflection": "🔍",
            "final_answer": "💡",
        }
        icon = icons.get(step.step_type.value, "▶")
        content_preview = step.content[:150] if len(step.content) > 150 else step.content
        print(f"  {icon} Step {step.step_index}: [{step.step_type.value}] {content_preview}")
    
    def on_plan_created(self, plan: list[str]):
        print(f"\n计划生成 ({len(plan)} 步):")
        for i, step in enumerate(plan):
            print(f"   {i+1}. {step}")
    
    def on_reflection(self, reflection: str, iteration: int):
        preview = reflection[:200] if len(reflection) > 200 else reflection
        print(f"\n第{iteration}轮反思: {preview}...")
    
    def on_tool_start(self, tool_name: str, tool_input: dict):
        print(f"  调用工具: {tool_name}({tool_input})")
    
    def on_tool_end(self, tool_name: str, tool_output: str):
        preview = tool_output[:100] if len(tool_output) > 100 else tool_output
        print(f"  工具返回: {tool_name} -> {preview}")


class CallbackManager:
    """回调管理器"""
    
    def __init__(self, callbacks: list[AgentCallback] | None = None):
        self.callbacks = callbacks or []
    
    def add(self, callback: AgentCallback):
        self.callbacks.append(callback)
    
    def fire(self, event: str, **kwargs):
        """触发事件"""
        for cb in self.callbacks:
            method = getattr(cb, event, None)
            if method and callable(method):
                try:
                    method(**kwargs)
                except Exception as e:
                    print(f"Callback {cb.__class__.__name__}.{event} 出错: {e}")
