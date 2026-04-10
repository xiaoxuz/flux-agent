#!/usr/bin/env python3
"""
Flux-Agent Skill 系统演示

演示 Skill 系统的核心能力：
1. Skill 加载与目录扫描
2. SkillRegistry 注册与目录摘要
3. 脚本执行（SkillExecutor）
4. References 按需加载
5. Agent + Skill 集成使用
"""

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from flux_agent.agents import (
    Skill,
    SkillLoader,
    SkillRegistry,
    SkillExecutor,
    create_agent,
    AgentInput,
    AgentConfig,
)


# ============================================================
# 辅助：创建一个临时的 Skill 目录用于演示
# ============================================================

def create_demo_skill_dir() -> str:
    """创建演示用的 skill 目录结构"""
    base = Path(tempfile.mkdtemp(prefix="flux_skills_"))

    # --- Skill 1: code-review ---
    skill1 = base / "code-review"
    skill1.mkdir()
    (skill1 / "SKILL.md").write_text("""\
---
name: code-review
description: 代码审查，检查代码质量、命名规范和潜在问题
allowed-tools: [python_repl]
---

# Code Review Skill

## Instructions
1. 仔细阅读提交的代码
2. 参考 references中的代码风格指南(style-guide.md)
3. 使用script中count_lines.py辅助来精确统计代码行数
4. 检查命名规范、错误处理、安全漏洞、性能问题
5. 给出具体改进建议和示例代码

## Output Format
- 问题列表（按严重程度排序）
- 每个问题附带修复建议
""", encoding="utf-8")

    # scripts
    scripts_dir = skill1 / "scripts"
    scripts_dir.mkdir()
    (scripts_dir / "count_lines.py").write_text("""\
#!/usr/bin/env python3
\"\"\"统计代码行数的辅助脚本\"\"\"
import sys

if len(sys.argv) > 1:
    path = sys.argv[1]
    try:
        with open(path) as f:
            lines = f.readlines()
        total = len(lines)
        code = sum(1 for l in lines if l.strip() and not l.strip().startswith('#'))
        print(f"文件: {path}")
        print(f"总行数: {total}")
        print(f"代码行: {code}")
        print(f"注释/空行: {total - code}")
    except FileNotFoundError:
        print(f"文件不存在: {path}")
else:
    print("用法: count_lines.py <file_path>")
""", encoding="utf-8")

    # references
    refs_dir = skill1 / "references"
    refs_dir.mkdir()
    (refs_dir / "style-guide.md").write_text("""\
# Python 代码风格指南

## 命名规范
- 变量/函数: snake_case
- 类: PascalCase
- 常量: UPPER_SNAKE_CASE

## 函数长度
- 单个函数不超过 50 行
- 超过 20 行考虑拆分

## 错误处理
- 不要用裸 except
- 捕获具体异常类型
""", encoding="utf-8")

    # assets
    assets_dir = skill1 / "assets"
    assets_dir.mkdir()
    (assets_dir / "review-template.md").write_text("""\
# Code Review Report

## 概述
- 文件: {{file}}
- 审查时间: {{date}}

## 问题列表
| # | 严重程度 | 问题 | 建议 |
|---|----------|------|------|
| 1 | ...      | ...  | ...  |

## 总结
""", encoding="utf-8")

    # --- Skill 2: data-analysis (带 disable-model-invocation) ---
    skill2 = base / "data-analysis"
    skill2.mkdir()
    (skill2 / "SKILL.md").write_text("""\
---
name: data-analysis
description: 数据分析工作流，从数据加载到可视化
disable-model-invocation: true
argument-hint: 传入数据文件路径或 CSV 内容
---

# Data Analysis Skill

## Instructions
1. 加载数据（CSV/JSON/Excel）
2. 数据清洗与预处理
3. 统计分析
4. 生成可视化图表
5. 输出分析报告
""", encoding="utf-8")

    print(f"[创建演示 Skill 目录] {base}")
    return str(base)


# ============================================================
# 演示 1: Skill 加载与目录扫描
# ============================================================

