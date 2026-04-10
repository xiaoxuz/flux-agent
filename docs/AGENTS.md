# Flux-Agent 智能 Agent 模块

> 开箱即用的多模式 Agent 能力

## 概述

`flux_agent.agents` 模块提供了多种开箱即用的 Agent 模式，所有模式通过统一的接口调用，输出格式完全一致。

## 架构总览

### 统一调用流程

```mermaid
flowchart TB
    User["用户调用 agent.invoke()"]
    Norm["_normalize_input()<br/>统一转换为 AgentInput"]
    Resolve["_resolve_active_skills()<br/>解析强制激活 / 显式引用"]

    User --> Norm --> Resolve

    Resolve -->|"有强制 Skill"| Inject["注入 Skill content<br/>到 messages"]
    Resolve -->|"无强制 Skill"| Agent

    Inject --> Agent["_run()<br/>各模式具体逻辑"]
    Agent --> Output["AgentOutput<br/>answer / steps / status"]

    style User fill:#e1f5fe
    style Output fill:#e8f5e9
```

### 四种 Agent 模式流程

```mermaid
flowchart TB
    subgraph REACT ["ReAct 模式"]
        direction TB
        R1["LLM 推理"] --> R2{需要工具?}
        R2 -->|Yes| R3["tool_call<br/>(用户工具 / Skill 工具)"]
        R3 --> R4["Observation<br/>工具返回结果"]
        R4 --> R1
        R2 -->|No| R5["Final Answer"]
    end

    subgraph DEEP ["Deep 模式"]
        direction TB
        D1["LLM + Deep 引擎"] --> D2{需要工具?}
        D2 -->|Yes| D3["tool_call"]
        D3 --> D4["Observation"]
        D4 --> D1
        D2 -->|No| D5["Final Answer"]
        D6["未安装 deepagents<br/>→ 降级到 ReAct"]
        style D6 fill:#fff3e0,stroke:#ff9800
    end

    subgraph PLAN ["Plan-Execute 模式"]
        direction TB
        P1["Planner LLM<br/>生成分步计划<br/>(含 Skill catalog)"]
        P2["Executor<br/>逐步执行<br/>(可调工具+Skill工具)"]
        P3{Replan?}
        P4["Replanner<br/>动态调整计划"]
        P5["Final Answer"]

        P1 --> P2 --> P3
        P3 -->|"需要调整"| P4 --> P2
        P3 -->|"继续/完成"| P5
    end

    subgraph REFLEX ["Reflexion 模式"]
        direction TB
        X1["Generator<br/>生成回答<br/>(含 Skill catalog)"]
        X2["Evaluator<br/>评估质量 (1-10分)"]
        X3{满意?}
        X4["Reflector<br/>反思不足"]
        X5["Final Answer"]

        X1 --> X2 --> X3
        X3 -->|"分数 < 阈值"| X4 --> X1
        X3 -->|"分数 >= 阈值<br/>或达到最大轮次"| X5
    end
```

### Skill 三层渐进式加载（Tool 驱动闭环）

```mermaid
sequenceDiagram
    participant U as 用户
    participant A as Agent (LLM)
    participant AT as activate_skill
    participant RS as run_skill_script
    participant LR as load_skill_reference

    Note over A: System Prompt 中已注入<br/>Skill 目录摘要 (name + desc)

    U->>A: "帮我检查这段代码质量"
    Note over A: 判断匹配 code-review skill

    A->>AT: activate_skill("code-review")
    AT-->>A: 返回 SKILL.md 完整内容<br/>+ 可用脚本列表<br/>+ 可用参考资料列表

    Note over A: 根据 Skill 指令执行任务<br/>判断需要参考风格指南

    A->>LR: load_skill_reference("code-review", "style-guide.md")
    LR-->>A: 返回风格指南文档内容

    Note over A: 判断需要统计代码行数

    A->>RS: run_skill_script("code-review", "count_lines.py", "main.py")
    RS-->>A: 返回脚本输出 (stdout)

    A->>U: 最终代码审查报告
```

### Tool 与 Skill Tool 的融合

```mermaid
flowchart LR
    subgraph UserTools ["用户注册的 Tools"]
        T1[search]
        T2[calculator]
        T3[...]
    end

    subgraph SkillTools ["自动生成的 Skill Tools"]
        S1[activate_skill]
        S2[run_skill_script]
        S3[load_skill_reference]
    end

    Merge["_get_all_tools()<br/>合并所有 tools"]
    UserTools --> Merge
    SkillTools --> Merge
    Merge --> LLM["LLM<br/>通过 tool_call 统一调用"]

    style SkillTools fill:#f3e5f5,stroke:#9c27b0
    style UserTools fill:#e3f2fd,stroke:#1976d2
```

### 构建阶段（_build）全景

