# nodes/builtin/control/loop.py
"""
循环节点

支持循环执行一组节点。
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from flux_agent.nodes.base import BaseNode, NodeConfig
from flux_agent.utils.expression import evaluate_condition


@dataclass
class LoopNodeConfig(NodeConfig):
    """循环节点配置"""

    condition: str = ""
    max_iterations: int = 10
    body_nodes: List[str] = field(default_factory=list)
    iteration_key: str = "data.iteration"
    break_on: str = ""
    delay: float = 0


class LoopNode(BaseNode):
    """循环节点"""

    node_type = "loop"
    config_class = LoopNodeConfig

    def execute(
        self, state: Dict[str, Any]
    ) -> Dict[str, Any]:
        result = state.copy() if state else {}

        iteration = self._get_nested(result, self.config.iteration_key, 0)

        return self._set_nested(result, self.config.iteration_key, iteration + 1)

    def should_continue(self, state: Dict[str, Any], context: Dict = None) -> bool:
        """判断是否继续循环"""
        iteration = self._get_nested(state, self.config.iteration_key, 0)

        if iteration >= self.config.max_iterations:
            return False

        if self.config.break_on:
            if evaluate_condition(self.config.break_on, state, context):
                return False

        if self.config.condition:
            return evaluate_condition(self.config.condition, state, context)

        return iteration < self.config.max_iterations
