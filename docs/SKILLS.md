# Flux-Agent Skill 系统

> 为 Agent 注入领域知识、执行脚本、引用资料的模块化扩展机制

## 概述

Skill 是一种结构化的扩展单元，让 Agent 能够：

1. **接收领域指令** — SKILL.md 正文注入 system prompt，指导 Agent 行为
2. **执行脚本** — 运行 `scripts/` 目录下的脚本，输出作为 observation 返回（不消耗 context）
3. **引用资料** — 按需加载 `references/` 目录下的文档，避免一股脑塞进 prompt

设计对标 [Agent Skills 开放标准](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)，支持渐进式加载（Progressive Disclosure）。

## 目录结构

```
skills/
└── my-skill/
    ├── SKILL.md          # 主指令文件（必需）
    ├── scripts/          # 可执行脚本（可选）
    │   ├── helper.py
    │   └── check.sh
    ├── references/       # 参考资料（可选，按需加载）
    │   ├── api-doc.md
    │   └── examples.md
    └── assets/           # 模板、资源文件（可选）
        └── template.md
```

## SKILL.md 格式

```markdown
---
name: my-skill
description: 用于数据分析任务的工作流指导
disable-model-invocation: false
user-invocable: true
allowed-tools: [python_repl, file_read]
argument-hint: 传入数据文件路径
---

# My Skill

## Instructions
1. 理解用户的数据分析需求
2. 加载并检查数据
3. 执行分析并输出结果

## Examples
用户: 帮我分析销售数据
Agent: [按照工作流执行...]
```

### Frontmatter 字段

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `name` | str | 目录名 | Skill 名称 |
| `description` | str | `""` | 描述（用于 LLM 选择判断） |
| `disable-model-invocation` | bool | `false` | 禁止 Agent 自动触发此 Skill |
| `user-invocable` | bool | `true` | 是否可被用户显式调用 |
| `allowed-tools` | list | `[]` | 预授权工具列表 |
| `argument-hint` | str | `""` | 参数使用提示 |

## 快速开始

### 1. 创建 Skill

```bash
mkdir -p skills/code-review
```

```markdown
# skills/code-review/SKILL.md
---
name: code-review
description: 代码审查，检查代码质量和潜在问题
---

# Code Review Skill

## Instructions
1. 仔细阅读提交的代码
2. 检查：命名规范、错误处理、安全漏洞、性能问题
3. 给出具体的改进建议和示例代码
```

### 2. 使用 Skill

```python
from langchain_openai import ChatOpenAI
from flux_agent.agents import create_agent, SkillLoader

llm = ChatOpenAI(model="gpt-4o")
loader = SkillLoader("skills")

agent = create_agent(
    "react",
    llm=llm,
    skills=loader.load_all(),
)

# Agent 会在 system prompt 中看到 Skill 目录，自主决定是否激活
result = agent.invoke("帮我检查这段 Python 代码的质量")
```

## Skill 选择机制

### 三层渐进式加载

```
┌─────────────────────────────────────────┐
│  第一层：Skill 目录摘要                    │
│  (~100 token/skill)                      │
│  所有 Skill 的 name + description          │
│  始终注入 system prompt                    │
├─────────────────────────────────────────┤
│  第二层：Skill 完整指令                    │
│  被激活 Skill 的 SKILL.md 正文             │
│  激活后注入 context                        │
├─────────────────────────────────────────┤
│  第三层：References / Scripts             │
│  按需加载参考资料、执行脚本                  │
│  仅在 Agent 需要时读取/执行                 │
└─────────────────────────────────────────┘
```

### 激活方式

**方式一：强制激活**（通过 `active_skills` 指定）

```python
from flux_agent.agents import AgentInput

result = agent.invoke(AgentInput(
    query="检查这个函数",
    active_skills=["code-review"],  # 强制激活指定 skill
))
```

**方式二：显式引用**（在 query 中提及）

```python
result = agent.invoke("使用 code-review 技能，检查这段代码")
```

**方式三：Agent 自主选择**

当 `auto_select_skills=True`（默认）时，所有可用 Skill 的目录摘要会注入 system prompt，Agent 根据用户请求自主判断是否需要激活某个 Skill。

```python
# Agent 看到 Skill 目录后自行判断
result = agent.invoke("帮我分析这段代码有什么问题")
```

## 脚本执行

Skill 可以关联脚本，脚本输出作为 observation 返回给 Agent，**不将脚本源码加载进 context**。

### 创建脚本

```bash
mkdir -p skills/my-skill/scripts
```

```python
# skills/my-skill/scripts/analyze.py
import sys
import json

data = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
print(f"分析结果: 共 {len(data)} 条记录")
```

### 执行脚本

