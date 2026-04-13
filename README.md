# Flux-Agent

面向生产环境的 LLM Agent 与 Workflow 编排框架。通过 JSON 配置或纯代码即可构建多 Agent 协作流，内置四种 Agent 模式、Skill 插件系统、MCP 协议接入、RAG 知识库，以及十余种开箱即用的工作流节点。

## 核心特性

- **JSON 配置驱动** - 无需编写代码，通过 JSON 配置即可定义复杂工作流
- **内置通用节点** - LLM 调用、条件分支、工具调用、HTTP 请求等开箱即用
- **多模式 Agent** - ReAct / Deep / Plan-Execute / Reflexion 四种模式，统一接口
- **Skill 系统** - 模块化扩展：领域指令注入、脚本执行、参考资料按需加载
- **MCP 协议接入** - 支持连接外部 MCP Server，自动将 MCP 工具注入 Agent 工具集
- **RAG 能力** - 知识库管理、向量检索、检索增强生成
- **多模态支持** - 支持图片、视频输入
- **可插拔扩展** - 用户可按规范开发自定义节点，注册即可使用
- **并行执行** - 原生支持 map-reduce、并行处理等模式
- **人工介入** - 支持工作流暂停、人工审核、断点恢复
- **子图嵌套** - 支持将工作流作为子图嵌入其他工作流

## 快速开始

### 安装

**基础安装（仅核心）：**
```bash
pip install flux-agent
```

**按需安装额外依赖：**

```bash
# OpenAI LLM 支持
pip install flux-agent[openai]

# Anthropic LLM 支持
pip install flux-agent[anthropic]

# Google LLM 支持
pip install flux-agent[google]

# 多个 LLM 提供商
pip install flux-agent[openai,anthropic]

# RAG 能力（向量存储）
pip install flux-agent[rag]

# 完整安装（所有功能）
pip install flux-agent[all]
```

| 安装选项 | 包含内容 |
|---------|---------|
| `openai` | OpenAI GPT 系列模型 |
| `anthropic` | Anthropic Claude 系列模型 |
| `google` | Google Gemini 系列模型 |
| `chroma` | Chroma 向量数据库 |
| `faiss` | FAISS 向量检索 |
| `rag` | 完整 RAG 支持 (chroma + text-splitters + faiss) |
| `llms` | 所有 LLM 提供商 |
| `agents` | Deep Agent 模式 |
| `mcp` | MCP 协议支持 |
| `all` | 全部功能 |

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

## 内置节点

| 节点类型 | 功能 | 说明 |
|---------|------|------|
| `LLMNode` | LLM 调用 | 支持 OpenAI、Anthropic、Gemini，多模态输入 |
| `ConditionNode` | 条件分支 | if/else、switch 分支路由 |
| `ToolNode` | 工具调用 | 执行预定义的工具/函数 |
| `TransformNode` | 数据转换 | set/get/filter/map 等操作 |
| `JsonNode` | JSON 编解码 | encode/decode JSON 数据 |
| `LoopNode` | 循环执行 | for/while 循环控制 |
| `ParallelNode` | 并行执行 | map-reduce 模式 |
| `HTTPRequestNode` | HTTP 调用 | REST API 调用 |
| `SubgraphNode` | 子图嵌套 | 嵌入其他工作流 |
| `HumanInputNode` | 人工介入 | 暂停等待人工输入 |
| `RagSearchNode` | RAG 检索 | 知识库向量检索 |
| `AgentNode` | 智能Agent | 在工作流中调用多模式Agent |

## 智能 Agent 模块

开箱即用的多模式 Agent 能力，所有模式输出格式一致：

```python
from langchain_openai import ChatOpenAI
from flux_agent.agents import create_agent

llm = ChatOpenAI(model="gpt-4o")

# ReAct 模式 - 简单问答
agent = create_agent("react", llm=llm, tools=[search])
result = agent.invoke("今天天气怎么样？")

# Plan-Execute 模式 - 复杂任务
agent = create_agent("plan_execute", llm=llm, enable_replan=True)
result = agent.invoke("分析市场趋势并给出建议")

# Reflexion 模式 - 自我反思改进
agent = create_agent("reflexion", llm=llm, max_iterations=3)
result = agent.invoke("写一个快速排序算法")

# 统一输出
print(result.answer)    # 最终回答
print(result.status)    # 执行状态
print(result.steps)     # 执行过程
```

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| `react` | ReAct 模式 | 简单问答、工具调用 |
| `deep` | Deep 模式 | 复杂任务、代码生成 |
| `plan_execute` | 先规划再执行 | 多步骤任务 |
| `reflexion` | 自我反思改进 | 高质量输出 |

