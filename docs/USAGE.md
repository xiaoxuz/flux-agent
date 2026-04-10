# Flux-Agent 使用文档

## 一、安装

```bash
pip install flux-agent
```

可选依赖：
```bash
pip install flux-agent[openai]      # OpenAI 模型
pip install flux-agent[anthropic]   # Anthropic 模型
pip install flux-agent[google]      # Google 模型
pip install flux-agent[all]         # 全部
```

---

## 二、快速开始

### 2.1 最简示例

```python
from flux_agent import WorkflowRunner

# 方式1：从 JSON 文件加载
runner = WorkflowRunner("workflow.json")

# 方式2：从字典配置
config = {
    "workflow": {"name": "hello"},
    "nodes": [
        {
            "id": "greet",
            "type": "LLMNode",
            "config": {
                "model_name": "gpt-4o-mini",
                "user_prompt": "用一句话介绍你自己",
                "output_key": "data.response"
            }
        }
    ],
    "edges": [
        {"from": "START", "to": "greet"},
        {"from": "greet", "to": "END"}
    ]
}
runner = WorkflowRunner(config_dict=config)

# 执行
result = runner.invoke({"data": {}})
print(result["data"]["response"])
```

### 2.2 带工具的工作流

```python
from flux_agent import WorkflowRunner

def greet(name: str) -> str:
    """生成问候语"""
    return f"你好, {name}!"

def get_weather(city: str) -> str:
    """获取城市天气"""
    return f"{city}今天天气晴朗"

# 注册工具
runner = WorkflowRunner(
    config_path="workflow.json",
    tools={"greet": greet, "get_weather": get_weather}
)

result = runner.invoke({"data": {"input": "北京"}})
```

---

## 三、WorkflowRunner API

### 3.1 初始化参数

```python
runner = WorkflowRunner(
    config_path="workflow.json",      # JSON 配置文件路径
    config_dict={...},                # 字典配置
    
    custom_nodes={"my_node": MyNode}, # 自定义节点
    tools={"search": search_func},     # 工具函数
    
    on_node_input=my_input_hook,      # 节点输入钩子
    on_node_output=my_output_hook,    # 节点输出钩子
)
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `config_path` | str | JSON 配置文件路径 |
| `config_dict` | dict | 字典配置 |
| `custom_nodes` | dict | 自定义节点映射 `{type: NodeClass}` |
| `tools` | dict | 工具函数映射 `{name: function}` |
| `on_node_input` | callable | 节点输入钩子 `(node_id, state) -> None` |
| `on_node_output` | callable | 节点输出钩子 `(node_id, state, output) -> None` |

### 3.2 执行方法

#### invoke - 同步执行

```python
result = runner.invoke(
    {"data": {"input": "..."}},   # 输入数据
    thread_id="session-1",         # 会话 ID
    interrupt_before=["node_id"],  # 在指定节点前中断
    interrupt_after=["node_id"]    # 在指定节点后中断
)
```

#### stream - 流式执行

```python
for chunk in runner.stream(
    {"data": {"input": "..."}},
    thread_id="session-1",
    stream_mode=["updates"]
):
    print(chunk)
```

#### resume - 恢复执行

```python
result = runner.resume(thread_id="session-1", resume_value="用户输入")
```

#### 异步方法

```python
result = await runner.ainvoke({"data": {...}})

async for chunk in runner.astream({"data": {...}}):
    print(chunk)
```

### 3.3 状态管理

```python
state = runner.get_state(thread_id="session-1")
history = list(runner.get_state_history(thread_id="session-1"))
runner.update_state(thread_id="session-1", values={"data": {"override": True}})

