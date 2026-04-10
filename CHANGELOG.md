# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.6] - 2025-04-08

### Added

- **Skill 系统 — Agent 模块化扩展机制**：
  - `Skill` 数据模型：支持 `scripts/`、`references/`、`assets/` 目录结构
  - `SkillLoader`：从 `skills/{name}/` 目录加载 Skill，支持 YAML frontmatter 解析（PyYAML + 降级），mtime 缓存失效
  - `SkillRegistry`：Skill 注册中心，管理全集、生成目录摘要（`build_skill_catalog_prompt()`）
  - `SkillExecutor`：执行 Skill 关联脚本（`.py`/`.sh`/`.js`），subprocess 隔离，支持超时和环境变量注入
  - `build_skill_tools()`：生成 3 个 LangChain Tool（`activate_skill`、`run_skill_script`、`load_skill_reference`），实现三层渐进式加载闭环
  - Frontmatter 扩展字段：`disable-model-invocation`、`user-invocable`、`allowed-tools`、`argument-hint`
  - 纯代码方式创建 Skill（无需目录，直接传 `Skill(...)` 对象）

- **Agent Skill 集成**：
  - 所有 4 种 Agent 模式（ReAct/Deep/PlanExecute/Reflexion）均支持 Skill
  - `BaseAgent` 新增：`_get_skill_tools()`、`_get_all_tools()`、`_resolve_active_skills()`、`_build_system_prompt_with_skills()`
  - 三种激活方式：强制激活（`active_skills`）、显式引用（query 中提及）、Agent 自主选择（LLM 通过 tool_call）
  - `AgentInput` 新增字段：`skills`（全集）、`active_skills`（强制激活列表）、`auto_select_skills`

- **Token Usage 全局 + 节点级追踪**：
  - state 顶层新增 `_token_usage` 字段，自定义 `merge_token_usage` reducer
  - 全局汇总：自动累加所有 LLMNode 的 `input_tokens`、`output_tokens`、`total_tokens`
  - 节点明细：`details` 列表记录每个节点每次执行的独立 token 用量
  - 多个 LLMNode 不再互相覆盖，reducer 自动汇总累加 + 明细追加

- **LLMNode 超时与重试配置**：
  - `timeout`: 请求超时时间（秒），默认 300.0（5分钟）
  - `max_retries`: 最大重试次数，默认 1
  - 参数直接传递给 ChatOpenAI，控制底层 httpx 客户端行为

- **文档**：
  - `docs/SKILLS.md` — Skill 系统完整文档（目录结构、API、代码级调用链流程图）
  - `docs/AGENTS.md` — 新增 5 张 Mermaid 架构流程图（统一调用流程、四模式对比、Skill 三层加载、Tool 融合、构建全景）
  - `examples/agents/demo_skills.py` — Skill 系统演示（加载/注册/脚本执行/引用加载/Agent 集成）

### Changed

- **Skill 选择机制重构**：移除关键词匹配（`SkillSelector.select_relevant_skills`），改为 LLM 驱动的 Tool-based 选择
- **`SkillSelector`**：标记为 deprecated，仅保留 `parse_skill_reference()` 向后兼容
- **LLMNode**：移除 `token_usage_key` 配置字段，token 用量改为写入 state 顶层 `_token_usage`
- **文档更新**：
  - CONFIG_REFERENCE.md 移除 token_usage_key，说明自动追踪机制
  - USAGE.md 新增 Token Usage 追踪章节
  - README.md 更新项目结构、新增 Skill 系统章节

### Fixed

- **`run_skill_script` 参数冲突**：`args` 与 Pydantic v2 保留字冲突，重命名为 `script_args`

## [0.2.5] - 2025-04-07

### Added

- **智能 Agent 模块（flux_agent.agents）**：
  - `create_agent()` 统一工厂函数，支持多种 Agent 模式
  - `ReActAgent`: ReAct 模式，包装 langgraph.prebuilt.create_react_agent
  - `DeepAgent`: Deep 模式，包装 deepagents（可选依赖，未安装时降级到 ReAct）
  - `PlanExecuteAgent`: 先规划再执行，适合复杂多步任务
  - `ReflexionAgent`: 自我反思改进，适合代码生成、写作
  - 统一的 `AgentInput`/`AgentOutput` 接口，所有模式输出格式一致
  - `AgentRegistry` 注册中心，支持自定义 Agent 模式扩展
  - `AgentCallback` 回调系统，支持执行过程监控

- **AgentNode 节点**：
  - 在工作流中调用智能 Agent 模块
  - 支持 react/deep/plan_execute/reflexion 四种模式
  - 可配置 tools、system_prompt 等

- **可选依赖**：
  - `pip install flux-agent[agents]` 安装 Deep Agent 支持

- **示例文件**：
  - `examples/agents/demo_agents.py` - 4 种模式演示
  - `examples/tools.py` - 示例工具函数
  - `examples/workflow/agent_demo.json` - AgentNode 工作流 JSON 配置
  - `examples/workflow/run_agent_demo.py` - AgentNode 工作流运行示例

- **文档**：
  - `docs/AGENTS.md` - 智能 Agent 模块完整文档
  - `docs/CONFIG_REFERENCE.md` - 添加 AgentNode 配置说明（3.10 节）

## [0.2.4] - 2025-04-03

### Added

- **LLMNode Structured Output 支持**：
  - `json_schema`: JSON Schema 字典约束输出格式
  - `json_schema_pydantic`: Pydantic 模型路径
  - `json_schema_typed_dict`: TypedDict 类路径
  - `include_raw`: 是否包含原始响应
  - 自动添加 title 字段支持 OpenAI JSON Schema

- **示例文件**：`examples/node/demo_llm_json_schema.py` - 5 个完整示例

### Fixed

- **变量插值 JSON 解析**：
  - 修复 `response_format: {type: "json_object"}` 返回字符串未解析的问题
  - 现在会自动将 JSON 字符串解析为 dict

- **LLMNode tools + json_schema 兼容**：
  - 修复同时配置 tools 和 json_schema 时 bind_tools 失败的问题
  - 调整执行顺序：Tool 循环结束后再做 structured output 格式化
  - `_get_llm()` 移除 with_structured_output，移到 execute 中处理
  - `_apply_structured_output(llm)` 改为纯函数

### Changed

- **文档更新**：
  - CONFIG_REFERENCE.md 添加 json_schema 参数说明
  - USAGE.md 添加 Structured Output 使用示例

## [0.2.3] - 2025-04-03

### Added

- **JsonNode - JSON 编解码节点**：
  - `encode`: Python 对象 → JSON 字符串
  - `decode`: JSON 字符串 → Python 对象
  - 支持 `indent` 缩进控制
  - 支持 `ensure_ascii` 中文编码控制
  - 支持 `error_on_fail` 错误处理

- **示例文件**：`examples/node/demo_json.py` - 6 个完整示例

### Fixed

- **变量插值保留原始类型**：
  - 修复 `_interpolate_dict` 和 `_interpolate_value` 将 list/dict 转为字符串的问题
  - 纯变量引用 `${data.items}` 现在会保留原始类型
  - 新增 `_try_get_raw_value` 方法统一处理

- **RAG 模块延迟导入**：
  - `langchain-text-splitters` 改为延迟导入
  - 默认安装不会因缺少该依赖而报错
  - 使用时提示安装 `pip install 'flux-agent[rag]'`

### Documentation

- `CONFIG_REFERENCE.md` - 添加 JsonNode 配置说明
- `USAGE.md` - 添加 JsonNode 使用示例
- `README.md` - 内置节点表格添加 JsonNode

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