```python
from flux_agent.agents import SkillExecutor

skill = loader.load("my-skill")

# 执行脚本
output = SkillExecutor.execute_script(
    skill=skill,
    script_name="analyze.py",
    args=['{"a":1,"b":2}'],
    timeout=30,
)
print(output)  # "分析结果: 共 2 条记录"
```

脚本执行时自动设置环境变量：

| 环境变量 | 说明 |
|----------|------|
| `SKILL_NAME` | 当前 Skill 名称 |
| `SKILL_DIR` | Skill 根目录路径 |

支持的脚本类型：`.py`（Python）、`.sh`（Bash）、`.js`（Node.js）、其他（直接执行）。

## References 按需加载

参考资料不会预加载，只在 Agent 需要时才读取。

```python
# 加载特定 reference
content = loader.load_reference(skill, "api-doc.md")
print(content)
```

SKILL.md 中可以引用：

```markdown
## 详细 API 文档
参见 [API 文档](references/api-doc.md)（按需加载）。
```

## SkillRegistry

`SkillRegistry` 是 Skill 的注册中心，管理 Skill 全集并生成目录摘要。

```python
from flux_agent.agents import SkillRegistry, SkillLoader

loader = SkillLoader("skills")
registry = SkillRegistry(loader)

# 从目录加载并注册所有 Skill
registry.load_and_register_all()

# 按名称获取
skill = registry.get("code-review")

# 获取所有可用 Skill
all_skills = registry.all_skills

# 获取可被 Agent 自动触发的 Skill
invocable = registry.invocable_skills

# 生成目录摘要（用于注入 system prompt）
catalog = registry.build_skill_catalog_prompt()
print(catalog)

# 生成已激活 Skill 的完整 prompt
prompt = registry.build_active_skills_prompt(
    active_skills=[skill],
    base_prompt="你是一个有帮助的助手。",
)
```

## AgentInput Skill 字段

```python
from flux_agent.agents import AgentInput

input = AgentInput(
    query="你的问题",
    skills=[...],                # 可用的 skills 全集
    active_skills=["skill-a"],   # 强制激活的 skill 名称列表
    auto_select_skills=True,     # 是否由 Agent 自主选择（默认 True）
)
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `skills` | `List[Skill]` | 可用的 Skill 全集 |
| `active_skills` | `List[str]` | 强制激活的 Skill 名称列表，优先级最高 |
| `auto_select_skills` | `bool` | 是否注入 Skill 目录让 Agent 自主选择 |

## API 参考

### Skill

```python
@dataclass
class Skill:
    name: str                    # 名称
    description: str             # 描述
    content: str                 # SKILL.md 正文
    source: str                  # 来源路径
    metadata: Dict               # frontmatter 其他字段
    scripts: Dict[str, str]      # 脚本映射 {文件名: 路径}
    references: Dict[str, str]   # 参考资料映射
    assets: Dict[str, str]       # 资源文件映射
    disable_model_invocation: bool  # 禁止自动触发
    user_invocable: bool         # 可被用户调用
    allowed_tools: List[str]     # 预授权工具
    argument_hint: str           # 参数提示
