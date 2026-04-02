# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.2] - 2025-04-02

### Added

- **LoopNode v3 - 循环迭代节点重构**：
  - 重新设计为基于子图的循环迭代节点
  - 子图 state 与主流程完全隔离（深拷贝输入）
  - 支持串行和并行执行
  - 支持 `max_iterations` 限制迭代次数
  - 支持 `on_error` 错误处理（raise/skip）
  - 支持 `emit_progress` 进度通知
  - 子图可引用主流程定义的 tools
  - 支持 `delay` 配置每轮延迟

- **LoopNode 配置参数**：
  - `input_key`: 主流程 state 中要遍历的数组路径
  - `results_key`: 所有迭代结果写入主流程 state 的路径
  - `subgraph_item_key`: 子图接收当前 item 的路径
  - `subgraph_meta_key`: 子图接收循环元信息的路径
  - `subgraph_result_path`: 从子图 state 提取结果的路径
  - `body_nodes` / `body_edges` / `body_entry_point`: 子图定义

### Documentation

- `CONFIG_REFERENCE.md` - 添加 LoopNode 完整配置参数
- `NODE_DEVELOPMENT.md` - 添加 LoopNode 节点开发指南
- `USAGE.md` - 添加 LoopNode 使用说明
- 示例 `examples/node/demo_loop.py` - 7 个完整示例

### Changed

- **依赖拆分优化**：按需安装，减小基础包体积
  - 核心依赖：langgraph, langchain-core, pydantic, requests, httpx
  - 可选 LLM：`openai`, `anthropic`, `google`
  - 可选向量存储：`chroma`, `faiss`
  - 安装方式：`pip install flux-agent[openai,rag]`

## [0.2.1] - 2025-04-01

### Added

- **LoopNode v3 - 循环迭代节点重构**：
  - 重新设计为基于子图的循环迭代节点
  - 子图 state 与主流程完全隔离（深拷贝输入）
  - 支持串行和并行执行
  - 支持 `max_iterations` 限制迭代次数
  - 支持 `on_error` 错误处理（raise/skip）
  - 支持 `emit_progress` 进度通知
  - 子图可引用主流程定义的 tools
  - 支持 `delay` 配置每轮延迟

- **LoopNode 配置参数**：
  - `input_key`: 主流程 state 中要遍历的数组路径
  - `results_key`: 所有迭代结果写入主流程 state 的路径
  - `subgraph_item_key`: 子图接收当前 item 的路径
  - `subgraph_meta_key`: 子图接收循环元信息的路径
  - `subgraph_result_path`: 从子图 state 提取结果的路径
  - `body_nodes` / `body_edges` / `body_entry_point`: 子图定义

### Documentation

- `CONFIG_REFERENCE.md` - 添加 LoopNode 完整配置参数
- `NODE_DEVELOPMENT.md` - 添加 LoopNode 节点开发指南
- `USAGE.md` - 添加 LoopNode 使用说明
- 示例 `examples/node/demo_loop.py` - 7 个完整示例

### Changed

- **依赖拆分优化**：按需安装，减小基础包体积
  - 核心依赖：langgraph, langchain-core, pydantic, requests, httpx
  - 可选 LLM：`openai`, `anthropic`, `google`
  - 可选向量存储：`chroma`, `faiss`
  - 安装方式：`pip install flux-agent[openai,rag]`

## [0.2.0] - 2025-03-27

### Added

- **RAG 模块**：全新的知识库管理模块
  - `KnowledgeBase` 类：创建、加载、检索能力
  - `KnowledgeBase.create()`：创建空白知识库
  - `KnowledgeBase.load()`：加载已有知识库
  - 支持 Chroma 和 File 两种向量存储
  - 支持 metadata 过滤检索
  - `get_by_metadata()` 方法：根据 metadata 获取文档

- **RagSearchNode**：独立的 RAG 检索节点
  - 支持 filter 过滤条件

- **LLMNode 多模态支持**：
  - 新增 `image_list` 配置：支持图片输入
  - 新增 `video_list` 配置：支持视频输入
  - 支持 URL、Base64、本地文件多种格式
  - 自动转换为模型所需的格式

- **WorkflowRunner 知识库集成**：
  - 新增 `knowledge_bases` 参数：传入知识库路径自动加载
  - LLMNode 和 RagSearchNode 可直接使用已加载的知识库

### Changed

- **RAG 模块重构**：
  - 简化为单一 `KnowledgeBase` 类
  - 移除全局注册表，改用参数传入
  - 删除冗余功能，只保留 Chroma 和 File 存储

- **依赖调整**：
  - 默认安装 `langchain-chroma` 和 `langchain-text-splitters`
  - `faiss-cpu` 移到 optional-dependencies

### Fixed

- 修复 Chroma get() 返回字典类型判断问题
- 修复 Chroma load() 缺少 collection_name 问题

## [0.1.1] - 2025-03-25

### Changed
- 包名从 auto-agent 改为 flux-agent
- 默认安装所有常用 LLM 依赖（OpenAI, Anthropic, Google, Community）

### Fixed
- 修复 license 字段格式问题

## [0.1.0] - 2025-03-24

### Added
- Initial release
- JSON-driven workflow configuration
- Built-in nodes: LLMNode, ConditionNode, TransformNode, ToolNode, HTTPRequestNode, LoopNode, ParallelNode, SubgraphNode, HumanInputNode
- Support for custom nodes via registry
- State management with LangGraph
- Streaming and async support
- Retry and cache policies
- Human-in-the-loop support
