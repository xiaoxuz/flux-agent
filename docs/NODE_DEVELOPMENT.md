# 节点开发指南

## 一、节点基类

所有节点必须继承 `BaseNode`：

```python
from auto_agent.nodes.base import BaseNode, NodeConfig
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
from auto_agent import WorkflowRunner
from my_nodes import MyNode

runner = WorkflowRunner(
    config_dict=config,
    custom_nodes={"my_node": MyNode}
)
```

### 方式2：entry_points（推荐）

在业务节点包的 `pyproject.toml` 中：

```toml
[project.entry-points."auto_agent.nodes"]
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
