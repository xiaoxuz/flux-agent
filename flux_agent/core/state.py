# core/state.py
"""
工作流状态模型

基于 LangGraph 的状态管理。
状态字段：messages, data, errors, metadata
"""

from __future__ import annotations
from typing import Annotated, Any, Callable, Dict, List, Optional, Union
from typing_extensions import TypedDict
from operator import add

try:
    from langgraph.graph.message import add_messages
except ImportError:

    def add_messages(left: List, right: List) -> List:
        if not right:
            return left
        if not left:
            return right
        return left + right


def merge_dicts(left: Dict, right: Dict) -> Dict:
    """合并两个字典（深度合并）"""
    result = left.copy()
    for key, value in right.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
    return result


def sum_values(left: Union[int, float], right: Union[int, float]) -> Union[int, float]:
    """数值累加"""
    return left + right


def merge_token_usage(left: Dict, right: Dict) -> Dict:
    """Token 用量合并：汇总累加 + 明细追加"""
    result = {
        "input_tokens": left.get("input_tokens", 0) + right.get("input_tokens", 0),
        "output_tokens": left.get("output_tokens", 0) + right.get("output_tokens", 0),
        "total_tokens": left.get("total_tokens", 0) + right.get("total_tokens", 0),
        "details": left.get("details", []) + right.get("details", []),
    }
    return result


REDUCERS: Dict[str, Optional[Callable]] = {
    "append": add,
    "add_messages": add_messages,
    "merge": merge_dicts,
    "sum": sum_values,
    "merge_token_usage": merge_token_usage,
    "override": None,
}


class BaseWorkflowState(TypedDict):
    """基础工作流状态"""

    messages: Annotated[List[Any], add_messages]
    data: Annotated[Dict[str, Any], merge_dicts]
    errors: Annotated[List[dict], add]
    metadata: Dict[str, Any]
    context: Annotated[Dict[str, Any], merge_dicts]
    _token_usage: Annotated[Dict[str, Any], merge_token_usage]


def get_nested_value(data: Dict, key: str, default: Any = None) -> Any:
    """获取嵌套字典的值

    Args:
        data: 数据字典
        key: 键路径，用点号分隔，如 "data.user.name"
        default: 默认值

    Returns:
        找到的值或默认值
    """
    keys = key.split(".")
    current = data

    for k in keys:
        if isinstance(current, dict) and k in current:
            current = current[k]
        elif isinstance(current, (list, tuple)) and k.isdigit():
            idx = int(k)
            if 0 <= idx < len(current):
                current = current[idx]
            else:
                return default
        else:
            return default

    return current


def set_nested_value(data: Dict, key: str, value: Any) -> Dict:
    """设置嵌套字典的值

    Args:
        data: 数据字典
        key: 键路径，用点号分隔
        value: 要设置的值

    Returns:
        更新后的字典
    """
    keys = key.split(".")
    result = data.copy() if data else {}
    current = result

    for k in keys[:-1]:
        if k not in current:
            current[k] = {}
        elif not isinstance(current[k], dict):
            current[k] = {}
        current = current[k]

    current[keys[-1]] = value
    return result


def delete_nested_value(data: Dict, key: str) -> Dict:
    """删除嵌套键

    Args:
        data: 数据字典
        key: 键路径

    Returns:
        更新后的字典
    """
    keys = key.split(".")
    if not keys:
        return data

    result = data.copy() if data else {}
    current = result

    for k in keys[:-1]:
        if k not in current:
            return result
        current = current[k]

    if keys[-1] in current:
        del current[keys[-1]]

    return result
