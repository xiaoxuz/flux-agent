# MCP 协议接入

通过 MCP（Model Context Protocol）连接外部工具服务器，所有 Agent 模式与 Workflow 均支持。

## 快速开始

### Agent 模式

```python
from flux_agent.agents import create_agent
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o")

agent = create_agent(
    "react",
    llm=llm,
    mcp_servers=[
        {
            "name": "math",
            "transport": "stdio",
            "command": "python",
            "args": ["mcp_math_server.py"],
            "tool_name_prefix": "math_",
        }
    ],
)

result = agent.invoke("计算 (15 + 27) * 3 的结果")
print(result.answer)
```

### Workflow 模式

在 workflow JSON 配置中声明 `mcp_servers`：

```python
config = {
    "workflow": {"name": "mcp-demo"},
    "mcp_servers": [
        {
            "name": "math",
            "transport": "stdio",
            "command": "python",
            "args": ["mcp_math_server.py"],
        }
    ],
    "nodes": [
        {
            "id": "agent",
            "type": "agent",
            "config": {
                "mode": "react",
                "model_name": "gpt-4o",
                "system_prompt": "你是一个助手，可以使用工具完成任务。",
                "user_prompt": "${data.question}",
            },
        }
    ],
    "edges": [
        {"from": "START", "to": "agent"},
        {"from": "agent", "to": "END"},
    ],
}

from flux_agent import WorkflowRunner

runner = WorkflowRunner(config_dict=config)
result = runner.invoke({"data": {"question": "计算 (15 + 27) * 3"}})
```

## 配置参数

每个 MCP Server 配置字典支持以下字段：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | str | 是 | 服务名称，用于标识和日志 |
| `transport` | str | 是 | 传输方式：`stdio` / `http` / `streamable_http` |
| `command` | str | stdio 时必填 | stdio 模式的启动命令（如 `"python"`、`"npx"`） |
| `args` | list | stdio 时必填 | stdio 模式的命令行参数 |
| `env` | dict | 否 | stdio 模式的环境变量 |
| `url` | str | http 时必填 | HTTP 模式的服务器 URL |
| `headers` | dict | 否 | HTTP 模式的请求头，可用于认证（如 Cookie、Authorization） |
| `tool_name_prefix` | str \| bool | 否 | 工具名前缀。`True` 表示自动使用服务名作为前缀；字符串则使用该字符串。工具最终命名为 `<prefix><tool_name>` |

## 传输方式

### stdio（本地进程）

适用于本地 CLI 工具、脚本等场景。MCP Server 作为子进程启动，通过标准输入输出通信。

```python
{
    "name": "filesystem",
    "transport": "stdio",
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
    "env": {"DEBUG": "1"},
    "tool_name_prefix": "fs_",
}
```

### streamable_http（远程 HTTP）

适用于远程 MCP 服务，支持通过 headers 传递认证信息。

```python
{
    "name": "mcp-gateway",
    "transport": "streamable_http",
    "url": "http://mcp-gateway/mcp",
    "headers": {"Authorization": "Bearer xxx"},
    "tool_name_prefix": "gw_",
}
```

### http（SSE）

旧版 SSE 传输方式，兼容早期 MCP 实现。

```python
{
    "name": "legacy-mcp",
    "transport": "http",
    "url": "http://server/sse",
    "headers": {"Authorization": "Bearer xxx"},
}
```

## 混合使用：代码工具 + MCP 工具

代码注册的工具与 MCP Server 提供的工具可以混合使用，MCP 工具自动注入 Agent 工具集：

```python
from langchain_core.tools import tool
from flux_agent.agents import create_agent

@tool
def greet(name: str) -> str:
    """打招呼"""
    return f"Hello, {name}!"

agent = create_agent(
    "react",
    llm=llm,
    tools=[greet],              # 代码注册的工具
    mcp_servers=MCP_SERVERS,    # MCP Server 提供的工具
)
```

## Supervisor 模式 + MCP

Supervisor Agent 的完整工具池（含 MCP 工具）会自动分发给各 worker：

```python
from flux_agent.agents import create_agent, WorkerConfig

supervisor = create_agent(
    "supervisor",
    llm=llm,
    mcp_servers=[
        {"name": "search", "transport": "stdio", "command": "python", "args": ["search_mcp.py"]},
        {"name": "file", "transport": "stdio", "command": "npx", "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]},
    ],
    workers={
        "researcher": WorkerConfig(
            mode="react",
            description="负责搜索信息",
            tools=["search_query"],   # 从 MCP 工具中筛选
        ),
        "writer": WorkerConfig(
            mode="plan_execute",
            description="负责撰写报告",
            tools=["write_file", "read_file"],  # 从 MCP 工具中筛选
        ),
    },
)
```

## 安装

```bash
pip install flux-agent[mcp]
```

包含依赖：`langchain-mcp-adapters>=0.1.0`、`mcp>=1.0.0`

## 架构说明

```
MCP Server(s)
    │
    ▼
MCPClientManager ─────────► MultiServerMCPClient (langchain-mcp-adapters)
    │                              │
    │   get_tools() (async)        │  tools/list (MCP 协议)
    │                              ▼
    │                       List[BaseTool] (仅异步 ainvoke)
    │                              │
    │   _wrap_mcp_tool_for_sync()  │
    │                              ▼
    │                       sync-compatible tools
    │                              │
    ▼                              ▼
BaseAgent._get_all_tools() ──► 完整工具池（user tools + skill tools + MCP tools）
```

**关键点：**

- `MCPClientManager` 采用懒加载模式，首次调用时才建立连接
- MCP 工具默认仅支持异步 `ainvoke`，项目通过 `_wrap_mcp_tool_for_sync()` 包装为同步/异步双模调用
- 所有 Agent 模式通过 `self._get_all_tools()` 统一获取工具，MCP 工具自动包含其中
- WorkflowRunner 同样支持 MCP，通过构造函数参数或 JSON 配置传入

## 示例

- `examples/agents/demo_mcp_agent.py` — Agent + MCP 集成演示
- `examples/node/demo_mcp.py` — MCP 工作流配置
