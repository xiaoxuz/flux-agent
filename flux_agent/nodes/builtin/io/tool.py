# nodes/tool.py
"""
工具节点

执行预定义的工具函数。
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
import importlib

from flux_agent.nodes.base import BaseNode, NodeConfig


@dataclass
class ToolNodeConfig(NodeConfig):
    """工具节点配置"""

    tool_name: str = ""
    args: Dict[str, Any] = field(default_factory=dict)
    output_key: str = "data.tool_result"
    parse_output: bool = True
    error_on_fail: bool = True


class ToolNode(BaseNode):
    """工具调用节点"""

    node_type = "tool"
    config_class = ToolNodeConfig

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:

        if self.config.tool_name not in self.tools:
            if self.config.error_on_fail:
                raise ValueError(f"未找到工具: {self.config.tool_name}")
            return {"errors": [f"未找到工具: {self.config.tool_name}"]}

        tool_def = self.tools[self.config.tool_name]

        args = self._interpolate_dict(self.config.args, state)

        try:
            if callable(tool_def):
                result = tool_def(**args)
            elif isinstance(tool_def, dict):
                result = self._execute_tool_def(tool_def, args)
            else:
                raise ValueError(f"无效的工具定义: {self.config.tool_name}")

            if self.config.parse_output and isinstance(result, str):
                import json

                try:
                    result = json.loads(result)
                except json.JSONDecodeError:
                    pass

            return self._set_nested({}, self.config.output_key, result)

        except Exception as e:
            if self.config.error_on_fail:
                raise
            return {"errors": [f"工具执行失败: {e}"]}

    def _execute_tool_def(self, tool_def: Dict, args: Dict) -> Any:
        """执行工具定义"""
        impl = tool_def.get("implementation")

        if callable(impl):
            return impl(**args)

        if isinstance(impl, str):
            if ":" in impl:
                module_path, func_name = impl.rsplit(":", 1)
            else:
                parts = impl.rsplit(".", 1)
                if len(parts) == 2:
                    module_path, func_name = parts
                else:
                    raise ValueError(f"无效的实现路径: {impl}")

            module = importlib.import_module(module_path)
            func = getattr(module, func_name)
            return func(**args)

        raise ValueError(f"无效的工具实现: {impl}")
