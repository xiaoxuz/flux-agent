# 技术架构文档

## 一、架构概览

Auto-Agent 是基于 LangGraph 构建的通用 Agent 编排框架，通过 JSON 配置驱动工作流。

```
┌─────────────────────────────────────────────────────────────┐
│                     JSON 配置文件                            │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    WorkflowParser                            │
│              (JSON → LangGraph StateGraph)                  │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    NodeRegistry                              │
│           管理内置节点和用户自定义节点                         │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   WorkflowRunner                             │
│               (StateGraph.compile + invoke)                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 二、核心组件

| 组件 | 职责 |
|-----|------|
| `WorkflowParser` | 解析 JSON 配置，构建 LangGraph StateGraph |
| `NodeRegistry` | 管理节点类型注册 |
| `WorkflowRunner` | 执行引擎，封装 invoke/stream/resume |
| `BaseNode` | 节点基类，定义统一接口 |

---

## 三、状态模型

```python
class BaseWorkflowState(TypedDict):
    messages: List[Any]    # 对话历史
    data: Dict[str, Any]   # 自定义数据存储
    errors: List[str]      # 错误记录
    _route: str            # 条件路由目标
```

**Reducer 机制：**

| 字段 | Reducer | 行为 |
|------|---------|------|
| `messages` | `add_messages` | 智能合并消息 |
| `data` | `merge` | 深度合并 |
| `errors` | `append` | 追加错误 |

---

## 四、节点执行流程

```
1. 从状态读取输入
2. 执行 execute() 方法
3. 返回状态更新
```

**节点返回值：**

```python
# 简单更新
return {"data": {"result": "..."}}

# 路由跳转
return {"_route": "next_node"}
```

---

## 五、条件边处理

```python
# condition_map 支持 END
if has_end_target:
    builder.add_conditional_edges(from_node, router)
else:
    builder.add_conditional_edges(from_node, router, condition_map)
```

---

## 六、工具调用流程

```
用户输入 → LLM 判断是否需要工具
    ↓
有 tool_calls → 执行工具 → 结果返回 LLM → 继续判断
    ↓
没有 tool_calls → 返回最终响应
```

---

## 七、持久化

使用 `MemorySaver` 进行状态持久化，支持 HumanInputNode 的暂停/恢复。

```python
from langgraph.checkpoint.memory import MemorySaver
checkpointer = MemorySaver()
graph = builder.compile(checkpointer=checkpointer)
```

---

## 八、错误处理

节点执行错误会记录到 `errors` 字段，配置 `retry_policy` 可自动重试。

---

## 九、性能优化

- **缓存**：配置 `cache_policy` 缓存节点结果
- **并行**：通过多条边实现并行执行
- **异步**：使用 `ainvoke`/`astream` 异步执行
