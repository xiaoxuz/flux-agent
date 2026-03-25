# nodes/transform.py
"""
数据转换节点

执行各种数据转换操作。
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from auto_agent.nodes.base import BaseNode, NodeConfig
from auto_agent.utils.expression import ExpressionEvaluator


@dataclass
class TransformNodeConfig(NodeConfig):
    """转换节点配置"""

    transforms: List[Dict[str, Any]] = field(default_factory=list)


class TransformNode(BaseNode):
    """
    数据转换节点

    支持的操作：
    - set: 设置值
    - get: 获取值到新位置
    - copy: 复制值
    - delete: 删除字段
    - default: 设置默认值
    - merge: 合并对象
    - increment: 递增数值
    - append: 追加到列表
    - map: 映射列表元素
    - filter: 过滤列表
    """

    node_type = "transform"
    config_class = TransformNodeConfig

    ACTIONS = {
        "set",
        "get",
        "copy",
        "delete",
        "default",
        "merge",
        "increment",
        "append",
        "map",
        "filter",
        "format",
    }

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """执行转换操作"""
        result = state.copy() if state else {}


        for transform in self.config.transforms:
            action = transform.get("action")

            if action not in self.ACTIONS:
                continue

            handler = getattr(self, f"_action_{action}", None)
            if handler:
                result = handler(result, transform)
        return result

    def _action_set(self, state: Dict, transform: Dict,) -> Dict:
        """设置值"""
        key = transform.get("key", "")
        value = transform.get("value")

        if isinstance(value, str):
            value = self._interpolate(value, state)

        return self._set_nested(state, key, value)

    def _action_get(self, state: Dict, transform: Dict) -> Dict:
        """获取值到新位置"""
        from_key = transform.get("from", "")
        to_key = transform.get("to", "")
        default = transform.get("default")

        value = self._get_nested(state, from_key, default)
        return self._set_nested(state, to_key, value)

    def _action_copy(self, state: Dict, transform: Dict) -> Dict:
        """复制值"""
        from_key = transform.get("from", "")
        to_key = transform.get("to", "")

        value = self._get_nested(state, from_key)
        if value is not None:
            return self._set_nested(state, to_key, value)
        return state

    def _action_delete(self, state: Dict, transform: Dict) -> Dict:
        """删除字段"""
        key = transform.get("key", "")
        return self._delete_nested(state, key)

    def _action_default(self, state: Dict, transform: Dict) -> Dict:
        """设置默认值（如果已存在则跳过）"""
        key = transform.get("key", "")
        value = transform.get("value")

        if isinstance(value, str):
            value = self._interpolate(value, state)

        current = self._get_nested(state, key)
        if current is None:
            return self._set_nested(state, key, value)
        return state

    def _action_merge(self, state: Dict, transform: Dict) -> Dict:
        """合并对象"""
        key = transform.get("key", "")
        value = transform.get("value", {})

        if isinstance(value, dict):
            value = self._interpolate_dict(value, state)

        current = self._get_nested(state, key, {})
        if not isinstance(current, dict):
            current = {}

        merged = {**current, **value}
        return self._set_nested(state, key, merged)

    def _action_increment(self, state: Dict, transform: Dict) -> Dict:
        """递增数值"""
        key = transform.get("key", "")
        amount = transform.get("amount", 1)

        current = self._get_nested(state, key, 0)
        if isinstance(current, (int, float)):
            return self._set_nested(state, key, current + amount)
        return state

    def _action_append(self, state: Dict, transform: Dict) -> Dict:
        """追加到列表"""
        key = transform.get("key", "")
        value = transform.get("value")

        if isinstance(value, str):
            value = self._interpolate(value, state)

        current = self._get_nested(state, key, [])
        if not isinstance(current, list):
            current = []

        return self._set_nested(state, key, current + [value])

    def _action_map(self, state: Dict, transform: Dict) -> Dict:
        """映射列表元素"""
        key = transform.get("key", "")
        expr = transform.get("expr", "item")

        current = self._get_nested(state, key, [])
        if not isinstance(current, list):
            return state

        try:
            mapped = []
            for item in current:
                result = self._eval_item_expr(expr, item)
                mapped.append(result)
            return self._set_nested(state, key, mapped)
        except Exception:
            return state

    def _action_filter(self, state: Dict, transform: Dict) -> Dict:
        """过滤列表"""
        key = transform.get("key", "")
        expr = transform.get("expr", "True")

        current = self._get_nested(state, key, [])
        if not isinstance(current, list):
            return state

        try:
            filtered = []
            for item in current:
                evaluator = ExpressionEvaluator({"item": item})
                if evaluator.evaluate(expr):
                    filtered.append(item)
            return self._set_nested(state, key, filtered)
        except Exception:
            return state

    def _action_format(self, state: Dict, transform: Dict) -> Dict:
        """格式化字符串"""
        key = transform.get("key", "")
        template = transform.get("template", "")

        current = self._get_nested(state, key, "")

        if isinstance(current, dict):
            formatted = template.format(**current)
        elif isinstance(current, str):
            formatted = template.format(current)
        else:
            formatted = template

        return self._set_nested(state, key, formatted)

    def _eval_item_expr(self, expr: str, item: Any) -> Any:
        """评估针对单个元素的表达式"""
        if expr == "item":
            return item

        if expr.endswith("()"):
            method = expr[:-2].replace("item.", "")
            if hasattr(item, method):
                return getattr(item, method)()

        if expr.startswith("item."):
            attr = expr[5:]
            if isinstance(item, dict) and attr in item:
                return item[attr]
            if hasattr(item, attr):
                return getattr(item, attr)

        return item
