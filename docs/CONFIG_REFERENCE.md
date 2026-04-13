# 配置参考

## 一、配置文件结构

```json
{
  "workflow": {...},    // 工作流元信息
  "nodes": [...],       // 节点列表
  "edges": [...],       // 边列表
  "tools": [...]        // 工具定义（可选）
  "mcp_servers": [...]  // MCP Server 配置（可选）
}
```

---

## 二、workflow 字段

```json
{
  "workflow": {
    "name": "my-workflow",
    "description": "工作流描述",
    "version": "1.0.0"
  }
}
```

---

## 三、nodes 字段

### 3.1 通用结构

```json
{
  "id": "node_id",
  "type": "LLMNode",
  "config": {...},
  "retry_policy": {...},
  "cache_policy": {...}
}
```

### 3.2 LLMNode

```json
{
  "id": "llm",
  "type": "LLMNode",
  "config": {
    "model_name": "gpt-4o-mini",
    "system_prompt": "你是一个助手",
    "user_prompt": "${data.input}",
    "output_key": "data.response",
    "temperature": 0,
    "max_tokens": 4096,
    "base_url": "",
    "api_key": "",
    "response_format": {"type": "json_object"},
    "save_to_messages": true,
    "tools": ["search"],
    "max_tool_iterations": 10,
    "timeout": 300.0,
    "max_retries": 1
  }
}
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `model_name` | str | "gpt-4o" | 模型名称 |
| `system_prompt` | str | "" | 系统提示词 |
| `user_prompt` | str | "" | 用户提示词 |
| `output_key` | str | "data.output" | 输出位置 |
| `temperature` | float | 0.0 | 温度 |
| `max_tokens` | int | 4096 | 最大 token |
| `base_url` | str | "" | 自定义 API 地址 |
| `api_key` | str | "" | 自定义 API Key |
| `response_format` | dict | null | `{"type": "json_object"}`，仅用于简单 JSON 输出 |
| `save_to_messages` | bool | true | 保存到 messages |
| `tools` | list | [] | 工具列表 |
| `max_tool_iterations` | int | 10 | 工具循环最大次数 |
| `timeout` | float | 300.0 | 请求超时时间（秒），默认 5 分钟 |
| `max_retries` | int | 1 | 请求失败最大重试次数 |
| `json_schema` | dict | null | JSON Schema 字典，用于结构化输出 |
| `json_schema_pydantic` | str | null | Pydantic 模型路径，如 "my_models:UserInfo" |
| `json_schema_typed_dict` | str | null | TypedDict 类路径 |
| `json_schema_strict` | bool | true | 是否启用 strict 模式 |
| `include_raw` | bool | false | 是否包含原始响应（包含 parsed/raw/parsing_error）|

**Token Usage 自动追踪**：LLMNode 会自动将 token 用量写入 state 顶层 `_token_usage` 字段（通过 `merge_token_usage` reducer 自动汇总累加 + 明细追加），无需手动配置。

**注意**：`response_format` 和 `json_schema`/`json_schema_pydantic` 不能同时使用。
- `response_format: {"type": "json_object"}` - 只保证输出是有效 JSON
- `json_schema` / `json_schema_pydantic` - 强制符合指定 schema（推荐）

**Structured Output 示例：**

```json
{
  "id": "llm",
  "type": "LLMNode",
  "config": {
    "model_name": "gpt-4o",
    "json_schema": {
      "type": "object",
      "properties": {
        "name": {"type": "string"},
        "age": {"type": "integer"}
      },
      "required": ["name"]
    }
  }
}
```

**Pydantic 模型示例：**

```json
{
  "config": {
    "model_name": "gpt-4o",
    "json_schema_pydantic": "myapp.schemas:UserInfo"
  }
}
```

### 3.3 ConditionNode

```json
{
  "id": "router",
  "type": "ConditionNode",
  "config": {
    "branches": [
      {"condition": "data.score >= 90", "target": "excellent"},
      {"condition": "data.score >= 60", "target": "pass"},
      {"condition": "default", "target": "fail"}
    ]
  }
}
```

**支持 END 退出：**

```json
{"condition": "data.error", "target": "END"}
```

**条件表达式：**

```
data.score > 60
data.name == "张三"
data.score >= 60 and data.attempts < 3
"error" in data.tags
data.value is null
```

### 3.4 TransformNode

```json
{
  "id": "transform",
  "type": "TransformNode",
  "config": {
    "transforms": [
      {"action": "set", "key": "data.x", "value": 1},
      {"action": "get", "from": "data.x", "to": "data.y", "default": ""},
      {"action": "copy", "from": "data.x", "to": "data.y"},
      {"action": "delete", "key": "data.x"},
      {"action": "default", "key": "data.x", "value": 0},
      {"action": "merge", "key": "data.config", "value": {"k": "v"}},
      {"action": "increment", "key": "data.count", "amount": 1},
      {"action": "append", "key": "data.items", "value": "new"},
      {"action": "map", "key": "data.items", "expr": "item.upper()"},
      {"action": "filter", "key": "data.items", "expr": "item > 0"},
      {"action": "format", "key": "data.user", "template": "{name}"}
    ]
  }
}
```

### 3.5 JsonNode

```json
{
  "id": "json",
  "type": "JsonNode",
  "config": {
    "action": "encode",
    "input_key": "data.obj",
    "output_key": "data.json_str",
    "indent": 2,
    "ensure_ascii": false,
    "error_on_fail": true
  }
}
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `action` | str | "encode" | 操作：encode（编码）或 decode（解码）|
| `input_key` | str | "data.input" | 输入数据路径 |
| `output_key` | str | "data.output" | 输出数据路径 |
| `indent` | int | 2 | 编码缩进（仅 encode 有效）|
| `ensure_ascii` | bool | false | 是否转义非 ASCII 字符（仅 encode 有效）|
| `default` | any | null | 解码失败时的默认值 |
| `error_on_fail` | bool | true | 失败时是否抛出错误 |

