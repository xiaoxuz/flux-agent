# 节点开发指南

## 一、节点基类

所有节点必须继承 `BaseNode`：

```python
from flux_agent.nodes.base import BaseNode, NodeConfig
from dataclasses import dataclass
from typing import Any, Dict

@dataclass
class MyNodeConfig(NodeConfig):
    my_param: str = ""
    output_key: str = "data.result"

class MyNode(BaseNode):
    node_type = "my_node"
    config_class = MyNodeConfig
    
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        # 读取输入
        input_value = self._get_nested(state, "data.input", "")
        
        # 处理
        result = f"{self.config.my_param}: {input_value}"
        
        # 返回
        return self._set_nested({}, self.config.output_key, result)
```

---

## 二、内置工具方法

| 方法 | 说明 |
|------|------|
| `_get_nested(state, key, default)` | 获取嵌套值 |
| `_set_nested(state, key, value)` | 设置嵌套值 |
| `_delete_nested(state, key)` | 删除嵌套键 |
| `_interpolate(template, state)` | 变量插值 |
| `_interpolate_dict(d, state)` | 字典插值 |

---

## 三、注册节点

### 方式1：WorkflowRunner 参数

```python
from flux_agent import WorkflowRunner
from my_nodes import MyNode

runner = WorkflowRunner(
    config_dict=config,
    custom_nodes={"my_node": MyNode}
)
```

### 方式2：entry_points（推荐）

在业务节点包的 `pyproject.toml` 中：

```toml
[project.entry-points."flux_agent.nodes"]
my_node = "my_package.nodes:MyNode"
```

---

## 四、使用工具

```python
class MyNode(BaseNode):
    def execute(self, state):
        if "search" in self.tools:
            result = self.tools["search"]("query")
        return {"data": {"result": result}}
```

---

## 五、错误处理

```python
def execute(self, state):
    try:
        result = self._do_work(state)
        return {"data": {"result": result}}
    except ValidationError as e:
        return {"errors": [f"校验失败: {e}"]}
    except Exception as e:
        raise
```

---

## 六、重试与缓存

```json
{
  "id": "my_node",
  "type": "my_node",
  "retry_policy": {
    "max_attempts": 3,
    "initial_interval": 1.0
  },
  "cache_policy": {
    "enabled": true,
    "ttl": 300
  }
}
```

---

## 七、单元测试

```python
def test_my_node():
    node = MyNode({"my_param": "test"})
    result = node.execute({"data": {"input": "hello"}})
    assert result["data"]["result"] == "test: hello"
```

---

## 八、LoopNode 循环迭代节点开发

LoopNode 是特殊的复合节点，它本身不是一个具体的业务逻辑节点，而是一个**容器节点**，用于循环执行一个子图（由 body_nodes 和 body_edges 定义）。

### 8.1 LoopNode 配置

```python
from flux_agent.nodes.builtin.control import LoopNode, LoopNodeConfig

# LoopNodeConfig 参数说明
config = {
    # 输入
    "input_key": "data.items",        # 主流程 state 中要遍历的数组路径
    
    # 子图定义
    "body_nodes": [...],              # 子图节点列表
    "body_edges": [...],              # 子图边列表
    "body_entry_point": "process",    # 子图入口节点
    
    # 子图输入映射
    "subgraph_item_key": "data.item",   # 子图中当前元素的路径
    "subgraph_meta_key": "data.meta",   # 子图中循环元信息的路径（可选）
    
    # 子图输出映射
    "subgraph_result_path": "data.result",  # 从子图 state 提取结果的路径
    
    # 输出
    "results_key": "data.results",     # 所有结果写回主流程的路径
    
    # 执行控制
    "max_iterations": 10,              # 最大迭代次数，<=0 不限制
    "parallel": False,                 # 是否并行执行
    "parallel_max_workers": 5,         # 并行最大线程数
    "delay": 0,                        # 串行模式每轮延迟(秒)
    "on_error": "raise",               # raise 抛出 / skip 跳过
    "emit_progress": True              # 是否发出进度事件
}
```

### 8.2 子图 state 结构

每次迭代时，子图收到的 state 是完全隔离的：

```python
{
    "data": {
        "item": <当前元素>,           # 由 subgraph_item_key 指定
        "meta": {                     # 由 subgraph_meta_key 指定（可选）
            "index": 0,               # 当前索引 (0-based)
            "total": 5,               # 总数
            "is_first": True,         # 是否第一个
            "is_last": False          # 是否最后一个
        }
    }
}
```

### 8.3 示例：开发一个使用 LoopNode 的工作流

```python
from flux_agent import WorkflowRunner

config = {
    "workflow": {"name": "loop-demo"},
    "nodes": [
        # 1. 准备数据
        {
            "id": "init",
            "type": "transform",
            "config": {
                "transforms": [
                    {"action": "set", "key": "data.items", "value": [1, 2, 3, 4, 5]}
                ]
            }
        },
        # 2. 循环处理
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
                        "id": "double",
                        "type": "transform",
                        "config": {
                            "transforms": [
                                {"action": "set", "key": "data.output", "value": "${data.item} * 2"}
                            ]
                        }
                    }
                ],
                "body_edges": [
                    {"from": "START", "to": "double"},
                    {"from": "double", "to": "END"}
                ]
            }
        }
    ],
    "edges": [
        {"from": "START", "to": "init"},
        {"from": "init", "to": "process_loop"},
        {"from": "process_loop", "to": "END"}
    ]
}

runner = WorkflowRunner(config_dict=config)
result = runner.invoke({"data": {}})
# result["data"]["results"] = [2, 4, 6, 8, 10]
```

### 8.4 子图引用主流程 tools

LoopNode 的子图可以引用主流程已定义的 tools：

```python
# 主流程定义 tools
def search_func(query: str) -> str:
    return f"搜索: {query}"

runner = WorkflowRunner(
    config_dict=config,
    tools={"search": search_func}  # 传入主流程 tools
)
```

在 body_nodes 中引用：
```json
{
    "id": "call_tool",
    "type": "tool",
    "config": {
        "tool_name": "search",
        "args": {"query": "${data.item}"}
    }
}
```

LoopNode 会自动从主流程 tools 中收集子图需要的工具。