```

### SkillLoader

| 方法 | 说明 |
|------|------|
| `list_skills()` | 列出所有可用 Skill 名称 |
| `load(name)` | 加载指定 Skill（带缓存失效检测） |
| `load_all()` | 加载所有 Skill |
| `load_reference(skill, ref_name)` | 按需加载 reference 文件 |
| `load_asset(skill, asset_name)` | 按需加载 asset 文件 |

### SkillRegistry

| 方法 | 说明 |
|------|------|
| `register(skill)` | 注册 Skill |
| `register_all(skills)` | 批量注册 |
| `load_and_register_all()` | 从 loader 加载并注册全部 |
| `get(name)` | 按名称获取 Skill |
| `all_skills` | 所有已注册 Skill |
| `invocable_skills` | 可自动触发的 Skill |
| `build_skill_catalog_prompt()` | 生成目录摘要 |
| `build_active_skills_prompt(skills, base)` | 生成已激活 Skill prompt |

### SkillExecutor

| 方法 | 说明 |
|------|------|
| `execute_script(skill, script_name, args, timeout, env)` | 执行脚本，返回 stdout |

## 代码级调用链流程图

Skill 在 Agent 中的完整生命周期，从初始化到运行时 LLM 自主调用，精确到文件和函数。

### 阶段一：构建阶段（Build Phase）

用户创建 Agent 实例时触发的调用链：

```
用户代码
│
│  agent = create_agent("react", llm=llm, skills=loader.load_all())
│
├─ factory.py : create_agent()
│   └─ 根据 mode 选择 Agent 类，传入 skills 参数
│
├─ react_agent.py : ReactAgent.__init__()
│   └─ 调用 super().__init__(skills=skills, ...)
│
├─ base.py : BaseAgent.__init__()                    ← 核心初始化
│   │
│   ├─ skill.py : SkillLoader.__init__(skills_dir)   ← 创建加载器
│   │
│   ├─ skill.py : SkillRegistry.__init__(loader)     ← 创建注册中心
│   │
│   ├─ skill.py : SkillRegistry.register_all(skills) ← 注册传入的 skills
│   │   └─ 遍历 skills，逐个调用 register(skill)
│   │       → self._skills[skill.name] = skill
│   │
│   └─ 调用子类 _build()
│
├─ react_agent.py : ReactAgent._build()              ← 构建内部 agent
│   │
│   ├─ base.py : BaseAgent._get_all_tools()          ← 合并所有 tools
│   │   │
│   │   ├─ self.tools                                 (用户注册的工具)
│   │   │
│   │   └─ base.py : BaseAgent._get_skill_tools()    ← 生成 Skill 工具
│   │       │
│   │       ├─ 检查 self._skill_registry.invocable_skills
│   │       │   └─ skill.py : SkillRegistry.invocable_skills
│   │       │       → 过滤 disable_model_invocation=False 的 skills
│   │       │
│   │       └─ skill.py : build_skill_tools(registry, loader)
│   │           → 生成 3 个 LangChain @tool:
│   │             • activate_skill      — 激活 skill，返回完整 content
│   │             • run_skill_script    — 执行 skill 脚本
│   │             • load_skill_reference — 按需加载参考资料
│   │
│   ├─ base.py : BaseAgent._build_system_prompt_with_skills()
│   │   │
│   │   ├─ skill.py : SkillRegistry.build_skill_catalog_prompt()
│   │   │   → 生成 Skill 目录摘要（~100 token/skill）
│   │   │   → 包含指令："you MUST call activate_skill tool..."
│   │   │
│   │   └─ 拼接: base_prompt + catalog 摘要
│   │
│   └─ langgraph.prebuilt.create_react_agent(
│       model=llm,
│       tools=[用户tools + activate_skill + run_skill_script + load_skill_reference],
│       prompt=base_prompt + skill_catalog,
│   )
│
└─ ✅ Agent 构建完成
    LLM 的 system prompt 中已包含 Skill 目录摘要
    LLM 可调用的 tools 中已包含 3 个 Skill Tool