**编码示例：**
```json
{"action": "encode", "input_key": "data.obj", "output_key": "data.json"}
```

**解码示例：**
```json
{"action": "decode", "input_key": "data.json", "output_key": "data.obj"}
```

### 3.6 ToolNode

```json
{
  "id": "tool",
  "type": "ToolNode",
  "config": {
    "tool_name": "search",
    "args": {"query": "${data.q}"},
    "output_key": "data.result",
    "parse_output": true,
    "error_on_fail": true
  }
}
```

### 3.6 HTTPRequestNode

```json
{
  "id": "http",
  "type": "HTTPRequestNode",
  "config": {
    "url": "https://api.example.com",
    "method": "POST",
    "headers": {"Authorization": "Bearer ${env.TOKEN}"},
    "params": {"page": 1},
    "body": {"q": "${data.query}"},
    "output_key": "data.response",
    "timeout": 30
  }
}
```

### 3.7 HumanInputNode

```json
{
  "id": "review",
  "type": "HumanInputNode",
  "config": {
    "prompt": "请审核：${data.content}",
    "output_key": "data.decision",
    "options": ["approve", "reject"],
    "timeout": 3600
  }
}
```

### 3.8 SubgraphNode

```json
{
  "id": "sub",
  "type": "SubgraphNode",
  "config": {
    "workflow_path": "./sub.json",
    "input_mapping": {"data.input": "data.query"},
    "output_mapping": {"data.result": "data.sub_result"}
  }
}
```

### 3.9 LoopNode

