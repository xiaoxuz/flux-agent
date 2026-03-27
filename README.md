# Flux-Agent

基于 LangGraph + LLM 的通用 Agent 编排框架。通过 JSON 配置文件即可启动多 Agent Node 工作流，支持复杂的自动化流程编排。

## 核心特性

- **JSON 配置驱动** - 无需编写代码，通过 JSON 配置即可定义复杂工作流
- **内置通用节点** - LLM 调用、条件分支、工具调用、HTTP 请求等开箱即用
- **RAG 能力** - 知识库管理、向量检索、检索增强生成
- **多模态支持** - 支持图片、视频输入
- **可插拔扩展** - 用户可按规范开发自定义节点，注册即可使用
- **并行执行** - 原生支持 map-reduce、并行处理等模式
- **人工介入** - 支持工作流暂停、人工审核、断点恢复
- **子图嵌套** - 支持将工作流作为子图嵌入其他工作流

## 快速开始

### 安装

```bash
pip install flux-agent
```

### RAG 知识库创建

```python
from flux_agent.rag import (
    KnowledgeBase,
    KnowledgeBaseConfig,
    KnowledgeChunkConfig,
    KnowledgeEmbeddingConfig,
)

config = KnowledgeBaseConfig(
    name="my_docs",
    persist_directory="./kb_data/my_docs",
    embedding_config=KnowledgeEmbeddingConfig(
        model="text-embedding-3-small",
    )
)

kb = KnowledgeBase.create(name="my_docs", config=config)
kb.add_texts(["知识库内容..."])
kb.generate()
```

### 工作流执行

```python
from flux_agent import WorkflowRunner

runner = WorkflowRunner("workflow.json")
result = runner.invoke({"data": {"input": "你好"}})
print(result)
```

### JSON 配置示例

```json
{
  "nodes": [
    {
      "id": "llm",
      "type": "llm",
      "config": {
        "model_name": "gpt-4o",
        "system_prompt": "你是一个助手",
        "user_prompt": "${data.input}"
      }
    }
  ],
  "edges": [
    {"from": "START", "to": "llm"},
    {"from": "llm", "to": "END"}
  ]
}
```

## 内置节点

| 节点类型 | 功能 | 说明 |
|---------|------|------|
| `LLMNode` | LLM 调用 | 支持 OpenAI、Anthropic、Gemini，多模态输入 |
| `ConditionNode` | 条件分支 | if/else、switch 分支路由 |
| `ToolNode` | 工具调用 | 执行预定义的工具/函数 |
| `TransformNode` | 数据转换 | set/get/filter/map 等操作 |
| `LoopNode` | 循环执行 | for/while 循环控制 |
| `ParallelNode` | 并行执行 | map-reduce 模式 |
| `HTTPRequestNode` | HTTP 调用 | REST API 调用 |
| `SubgraphNode` | 子图嵌套 | 嵌入其他工作流 |
| `HumanInputNode` | 人工介入 | 暂停等待人工输入 |
| `RagSearchNode` | RAG 检索 | 知识库向量检索 |

## 文档

- [使用文档](./docs/USAGE.md) - 快速开始、API 参考、完整示例
- [RAG 模块](./docs/RAG.md) - 知识库创建、检索、过滤
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
│   │   ├── executor.py       # 执行引擎
│   │   ├── parser.py         # 配置解析器
│   │   ├── registry.py       # 节点注册表
│   │   └── state.py          # 状态模型
│   │
│   ├── nodes/                # 节点模块
│   │   ├── base/             # 基类层
│   │   │   ├── node.py       # 节点基类
│   │   │   └── config.py     # 配置模型
│   │   ├── builtin/          # 内置节点
│   │   │   ├── control/      # condition, loop
│   │   │   ├── llm/          # LLM 调用（支持多模态）
│   │   │   ├── rag/          # RagSearchNode
│   │   │   ├── transform/    # 数据转换
│   │   │   └── io/           # http, tool, parallel, subgraph, human
│   │   └── ...
│   │
│   ├── rag/                  # RAG 模块
│   │   ├── knowledge_base.py # 知识库管理
│   │   ├── document_loader.py # 文档加载
│   │   ├── embeddings.py    # Embedding
│   │   └── vector_store.py  # 向量存储
│   │
│   ├── utils/                # 工具函数
│   │   └── expression.py     # 表达式解析
│   │
│   └── tools/                # 工具模块
│
├── examples/                 # 示例脚本
│   ├── rag/                 # RAG 示例
│   └── demo_*.py
│
├── docs/                     # 文档
│   ├── RAG.md               # RAG 模块指南
│   ├── USAGE.md             # 使用指南
│   ├── TECHNICAL.md         # 技术架构
│   └── ...
│
├── pyproject.toml            # 包配置
├── CHANGELOG.md              # 变更日志
└── README.md
```

## 依赖

- Python >= 3.10
- langgraph >= 0.3
- langchain-core >= 0.3
- langchain-chroma >= 0.1
- pydantic >= 2.0

可选依赖：
- `faiss-cpu` - FAISS 向量存储

## License

MIT
