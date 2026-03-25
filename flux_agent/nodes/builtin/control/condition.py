# nodes/builtin/control/condition.py
"""
条件节点

根据条件表达式路由到不同的目标节点。
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from flux_agent.nodes.base import BaseNode, NodeConfig
from flux_agent.utils.expression import evaluate_condition


@dataclass
class ConditionNodeConfig(NodeConfig):
    """条件节点配置"""

    branches: List[Dict[str, str]] = field(default_factory=list)
    mode: str = "first_match"


class ConditionNode(BaseNode):
    """
    条件分支节点

    根据条件表达式决定执行路径：
    - 按顺序评估每个分支的条件
    - 返回第一个满足条件的分支目标
    - 支持默认分支（condition: "default"）
    """

    node_type = "condition"
    config_class = ConditionNodeConfig

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """评估条件并返回目标节点"""

        for branch in self.config.branches:
            condition = branch.get("condition", "default")
            target = branch.get("target")

            if condition == "default":
                self._log_decision(state, condition, target, is_default=True)
                return {"_route": target}

            try:
                if evaluate_condition(condition, state):
                    self._log_decision(state, condition, target)
                    return {"_route": target}
            except Exception as e:
                continue

        raise ValueError("没有匹配的条件分支，且没有默认分支")

    def _log_decision(self, state: Dict, condition: str, target: str, is_default: bool = False):
        """记录决策日志"""
        import logging

        logger = logging.getLogger(__name__)

        if is_default:
            logger.debug(f"条件节点: 使用默认分支 -> {target}")
        else:
            logger.debug(f"条件节点: 条件 '{condition}' 满足 -> {target}")

    def get_all_targets(self) -> List[str]:
        """获取所有可能的目标节点"""
        return [branch.get("target") for branch in self.config.branches if branch.get("target")]