```json
{
  "id": "process_loop",
  "type": "LoopNode",
  "config": {
    "input_key": "data.items",
    "results_key": "data.results",
    "subgraph_item_key": "data.item",
    "subgraph_meta_key": "data.meta",
    "subgraph_result_path": "data.result",
    "body_nodes": [...],
    "body_edges": [...],
    "body_entry_point": "process",
    "max_iterations": 10,
    "parallel": false,
    "parallel_max_workers": 5,
    "delay": 0,
    "on_error": "raise",
    "emit_progress": true
  }
}
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `input_key` | str | "data.items" | 主流程 state 中要遍历的数组路径 |
| `results_key` | str | "data.results" | 所有迭代结果写入主流程 state 的路径 |
| `subgraph_item_key` | str | "data.item" | 子图接收当前 item 的路径 |
| `subgraph_meta_key` | str | "data.meta" | 子图接收循环元信息的路径，设为空则不注入 |
| `subgraph_result_path` | str | "" | 从子图最终 state 中提取结果的路径，为空则取整个 state |
| `body_nodes` | list | [] | 子图节点配置列表 |
| `body_edges` | list | [] | 子图边配置列表 |
| `body_entry_point` | str | "" | 子图入口节点 ID |
| `max_iterations` | int | 0 | 最大迭代次数，<=0 不限制 |
| `parallel` | bool | false | 是否并行执行 |
| `parallel_max_workers` | int | 5 | 并行执行的最大线程数 |
| `delay` | float | 0 | 串行模式下每轮延迟(秒) |
| `on_error` | str | "raise" | 错误处理：raise 抛出 / skip 跳过 |
| `emit_progress` | bool | true | 是否发出进度事件 |

**子图 state 结构：**

子图每次执行时收到的 state 完全隔离，只包含：
```python
{
    "data": {
        "item": <当前元素>,           # 由 subgraph_item_key 指定
        "meta": {                     # 由 subgraph_meta_key 指定（可选）
            "index": 0,               # 当前索引 (0-based)
            "total": 5,               # 总数
            "is_first": true,         # 是否第一个
            "is_last": false          # 是否最后一个
        }
    }
}
```

**子图引用主流程 tools：**

在 body_nodes 中可以直接引用主流程已定义的 tools：
```json
{
  "id": "call_tool",
  "type": "tool",
  "config": {
    "tool_name": "my_tool",
    "args": {"query": "${data.item}"}
  }
}
```

### 3.10 AgentNode

在工作流中调用智能 Agent，支持多种 Agent 模式。

```json
{
  "id": "agent",
  "type": "AgentNode",
  "config": {
    "mode": "react",
    "query": "${data.question}",
    "output_key": "data.answer",
    "tools": ["search"],
    "system_prompt": "你是一个助手",
    "max_steps": 10,
    "agent_config": {
      "verbose": true,
      "temperature": 0.7
    }
  }
}
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `mode` | str | "react" | Agent 模式：react / deep / plan_execute / reflexion |
| `query` | str | - | Agent 输入的问题/任务，支持变量插值 |
| `output_key` | str | "data.output" | Agent 输出写入位置 |
| `tools` | list | [] | 工具名称列表 |
| `system_prompt` | str | None | 自定义系统提示词 |
| `max_steps` | int | 10 | 最大执行步数 |
| `agent_config` | dict | {} | Agent 配置（verbose, temperature 等） |
| `context` | str | None | 额外上下文信息 |
| `messages` | list | [] | 对话历史 |

**支持的模式：**

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| `react` | ReAct 模式 | 简单问答、工具调用 |
| `deep` | Deep 模式 | 复杂任务、代码生成 |
| `plan_execute` | 计划执行模式 | 多步骤任务 |
| `reflexion` | 反思模式 | 高质量输出 |

**模式特定配置：**

```json
// Plan-Execute 模式
{
  "mode": "plan_execute",
  "agent_config": {
    "enable_replan": true
  }
}

// Reflexion 模式
{
  "mode": "reflexion",
  "agent_config": {
    "max_iterations": 3,
    "quality_threshold": 8.0
  }
}
```

**工具解析：**

AgentNode 会从父上下文（WorkflowRunner 或 SubgraphNode）中解析工具：

```json
{
  "tools": [
    {"name": "search", "implementation": "my_tools:search_func"}
  ],
  "nodes": [
    {
      "id": "agent",
      "type": "AgentNode",
      "config": {
        "mode": "react",
        "query": "${data.q}",
        "tools": ["search"]
      }
    }
  ]
}
```

**完整示例：**

```json
{
  "workflow": {
    "name": "research-agent",
    "version": "1.0.0"
  },
  "tools": [
    {"name": "web_search", "implementation": "tools:web_search"}
  ],
  "nodes": [
    {
      "id": "research",
      "type": "AgentNode",
      "config": {
        "mode": "plan_execute",
        "query": "研究 ${data.topic} 并给出分析报告",
        "output_key": "data.report",
        "tools": ["web_search"],
        "system_prompt": "你是一个专业研究员",
        "agent_config": {
          "verbose": true,
          "enable_replan": true
        }
      }
    }
  ],
  "edges": [
    {"from": "START", "to": "research"},
    {"from": "research", "to": "END"}
  ]
}
```

**与 LLMNode 的区别：**

| 特性 | LLMNode | AgentNode |
|------|---------|-----------|
| 执行模式 | 单次调用 | 多步推理 |
| 工具使用 | 简单工具调用 | 智能决策+工具调用 |
| 输出保证 | 原始 LLM 输出 | 结构化 AgentOutput |
| 适用场景 | 简单任务 | 复杂推理任务 |

---

## 四、edges 字段

### 4.1 普通边