```mermaid
flowchart TB
    Init["BaseAgent.__init__()"]
    Reg["SkillRegistry<br/>注册传入的 skills"]
    ST["build_skill_tools()<br/>生成 3 个 Skill Tool"]
    Merge["_get_all_tools()<br/>用户 tools + skill tools"]
    Catalog["build_skill_catalog_prompt()<br/>Skill 目录摘要"]
    SP["System Prompt<br/>= base + catalog"]

    Init --> Reg --> ST --> Merge

    Reg --> Catalog --> SP

    Merge --> Build
    SP --> Build

    Build["_build()<br/>创建内部 agent 实例"]

    subgraph 各模式构建
        B1["ReactAgent: create_react_agent(tools=all, prompt=SP)"]
        B2["DeepAgent: create_deep_agent(tools=all, prompt=SP)"]
        B3["PlanExecute: executor = create_react_agent(tools=all)"]
        B4["Reflexion: executor = create_react_agent(tools=all)"]
    end

    Build --> B1 & B2 & B3 & B4

    style Init fill:#e1f5fe
    style Build fill:#e8f5e9
```

## 安装

```bash
# 基础安装（ReAct、Plan-Execute、Reflexion）
pip install flux-agent

# 完整安装（包含 Deep 模式）
pip install flux-agent[agents]
```

## 快速开始

```python
from langchain_openai import ChatOpenAI
from flux_agent.agents import create_agent

llm = ChatOpenAI(model="gpt-4o")

# 创建 Agent
agent = create_agent("react", llm=llm)

# 执行
result = agent.invoke("什么是量子计算？")

# 获取结果
print(result.answer)
```

## 支持的 Agent 模式

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| `react` | ReAct 模式，推理+行动循环 | 简单问答、工具调用 |
| `deep` | Deep 模式，任务规划+文件系统 | 复杂任务、代码生成 |
| `plan_execute` | 先规划再执行 | 多步骤任务、研究型任务 |
| `reflexion` | 自我反思改进 | 代码生成、高质量输出 |

## 统一接口

### AgentInput

```python
from flux_agent.agents import AgentInput

input = AgentInput(
    query="你的问题",              # 必填：用户的问题/任务
    messages=[...],               # 可选：对话历史
    context="额外上下文",          # 可选：额外信息
    system_prompt="自定义提示词",  # 可选：覆盖默认提示词
    max_steps=10,                 # 可选：最大步数
    config={}                     # 可选：模式特定配置
)
```

### AgentOutput

```python
result = agent.invoke("问题")

result.answer         # 最终回答
result.status         # 执行状态: success/failed/partial/interrupted
result.steps          # 执行步骤列表
result.total_steps    # 总步数
result.elapsed_time   # 耗时(秒)
result.error          # 错误信息(如有)
result.metadata       # 额外元数据
```

## 详细用法

### ReAct 模式

ReAct（Reasoning + Acting）是最常用的 Agent 模式，适合简单的问答和工具调用场景。

```python
from langchain_openai import ChatOpenAI
from langchain_community.tools import TavilySearchResults
from flux_agent.agents import create_agent

llm = ChatOpenAI(model="gpt-4o")
search = TavilySearchResults()

agent = create_agent(
    "react",
    llm=llm,
    tools=[search],
)

result = agent.invoke("今天北京天气怎么样？")
print(result.answer)
```

### Deep 模式

Deep 模式提供更强大的能力：任务规划、文件系统、子 Agent 等。

```python
agent = create_agent(
    "deep",
    llm=llm,
    tools=[search],
)

result = agent.invoke("分析2024年AI领域的重要突破")
```

> **注意**: Deep 模式需要安装 `deepagents`: `pip install flux-agent[agents]`。未安装时会自动降级到 ReAct 模式。

### Plan-Execute 模式

适合复杂的多步骤任务，先制定计划再逐步执行。

```python
agent = create_agent(
    "plan_execute",
    llm=llm,
    tools=[search],
    enable_replan=True,  # 启用动态重规划
)

result = agent.invoke("分析中国新能源汽车市场趋势并给出投资建议")

# 查看生成的计划
print(result.metadata.get("plan"))
```

**工作流程**：
1. Planner 生成执行计划
2. Executor 逐步执行
3. Replanner 根据结果调整计划（可选）

### Reflexion 模式

通过自我反思不断改进输出质量，适合代码生成、写作等需要高质量输出的场景。

```python
agent = create_agent(
    "reflexion",
    llm=llm,
    max_iterations=3,        # 最多反思 3 轮
    quality_threshold=8.0,   # 8 分以上满意
)

result = agent.invoke("写一个 Python 快速排序算法，要求有完整注释和单元测试")

# 查看反思过程
from flux_agent.agents import StepType
for step in result.get_steps_by_type(StepType.REFLECTION):
    print(f"反思: {step.content[:200]}...")
```

**工作流程**：
1. Generator 生成初始回答
2. Evaluator 评估质量
3. Reflector 反思不足
4. Generator 改进回答
5. 循环直到满意或达到最大轮次

## 统一输出格式

