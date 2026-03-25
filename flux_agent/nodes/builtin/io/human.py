# nodes/human.py
"""
人工输入节点

暂停工作流等待人工输入。
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from flux_agent.nodes.base import BaseNode, NodeConfig


@dataclass
class HumanInputNodeConfig(NodeConfig):
    """人工输入节点配置"""

    prompt: str = "请输入"
    output_key: str = "data.human_input"
    timeout: int = 3600
    default_value: Any = None
    options: List[str] = field(default_factory=list)
    input_type: str = "text"
    required: bool = True


class HumanInputNode(BaseNode):
    """人工输入节点"""

    node_type = "human_input"
    config_class = HumanInputNodeConfig

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        prompt_text = self._interpolate(self.config.prompt, state)

        interrupt_data = {
            "type": "human_input",
            "prompt": prompt_text,
            "timeout": self.config.timeout,
            "default": self.config.default_value,
            "options": self.config.options,
            "input_type": self.config.input_type,
            "required": self.config.required,
        }

        try:
            from langgraph.types import interrupt

            result = interrupt(interrupt_data)
            return self._set_nested({}, self.config.output_key, result)
        except ImportError:
            return {
                "__interrupt__": [interrupt_data],
                "data": {"_waiting_for_input": self.config.output_key},
            }