详细文档: [AGENTS.md](docs/AGENTS.md)

## Skill 系统

为 Agent 注入领域知识、执行脚本、引用资料的模块化扩展机制：

```
skills/
└── code-review/
    ├── SKILL.md          # 主指令（注入 system prompt）
    ├── scripts/          # 可执行脚本（输出作为 observation）
    │   └── check.py
    └── references/       # 参考资料（按需加载）
        └── style-guide.md
```

### 基本用法

```python
from flux_agent.agents import create_agent, SkillLoader, AgentInput

# 加载所有 Skill
loader = SkillLoader("skills")
agent = create_agent("react", llm=llm, skills=loader.load_all())

# Agent 自主选择 — Skill 目录摘要注入 system prompt，LLM 自行判断
result = agent.invoke("帮我检查一下代码质量")

# 强制激活指定 Skill
result = agent.invoke(AgentInput(
    query="检查这段代码",
    active_skills=["code-review"],
))
```

### 三层渐进式加载

| 层级 | 内容 | 时机 |
|------|------|------|
| **目录摘要** | name + description (~100 token/skill) | 始终注入 system prompt |
| **完整指令** | SKILL.md 正文 | Skill 被激活后注入 |
| **资源加载** | scripts 执行 / references 读取 | Agent 按需触发 |

### 脚本执行

Skill 脚本输出作为 observation 返回，不消耗 context：

```python
from flux_agent.agents import SkillExecutor

skill = loader.load("code-review")
output = SkillExecutor.execute_script(skill, "check.py", args=["main.py"])
```

详细文档: [SKILLS.md](docs/SKILLS.md)

## MCP 协议接入

通过 MCP（Model Context Protocol）连接外部工具服务器，所有 Agent 模式均支持：

```python
from flux_agent.agents import create_agent

agent = create_agent(
    "react",
    llm=llm,
    mcp_servers=[
        {
            "name": "my-mcp-server",
            "transport": "streamable_http",
            "url": "http://localhost:8080/mcp",
            "headers": {"Authorization": "Bearer xxx"},
            "tool_name_prefix": "srv_",
        }
    ],
)
```

MCP 工具会自动注册到 Agent 工具集，与其他工具无缝协作。示例：
- `examples/agents/demo_mcp_agent.py` — Agent + MCP 集成演示
- `examples/node/demo_mcp.py` — MCP 工作流配置

详细文档: [SKILLS.md](docs/SKILLS.md)

## 文档

- [使用文档](docs/USAGE.md) - 快速开始、API 参考、完整示例
- [智能 Agent 模块](docs/AGENTS.md) - 多模式 Agent 开箱即用
- [Skill 系统](docs/SKILLS.md) - Skill 扩展机制完整指南
- [RAG 模块](docs/RAG.md) - 知识库创建、检索、过滤
- [配置参考](docs/CONFIG_REFERENCE.md) - JSON 配置完整说明
- [节点开发指南](docs/NODE_DEVELOPMENT.md) - 自定义节点开发规范
- [开发指南](docs/DEVELOPMENT.md) - 开发、测试、发布流程
- [技术架构](docs/TECHNICAL.md) - 架构设计、核心概念

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
│   ├── agents/               # 智能 Agent 模块
│   │   ├── base.py           # 基类、输入输出定义
│   │   ├── skill.py          # Skill 模型、加载器、注册中心、执行器
│   │   ├── registry.py       # Agent 注册中心
│   │   ├── factory.py        # create_agent() 工厂
│   │   ├── react_agent.py    # ReAct 模式
│   │   ├── deep_agent.py     # Deep 模式
│   │   ├── plan_execute_agent.py  # Plan-Execute 模式
│   │   └── reflexion_agent.py     # Reflexion 模式
│   │
│   ├── utils/                # 工具函数
│   │   └── expression.py     # 表达式解析
│   │
│   └── tools/                # 工具模块
│
├── examples/                 # 示例脚本
│   ├── agents/              # Agent 示例
│   │   ├── demo_agents.py   # 4 种 Agent 模式演示
│   │   └── demo_skills.py   # Skill 系统演示
│   ├── rag/                 # RAG 示例
│   └── node/                # 节点示例
│
├── docs/                     # 文档
│   ├── AGENTS.md            # Agent 模块指南
│   ├── SKILLS.md            # Skill 系统指南
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
- pydantic >= 2.0

可选依赖：
- `langchain-openai` - OpenAI 模型
- `langchain-anthropic` - Anthropic 模型
- `langchain-google-genai` - Google 模型
- `langchain-chroma` - Chroma 向量存储
- `faiss-cpu` - FAISS 向量存储
- `langchain-mcp-adapters` / `mcp` - MCP 协议支持

## License

MIT
