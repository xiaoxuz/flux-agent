# nodes/builtin/control/loop.py
"""
循环迭代节点 v3 - 简洁版

职责：
  从主流程 state 中取出一个数组，逐项（或并行）执行子图，
  收集所有子图结果，写回主流程 state。

核心原则：
  1. 子图 state 与主流程 state 完全隔离（深拷贝输入，结果通过配置路径回写）
  2. 子图每次执行拿到的是一个全新的 state，只包含当前 item 和循环元信息
  3. 不做条件退出，不做 continue/break 策略 —— 就是朴素的 for-each
"""

from __future__ import annotations

import logging
import time
import concurrent.futures
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable

from flux_agent.nodes.base import BaseNode, NodeConfig

logger = logging.getLogger(__name__)


# ============================================================
# 配置
# ============================================================
@dataclass
class LoopNodeConfig(NodeConfig):
    """循环节点配置 - 只保留必要字段"""

    # ---- 输入 ----
    # 主流程 state 中要遍历的数组路径，如 "data.items"
    input_key: str = "data.items"

    # ---- 子图定义 ----
    body_nodes: List[Dict] = field(default_factory=list)
    body_edges: List[Dict] = field(default_factory=list)
    body_entry_point: str = ""

    # 子图接收当前 item 的路径（写入子图初始 state 的位置）
    # 默认 "item"，子图节点通过 state["item"] 拿到当前元素
    subgraph_item_key: str = "data.item"

    # 子图接收循环元信息的路径，设为空字符串则不注入
    subgraph_meta_key: str = "data.meta"

    # 从子图最终 state 中提取结果的路径
    # 为空则取整个子图 state
    subgraph_result_path: str = ""

    # ---- 输出 ----
    # 所有迭代结果写入主流程 state 的路径
    results_key: str = "data.results"

    # ---- 执行控制 ----
    max_iterations: int = 0          # <=0 不限制
    parallel: bool = False
    parallel_max_workers: int = 5
    delay: float = 0                 # 串行模式下每轮延迟(秒)
    on_error: str = "raise"          # raise | skip
    emit_progress: bool = True


