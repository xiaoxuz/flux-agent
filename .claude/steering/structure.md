# Flux-Agent 项目结构规范

## 目录组织

```
flux-agent/
├── flux_agent/               # 主包目录
│   ├── core/                 # 核心引擎
│   │   ├── executor.py       # 工作流执行引擎
│   │   ├── parser.py         # 配置解析器
│   │   ├── registry.py       # 节点注册表
│   │   └── state.py          # 状态模型
│   │
│   ├── nodes/                # 节点模块
│   │   ├── base/             # 节点基类层
│   │   │   ├── node.py       # 节点基类
│   │   │   └── config.py     # 节点配置模型
│   │   │
│   │   ├── builtin/          # 内置节点实现
│   │   │   ├── control/      # 控制流节点
│   │   │   │   ├── condition.py   # ConditionNode
│   │   │   │   └── loop.py        # LoopNode
│   │   │   │
│   │   │   ├── llm/          # LLM 相关节点
│   │   │   │   ├── llm.py         # LLMNode
│   │   │   │   └── agent.py       # AgentNode
│   │   │   │
│   │   │   ├── rag/          # RAG 节点
│   │   │   │   └── search.py      # RagSearchNode
│   │   │   │
│   │   │   ├── transform/    # 数据转换节点
│   │   │   │   ├── transform.py   # TransformNode
│   │   │   │   └── json.py        # JsonNode
│   │   │   │
│   │   │   └── io/           # IO 节点
│   │   │       ├── http.py        # HTTPRequestNode
│   │   │       ├── tool.py        # ToolNode
│   │   │       ├── parallel.py    # ParallelNode
│   │   │       ├── subgraph.py    # SubgraphNode
│   │   │       └── human.py       # HumanInputNode
│   │   │
│   │   ├── business/         # 业务节点（用户扩展）
│   │   └── examples/         # 示例节点代码
│   │
│   ├── agents/               # 智能 Agent 模块
│   │   ├── base.py           # Agent 基类、输入输出定义
│   │   ├── registry.py       # Agent 注册中心
│   │   ├── factory.py        # create_agent() 工厂函数
│   │   ├── react_agent.py    # ReAct 模式实现
│   │   ├── deep_agent.py     # Deep 模式实现
│   │   ├── plan_execute_agent.py  # Plan-Execute 模式
│   │   ├── reflexion_agent.py     # Reflexion 模式
│   │   └── utils/            # Agent 工具函数
│   │
│   ├── rag/                  # RAG 模块
│   │   ├── knowledge_base.py    # 知识库管理
│   │   ├── document_loader.py   # 文档加载
│   │   ├── embeddings.py        # Embedding 封装
│   │   └── vector_store.py      # 向量存储
│   │
│   ├── tools/                # 工具模块
│   │   ├── web_fetch.py
│   │   └── generate_mermaid.py
│   │
│   └── utils/                # 通用工具
│       └── expression.py     # 表达式解析器
│
├── examples/                 # 使用示例
│   ├── *.json                # 工作流配置示例
│   ├── demo_*.py             # Python 示例脚本
│   └── rag/                  # RAG 专项示例
│
├── docs/                     # 文档
│   ├── USAGE.md             # 使用指南
│   ├── AGENTS.md            # Agent 模块文档
│   ├── RAG.md               # RAG 模块文档
│   ├── CONFIG_REFERENCE.md  # 配置参考
│   ├── NODE_DEVELOPMENT.md  # 节点开发指南
│   ├── TECHNICAL.md         # 技术架构
│   └── DEVELOPMENT.md       # 开发流程
│
├── tests/                    # 测试目录
├── pyproject.toml           # 包配置
├── CHANGELOG.md             # 变更日志
└── README.md                # 项目说明
```

## 代码规范

### 文件命名
- Python 模块：snake_case.py
- 类名：PascalCase
- 函数/变量：snake_case
- 常量：UPPER_SNAKE_CASE

### 导入规范
- 延迟导入：RAG、Agents 等重型模块使用延迟导入
- 类型导入：使用 `from __future__ import annotations`

### 类型注解
- 所有公共 API 必须有类型注解
- 复杂类型使用 TypeAlias
- Pydantic 模型用于配置验证

## 新增功能规范

### 新增节点
1. 在 `flux_agent/nodes/builtin/` 对应分类下创建模块
2. 继承 `BaseNode`，实现 `execute` 方法
3. 在 `__init__.py` 中导出并注册
4. **必须提供**：对应的示例配置到 `examples/`
5. **必须提供**：文档更新到 `docs/` 相关文件

### 新增 Agent 模式
1. 在 `flux_agent/agents/` 创建 `*_agent.py`
2. 继承 `BaseAgent`
3. 在 `factory.py` 注册
4. 更新 `AGENTS.md` 文档

### 文档要求
- README.md：更新功能列表和快速开始
- 对应专项文档：详细使用说明
- examples/：可运行的示例代码

## 测试要求

### 单元测试
- 测试文件：`tests/test_*.py`
- 覆盖率：核心功能必须覆盖
- 使用 pytest-asyncio 测试异步代码

### 集成测试
- 工作流端到端测试
- 节点组合测试
- 配置解析测试

## 发布检查清单
- [ ] 版本号更新（pyproject.toml + __init__.py）
- [ ] CHANGELOG.md 更新
- [ ] 测试通过
- [ ] 文档同步
- [ ] 示例可运行
