# Flux-Agent 技术规范

## 核心技术栈

### 基础框架
- **Python** >= 3.10
- **LangGraph** >= 0.3 - 工作流编排核心
- **LangChain-core** >= 0.3 - LLM 抽象层
- **Pydantic** >= 2.0 - 数据验证和配置模型

### 网络与 HTTP
- **requests** >= 2.28.0
- **httpx** >= 0.27.0

### 可选依赖（按需安装）

#### LLM 提供商
- `openai`: langchain-openai >= 0.2.0
- `anthropic`: langchain-anthropic >= 0.3.0
- `google`: langchain-google-genai >= 2.0.0

#### 向量存储（RAG）
- `chroma`: langchain-chroma >= 0.1.0
- `faiss`: faiss-cpu >= 1.7.0
- `rag`: 完整 RAG 支持（chroma + text-splitters + faiss）

#### Agent 模式
- `agents`: deepagents >= 0.1.0

## 开发工具

### 代码质量
- **black** - 代码格式化（行宽 100）
- **ruff** - 快速 linting
- **mypy** - 类型检查

### 测试
- **pytest** >= 7.0
- **pytest-asyncio** >= 0.21.0 - 异步测试
- **pytest-cov** >= 4.0 - 覆盖率
- 要求：单元测试覆盖所有核心功能

### 构建发布
- **build** >= 1.0
- **twine** >= 4.0
- setuptools + wheel

## 技术约束

### LangGraph/LangChain 版本策略
- 参考 /langgraph-docs 和 /langchain-architecture
- 保持与官方版本兼容
- 重大版本更新需充分测试

### 性能考虑
- 节点执行异步支持
- 状态管理高效序列化
- 向量检索支持批量查询

### 扩展性设计
- 节点注册表支持动态注册
- 插件化入口点（entry-points）
- 延迟导入优化启动速度

## 架构决策

### 配置驱动
- JSON/YAML 作为工作流定义标准格式
- Pydantic 模型保证配置类型安全

### 模块化设计
- 核心功能精简，可选功能按需安装
- 每个节点类型独立模块
- RAG、Agents 作为独立子模块

### 状态管理
- 基于 LangGraph 的 StateGraph
- 支持状态持久化和断点恢复
- 人工介入节点支持工作流暂停
