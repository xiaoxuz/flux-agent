# nodes/builtin/transform/json.py
"""
JSON 处理节点

提供 JSON 编码和解码功能。
"""

from __future__ import annotations
import json
from typing import Any, Dict
from dataclasses import dataclass

from flux_agent.nodes.base import BaseNode, NodeConfig


@dataclass
class JsonNodeConfig(NodeConfig):
    """JSON 节点配置"""

    action: str = "encode"  # encode | decode
    input_key: str = "data.input"
    output_key: str = "data.output"
    indent: int = 2  # encode 缩进
    ensure_ascii: bool = False  # encode 是否转义非 ASCII 字符
    default: Any = None  # decode 失败时的默认值
    error_on_fail: bool = True  # 是否在失败时抛出错误


class JsonNode(BaseNode):
    """
    JSON 处理节点

    支持的操作：
    - encode: 将 Python 对象编码为 JSON 字符串
    - decode: 将 JSON 字符串解码为 Python 对象

    Example:
        # 编码
        {"action": "encode", "input_key": "data.obj", "output_key": "data.json_str"}

        # 解码
        {"action": "decode", "input_key": "data.json_str", "output_key": "data.obj"}
    """

    node_type = "json"
    config_class = JsonNodeConfig

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        input_value = self._get_nested(state, self.config.input_key)

        if input_value is None:
            if self.config.error_on_fail:
                raise ValueError(f"输入值为空: {self.config.input_key}")
            return self._set_nested({}, self.config.output_key, self.config.default)

        try:
            if self.config.action == "encode":
                result = self._encode(input_value)
            elif self.config.action == "decode":
                result = self._decode(input_value)
            else:
                raise ValueError(f"未知的操作: {self.config.action}")

            return self._set_nested({}, self.config.output_key, result)

        except Exception as e:
            if self.config.error_on_fail:
                raise
            return self._set_nested({}, self.config.output_key, self.config.default)

    def _encode(self, value: Any) -> str:
        """编码为 JSON 字符串"""
        return json.dumps(
            value, indent=self.config.indent, ensure_ascii=self.config.ensure_ascii, default=str
        )

    def _decode(self, value: Any) -> Any:
        """解码 JSON 字符串"""
        if isinstance(value, bytes):
            value = value.decode("utf-8")
        if not isinstance(value, str):
            raise ValueError(f"解码需要字符串输入，得到: {type(value).__name__}")
        return json.loads(value)