所有模式的输出格式完全一致：

```python
# 不管什么模式
for mode in ["react", "plan_execute", "reflexion"]:
    agent = create_agent(mode, llm=llm)
    result = agent.invoke("问题")
    
    print(f"模式: {result.agent_mode.value}")
    print(f"回答: {result.answer}")
    print(f"状态: {result.status.value}")
    print(f"步数: {result.total_steps}")
    print(f"耗时: {result.elapsed_time:.2f}s")
```

## 多种调用方式

```python
agent = create_agent("react", llm=llm)

# 方式1：字符串
result = agent.invoke("你好")

# 方式2：字典
result = agent.invoke({"query": "你好", "max_steps": 5})

# 方式3：AgentInput 对象
result = agent.invoke(AgentInput(
    query="你好",
    context="用户是程序员",
    max_steps=5,
))
```

## Skill 能力

Agent 支持 Skill 系统 — 为 Agent 注入领域知识、执行脚本、引用资料的模块化扩展机制。

```python
from flux_agent.agents import create_agent, SkillLoader, AgentInput

loader = SkillLoader("skills")
agent = create_agent("react", llm=llm, skills=loader.load_all())

# Agent 自主选择 Skill
result = agent.invoke("帮我检查一下代码质量")

# 强制激活指定 Skill
result = agent.invoke(AgentInput(
    query="检查这段代码",
    active_skills=["code-review"],
))
```

> 完整文档请参阅 [Skill 系统文档](SKILLS.md)

## 自定义 Agent 模式

通过 `AgentRegistry` 注册自定义 Agent：

```python
from flux_agent.agents import BaseAgent, AgentMode, AgentInput, AgentOutput, AgentRegistry

@AgentRegistry.register("my_custom")
class MyCustomAgent(BaseAgent):
    @property
    def mode(self) -> AgentMode:
        return "my_custom"
    
    def _build(self):
        # 构建内部逻辑
        pass
    
    def _run(self, agent_input: AgentInput) -> AgentOutput:
        # 执行逻辑
        response = self.llm.invoke(agent_input.to_messages())
        return AgentOutput(
            answer=response.content,
            status="success",
            agent_mode=self.mode,
            steps=[],
            total_steps=1,
        )

# 使用自定义模式
agent = create_agent("my_custom", llm=llm)
```

## 回调监控

```python
from flux_agent.agents import AgentCallback, AgentConfig
from flux_agent.agents.utils import PrintCallback

# 使用内置打印回调
agent = create_agent(
    "react",
    llm=llm,
    config=AgentConfig(verbose=True),
)

# 自定义回调
class MyCallback(AgentCallback):
    def on_step(self, step):
        print(f"Step {step.step_index}: {step.step_type.value}")
    
    def on_agent_end(self, output):
        print(f"完成: {output.total_steps} 步")

agent = create_agent(
    "plan_execute",
    llm=llm,
    config=AgentConfig(callbacks=[MyCallback()]),
)
```

## 与 LangGraph 编排结合

```python
from langgraph.graph import StateGraph, START, END

# 创建不同模式的 Agent
researcher = create_agent("react", llm=llm, tools=[search])
writer = create_agent("reflexion", llm=llm)

# 编排工作流
def research_node(state):
    result = researcher.invoke(state["query"])
    return {"research": result.answer}

def write_node(state):
    prompt = f"基于研究写报告: {state['research']}"
    result = writer.invoke(prompt)
    return {"report": result.answer}

graph = StateGraph(dict)
graph.add_node("research", research_node)
graph.add_node("write", write_node)
graph.add_edge(START, "research")
graph.add_edge("research", "write")
graph.add_edge("write", END)

workflow = graph.compile()
result = workflow.invoke({"query": "分析AI趋势"})
```

## API 参考

### create_agent()

```python
def create_agent(
    mode: str | AgentMode,      # Agent 模式
    llm: BaseChatModel,          # LLM 实例
    tools: list[BaseTool] = None, # 工具列表
    system_prompt: str = None,    # 系统提示词
    config: AgentConfig = None,   # Agent 配置
    **kwargs,                     # 模式特定参数
) -> BaseAgent
```

### AgentConfig

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `verbose` | bool | False | 是否打印详细日志 |
| `max_steps` | int | 10 | 最大执行步数 |
| `temperature` | float | 0.0 | LLM 温度 |
| `callbacks` | list | None | 回调列表 |

### 模式特定参数

**PlanExecuteAgent**:
- `enable_replan`: 是否启用动态重规划

**ReflexionAgent**:
- `max_iterations`: 最大反思轮次
- `quality_threshold`: 质量阈值（1-10）
- `evaluator_llm`: 评估用的 LLM（可与生成器不同）

## 更多资源

- [Skill 系统文档](SKILLS.md)
- [配置参考](CONFIG_REFERENCE.md)
- [节点开发](NODE_DEVELOPMENT.md)
- [使用指南](USAGE.md)
