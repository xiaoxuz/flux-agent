# flux_agent/mcp/__init__.py
"""
MCP (Model Context Protocol) 集成

支持 stdio / http / streamable_http 三种传输方式。

用法:
    from flux_agent.mcp import MCPClientManager

    manager = MCPClientManager([{
        "name": "my-server",
        "transport": "stdio",
        "command": "python",
        "args": ["mcp_server.py"],
    }])
    tools = await manager.get_tools()
"""

from .client import MCPClientManager, mcp_server_from_config, MCP_TRANSPORT_TYPES

__all__ = [
    "MCPClientManager",
    "mcp_server_from_config",
    "MCP_TRANSPORT_TYPES",
]
