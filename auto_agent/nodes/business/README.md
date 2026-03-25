# Business Nodes

此目录存放项目特定的业务节点。

## 开发流程

1. 创建节点文件：`{业务域}_{动作}.py`
2. 实现节点类（继承 BaseNode）
3. 在 `__init__.py` 中导出并注册
4. 在工作流 JSON 中使用

## 命名规范

| 类型 | 格式 | 示例 |
|------|------|------|
| 文件名 | `{业务域}_{动作}.py` | `order_analyze.py` |
| 类名 | `{业务域}{动作}Node` | `OrderAnalyzeNode` |
| node_type | `{业务域}_{动作}` | `order_analyze` |

## 与 examples/ 的区别

- `examples/`: 演示用途，展示节点开发模式
- `business/`: 生产代码，实际业务节点
