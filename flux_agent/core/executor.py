# core/executor.py
"""
工作流执行引擎

封装 LangGraph 的 invoke/stream/resume 等方法。
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Union
import json
import logging
from pathlib import Path

from .parser import WorkflowParser, parse_workflow, load_workflow_from_file
from .state import set_nested_value, get_nested_value
from flux_agent.mcp import MCPClientManager, mcp_server_from_config

logger = logging.getLogger(__name__)


class WorkflowRunner:
    """工作流执行引擎"""

    def __init__(
        self,
        config_path: str = None,
        config_dict: Dict[str, Any] = None,
        custom_nodes: Dict[str, type] = None,
        tools: Dict[str, Any] = None,
        knowledge_bases: Dict[str, Any] = None,
        mcp_servers: List[Dict[str, Any]] = None,
        on_node_input: callable = None,
        on_node_output: callable = None,
    ):
        if config_path:
            self.config = self._load_config_from_file(config_path)
        elif config_dict:
            self.config = config_dict
        else:
            raise ValueError("必须提供 config_path 或 config_dict")

        self.custom_nodes = custom_nodes or {}
        self.tools = tools or {}
        self.checkpointer_type = "memory"
        self.on_node_input = on_node_input
        self.on_node_output = on_node_output

        # MCP 支持：优先使用传入参数，其次从 config_dict 提取
        mcp_configs = mcp_servers or mcp_server_from_config(self.config or {})
        self.mcp_manager = MCPClientManager(mcp_configs) if mcp_configs else None

        self.parser = WorkflowParser(
            self.config, custom_nodes, self.tools, mcp_manager=self.mcp_manager
        )
        self._parsed = None
        self._graph = None
        self._checkpointer = None

        if knowledge_bases:
            self._load_knowledge_bases(knowledge_bases)

    def _load_knowledge_bases(self, knowledge_bases: Dict[str, Any]):
        """加载知识库到全局存储"""
        from flux_agent.rag import KnowledgeBase, add_knowledge_base

        for name, kb_config in knowledge_bases.items():
            try:
                add_knowledge_base(name, KnowledgeBase.load(name=name, config=kb_config))
                logger.info(f"已加载知识库: {name}")
            except Exception as e:
                logger.warning(f"加载知识库失败: {name}, 错误: {e}")

    def _load_config_from_file(self, path: str) -> Dict[str, Any]:
        config_path = Path(path)
        if not config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {path}")
        return json.loads(config_path.read_text(encoding="utf-8"))

    def _init_checkpointer(self):
        if self._checkpointer:
            return self._checkpointer

        try:
            from langgraph.checkpoint.memory import MemorySaver

            self._checkpointer = MemorySaver()
        except ImportError:
            logger.warning("langgraph 未安装，checkpointer 不可用")

        return self._checkpointer

    def _set_thread_id_to_nodes(self, thread_id: str):
        """设置节点 thread_id 用于缓存隔离"""
        nodes_instances = self._parsed.get("nodes_instances", {})
        for node_instance in nodes_instances.values():
            if hasattr(node_instance, "set_thread_id"):
                node_instance.set_thread_id(thread_id)

    def _build_graph(self):
        if self._graph:
            return self._graph

        self._parsed = self.parser.parse()

        try:
            from langgraph.graph import StateGraph, START, END
        except ImportError:
            raise ImportError("请安装 langgraph: pip install langgraph")

        builder = StateGraph(self._parsed["state_schema"])

        self._add_nodes(builder)
        self._add_edges(builder)

        if self._parsed["entry_point"]:
            builder.add_edge(START, self._parsed["entry_point"])

        checkpointer = self._init_checkpointer()
        self._graph = builder.compile(checkpointer=checkpointer)

        return self._graph

    def _add_nodes(self, builder):
        """添加所有节点"""
        for node_id, node_func in self._parsed["nodes"].items():
            node_instance = self._parsed["nodes_instances"].get(node_id)
            if node_instance and hasattr(node_instance, "set_hooks"):
                node_instance.set_hooks(self.on_node_input, self.on_node_output)
            builder.add_node(node_id, node_func)

    def _add_edges(self, builder):
        """添加所有边"""
        from langgraph.graph import START, END

        for edge in self._parsed["edges"]:
            if edge["type"] == "conditional":
                self._add_conditional_edge(builder, edge)
            else:
                self._add_normal_edge(builder, edge)

    def _add_normal_edge(self, builder, edge):
        """添加普通边"""
        from langgraph.graph import START, END

        from_node = edge["from"]
        to_node = edge["to"]

        if from_node == "START":
            builder.add_edge(START, to_node)
        elif to_node == "END":
            builder.add_edge(from_node, END)
        else:
            builder.add_edge(from_node, to_node)

    def _add_conditional_edge(self, builder, edge):
        """添加条件边"""
        from langgraph.graph import END

        from_node = edge["from"]
        condition_map = edge.get("condition_map", {})
        branches = self._parsed.get("condition_branches", {}).get(from_node, {})

        has_end = self._has_end_target(condition_map, branches)
        router = self._create_router(condition_map, branches)

        if has_end:
            builder.add_conditional_edges(from_node, router)
        else:
            builder.add_conditional_edges(from_node, router, condition_map)

    def _has_end_target(self, condition_map: dict, branches: dict) -> bool:
        """检测是否有 END 目标"""
        return any(v == "END" for v in condition_map.values()) or any(
            v == "END" for v in branches.values()
        )

    def _create_router(self, condition_map: dict, branches: dict):
        """创建路由函数"""
        from langgraph.graph import END
        from flux_agent.utils.expression import evaluate_condition

        def router(state):
            route_value = state.get("_route") if isinstance(state, dict) else None

            if route_value and route_value in condition_map:
                target = condition_map[route_value]
                return END if target == "END" else target

            for condition, target in branches.items():
                if condition == "default":
                    continue
                try:
                    if evaluate_condition(condition, state):
                        return END if target == "END" else target
                except Exception:
                    continue

            default_target = branches.get("default") or condition_map.get("default")
            if default_target:
                return END if default_target == "END" else default_target

            return END

        return router

    def compile(self):
        return self._build_graph()

    def invoke(
        self,
        input_data: Dict[str, Any],
        thread_id: str = None,
        interrupt_before: List[str] = None,
        interrupt_after: List[str] = None,
    ) -> Dict[str, Any]:
        graph = self._build_graph()

        effective_thread_id = thread_id or "default"

        self._set_thread_id_to_nodes(effective_thread_id)

        config = {"configurable": {"thread_id": effective_thread_id}, "recursion_limit": 100}

        if interrupt_before:
            config["interrupt_before"] = interrupt_before
        if interrupt_after:
            config["interrupt_after"] = interrupt_after

        state = {"data": input_data.get("data", {}), "messages": input_data.get("messages", [])}
        state.update(input_data)
        state.setdefault("_token_usage", {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "details": []})

        try:
            result = graph.invoke(state, config=config)
            return result
        except Exception as e:
            logger.error(f"工作流执行失败: {e}")
            raise

    def stream(
        self,
        input_data: Dict[str, Any],
        thread_id: str = None,
        stream_mode: List[str] = None,
        subgraphs: bool = False,
    ):
        graph = self._build_graph()

        config = {"configurable": {"thread_id": thread_id or "default"}}

        state = {"data": input_data.get("data", {}), "messages": input_data.get("messages", [])}
        state.update(input_data)
        state.setdefault("_token_usage", {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "details": []})

        for chunk in graph.stream(
            state, config=config, stream_mode=stream_mode or ["updates"], subgraphs=subgraphs
        ):
            yield chunk

    def resume(self, thread_id: str, resume_value: Any) -> Dict[str, Any]:
        try:
            from langgraph.types import Command
        except ImportError:
            raise ImportError("请安装 langgraph: pip install langgraph")

        graph = self._build_graph()
        config = {"configurable": {"thread_id": thread_id}}

        return graph.invoke(Command(resume=resume_value), config=config)

    def get_state(self, thread_id: str, subgraphs: bool = False) -> Dict[str, Any]:
        graph = self._build_graph()
        config = {"configurable": {"thread_id": thread_id}}

        return graph.get_state(config, subgraphs=subgraphs)

    def get_state_history(self, thread_id: str):
        graph = self._build_graph()
        config = {"configurable": {"thread_id": thread_id}}

        return graph.get_state_history(config)

    def update_state(self, thread_id: str, values: Dict[str, Any]) -> None:
        graph = self._build_graph()
        config = {"configurable": {"thread_id": thread_id}}

        graph.update_state(config, values)

    def get_graph(self):
        return self._build_graph()

    async def ainvoke(self, input_data: Dict[str, Any], thread_id: str = None) -> Dict[str, Any]:
        graph = self._build_graph()

        config = {"configurable": {"thread_id": thread_id or "default"}}

        state = {"data": input_data.get("data", {}), "messages": input_data.get("messages", [])}
        state.update(input_data)
        state.setdefault("_token_usage", {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "details": []})

        return await graph.ainvoke(state, config=config)

    async def astream(
        self, input_data: Dict[str, Any], thread_id: str = None, stream_mode: List[str] = None
    ):
        graph = self._build_graph()

        config = {"configurable": {"thread_id": thread_id or "default"}}

        state = {"data": input_data.get("data", {}), "messages": input_data.get("messages", [])}
        state.update(input_data)
        state.setdefault("_token_usage", {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "details": []})

        async for chunk in graph.astream(
            state, config=config, stream_mode=stream_mode or ["updates"]
        ):
            yield chunk