# ============================================================
# 节点实现
# ============================================================
class LoopNode(BaseNode):
    """循环迭代节点"""

    node_type = "loop"
    config_class = LoopNodeConfig

    def __init__(self, config: Dict[str, Any], **kwargs):
        super().__init__(config, **kwargs)
        self._body_runner = None
        self._parent_tools: Dict = kwargs.get("tools", {})
        self._parent_knowledge_bases: Dict = kwargs.get("knowledge_bases", {})
        self._event_callback: Optional[Callable] = kwargs.get("event_callback")

    # ============================================================
    # 主入口
    # ============================================================
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        cfg = self.config

        # 1. 取数组
        items = self._get_nested(state, cfg.input_key, [])
        print(items)
        if not isinstance(items, list):
            items = [items]

        if not items or not cfg.body_nodes:
            return self._set_nested({}, cfg.results_key, [])

        # 2. 限制数量
        if cfg.max_iterations > 0:
            items = items[: cfg.max_iterations]

        # 3. 构建子图 runner（可复用）
        runner = self._get_body_runner()

        # 4. 执行
        if cfg.parallel:
            results = self._run_parallel(items, runner)
        else:
            results = self._run_sequential(items, runner)

        # 5. 写回主流程 state
        output: Dict[str, Any] = {}
        output = self._set_nested(output, cfg.results_key, results)
        return output

    # ============================================================
    # 串行执行
    # ============================================================
    def _run_sequential(self, items: List, runner) -> List[Any]:
        cfg = self.config
        total = len(items)
        results: List[Any] = []
        for index, item in enumerate(items):
            sub_state = self._build_subgraph_state(item, index, total)

            try:
                final_state = runner.invoke(sub_state)
                result = self._extract_result(final_state)
            except Exception as exc:
                logger.error(f"[LoopNode] 迭代 {index} 失败: {exc}")
                if cfg.on_error == "raise":
                    raise
                result = {"_error": str(exc), "_index": index}

            results.append(result)
            self._emit_progress(index, total, result)

            if cfg.delay > 0 and index < total - 1:
                time.sleep(cfg.delay)

        return results

    # ============================================================
    # 并行执行
    # ============================================================
    def _run_parallel(self, items: List, runner) -> List[Any]:
        cfg = self.config
        total = len(items)
        results: List[Any] = [None] * total

        def _invoke_one(index: int, item: Any):
            sub_state = self._build_subgraph_state(item, index, total)
            final_state = runner.invoke(sub_state)
            return index, self._extract_result(final_state)

        max_workers = min(cfg.parallel_max_workers, total)

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
            future_map = {
                pool.submit(_invoke_one, i, item): i
                for i, item in enumerate(items)
            }

            for future in concurrent.futures.as_completed(future_map):
                idx = future_map[future]
                try:
                    _, result = future.result()
                except Exception as exc:
                    logger.error(f"[LoopNode] 并行迭代 {idx} 失败: {exc}")
                    if cfg.on_error == "raise":
                        # 取消剩余
                        for f in future_map:
                            f.cancel()
                        raise
                    result = {"_error": str(exc), "_index": idx}

                results[idx] = result
                self._emit_progress(idx, total, result)

        return results

    # ============================================================
    # 子图 state 构建（完全隔离）
    # ============================================================
    def _build_subgraph_state(
        self, item: Any, index: int, total: int
    ) -> Dict[str, Any]:
        """
        为子图创建一个干净的 state，与主流程无共享引用。
        """
        cfg = self.config
        sub_state: Dict[str, Any] = {
            "data":{},
        }

        # 写入当前 item（深拷贝确保隔离）
        sub_state = self._set_nested(sub_state, cfg.subgraph_item_key, deepcopy(item))

        # 写入循环元信息
        if cfg.subgraph_meta_key:
            meta = {
                "index": index,
                "total": total,
                "is_first": index == 0,
                "is_last": index == total - 1,
            }
            sub_state = self._set_nested(sub_state, cfg.subgraph_meta_key, meta)

        return sub_state

    # ============================================================
    # 结果提取
    # ============================================================
    def _extract_result(self, final_state: Dict[str, Any]) -> Any:
        """从子图最终 state 提取结果"""
        if not final_state:
            return None

        if self.config.subgraph_result_path:
            return self._get_nested(final_state, self.config.subgraph_result_path)

        # 默认返回整个 state，但去掉循环元信息避免冗余
        result = dict(final_state)
        if self.config.subgraph_meta_key and self.config.subgraph_meta_key in result:
            result.pop(self.config.subgraph_meta_key, None)
        return result

    # ============================================================
    # 子图 Runner 构建 / 缓存
    # ============================================================
    def _get_body_runner(self):
        if self._body_runner is not None:
            return self._body_runner

        from flux_agent.core.executor import WorkflowRunner

        cfg = self.config
        body_config = {
            "nodes": cfg.body_nodes,
            "edges": cfg.body_edges,
            "entry_point": cfg.body_entry_point,
            "workflow": {},
            "tools": [],
        }

        self._body_runner = WorkflowRunner(
            config_dict=body_config,
            tools=self._collect_body_tools(),
            knowledge_bases=self._parent_knowledge_bases,
        )
        return self._body_runner

    def _collect_body_tools(self) -> Dict:
        """从子图节点配置里收集需要的 tools"""
        needed: Dict = {}
        for node_cfg in self.config.body_nodes:
            inner = node_cfg.get("config", {})
            # 单个 tool
            name = inner.get("tool_name")
            if name and name in self._parent_tools:
                needed[name] = self._parent_tools[name]
            # 多个 tools
            for n in inner.get("tools", []):
                if n in self._parent_tools:
                    needed[n] = self._parent_tools[n]
        return needed

    def reset(self):
        """重置缓存的子图 runner"""
        self._body_runner = None

    # ============================================================
    # 进度通知
    # ============================================================
    def _emit_progress(self, current: int, total: int, result: Any):
        if not self.config.emit_progress:
            return

        progress = (current + 1) / total if total > 0 else 1.0
        logger.info(
            f"[LoopNode] 迭代进度: {current + 1}/{total} ({progress:.0%})"
        )

        if self._event_callback:
            try:
                self._event_callback(
                    {
                        "type": "loop_progress",
                        "node_id": self.config.id if hasattr(self.config, "id") else "",
                        "current": current + 1,
                        "total": total,
                        "progress": round(progress, 4),
                    }
                )
            except Exception as exc:
                logger.warning(f"[LoopNode] 事件回调失败: {exc}")