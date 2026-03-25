# core/parser.py
"""
工作流配置解析器

将 JSON 配置解析为 LangGraph StateGraph。
"""

from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional, Type
import json
import logging
from pathlib import Path

from .state import BaseWorkflowState, REDUCERS
from .registry import NodeRegistry, load_node_class
from ..nodes import BUILTIN_NODES

logger = logging.getLogger(__name__)


class WorkflowParser:
    """工作流配置解析器"""

    def __init__(
        self,
        config: Dict[str, Any],
        custom_nodes: Dict[str, Type] = None,
        tools: Dict[str, Any] = None,
    ):
        self.config = config
        self.custom_nodes = custom_nodes or {}
        self.external_tools = tools or {}
        self.registry = NodeRegistry()

        self._register_builtin_nodes()
        self._register_custom_nodes()

        self.workflow_config = config.get("workflow", {})
        self.nodes_config = config.get("nodes", [])
        self.edges_config = config.get("edges", [])
        self.tools_config = config.get("tools", [])
        self.entry_point = config.get("entry_point")

        self._parsed_nodes: Dict[str, Callable] = {}
        self._tools: Dict[str, Any] = {}
        self._condition_branches: Dict[str, Dict[str, str]] = {}

    def _register_builtin_nodes(self):
        for node_type, node_class in BUILTIN_NODES.items():
            self.registry.register(node_type, node_class)

    def _register_custom_nodes(self):
        for node_type, node_class in self.custom_nodes.items():
            self.registry.register(node_type, node_class)

    def parse(self) -> Dict[str, Any]:
        state_schema = self._build_state_schema()

        self._parse_tools()

        nodes = self._parse_nodes()
        edges = self._parse_edges()

        return {
            "workflow": self.workflow_config,
            "state_schema": state_schema,
            "nodes": nodes,
            "nodes_instances": self._parsed_nodes,
            "edges": edges,
            "tools": self._tools,
            "entry_point": self.entry_point,
            "condition_branches": self._condition_branches,
        }

    def _build_state_schema(self) -> type:
        return BaseWorkflowState

    def _parse_tools(self):
        for tool_def in self.tools_config:
            name = tool_def.get("name")
            if not name:
                continue

            impl = tool_def.get("implementation")

            if isinstance(impl, str):
                try:
                    impl_func = load_node_class(impl)
                    self._tools[name] = impl_func
                except Exception as e:
                    logger.warning(f"加载工具 {name} 失败: {e}")
            elif callable(impl):
                self._tools[name] = impl
            elif isinstance(impl, dict):
                self._tools[name] = impl

        self._tools.update(self.external_tools)

    def _parse_nodes(self) -> Dict[str, Callable]:
        nodes = {}

        for node_config in self.nodes_config:
            node_id = node_config.get("id")
            node_type = node_config.get("type")
            config = node_config.get("config", {})

            if not node_id or not node_type:
                logger.warning(f"节点配置不完整: {node_config}")
                continue

            node_class = self.registry.get(node_type)
            if not node_class:
                logger.error(f"未知节点类型: {node_type}")
                raise ValueError(f"未知节点类型: {node_type}")

            node_instance = node_class(
                config,
                tools=self._tools,
                retry_policy=node_config.get("retry_policy"),
                cache_policy=node_config.get("cache_policy"),
            )
            node_instance._node_id = node_id

            self._parsed_nodes[node_id] = node_instance

            nodes[node_id] = self._create_node_function(node_id, node_instance)

            if node_type in ("condition", "ConditionNode"):
                branches = config.get("branches", [])
                self._condition_branches[node_id] = {
                    b.get("condition", "default"): b.get("target") for b in branches
                }

        return nodes

    def _create_node_function(self, node_id: str, node_instance) -> Callable:
        def node_function(state: Dict):
            result = node_instance(state)

            if isinstance(result, dict):
                if "_next_node" in result:
                    pass

            return result

        node_function.__name__ = node_id
        return node_function

    def _parse_edges(self) -> List[Dict[str, Any]]:
        edges = []

        for edge_config in self.edges_config:
            from_node = edge_config.get("from")
            to_node = edge_config.get("to")
            condition_map = edge_config.get("condition_map")

            if condition_map:
                edges.append(
                    {"type": "conditional", "from": from_node, "condition_map": condition_map}
                )
            else:
                edges.append({"type": "normal", "from": from_node, "to": to_node})

        return edges


def parse_workflow(config: Dict[str, Any], custom_nodes: Dict = None) -> Dict[str, Any]:
    parser = WorkflowParser(config, custom_nodes)
    return parser.parse()


def load_workflow_from_file(path: str, custom_nodes: Dict = None) -> Dict[str, Any]:
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {path}")

    config = json.loads(config_path.read_text(encoding="utf-8"))
    return parse_workflow(config, custom_nodes)