def demo_skill_loading(skills_dir: str):
    print("=" * 60)
    print("演示 1: Skill 加载与目录扫描")
    print("=" * 60)

    loader = SkillLoader(skills_dir)

    # 列出所有 skill
    names = loader.list_skills()
    print(f"\n可用 Skills: {names}")

    # 加载单个 skill
    skill = loader.load("code-review")
    print(f"\nSkill: {skill}")
    print(f"  name: {skill.name}")
    print(f"  description: {skill.description}")
    print(f"  scripts: {list(skill.scripts.keys())}")
    print(f"  references: {list(skill.references.keys())}")
    print(f"  assets: {list(skill.assets.keys())}")
    print(f"  allowed_tools: {skill.allowed_tools}")
    print(f"  disable_model_invocation: {skill.disable_model_invocation}")

    # 加载带 disable-model-invocation 的 skill
    skill2 = loader.load("data-analysis")
    print(f"\nSkill: {skill2}")
    print(f"  disable_model_invocation: {skill2.disable_model_invocation}")
    print(f"  argument_hint: {skill2.argument_hint}")
    print()


# ============================================================
# 演示 2: SkillRegistry 注册与目录摘要
# ============================================================

def demo_skill_registry(skills_dir: str):
    print("=" * 60)
    print("演示 2: SkillRegistry 注册与目录摘要")
    print("=" * 60)

    loader = SkillLoader(skills_dir)
    registry = SkillRegistry(loader)
    registry.load_and_register_all()

    print(f"\n已注册 Skills: {[s.name for s in registry.all_skills]}")
    print(f"可自动触发 Skills: {[s.name for s in registry.invocable_skills]}")

    # 生成 catalog prompt
    catalog = registry.build_skill_catalog_prompt()
    print(f"\n--- Skill 目录摘要 (注入 system prompt) ---")
    print(catalog)

    # 按名称获取
    skill = registry.get("code-review")
    print(f"\n按名称获取: {skill}")
    print()


# ============================================================
# 演示 3: 脚本执行
# ============================================================

def demo_script_execution(skills_dir: str):
    print("=" * 60)
    print("演示 3: 脚本执行 (SkillExecutor)")
    print("=" * 60)

    loader = SkillLoader(skills_dir)
    skill = loader.load("code-review")

    print(f"\nSkill '{skill.name}' 可用脚本: {list(skill.scripts.keys())}")

    # 执行脚本（不带参数）
    print("\n--- 执行 count_lines.py (无参数) ---")
    output = SkillExecutor.execute_script(skill, "count_lines.py")
    print(f"输出: {output}")

    # 执行脚本（带参数 — 用 SKILL.md 自身作为测试文件）
    skill_md_path = skill.source
    print(f"--- 执行 count_lines.py {skill_md_path} ---")
    output = SkillExecutor.execute_script(skill, "count_lines.py", args=[skill_md_path])
    print(f"输出: {output}")
    print()


# ============================================================
# 演示 4: References 按需加载
# ============================================================

def demo_references(skills_dir: str):
    print("=" * 60)
    print("演示 4: References 按需加载")
    print("=" * 60)

    loader = SkillLoader(skills_dir)
    skill = loader.load("code-review")

    print(f"\n可用 References: {list(skill.references.keys())}")

    # 按需加载
    content = loader.load_reference(skill, "style-guide.md")
    print(f"\n--- style-guide.md 内容 ---")
    print(content[:300])

    # 加载 asset
    print(f"\n可用 Assets: {list(skill.assets.keys())}")
    template = loader.load_asset(skill, "review-template.md")
    print(f"\n--- review-template.md 内容 ---")
    print(template[:300])
    print()


# ============================================================
# 演示 5: Agent + Skill 集成
# ============================================================

def demo_agent_with_skills(skills_dir: str):
    print("=" * 60)
    print("演示 5: Agent + Skill[目录] 集成")
    print("=" * 60)

    try:
        from langchain_openai import ChatOpenAI
        from dotenv import load_dotenv
        load_dotenv()

        llm = ChatOpenAI(
            model="gpt-4.1",
            temperature=0,
            base_url=os.getenv("OPENAI_BASE_URL"),
            api_key=os.getenv("OPENAI_API_KEY"),
        )
    except Exception as e:
        print(f"\n跳过（需要 LLM 配置）: {e}")
        print("  设置 OPENAI_API_KEY 后重试")
        return

    loader = SkillLoader(skills_dir)
    all_skills = loader.load_all()

    agent = create_agent(
        "react",
        llm=llm,
        skills=all_skills,
        config=AgentConfig(verbose=True),
    )

    print(f"\nAgent 已注册 {len(agent.skill_registry.all_skills)} 个 Skills")
    print(f"可自动触发: {[s.name for s in agent.skill_registry.invocable_skills]}")

    # 方式一: Agent 自主选择（通过 catalog）
    print("\n--- 方式一: Agent 自主选择 ---")
    result = agent.invoke("帮我检查一下这段代码: def add(a,b): return a+b")
    print(f"回答: {result.answer[:200]}...")

    # 方式二: 强制激活
    print("\n--- 方式二: 强制激活 active_skills ---")
    result = agent.invoke(AgentInput(
        query="帮我检查一下这段代码: def add(a,b): return a+b",
        active_skills=["code-review"],
    ))
    print(f"回答: {result.answer[:200]}...")
    print()


