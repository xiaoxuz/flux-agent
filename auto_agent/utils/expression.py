# utils/expression.py
"""
表达式解析器

用于安全评估条件表达式。
"""

from __future__ import annotations
import re
import operator
from typing import Any, Dict, Optional, Union


class ExpressionEvaluator:
    """
    安全的表达式评估器

    支持的条件表达式语法：
    - 比较：==, !=, >, <, >=, <=
    - 逻辑：and, or, not
    - 包含：in, not in
    - 空值：is null, is not null
    - 类型：is int, is str, is list, etc.
    """

    OPERATORS = {
        "==": operator.eq,
        "!=": operator.ne,
        ">": operator.gt,
        "<": operator.lt,
        ">=": operator.ge,
        "<=": operator.le,
        "and": lambda a, b: a and b,
        "or": lambda a, b: a or b,
        "in": lambda a, b: a in b,
        "not in": lambda a, b: a not in b,
    }

    TYPE_CHECKS = {
        "int": int,
        "str": str,
        "float": float,
        "bool": bool,
        "list": list,
        "dict": dict,
        "none": type(None),
        "null": type(None),
    }

    def __init__(self, state: Dict[str, Any]):
        self.state = state

    def evaluate(self, expression: str) -> bool:
        """
        评估表达式

        Args:
            expression: 条件表达式字符串

        Returns:
            布尔值结果
        """
        expression = expression.strip()

        if not expression or expression == "default":
            return True

        try:
            return self._eval_expression(expression)
        except Exception as e:
            raise ValueError(f"表达式评估失败: {expression}, 错误: {e}")

    def _eval_expression(self, expr: str) -> bool:
        """递归评估表达式"""
        expr = expr.strip()

        if " or " in expr:
            parts = self._split_by_operator(expr, " or ")
            return any(self._eval_expression(p) for p in parts)

        if " and " in expr:
            parts = self._split_by_operator(expr, " and ")
            return all(self._eval_expression(p) for p in parts)

        if expr.startswith("not "):
            return not self._eval_expression(expr[4:])

        if expr.startswith("(") and expr.endswith(")"):
            return self._eval_expression(expr[1:-1])

        return self._eval_comparison(expr)

    def _eval_comparison(self, expr: str) -> bool:
        """评估比较表达式"""
        expr = expr.strip()

        if " is not " in expr:
            left, right = expr.split(" is not ", 1)
            left_val = self._get_value(left.strip())
            right_val = self._parse_right_value(right.strip())
            return left_val is not right_val

        if " is " in expr:
            left, right = expr.split(" is ", 1)
            left_val = self._get_value(left.strip())
            right_str = right.strip().lower()

            if right_str in ("null", "none"):
                return left_val is None

            if right_str in self.TYPE_CHECKS:
                return isinstance(left_val, self.TYPE_CHECKS[right_str])

            right_val = self._parse_right_value(right.strip())
            return left_val is right_val

        if " not in " in expr:
            left, right = expr.split(" not in ", 1)
            left_val = self._get_value(left.strip())
            right_val = self._get_value(right.strip())
            return left_val not in right_val

        if " in " in expr:
            left, right = expr.split(" in ", 1)
            left_val = self._get_value(left.strip())
            right_val = self._get_value(right.strip())
            return left_val in right_val

        for op in ["!=", "==", ">=", "<=", ">", "<"]:

            if op in expr:
                left, right = expr.split(op, 1)
                left_val = self._get_value(left.strip())
                right_val = self._get_value(right.strip())

                if op in [">", "<", ">=", "<="]:
                    left_val, right_val = self._coerce_for_comparison(left_val, right_val)
                try:
                    return self.OPERATORS[op](left_val, right_val)
                except TypeError:
                    return False

        if expr.startswith("!"):
            return not self._get_value(expr[1:].strip())

        val = self._get_value(expr)
        return bool(val)

    def _split_by_operator(self, expr: str, op: str) -> list[str]:
        """按操作符分割表达式（忽略括号内的）"""
        parts = []
        current = ""
        depth = 0

        tokens = expr.split()
        i = 0

        while i < len(tokens):
            token = tokens[i]

            if token == "(":
                depth += 1
                current += " " + token
            elif token == ")":
                depth -= 1
                current += " " + token
            elif token == op and depth == 0:
                parts.append(current.strip())
                current = ""
            else:
                current += " " + token

            i += 1

        if current.strip():
            parts.append(current.strip())

        return parts

    def _coerce_for_comparison(self, left: Any, right: Any) -> tuple[Any, Any]:
        """数值比较前的类型转换"""
        if isinstance(right, (int, float)) and isinstance(left, str):
            try:
                left = float(left) if "." in left else int(left)
            except ValueError:
                pass
        elif isinstance(left, (int, float)) and isinstance(right, str):
            try:
                right = float(right) if "." in right else int(right)
            except ValueError:
                pass
        return left, right

    def _get_value(self, expr: str) -> Any:
        """
        获取表达式的值

        支持：
        - 变量引用：data.field
        - 字面量：数字、字符串、布尔值
        - 列表/字典访问：data.items[0]
        """
        expr = expr.strip()

        if not expr:
            return None

        if expr.startswith('"') and expr.endswith('"'):
            return expr[1:-1]

        if expr.startswith("'") and expr.endswith("'"):
            return expr[1:-1]

        if expr.lower() == "true":
            return True

        if expr.lower() == "false":
            return False

        if expr.lower() in ("null", "none"):
            return None

        try:
            if "." in expr or "e" in expr.lower():
                return float(expr)
            return int(expr)
        except ValueError:
            pass

        if expr.startswith("data."):
            key_path = expr[5:]
            data = self.state.get("data", {}) if isinstance(self.state, dict) else {}
            return self._get_nested(data, key_path)

        if expr.startswith("env."):
            import os

            return os.environ.get(expr[4:], "")

        return self._get_nested(self.state, expr)

    def _parse_right_value(self, expr: str) -> Any:
        """解析右侧值"""
        expr = expr.strip().lower()

        if expr in ("null", "none"):
            return None
        if expr == "true":
            return True
        if expr == "false":
            return False

        return self._get_value(expr)

    def _get_nested(self, data: Dict, key: str) -> Any:
        """获取嵌套值"""
        if not data:
            return None

        pattern = r"[\.\[\]]+"
        keys = [k for k in re.split(pattern, key) if k]
        current = data

        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            elif isinstance(current, (list, tuple)) and k.isdigit():
                idx = int(k)
                if 0 <= idx < len(current):
                    current = current[idx]
                else:
                    return None
            else:
                return None

        return current


def evaluate_condition(
    expression: str, state: Dict[str, Any]
) -> bool:
    """
    评估条件表达式的便捷函数

    Args:
        expression: 条件表达式
        state: 工作流状态

    Returns:
        布尔值结果
    """
    evaluator = ExpressionEvaluator(state)
    a = evaluator.evaluate(expression)
    return a
