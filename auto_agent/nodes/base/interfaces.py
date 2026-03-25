# nodes/base/interfaces.py
"""
节点接口定义

定义节点的标准接口和类型注解。
"""

from __future__ import annotations
from typing import Any, Dict, List, Literal, Optional, Union
from typing_extensions import Protocol, runtime_checkable


@runtime_checkable
class INode(Protocol):
    """
    节点接口协议

    所有节点必须实现此接口。
    用于类型检查和接口验证。
    """

    node_type: str

    def execute(
        self, state: Dict[str, Any]
    ) -> Union[Dict[str, Any], str, List]:
        """执行节点逻辑"""
        ...


@runtime_checkable
class IConfigurable(Protocol):
    """可配置接口"""

    def _parse_config(self, config: Dict[str, Any]) -> Any:
        """解析配置"""
        ...


@runtime_checkable
class IValidatable(Protocol):
    """可验证接口"""

    def validate_input(self, state: Dict[str, Any]) -> bool:
        """验证输入"""
        ...


# 节点执行结果类型
NodeResult = Union[Dict[str, Any], str, List[Any]]

# 条件分支结果类型
ConditionResult = Literal["__continue__", "__break__"]

# 路由结果类型
RouteResult = str
