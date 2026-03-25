# 配置参考

## 一、配置文件结构

```json
{
  "workflow": {...},    // 工作流元信息
  "nodes": [...],       // 节点列表
  "edges": [...],       // 边列表
  "tools": [...]        // 工具定义（可选）
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
    "max_tool_iterations": 10
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
| `response_format` | dict | null | 响应格式 |
| `save_to_messages` | bool | true | 保存到 messages |
| `tools` | list | [] | 工具列表 |
| `max_tool_iterations` | int | 10 | 工具循环最大次数 |

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

### 3.5 ToolNode

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

## 五、tools 字段

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

## 六、retry_policy

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

## 七、cache_policy

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

## 八、变量插值

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
