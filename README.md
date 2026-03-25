# Flux-Agent

基于 LangGraph + LLM 的通用 Agent 编排框架。通过 JSON 配置文件即可启动多 Agent Node 工作流，支持复杂的自动化流程编排。

## 核心特性

- **JSON 配置驱动** - 无需编写代码，通过 JSON 配置即可定义复杂工作流
- **内置通用节点** - LLM 调用、条件分支、工具调用、HTTP 请求等开箱即用
- **可插拔扩展** - 用户可按规范开发自定义节点，注册即可使用
- **并行执行** - 原生支持 map-reduce、并行处理等模式
- **人工介入** - 支持工作流暂停、人工审核、断点恢复
- **子图嵌套** - 支持将工作流作为子图嵌入其他工作流
- **状态持久化** - 支持内存、SQLite、PostgreSQL 等多种存储后端

## 快速开始

### 安装

```bash
pip install flux-agent
```

### 最简示例

```python
from flux_agent import WorkflowRunner

# 从 JSON 配置加载工作流
runner = WorkflowRunner("workflow.json")

# 执行
result = runner.invoke({"user_input": "你好"})
print(result)
```

### JSON 配置示例

```json
{
  "workflow": {
    "name": "simple-chain",
    "description": "简单的 LLM 调用链"
  },
  "nodes": [
    {
      "id": "greet",
      "type": "LLMNode",
      "config": {
        "model": "openai",
        "model_name": "gpt-4o",
        "system_prompt": "你是一个友好的助手",
        "user_prompt": "${data.user_input}",
        "output_key": "data.response"
      }
    }
  ],
  "edges": [
    {"from": "START", "to": "greet"},
    {"from": "greet", "to": "END"}
  ]
}
```

## 内置节点

| 节点类型 | 功能 | 说明 |
|---------|------|------|
| `LLMNode` | LLM 调用 | 支持 OpenAI、Anthropic、Gemini 等 |
| `ConditionNode` | 条件分支 | if/else、switch 分支路由 |
| `ToolNode` | 工具调用 | 执行预定义的工具/函数 |
| `TransformNode` | 数据转换 | set/get/filter/map 等操作 |
| `LoopNode` | 循环执行 | for/while 循环控制 |
| `ParallelNode` | 并行执行 | map-reduce 模式 |
| `HTTPRequestNode` | HTTP 调用 | REST API 调用 |
| `SubgraphNode` | 子图嵌套 | 嵌入其他工作流 |
| `HumanInputNode` | 人工介入 | 暂停等待人工输入 |

## 文档

- [使用文档](./docs/USAGE.md) - 快速开始、API 参考、完整示例
- [配置参考](./docs/CONFIG_REFERENCE.md) - JSON 配置完整说明
- [节点开发指南](./docs/NODE_DEVELOPMENT.md) - 自定义节点开发规范
- [外部节点开发](./docs/EXTERNAL_NODES.md) - 独立包开发与注册
- [开发指南](./docs/DEVELOPMENT.md) - 开发、测试、发布流程
- [技术架构](./docs/TECHNICAL.md) - 架构设计、核心概念

## 项目结构

```
flux-agent/
├── flux_agent/               # 包目录
│   ├── core/                 # 核心引擎
│   │   ├── state.py          # 状态模型
│   │   ├── registry.py       # 节点注册表
│   │   ├── parser.py         # 配置解析器
│   │   └── executor.py       # 执行引擎
│   │
│   ├── nodes/                # 节点模块
│   │   ├── base/             # 基类层
│   │   │   ├── node.py       # 节点基类
│   │   │   ├── config.py     # 配置模型
│   │   │   └── interfaces.py # 接口协议
│   │   ├── builtin/          # 内置节点
│   │   │   ├── control/      # condition, loop
│   │   │   ├── llm/          # LLM 调用
│   │   │   ├── transform/    # 数据转换
│   │   │   └── io/           # http, tool, parallel, subgraph, human
│   │   ├── examples/         # 示例节点
│   │   └── business/         # 业务节点
│   │
│   ├── utils/                # 工具函数
│   │   └── expression.py     # 表达式解析
│   │
│   └── tools/                # 工具模块
│
├── examples/                 # 示例脚本（不发布）
│   ├── demo_*.py
│   └── *.json
│
├── docs/                     # 文档（不发布）
│   ├── TECHNICAL.md          # 技术架构
│   ├── USAGE.md              # 使用指南
│   ├── NODE_DEVELOPMENT.md   # 节点开发
│   ├── EXTERNAL_NODES.md     # 外部节点注册
│   └── CONFIG_REFERENCE.md   # 配置参考
│
├── pyproject.toml            # 包配置
├── LICENSE                   # MIT License
├── CHANGELOG.md              # 变更日志
└── README.md
```

## 依赖

- Python >= 3.10
- langgraph >= 0.3
- langchain-core >= 0.3
- pydantic >= 2.0

## License

MIT
