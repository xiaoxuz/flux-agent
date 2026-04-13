# flux_agent/mcp/client.py
"""
MCP Client Manager

封装 langchain-mcp-adapters 的 MultiServerMCPClient，
为 Workflow 和 Agent 模式提供统一的 MCP 工具接入。
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# 支持的传输方式
MCP_TRANSPORT_TYPES = ("stdio", "http", "streamable_http")


class MCPClientManager:
    """
    MCP Server 管理器

    管理多个 MCP Server 连接，提供统一的 get_tools() 接口。
    内部使用 langchain_mcp_adapters.client.MultiServerMCPClient。
    """

    def __init__(self, server_configs: Optional[List[Dict[str, Any]]] = None):
        """
        Args:
            server_configs: MCP Server 配置列表，每项包含:
                - name (str): 服务名称
                - transport (str): "stdio" | "http" | "streamable_http"
                - command (str): stdio 模式的命令（可选）
                - args (list): stdio 模式的参数（可选）
                - env (dict): stdio 模式的环境变量（可选）
                - url (str): http/streamable_http 模式的 URL（可选）
                - headers (dict): http/streamable_http 模式的请求头（可选）
                - tool_name_prefix (str|bool): 工具名前缀，True 表示使用服务名
        """
        self._server_configs = server_configs or []
        self._client = None
        self._tools: Optional[List] = None
        self._initialized = False
        self._init_error: Optional[str] = None

    def _build_connections(self) -> Dict[str, Any]:
        """将 server_configs 转换为 MultiServerMCPClient 所需的 connections 格式"""
        connections = {}
        for cfg in self._server_configs:
            name = cfg.get("name", f"server_{len(connections)}")
            transport = cfg.get("transport", "stdio")
            conn: Dict[str, Any] = {"transport": transport}

            if transport == "stdio":
                conn["command"] = cfg.get("command", "python")
                conn["args"] = cfg.get("args", [])
                if "env" in cfg:
                    conn["env"] = cfg["env"]
            elif transport in ("http", "streamable_http"):
                conn["url"] = cfg.get("url", "")
                if "headers" in cfg:
                    conn["headers"] = cfg["headers"]

            connections[name] = conn

        return connections

    def _init_client(self):
        """延迟初始化 MCP Client"""
        if self._initialized:
            return

        try:
            from langchain_mcp_adapters.client import MultiServerMCPClient
        except ImportError:
            self._init_error = (
                "MCP 支持未安装，请运行: pip install flux-agent[mcp]"
            )
            logger.warning(self._init_error)
            self._initialized = True
            return

        try:
            connections = self._build_connections()
            if not connections:
                self._initialized = True
                return

            # 构建 tool_name_prefix: 如果有任何一个 server 配置了 prefix，就启用
            default_prefix = False
            for cfg in self._server_configs:
                if cfg.get("tool_name_prefix"):
                    default_prefix = True
                    break

            self._client = MultiServerMCPClient(
                connections,
                tool_name_prefix=default_prefix,
            )
        except Exception as e:
            self._init_error = f"MCP Client 初始化失败: {e}"
            logger.warning(self._init_error)

        self._initialized = True

    async def get_tools(self) -> List:
        """
        获取所有 MCP 工具（LangChain BaseTool 列表）

        返回空列表如果:
        - MCP 依赖未安装
        - 初始化失败
        - 无配置 server
        """
        if self._tools is not None:
            return self._tools

        self._init_client()

        if self._client is None:
            return []

        try:
            self._tools = await self._client.get_tools()
            logger.info(f"MCP 工具加载完成: {len(self._tools)} 个工具")
        except Exception as e:
            self._init_error = f"MCP 工具加载失败: {e}"
            logger.warning(self._init_error)
            self._tools = []

        return self._tools

    async def get_tools_by_server(self, server_name: str) -> List:
        """获取指定 Server 的工具"""
        if self._client is None:
            return []

        try:
            return await self._client.get_tools(server_name=server_name)
        except Exception as e:
            logger.warning(f"获取 Server {server_name} 的工具失败: {e}")
            return []

    @property
    def available(self) -> bool:
        """MCP Client 是否可用"""
        self._init_client()
        return self._client is not None

    @property
    def error(self) -> Optional[str]:
        """获取初始化错误信息"""
        return self._init_error

    async def close(self):
        """关闭所有连接"""
        if self._client is not None and hasattr(self._client, "close"):
            try:
                await self._client.close()
            except Exception as e:
                logger.debug(f"MCP Client 关闭失败: {e}")


def mcp_server_from_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    从 workflow JSON 配置中提取 MCP Server 配置

    返回 server_configs 列表，可以直接传给 MCPClientManager
    """
    mcp_servers = config.get("mcp_servers", [])
    if not isinstance(mcp_servers, list):
        return []
    return mcp_servers