# 获取图可视化
graph = runner.get_graph()
mermaid = graph.get_graph(xray=True).draw_mermaid()
```

---

## 四、内置节点

### 4.1 LLMNode - LLM 调用

```json
{
  "id": "analyze",
  "type": "LLMNode",
  "config": {
    "model_name": "gpt-4o-mini",
    "system_prompt": "你是一个分析助手",
    "user_prompt": "分析：${data.input}",
    "output_key": "data.analysis",
    "temperature": 0,
    "max_tokens": 4096,
    "base_url": "",
    "api_key": "",
    "response_format": {"type": "json_object"},
    "save_to_messages": true,
    "tools": ["search", "calculate"],
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
| `user_prompt` | str | "" | 用户提示词，支持变量插值 |
| `output_key` | str | "data.output" | 输出存储位置 |
| `temperature` | float | 0.0 | 温度参数 |
| `max_tokens` | int | 4096 | 最大 token 数 |
| `base_url` | str | "" | 自定义 API 地址 |
| `api_key` | str | "" | 自定义 API Key |
| `response_format` | dict | null | `{"type": "json_object"}`，简单 JSON 输出 |
| `save_to_messages` | bool | true | 是否保存到 messages |
| `tools` | list | [] | 工具名称列表 |
| `max_tool_iterations` | int | 10 | 工具调用最大循环次数 |
| `timeout` | float | 300.0 | 请求超时时间（秒），默认 5 分钟 |
| `max_retries` | int | 1 | 请求失败最大重试次数 |
| `json_schema` | dict | null | JSON Schema 约束输出格式 |
| `json_schema_pydantic` | str | null | Pydantic 模型路径 |
| `include_raw` | bool | false | 是否包含原始响应 |

**工具调用循环**：配置 `tools` 后，LLMNode 自动执行：LLM 判断 → 执行工具 → 结果返回 LLM → 循环直到完成。

**Structured Output（结构化输出）**：让模型输出符合指定格式（推荐使用 `json_schema` 或 `json_schema_pydantic`，不要和 `response_format` 同时使用）

```json
{
  "id": "llm",
  "type": "LLMNode",
  "config": {
    "model_name": "gpt-4o",
    "user_prompt": "提取用户信息",
    "json_schema": {
      "type": "object",
      "properties": {
        "name": {"type": "string", "description": "用户名"},
        "age": {"type": "integer", "description": "年龄"}
      },
      "required": ["name"]
    }
  }
}
```

**Pydantic 模型方式**：

```json
{
  "config": {
    "model_name": "gpt-4o",
    "json_schema_pydantic": "myapp.models:UserInfo"
  }
}
```

返回结果会自动解析为 Pydantic 对象或字典。

### 4.2 ConditionNode - 条件分支

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

**支持直接退出：**

```json
{
  "branches": [
    {"condition": "data.error", "target": "END"},
    {"condition": "default", "target": "continue"}
  ]
}
```

**条件表达式：**

```
data.score > 60
data.name == "张三"
data.score >= 60 and data.attempts < 3
"error" in data.tags
data.value is null
```

### 4.3 TransformNode - 数据转换

```json
{
  "id": "transform",
  "type": "TransformNode",
  "config": {
    "transforms": [
      {"action": "set", "key": "data.status", "value": "processing"},
      {"action": "get", "from": "data.input", "to": "data.backup", "default": ""},
      {"action": "copy", "from": "data.original", "to": "data.copy"},
      {"action": "delete", "key": "data.temp"},
      {"action": "default", "key": "data.timeout", "value": 30},
      {"action": "merge", "key": "data.config", "value": {"debug": true}},
      {"action": "increment", "key": "data.counter", "amount": 1},
      {"action": "append", "key": "data.logs", "value": "新日志"},
      {"action": "map", "key": "data.prices", "expr": "item * 1.1"},
      {"action": "filter", "key": "data.items", "expr": "item > 0"},
      {"action": "format", "key": "data.user", "template": "姓名：{name}"}
    ]
  }
}
```

| 操作 | 说明 |
|------|------|
| `set` | 设置值，支持变量插值 |
| `get` | 获取值到新位置 |
| `copy` | 复制值 |
| `delete` | 删除字段 |
| `default` | 设置默认值（已存在则跳过） |
| `merge` | 合并对象 |
| `increment` | 递增数值 |
| `append` | 追加到列表 |
| `map` | 映射列表元素 |
| `filter` | 过滤列表 |
| `format` | 格式化字符串 |

### 4.4 JsonNode - JSON 编解码

```json
{
  "id": "json",
  "type": "JsonNode",
  "config": {
    "action": "encode",
    "input_key": "data.obj",
    "output_key": "data.json_str",
    "indent": 2,
    "ensure_ascii": false
  }
}
```

**编码：**

```json
{
  "id": "encode",
  "type": "JsonNode",
  "config": {
    "action": "encode",
    "input_key": "data.user",
    "output_key": "data.json",
    "indent": 2,
    "ensure_ascii": false
  }
}
```

**解码：**

```json
{
  "id": "decode",
  "type": "JsonNode",
  "config": {
    "action": "decode",
    "input_key": "data.json",
    "output_key": "data.obj",
    "error_on_fail": false,
    "default": {}
  }
}
```

| 参数 | 说明 |
|------|------|
| `action` | `encode` 编码 / `decode` 解码 |
| `indent` | 编码缩进，默认 2 |
| `ensure_ascii` | 是否转义中文，默认 false |
| `default` | 解码失败时的默认值 |
| `error_on_fail` | 失败时是否抛出错误，默认 true |

### 4.5 ToolNode - 工具调用

```json
{
  "id": "search",
  "type": "ToolNode",
  "config": {
    "tool_name": "web_search",
    "args": {"query": "${data.search_query}", "limit": 10},
    "output_key": "data.search_result",
    "parse_output": true,
    "error_on_fail": true
  }
}
```

### 4.6 HTTPRequestNode - HTTP 调用

```json
{
  "id": "api_call",
  "type": "HTTPRequestNode",
  "config": {
    "url": "https://api.example.com/data",
    "method": "POST",
    "headers": {"Authorization": "Bearer ${env.API_TOKEN}"},
    "body": {"query": "${data.input}"},
    "output_key": "data.api_result",
    "timeout": 30
  }
}
```

### 4.7 HumanInputNode - 人工介入

```json
{
  "id": "review",
  "type": "HumanInputNode",
  "config": {
    "prompt": "请审核：${data.content}",
    "output_key": "data.decision",
    "options": ["approved", "rejected"],
    "timeout": 3600
  }
}
```

### 4.8 SubgraphNode - 子图嵌套

```json
{
  "id": "subworkflow",
  "type": "SubgraphNode",
  "config": {
    "workflow_path": "./sub_workflow.json",
    "input_mapping": {"data.input": "data.query"},
    "output_mapping": {"data.result": "data.sub_result"}
  }
}
```

### 4.9 LoopNode - 循环迭代

LoopNode 用于循环遍历数组，对每个元素执行子图（body_nodes + body_edges），并收集所有子图结果。

**基本用法：**

```json
{
  "id": "process_loop",
  "type": "loop",
  "config": {
    "input_key": "data.items",
    "results_key": "data.results",
    "subgraph_item_key": "data.item",
    "subgraph_result_path": "data.output",
    
    "body_nodes": [
      {
        "id": "transform_item",
        "type": "transform",
        "config": {
          "transforms": [
            {"action": "set", "key": "data.output", "value": "${data.item} * 2"}
          ]
        }
      }
    ],
    "body_edges": [
      {"from": "START", "to": "transform_item"},
      {"from": "transform_item", "to": "END"}
    ]
  }
}
```

**子图 state 变量：**

| 变量 | 说明 |
|------|------|
| `${data.item}` | 当前遍历的元素 |
| `${data.meta.index}` | 当前索引 (0-based) |
| `${data.meta.total}` | 总数 |
| `${data.meta.is_first}` | 是否第一个 |
| `${data.meta.is_last}` | 是否最后一个 |

**并行执行：**

```json
{
  "id": "parallel_loop",
  "type": "loop",
  "config": {
    "input_key": "data.items",
    "results_key": "data.results",
    "subgraph_item_key": "data.item",
    "subgraph_result_path": "data.output",
    "parallel": true,
    "parallel_max_workers": 3,
    
    "body_nodes": [...],
    "body_edges": [...]
  }
}
```

**错误处理：**

```json
{
  "id": "safe_loop",
  "type": "loop",
  "config": {
    "input_key": "data.items",
    "results_key": "data.results",
    "on_error": "skip",
    
    "body_nodes": [...],
    "body_edges": [...]
  }
}
```

- `on_error: "raise"` - 遇到错误立即抛出（默认）
- `on_error: "skip"` - 遇到错误跳过该项，结果中包含 `_error` 字段

**限制迭代次数：**

```json
{
  "id": "limited_loop",
  "type": "loop",
  "config": {
    "input_key": "data.items",
    "results_key": "data.results",
    "max_iterations": 5,
    
    "body_nodes": [...],
    "body_edges": [...]
  }
}
```

---

## Token Usage 追踪

工作流自动追踪所有 LLMNode 的 token 用量，结果存储在 state 顶层 `_token_usage` 字段中，包含全局汇总和每个节点的明细。

```python
result = runner.invoke({"data": {"input": "..."}})
usage = result["_token_usage"]

# 全局汇总
print(f"总 token: {usage['total_tokens']}")
print(f"输入 token: {usage['input_tokens']}")
print(f"输出 token: {usage['output_tokens']}")

# 每个节点的明细
for detail in usage["details"]:
    print(f"  节点 {detail['node_id']}: {detail['total_tokens']} tokens")
```

输出示例：
```json
{
  "_token_usage": {
    "input_tokens": 350,
    "output_tokens": 180,
    "total_tokens": 530,
    "details": [
      {"node_id": "analyze", "input_tokens": 200, "output_tokens": 100, "total_tokens": 300},
      {"node_id": "summarize", "input_tokens": 150, "output_tokens": 80, "total_tokens": 230}
    ]
  }
}
```

多个 LLMNode 的 token 用量会通过 `merge_token_usage` reducer 自动汇总累加 + 明细追加，无需手动配置。

---

## 五、条件边与退出

### 5.1 condition_map

```json
{
  "edges": [
    {"from": "START", "to": "check"},
    {
      "from": "check",
      "condition_map": {
        "pass": "success_handler",
        "fail": "error_handler"
      }
    }
  ]
}
```

### 5.2 直接退出 END

**方式1：condition_map 中使用 END**

```json
{
  "from": "check",
  "condition_map": {
    "exit": "END",
    "continue": "next_node"
  }
}
```

**方式2：ConditionNode branches 中使用 END**

```json
{
  "branches": [
    {"condition": "data.error", "target": "END"},
    {"condition": "default", "target": "continue"}
  ]
}
```

---

## 六、工具注册

### 6.1 代码注册（推荐）

```python
def search(query: str, limit: int = 10) -> str:
    """搜索网络"""
    return do_search(query, limit)

runner = WorkflowRunner(
    config_path="workflow.json",
    tools={"search": search}
)
```

### 6.2 配置文件定义

```json
{
  "tools": [
    {"name": "search", "implementation": "my_tools.web_search:search_func"}
  ]
}
```

### 6.3 工具函数要求

```python
def my_tool(param1: str, param2: int = 10) -> str:
    """工具描述（必需）"""
    return f"结果: {param1}"
```

---

## 七、节点钩子

```python
def input_hook(node_id, state):
    print(f"[IN] {node_id}: {state.get('data', {})}")

def output_hook(node_id, state, output):
    print(f"[OUT] {node_id}: {output}")

runner = WorkflowRunner(
    config_path="workflow.json",
    on_node_input=input_hook,
    on_node_output=output_hook
)
```

---

## 八、重试与缓存

### 8.1 重试策略

```json
{
  "id": "api_call",
  "type": "HTTPRequestNode",
  "retry_policy": {
    "max_attempts": 3,
    "initial_interval": 1.0,
    "max_interval": 10.0,
    "backoff_multiplier": 2.0,
    "retry_on": ["ConnectionError", "TimeoutError"]
  }
}
```

### 8.2 缓存策略

```json
{
  "id": "expensive_llm",
  "type": "LLMNode",
  "cache_policy": {
    "enabled": true,
    "ttl": 300,
    "key_template": "${data.input}"
  }
}
```

---

## 九、完整示例

```json
{
  "workflow": {"name": "content-review"},
  "nodes": [
    {
      "id": "init",
      "type": "TransformNode",
      "config": {
        "transforms": [{"action": "set", "key": "data.status", "value": "processing"}]
      }
    },
    {
      "id": "analyze",
      "type": "LLMNode",
      "config": {
        "model_name": "gpt-4o-mini",
        "system_prompt": "分析文本的情感：正面/负面/中性",
        "user_prompt": "${data.content}",
        "response_format": {"type": "json_object"},
        "output_key": "data.analysis"
      }
    },
    {
      "id": "route",
      "type": "ConditionNode",
      "config": {
        "branches": [
          {"condition": "data.analysis.sentiment == '负面'", "target": "review"},
          {"condition": "default", "target": "publish"}
        ]
      }
    },
    {
      "id": "review",
      "type": "HumanInputNode",
      "config": {
        "prompt": "内容可能有问题，请审核：${data.content}",
        "output_key": "data.decision",
        "options": ["approve", "reject"]
      }
    },
    {
      "id": "publish",
      "type": "TransformNode",
      "config": {
        "transforms": [{"action": "set", "key": "data.status", "value": "published"}]
      }
    }
  ],
  "edges": [
    {"from": "START", "to": "init"},
    {"from": "init", "to": "analyze"},
    {"from": "analyze", "to": "route"},
    {"from": "route", "condition_map": {"review": "review", "publish": "publish"}},
    {"from": "review", "to": "publish"},
    {"from": "publish", "to": "END"}
  ]
}
```