```json
{"from": "node_a", "to": "node_b"}
{"from": "START", "to": "first"}
{"from": "last", "to": "END"}
```

### 4.2 条件边

```json
{
  "from": "check",
  "condition_map": {
    "pass": "success",
    "fail": "error",
    "exit": "END"
  }
}
```

---

## 九、mcp_servers 字段

配置外部 MCP（Model Context Protocol）Server，让 LLMNode 和 Agent 可以调用 MCP 工具。

### 9.1 支持的传输方式

| 方式 | 说明 | 适用场景 |
|------|------|----------|
| `stdio` | 本地进程通信 | 本地 CLI 工具、脚本 |
| `http` | Server-Sent Events | 远程 HTTP 服务 |
| `streamable_http` | 无状态 HTTP | MCP 协议推荐的远程连接方式 |

### 9.2 字段说明

```json
{
  "mcp_servers": [
    {
      "name": "filesystem",
      "transport": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp/allowed-dir"],
      "env": {"NODE_ENV": "production"},
      "tool_name_prefix": "fs_"
    },
    {
      "name": "web-search",
      "transport": "streamable_http",
      "url": "https://mcp-gateway.example.com/mcp",
      "headers": {"Authorization": "Bearer sk-xxx"},
      "tool_name_prefix": true
    }
  ]
}
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `name` | str | 自动生成 | Server 名称，用于标识和日志 |
| `transport` | str | "stdio" | 传输方式：stdio / http / streamable_http |
| `command` | str | "python" | stdio 模式的启动命令 |
| `args` | list | [] | stdio 模式的命令行参数 |
| `env` | dict | {} | stdio 模式的环境变量 |
| `url` | str | "" | http/streamable_http 模式的 URL |
| `headers` | dict | {} | http/streamable_http 模式的请求头 |
| `tool_name_prefix` | bool\|str | false | 是否添加工具名前缀。`true` 使用 server name 作为前缀 |

### 9.3 完整工作流示例

```json
{
  "workflow": {"name": "mcp-demo"},
  "mcp_servers": [
    {
      "name": "filesystem",
      "transport": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp/docs"],
      "tool_name_prefix": true
    }
  ],
  "tools": [
    {"name": "web_search", "implementation": "my_tools:search"}
  ],
  "nodes": [
    {
      "id": "answer",
      "type": "LLMNode",
      "config": {
        "model_name": "gpt-4o",
        "system_prompt": "你是一个助手，可以读取文件并搜索网络",
        "user_prompt": "读取 /tmp/docs/readme.md 的内容，并搜索关于 ${data.topic} 的信息",
        "tools": ["web_search", "fs_read_file"],
        "output_key": "data.answer"
      }
    }
  ],
  "edges": [
    {"from": "START", "to": "answer"},
    {"from": "answer", "to": "END"}
  ]
}
```

**说明**：
- `fs_read_file` 是 filesystem MCP Server 自动提供的工具
- `web_search` 是代码注册的本地工具
- 两类工具在 LLMNode 中完全等价使用

### 9.4 编程方式使用

```python
from flux_agent import WorkflowRunner

runner = WorkflowRunner(
    config_dict=config,
    mcp_servers=[
        {
            "name": "math",
            "transport": "stdio",
            "command": "python",
            "args": ["mcp_servers/math_server.py"],
        }
    ],
)
```

---

## 十、tools 字段

### 5.1 配置文件定义

```json
{
  "tools": [
    {"name": "search", "implementation": "my_tools:search_func"}
  ]
}
```

### 5.2 代码注册（推荐）

```python
def search(query: str) -> str:
    """搜索网络"""
    return do_search(query)

runner = WorkflowRunner(config_path="workflow.json", tools={"search": search})
```

---

## 十一、retry_policy

```json
{
  "retry_policy": {
    "max_attempts": 3,
    "initial_interval": 1.0,
    "max_interval": 10.0,
    "backoff_multiplier": 2.0,
    "retry_on": ["ConnectionError"]
  }
}
```

---

## 十二、cache_policy

```json
{
  "cache_policy": {
    "enabled": true,
    "ttl": 300,
    "key_template": "${data.input}"
  }
}
```

---

## 十三、变量插值

```json
{
  "user_prompt": "用户 ${data.name} 的问题是：${data.question}"
}
```

| 语法 | 说明 |
|------|------|
| `${data.field}` | 状态数据 |
| `${env.VAR}` | 环境变量 |
| `${context.field}` | 运行时上下文 |