# ============================================================
# 演示 6: 动态创建 Skill（纯代码方式）
# ============================================================

def demo_programmatic_skill():
    print("=" * 60)
    print("演示 6: 纯代码方式创建 Skill")
    print("=" * 60)

    skill = Skill(
        name="quick-translate",
        description="快速翻译，支持中英文互译",
        content="""\
# Quick Translate

## Instructions
1. 检测输入语言
2. 中文 → 英文，英文 → 中文
3. 保持专业术语准确
4. 输出格式：原文 | 译文
""",
        scripts={},
        references={},
    )

    print(f"\n创建 Skill: {skill}")
    print(f"  catalog_entry:\n{skill.catalog_entry()}")

    # 注册到 registry
    registry = SkillRegistry()
    registry.register(skill)
    print(f"\n注册到 Registry: {[s.name for s in registry.all_skills]}")
    print(f"Catalog prompt:\n{registry.build_skill_catalog_prompt()}")
    print()

# ============================================================
# 演示 7: Agent + Skill 集成 - 代码
# ============================================================

def demo_agent_with_dynamic_skills(skills_dir: str):
    print("=" * 60)
    print("演示 6: Agent + Skill[代码] 集成")
    print("=" * 60)

    try:
        from langchain_openai import ChatOpenAI
        from dotenv import load_dotenv
        load_dotenv()

        llm = ChatOpenAI(
            model="gpt-4.1",
            temperature=0,
            base_url=os.getenv("OPENAI_BASE_URL"),
            api_key=os.getenv("OPENAI_API_KEY"),
        )
    except Exception as e:
        print(f"\n跳过（需要 LLM 配置）: {e}")
        print("  设置 OPENAI_API_KEY 后重试")
        return

    skill = Skill(
            name="quick-translate",
            description="快速翻译，支持中英文互译",
            content="""\
    # Quick Translate

    ## Instructions
    1. 检测输入语言
    2. 中文 → 英文，英文 → 中文
    3. 保持专业术语准确
    4. 输出格式：原文 | 译文
    """,
            scripts={},
            references={},
        )

    print(f"\n创建 Skill: {skill}")
    print(f"  catalog_entry:\n{skill.catalog_entry()}")

    agent = create_agent(
        "react",
        llm=llm,
        skills=[skill],
        config=AgentConfig(verbose=True),
    )

    print(f"\nAgent 已注册 {len(agent.skill_registry.all_skills)} 个 Skills")
    print(f"可自动触发: {[s.name for s in agent.skill_registry.invocable_skills]}")

    # 方式一: Agent 自主选择（通过 catalog）
    print("\n--- 方式一: Agent 自主选择 ---")
    result = agent.invoke("/quick-translate 使用这个技能, 输入：帮我检查一下这段代码: def add(a,b): return a+b")
    print(f"回答: {result.answer[:200]}...")

    print(f"回答: {result.answer[:200]}...")
    print()


# ============================================================
# Main
# ============================================================

def main():
    print("\n" + "=" * 60)
    print("  Flux-Agent Skill 系统演示")
    print("=" * 60 + "\n")

    skills_dir = create_demo_skill_dir()
    print(f"临时目录: {skills_dir}")

    try:
        # demo_skill_loading(skills_dir)
        # demo_skill_registry(skills_dir)
        # demo_script_execution(skills_dir)
        # demo_references(skills_dir)
        # demo_programmatic_skill()

        # # Agent 集成 - 目录skill
        # demo_agent_with_skills(skills_dir)
        # Agent 集成 - 代码定义 skill
        demo_agent_with_dynamic_skills(skills_dir)

    finally:
        # 清理临时目录
        import shutil
        shutil.rmtree(skills_dir, ignore_errors=True)
        print(f"[清理临时目录] {skills_dir}")

    print("\n" + "=" * 60)
    print("  演示完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
