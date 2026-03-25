# nodes/base/node.py
"""
节点基类

定义所有节点的统一接口和通用功能。
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
import re
import os
import time
import logging
from datetime import datetime

from .config import NodeConfig, RetryPolicy, CachePolicy

logger = logging.getLogger(__name__)


class BaseNode(ABC):
    """
    节点基类

    所有内置节点和用户自定义节点都必须继承此类。

    子类需要实现：
    - node_type: 节点类型标识（类属性）
    - config_class: 配置类（类属性，可选）
    - execute: 执行方法

    Example:
        ```python
        from flux_agent.nodes.base import BaseNode, NodeConfig
        from dataclasses import dataclass

        @dataclass
        class MyConfig(NodeConfig):
            my_param: str = ""

        class MyNode(BaseNode):
            node_type = "my_node"
            config_class = MyConfig

            def execute(self, state):
                # 实现逻辑
                return {"data": {"result": "..."}}
        ```
    """

    node_type: str = "base"
    config_class: type = NodeConfig

    def __init__(self, config: Dict[str, Any], **kwargs):
        self.raw_config = config
        self.config = self._parse_config(config)
        self.tools = kwargs.get("tools", {})
        self.retry_policy = self._parse_retry_policy(kwargs.get("retry_policy"))
        self.cache_policy = self._parse_cache_policy(kwargs.get("cache_policy"))
        self._on_node_input = None
        self._on_node_output = None
        self._cache = {}
        self._thread_id = None

    def set_thread_id(self, thread_id: str):
        """设置 thread_id，用于缓存隔离"""
        self._thread_id = thread_id

    def _get_cache_key(self, state: Dict) -> str:
        """生成缓存键"""
        if not self.cache_policy or not self.cache_policy.key_template:
            import json

            state_str = json.dumps(state, sort_keys=True, default=str)
            return str(hash(state_str))

        key = self._interpolate(self.cache_policy.key_template, state)
        return f"{self._thread_id}:{key}" if self._thread_id else key

    def _get_cached_result(self, state: Dict) -> Optional[Any]:
        """获取缓存结果"""
        if not self.cache_policy or not self.cache_policy.enabled:
            return None

        cache_key = self._get_cache_key(state)
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if time.time() - cached["timestamp"] < self.cache_policy.ttl:
                logger.info(f"命中缓存: [{getattr(self, '_node_id', self.node_type)}]")
                return cached["result"]
            else:
                del self._cache[cache_key]
        return None

    def _set_cached_result(self, state: Dict, result: Any):
        """设置缓存结果"""
        if not self.cache_policy or not self.cache_policy.enabled:
            return

        cache_key = self._get_cache_key(state)
        self._cache[cache_key] = {"result": result, "timestamp": time.time()}

    def set_hooks(self, on_node_input: callable = None, on_node_output: callable = None):
        """设置节点钩子"""
        self._on_node_input = on_node_input
        self._on_node_output = on_node_output

    def _parse_config(self, config: Dict[str, Any]) -> NodeConfig:
        """解析配置"""
        if hasattr(self.config_class, "__dataclass_fields__"):
            valid_fields = {}
            for key, value in config.items():
                if key in self.config_class.__dataclass_fields__:
                    valid_fields[key] = value
            return self.config_class(**valid_fields)
        return self.config_class(**config)

    def _parse_retry_policy(self, config: Optional[Dict]) -> Optional[RetryPolicy]:
        """解析重试策略"""
        if not config:
            return None
        return RetryPolicy(
            max_attempts=config.get("max_attempts", 3),
            initial_interval=config.get("initial_interval", 1.0),
            max_interval=config.get("max_interval", 10.0),
            backoff_multiplier=config.get("backoff_multiplier", 2.0),
            retry_on=config.get("retry_on", []),
        )

    def _parse_cache_policy(self, config: Optional[Dict]) -> Optional[CachePolicy]:
        """解析缓存策略"""
        if not config:
            return None
        return CachePolicy(
            enabled=config.get("enabled", True),
            ttl=config.get("ttl", 300),
            key_template=config.get("key_template", ""),
            scope=config.get("scope", "thread"),
        )

    @abstractmethod
    def execute(self, state: Dict[str, Any]) -> Union[Dict[str, Any], Any]:
        """
        执行节点逻辑

        Args:
            state: 当前工作流状态

        Returns:
            状态更新字典或 Command 对象
        """
        pass

    def validate_input(self, state: Dict[str, Any]) -> bool:
        """
        验证输入

        Args:
            state: 工作流状态

        Returns:
            是否验证通过
        """
        if not self.config.input_keys:
            return True

        for key in self.config.input_keys:
            if not self._has_nested_key(state, key):
                return False
        return True

    def __call__(
        self, state: Dict[str, Any]
    ) -> Union[Dict[str, Any], Any]:
        """使节点可作为函数调用"""
        node_id = getattr(self, "_node_id", self.node_type)
        start_time = time.time()

        logger.info(f"▶ 进入节点: [{node_id}] type={self.node_type}")
        logger.debug(f"  输入状态: data={state.get('data', {})}")

        if self._on_node_input:
            self._on_node_input(node_id, state)

        if not self.validate_input(state):
            missing = [k for k in self.config.input_keys if not self._has_nested_key(state, k)]
            raise ValueError(f"缺少必需的输入字段: {missing}")

        cached_result = self._get_cached_result(state)
        if cached_result is not None:
            if self._on_node_output:
                self._on_node_output(node_id, state, cached_result)
            return cached_result

        on_error = getattr(self.config, "on_error", "stop")
        max_attempts = self.retry_policy.max_attempts if self.retry_policy else 1

        for attempt in range(1, max_attempts + 1):
            try:
                result = self.execute(state)

                self._set_cached_result(state, result)

                elapsed = time.time() - start_time
                logger.info(f"◀ 离开节点: [{node_id}] 耗时={elapsed:.3f}s")
                if logger.isEnabledFor(logging.DEBUG):
                    result_preview = str(result)[:200] if result else "{}"
                    logger.debug(f"  输出状态: {result_preview}")

                if self._on_node_output:
                    self._on_node_output(node_id, state, result)

                return result

            except Exception as e:
                exc_type_name = type(e).__name__
                if exc_type_name == "GraphInterrupt":
                    elapsed = time.time() - start_time
                    logger.info(f"⏸ 节点等待输入: [{node_id}] 耗时={elapsed:.3f}s")
                    raise

                should_retry = False
                if self.retry_policy and attempt < max_attempts:
                    if (
                        not self.retry_policy.retry_on
                        or exc_type_name in self.retry_policy.retry_on
                    ):
                        should_retry = True

                if should_retry:
                    wait_time = min(
                        self.retry_policy.initial_interval
                        * (self.retry_policy.backoff_multiplier ** (attempt - 1)),
                        self.retry_policy.max_interval,
                    )
                    logger.warning(
                        f"🔄 重试节点: [{node_id}] 第 {attempt}/{max_attempts} 次，{wait_time:.1f}s 后重试"
                    )
                    time.sleep(wait_time)
                    continue

                elapsed = time.time() - start_time

                logger.error(f"✗ 节点失败: [{node_id}] 耗时={elapsed:.3f}s 错误={e}")

                error_entry = {
                    "node_id": node_id,
                    "error": str(e),
                    "error_type": exc_type_name,
                    "timestamp": datetime.now().isoformat(),
                }
                if "errors" not in state:
                    state["errors"] = []
                state["errors"].append(error_entry)

                if self._on_node_output:
                    self._on_node_output(node_id, state, {"error": error_entry})

                if on_error == "continue":
                    logger.warning(f"⚠ 节点错误继续: [{node_id}]")
                    return {}
                else:
                    raise

    # ============================================================
    # 嵌套数据操作工具方法
    # ============================================================

    def _get_nested(self, data: Dict, key: str, default: Any = None) -> Any:
        """
        获取嵌套字典的值

        支持点号分隔的键路径，如 "data.user.name"
        支持列表索引，如 "data.items[0]"

        Args:
            data: 数据字典
            key: 键路径
            default: 默认值

        Returns:
            找到的值或默认值
        """
        keys = self._parse_key_path(key)
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

    def _set_nested(self, data: Dict, key: str, value: Any) -> Dict:
        """
        设置嵌套字典的值

        Args:
            data: 数据字典
            key: 键路径
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

    def _has_nested_key(self, data: Dict, key: str) -> bool:
        """检查嵌套键是否存在"""
        return self._get_nested(data, key) is not None

    def _delete_nested(self, data: Dict, key: str) -> Dict:
        """删除嵌套键"""
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

    def _parse_key_path(self, key: str) -> List[str]:
        """
        解析键路径

        "data.items[0].name" -> ["data", "items", "0", "name"]
        """
        pattern = r"[\.\[\]]+"
        parts = re.split(pattern, key)
        return [p for p in parts if p]

    # ============================================================
    # 变量插值
    # ============================================================

    def _interpolate(self, template: str, state: Dict) -> str:
        """
        变量插值

        支持：
        - ${data.field} - 状态字段
        - ${context.field} - 上下文字段
        - ${env.VAR} - 环境变量
        - ${env.NOW} - 当前时间
        - ${env.UUID} - 生成 UUID

        Args:
            template: 模板字符串
            state: 工作流状态
            context: 运行时上下文

        Returns:
            插值后的字符串
        """
        if not template or "${" not in template:
            return template

        pattern = r"\$\{([^}]+)\}"

        def replace(match):
            key = match.group(1).strip()

            if key.startswith("env."):
                var_name = key[4:]
                if var_name == "NOW":
                    return datetime.now().isoformat()
                elif var_name == "UUID":
                    import uuid

                    return str(uuid.uuid4())
                elif var_name == "RANDOM":
                    import random

                    return str(random.random())
                return os.environ.get(var_name, "")
            if key.startswith("data."):
                value = self._get_nested(state, key)
                return str(value) if value is not None else ""
            if key.startswith("context."):
                value = self._get_nested(state, key)
                return str(value) if value is not None else ""

            if key.startswith("config."):
                config_key = key[7:]
                return str(getattr(self.config, config_key, ""))

            value = self._get_nested(state, key)
            return str(value) if value is not None else ""

        return re.sub(pattern, replace, template)

    def _interpolate_dict(self, template: Dict, state: Dict) -> Dict:
        """递归插值字典"""
        result = {}
        for key, value in template.items():
            if isinstance(value, str):
                result[key] = self._interpolate(value, state)
            elif isinstance(value, dict):
                result[key] = self._interpolate_dict(value, state)
            elif isinstance(value, list):
                result[key] = [
                    self._interpolate(v, state) if isinstance(v, str) else v for v in value
                ]
            else:
                result[key] = value
        return result

    def _interpolate_value(self, value: Any, state: Dict) -> Any:
        """插值任意值"""
        if isinstance(value, str):
            return self._interpolate(value, state)
        elif isinstance(value, dict):
            return self._interpolate_dict(value, state)
        elif isinstance(value, list):
            return [self._interpolate_value(v, state) for v in value]
        return value

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} type={self.node_type}>"