```

### 阶段二：调用阶段（Invoke Phase）

用户调用 `agent.invoke()` 时的执行流程：

```
用户代码
│
│  result = agent.invoke("帮我检查这段代码的质量")
│
├─ base.py : BaseAgent.invoke(input)
│   │
│   ├─ base.py : BaseAgent._normalize_input(input)
│   │   → str/dict/AgentInput 统一转为 AgentInput
│   │
│   └─ 调用子类 _run(agent_input)
│
├─ react_agent.py : ReactAgent._run(agent_input)
│   │
│   ├─ base.py : AgentInput.to_messages()
│   │   → 转换为 [HumanMessage("帮我检查这段代码的质量")]
│   │
│   ├─ base.py : BaseAgent._resolve_active_skills(agent_input)
│   │   │
│   │   ├─ 优先级1: agent_input.active_skills
│   │   │   → 如果指定了，从 registry 获取并返回
│   │   │
│   │   ├─ 优先级2: SkillSelector.parse_skill_reference(query)
│   │   │   → 匹配 "使用 xxx 技能" 模式
│   │   │
│   │   └─ 优先级3: 返回空列表（由 LLM 通过 tool_call 自行选择）
│   │
│   ├─ [如果有强制 skills]
│   │   → 拼接 SystemMessage(content="# Active Skills\n{skill.content}")
│   │   → 插入 messages 最前面
│   │
│   ├─ react_agent.py : ReactAgent._rebuild_agent_if_needed()
│   │   → 检查 skill 注册表是否有变化，有变化则重建
│   │
│   └─ langgraph agent.invoke({"messages": messages})
│       → LLM 开始推理循环...
```

### 阶段三：LLM 自主选择 Skill（Tool-Driven 闭环）

LLM 在推理循环中通过 tool_call 自主完成三层渐进式加载：

```
LLM 推理循环（ReAct Loop）
│
│  LLM 看到 system prompt 中的 Skill 目录摘要:
│  "- code-review: 代码审查，检查代码质量和潜在问题"
│  "you MUST call activate_skill tool..."
│
│  LLM 判断: 用户要检查代码 → 匹配 code-review skill
│
├─ 第一层: tool_call activate_skill("code-review")
│   │
│   └─ skill.py : activate_skill()                    ← @tool 函数
│       │
│       ├─ skill.py : SkillRegistry.get("code-review")
│       │   → 返回 Skill 对象
│       │
│       ├─ 检查 skill.disable_model_invocation
│       │
│       └─ 拼接返回:
│           • skill.content (SKILL.md 完整正文)
│           • "Available Scripts: count_lines.py"
│           • "Available References: style-guide.md"
│
│  LLM 收到 Observation: Skill 完整指令 + 可用资源列表
│  LLM 按照指令执行，判断需要参考风格指南...
│
├─ 第二层: tool_call load_skill_reference("code-review", "style-guide.md")
│   │
│   └─ skill.py : load_skill_reference()              ← @tool 函数
│       │
│       ├─ skill.py : SkillRegistry.get("code-review")
│       │
│       ├─ 检查 skill.references["style-guide.md"] 是否存在
│       │
│       └─ skill.py : SkillLoader.load_reference(skill, "style-guide.md")
│           → Path(ref_path).read_text() → 返回文档内容
│
│  LLM 收到 Observation: 风格指南全文
│  LLM 判断需要统计代码行数...
│
├─ 第三层: tool_call run_skill_script("code-review", "count_lines.py", "main.py")
│   │
│   └─ skill.py : run_skill_script()                  ← @tool 函数
│       │
│       ├─ skill.py : SkillRegistry.get("code-review")
│       │
│       ├─ 检查 skill.scripts["count_lines.py"] 是否存在
│       │
│       └─ skill.py : SkillExecutor.execute_script(skill, "count_lines.py", args=["main.py"])
│           │
│           ├─ SkillExecutor._build_command(script_path, args)
│           │   → ["python", "/path/to/count_lines.py", "main.py"]
│           │
│           ├─ 设置环境变量: SKILL_NAME, SKILL_DIR
│           │
│           └─ subprocess.run(cmd, capture_output=True, timeout=30)
│               → 返回 stdout
│
│  LLM 收到 Observation: "文件: main.py\n总行数: 42\n代码行: 35"
│
├─ LLM 综合所有信息，生成最终代码审查报告
│
└─ 返回 Final Answer → 回到 ReactAgent._run() 解析结果
```

### 各 Agent 模式差异

| 阶段 | ReactAgent | DeepAgent | PlanExecuteAgent | ReflexionAgent |
|------|-----------|-----------|-----------------|---------------|
| `_build()` | `create_react_agent(tools=all, prompt=catalog)` | 同 React（降级时委托 ReactAgent） | executor = `create_react_agent(tools=all)` | executor = `create_react_agent(tools=all)` |
| `_run()` 强制 Skill | SystemMessage 注入 messages | 同 React | `_selected_skills` 存储 | `_selected_skills` 存储 |
| Catalog 注入位置 | `_build()` 时写入 prompt | `_build()` 时写入 prompt | `_generate_plan()` 的 system prompt | `_generate()` 的 system prompt |
| LLM 自主选择 | 通过 tool_call 闭环 | 同 React | executor 继承 skill tools | executor 继承 skill tools |

### 关键文件索引

| 文件 | 核心函数 | 职责 |
|------|---------|------|
| `factory.py` | `create_agent()` | 工厂入口，按 mode 创建 Agent |
| `base.py:137` | `BaseAgent.__init__()` | 初始化 SkillLoader/Registry，调用 `_build()` |
| `base.py:185` | `BaseAgent.invoke()` | 统一调用入口，转发到 `_run()` |
| `base.py:261` | `_resolve_active_skills()` | 三级优先级解析强制/引用/自动 |
| `base.py:309` | `_build_system_prompt_with_skills()` | 拼接 base + catalog + active skills |
| `base.py:341` | `_get_skill_tools()` | 生成并缓存 3 个 Skill LangChain Tool |
| `base.py:360` | `_get_all_tools()` | 合并用户 tools + skill tools |
| `skill.py:436` | `build_skill_tools()` | 工厂函数，创建 activate/run/load 三个 @tool |
| `skill.py:451` | `activate_skill()` | 第一层 — 返回 SKILL.md 全文 + 资源列表 |
| `skill.py:486` | `run_skill_script()` | 第三层 — 调用 SkillExecutor 执行脚本 |
| `skill.py:512` | `load_skill_reference()` | 第三层 — 调用 SkillLoader 加载参考资料 |
| `skill.py:347` | `SkillExecutor.execute_script()` | subprocess 执行脚本，返回 stdout |
| `skill.py:286` | `SkillRegistry.build_skill_catalog_prompt()` | 生成目录摘要注入 system prompt |
| `react_agent.py:60` | `ReactAgent._build()` | 合并 tools + catalog → create_react_agent |
| `react_agent.py:94` | `ReactAgent._run()` | 解析强制 skills → 执行 agent → 提取结果 |

## 更多资源

- [Agent 模块文档](AGENTS.md)
- [配置参考](CONFIG_REFERENCE.md)
- [使用指南](USAGE.md)
