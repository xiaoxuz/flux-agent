# nodes/examples/advanced_node.py
"""
进阶节点示例

演示完整的节点开发：配置、验证、日志、错误处理。
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
import logging
import time

from flux_agent.nodes.base import BaseNode, NodeConfig


logger = logging.getLogger(__name__)


@dataclass
class AdvancedProcessNodeConfig(NodeConfig):
    """进阶处理节点配置"""

    process_mode: str = "default"  # default, strict, batch
    max_retries: int = 3
    timeout: int = 30
    output_fields: List[str] = field(default_factory=lambda: ["status", "result", "metrics"])


class AdvancedProcessNode(BaseNode):
    """
    进阶处理节点

    功能：
    - 支持多种处理模式
    - 完整的错误处理
    - 性能指标记录
    - 输入验证

    这是一个完整的节点示例，包含：
    - 配置验证
    - 输入验证
    - 错误处理
    - 日志记录
    - 性能监控

    Example:
        ```python
        from flux_agent.nodes.examples import AdvancedProcessNode

        config = {
            "process_mode": "strict",
            "max_retries": 5,
            "timeout": 60,
            "output_fields": ["status", "result", "metrics", "warnings"]
        }

        node = AdvancedProcessNode(config)
        result = node.execute({"data": {"items": [...]}})
        ```
    """

    node_type = "advanced_process"
    config_class = AdvancedProcessNodeConfig

    def validate_input(self, state: Dict[str, Any]) -> bool:
        """验证输入"""
        items = self._get_nested(state, "data.items")

        if items is None:
            logger.error("缺少必需的输入字段: data.items")
            return False

        if not isinstance(items, list):
            logger.error("data.items 必须是列表类型")
            return False

        if len(items) == 0:
            logger.warning("data.items 为空列表")

        return True

    def execute(
        self, state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行处理"""
        start_time = time.time()

        # 1. 验证输入
        if not self.validate_input(state):
            return self._build_error_result("输入验证失败")

        # 2. 获取输入数据
        items = self._get_nested(state, "data.items", [])

        # 3. 执行处理
        try:
            result = self._process_items(items)
        except Exception as e:
            logger.exception("处理失败")
            return self._build_error_result(str(e))

        # 4. 构建输出
        elapsed = time.time() - start_time

        return self._build_success_result(result, elapsed)

    def _process_items(self, items: List[Any]) -> List[Any]:
        """处理数据项"""
        if self.config.process_mode == "strict":
            return self._process_strict(items)
        elif self.config.process_mode == "batch":
            return self._process_batch(items)
        else:
            return self._process_default(items)

    def _process_default(self, items: List[Any]) -> List[Any]:
        """默认处理模式"""
        return [self._transform(item) for item in items]

    def _process_strict(self, items: List[Any]) -> List[Any]:
        """严格模式：遇到错误立即停止"""
        results = []
        for i, item in enumerate(items):
            try:
                results.append(self._transform(item))
            except Exception as e:
                raise ValueError(f"处理第 {i+1} 项时失败: {e}")
        return results

    def _process_batch(self, items: List[Any]) -> List[Any]:
        """批处理模式"""
        return [self._transform(item) for item in items]

    def _transform(self, item: Any) -> Any:
        """转换单个数据项"""
        if isinstance(item, str):
            return item.upper()
        elif isinstance(item, dict):
            return {k: v for k, v in item.items() if v is not None}
        elif isinstance(item, (int, float)):
            return item * 2
        return item

    def _build_success_result(self, result: Any, elapsed: float) -> Dict[str, Any]:
        """构建成功结果"""
        output = {
            "data": {
                "status": "success",
                "result": result,
                "metrics": {
                    "elapsed_seconds": round(elapsed, 3),
                    "items_processed": len(result) if isinstance(result, list) else 1,
                },
            }
        }

        if "warnings" in self.config.output_fields:
            output["data"]["warnings"] = []

        return output

    def _build_error_result(self, error: str) -> Dict[str, Any]:
        """构建错误结果"""
        return {"errors": [error], "data": {"status": "failed", "result": None, "metrics": {}}}
