# nodes/examples/simple_node.py
"""
简单数据节点示例

演示最基本的自定义节点开发。
"""

from __future__ import annotations
from typing import Any, Dict, Optional
from dataclasses import dataclass

from auto_agent.nodes.base import BaseNode, NodeConfig


@dataclass
class SimpleDataNodeConfig(NodeConfig):
    """简单数据节点配置"""

    prefix: str = ""
    suffix: str = ""
    output_key: str = "data.result"


class SimpleDataNode(BaseNode):
    """
    简单数据节点

    功能：
    - 读取输入数据
    - 添加前缀和后缀
    - 输出处理结果

    这是一个最简单的节点示例，适合入门学习。

    Example:
        ```python
        from auto_agent.nodes.examples import SimpleDataNode

        config = {
            "prefix": "Hello, ",
            "suffix": "!",
            "output_key": "data.greeting"
        }

        node = SimpleDataNode(config)
        result = node.execute({"data": {"input": "World"}})
        # result = {"data": {"greeting": "Hello, World!"}}
        ```
    """

    node_type = "simple_data"
    config_class = SimpleDataNodeConfig

    def execute(
        self, state: Dict[str, Any]
    ) -> Dict[str, Any]:
        # 1. 从状态读取输入
        input_value = self._get_nested(state, "data.input", "")

        # 2. 执行处理逻辑
        result = f"{self.config.prefix}{input_value}{self.config.suffix}"

        # 3. 返回状态更新
        return self._set_nested({}, self.config.output_key, result)
