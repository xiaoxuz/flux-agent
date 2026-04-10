"""
flux_agent/agents/skill.py
Skill 数据模型、加载器、注册中心、执行器
"""
from __future__ import annotations

import logging
import os
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


# ============================================================
# Skill 数据模型
# ============================================================

@dataclass
class Skill:
    """Skill 定义 — 对标 Agent Skills 开放标准"""
    name: str                    # skill 名称
    description: str             # 描述（用于 LLM 选择判断）
    content: str                 # SKILL.md 正文（instructions）
    source: str = ""             # 来源路径或 URL
    metadata: Dict = field(default_factory=dict)  # YAML frontmatter 中的其他字段

    # 目录资源映射
    scripts: Dict[str, str] = field(default_factory=dict)      # name -> script_path
    references: Dict[str, str] = field(default_factory=dict)   # name -> ref_file_path
    assets: Dict[str, str] = field(default_factory=dict)       # name -> asset_path

    # frontmatter 扩展字段
    disable_model_invocation: bool = False    # 禁止 agent 自动触发
    user_invocable: bool = True               # 是否可被用户 slash 调用
    allowed_tools: List[str] = field(default_factory=list)     # 预授权工具
    argument_hint: str = ""                   # 参数提示 ($ARGUMENTS 用法说明)

    def __repr__(self) -> str:
        return f"<Skill name={self.name}>"

    def catalog_entry(self) -> str:
        """生成用于 Skill 目录摘要的简短条目（~100 token）"""
        parts = [f"- **{self.name}**: {self.description}"]
        if self.argument_hint:
            parts.append(f"  参数: {self.argument_hint}")
        if self.scripts:
            parts.append(f"  脚本: {', '.join(self.scripts.keys())}")
        if self.references:
            parts.append(f"  参考资料: {', '.join(self.references.keys())}")
        return "\n".join(parts)


# ============================================================
# Skill 加载器
# ============================================================

def _parse_frontmatter(text: str) -> Dict:
    """
    解析 YAML frontmatter — 优先使用 PyYAML，不可用时降级为简易解析。
    """
    try:
        import yaml
        return yaml.safe_load(text) or {}
    except ImportError:
        pass

    # 降级：简易 key: value 解析（支持列表和引号）
    result: Dict = {}
    for line in text.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        # 去除引号
        if (value.startswith('"') and value.endswith('"')) or \
           (value.startswith("'") and value.endswith("'")):
            value = value[1:-1]
        # 简易布尔
        if value.lower() in ("true", "yes"):
            result[key] = True
        elif value.lower() in ("false", "no"):
            result[key] = False
        # 简易列表 [a, b, c]
        elif value.startswith("[") and value.endswith("]"):
            items = [v.strip().strip('"').strip("'") for v in value[1:-1].split(",")]
            result[key] = [i for i in items if i]
        else:
            result[key] = value
    return result


class SkillLoader:
    """
    Skill 加载器 — 从 skills/{name}/ 目录结构加载 Skill

    目录结构:
        my-skill/
        ├── SKILL.md          # 主指令（必需）
        ├── scripts/          # 可执行脚本
        │   └── helper.py
        ├── references/       # 参考资料（按需加载）
        │   └── api-doc.md
        └── assets/           # 模板等资源
            └── template.md
    """

    def __init__(self, skills_dir: str = "skills"):
        self.skills_dir = Path(skills_dir)
        self._cache: Dict[str, tuple[float, Skill]] = {}  # name -> (mtime, Skill)

    def list_skills(self) -> List[str]:
        """列出所有可用的 skill 名称"""
        if not self.skills_dir.exists():
            return []
        return [d.name for d in self.skills_dir.iterdir() if d.is_dir()]

    def load(self, name: str) -> Skill:
        """加载指定 skill（带缓存失效检测）"""
        skill_dir = self.skills_dir / name
        skill_path = skill_dir / "SKILL.md"

        if not skill_path.exists():
            # 大小写兼容
            for skill_name in self.list_skills():
                if skill_name.lower() == name.lower():
                    skill_dir = self.skills_dir / skill_name
                    skill_path = skill_dir / "SKILL.md"
                    name = skill_name
                    break
            else:
                raise ValueError(f"Skill not found: {name}")

        # 缓存失效检测
        mtime = skill_path.stat().st_mtime
        if name in self._cache:
            cached_mtime, cached_skill = self._cache[name]
            if cached_mtime >= mtime:
                return cached_skill

        content = skill_path.read_text(encoding="utf-8")
        skill = self._parse_skill(content, name, str(skill_path))

        # 扫描子目录资源
        skill.scripts = self._scan_subdir(skill_dir / "scripts")
        skill.references = self._scan_subdir(skill_dir / "references")
        skill.assets = self._scan_subdir(skill_dir / "assets")

        self._cache[name] = (mtime, skill)
        return skill

    def load_all(self) -> List[Skill]:
        """加载所有可用的 skills"""
        skills = []
        for name in self.list_skills():
            try:
                skills.append(self.load(name))
            except Exception as e:
                logger.warning(f"Failed to load skill '{name}': {e}")
                continue
        return skills

    def load_reference(self, skill: Skill, ref_name: str) -> str:
        """按需加载某个 reference 文件内容"""
        ref_path = skill.references.get(ref_name)
        if not ref_path:
            raise ValueError(f"Reference not found: {ref_name} (available: {list(skill.references.keys())})")
        return Path(ref_path).read_text(encoding="utf-8")

    def load_asset(self, skill: Skill, asset_name: str) -> str:
        """按需加载某个 asset 文件内容"""
        asset_path = skill.assets.get(asset_name)
        if not asset_path:
            raise ValueError(f"Asset not found: {asset_name} (available: {list(skill.assets.keys())})")
        return Path(asset_path).read_text(encoding="utf-8")

    # ---- internal ----

    def _parse_skill(self, content: str, name: str, source: str) -> Skill:
        """解析 SKILL.md 文件，提取 YAML frontmatter 和正文"""
        metadata: Dict = {}
        body = content

        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                frontmatter_text = parts[1].strip()
                metadata = _parse_frontmatter(frontmatter_text)
                body = parts[2].strip()

        fm_name = metadata.pop("name", None)
        description = metadata.pop("description", "")

        # 提取扩展字段
        disable_model_invocation = bool(metadata.pop("disable-model-invocation", False))
        user_invocable = bool(metadata.pop("user-invocable", True))
        allowed_tools_raw = metadata.pop("allowed-tools", [])
        if isinstance(allowed_tools_raw, str):
            allowed_tools_raw = [t.strip() for t in allowed_tools_raw.split(",")]
        argument_hint = str(metadata.pop("argument-hint", ""))

        return Skill(
            name=fm_name or name,
            description=description,
            content=body,
            source=source,
            metadata=metadata,
            disable_model_invocation=disable_model_invocation,
            user_invocable=user_invocable,
            allowed_tools=list(allowed_tools_raw),
            argument_hint=argument_hint,
        )

    @staticmethod
    def _scan_subdir(dir_path: Path) -> Dict[str, str]:
        """扫描子目录，返回 {文件名: 绝对路径} 映射"""
        if not dir_path.is_dir():
            return {}
        return {
            f.name: str(f.resolve())
            for f in dir_path.iterdir()
            if f.is_file()
        }


# ============================================================
# Skill 注册中心 — 管理 Skill 元数据，生成目录摘要
# ============================================================

class SkillRegistry:
    """
    Skill 注册中心

    职责：
    1. 维护可用 Skill 全集
    2. 生成 Skill 目录摘要（注入 system prompt，供 LLM 自主选择）
    3. 按名称检索 Skill
    """

    def __init__(self, loader: SkillLoader | None = None):
        self._loader = loader
        self._skills: Dict[str, Skill] = {}

    def register(self, skill: Skill) -> None:
        """注册一个 Skill"""
        self._skills[skill.name] = skill

    def register_all(self, skills: List[Skill]) -> None:
        """批量注册"""
        for s in skills:
            self.register(s)

    def load_and_register_all(self) -> None:
        """从 loader 加载并注册所有 Skill"""
        if self._loader:
            for s in self._loader.load_all():
                self.register(s)

    def get(self, name: str) -> Optional[Skill]:
        """按名称获取 Skill"""
        skill = self._skills.get(name)
        if skill:
            return skill
        # 大小写兼容
        for k, v in self._skills.items():
            if k.lower() == name.lower():
                return v
        return None

    @property
    def all_skills(self) -> List[Skill]:
        return list(self._skills.values())

    @property
    def invocable_skills(self) -> List[Skill]:
        """可被 Agent 自动触发的 Skill（排除 disable_model_invocation=True）"""
        return [s for s in self._skills.values() if not s.disable_model_invocation]

    def build_skill_catalog_prompt(self, include_non_invocable: bool = False) -> str:
        """
        生成 Skill 目录摘要 — 仅包含 name + description（约 100 token / skill）

        注入 system prompt 后，LLM 根据此目录自主决定激活哪些 Skill。
        """
        skills = self.all_skills if include_non_invocable else self.invocable_skills
        if not skills:
            return ""

        lines = [
            "# Available Skills",
            "",
            "Below is the list of available skills. When a user's request matches a skill, "
            "you MUST call the `activate_skill` tool with the skill name to load its full instructions. "
            "After activation, follow the instructions. If the skill has scripts or references, "
            "use `run_skill_script` or `load_skill_reference` tools as needed.",
            "",
        ]
        for s in skills:
            lines.append(s.catalog_entry())

        lines.append("")
        lines.append(
            "**Important**: Do NOT guess skill instructions. Always call `activate_skill` first "
            "to get the actual content before proceeding."
        )
        return "\n".join(lines)

    def build_active_skills_prompt(
        self,
        active_skills: List[Skill],
        base_prompt: str = "",
    ) -> str:
        """构建包含已激活 Skill 完整内容的 system prompt"""
        parts = [base_prompt] if base_prompt else []

        if active_skills:
            parts.append("\n\n# Active Skills\n")
            parts.append("Follow the instructions in these skills:\n")
            for skill in active_skills:
                parts.append(f"\n---\n## Skill: {skill.name}\n")
                parts.append(skill.content)

        return "\n".join(parts)


# ============================================================
# Skill 执行器 — 执行 Skill 关联的脚本
# ============================================================

class SkillExecutor:
    """
    执行 Skill 关联的脚本

    脚本输出作为 observation 返回给 Agent，不将脚本源码加载进 context（token 高效）。
    """

    DEFAULT_TIMEOUT = 30  # 秒

    @staticmethod
    def execute_script(
        skill: Skill,
        script_name: str,
        args: List[str] | None = None,
        timeout: int | None = None,
        env: Dict[str, str] | None = None,
    ) -> str:
        """
        执行 skill 的脚本，返回 stdout。

        Args:
            skill: Skill 实例
            script_name: 脚本文件名（如 helper.py）
            args: 传给脚本的参数列表
            timeout: 超时秒数
            env: 额外环境变量

        Returns:
            脚本的 stdout 输出

        Raises:
            ValueError: 脚本不存在
            RuntimeError: 脚本执行失败
        """
        script_path = skill.scripts.get(script_name)
        if not script_path:
            raise ValueError(
                f"Script '{script_name}' not found in skill '{skill.name}' "
                f"(available: {list(skill.scripts.keys())})"
            )

        # 确定执行方式
        cmd = SkillExecutor._build_command(script_path, args)

        # 构建环境变量
        run_env = os.environ.copy()
        run_env["SKILL_NAME"] = skill.name
        run_env["SKILL_DIR"] = str(Path(script_path).parent.parent)
        if env:
            run_env.update(env)

        effective_timeout = timeout or SkillExecutor.DEFAULT_TIMEOUT

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=effective_timeout,
                cwd=str(Path(script_path).parent),
                env=run_env,
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError(
                f"Script '{script_name}' timed out after {effective_timeout}s"
            )
        except OSError as e:
            raise RuntimeError(f"Failed to execute script '{script_name}': {e}")

        if result.returncode != 0:
            stderr_snippet = result.stderr[:500] if result.stderr else "(no stderr)"
            raise RuntimeError(
                f"Script '{script_name}' exited with code {result.returncode}: {stderr_snippet}"
            )

        return result.stdout

    @staticmethod
    def _build_command(script_path: str, args: List[str] | None) -> List[str]:
        """根据脚本类型构建命令"""
        path = Path(script_path)
        suffix = path.suffix.lower()
        base_args = args or []

        if suffix == ".py":
            return ["python", str(path)] + base_args
        elif suffix == ".sh":
            return ["bash", str(path)] + base_args
        elif suffix == ".js":
            return ["node", str(path)] + base_args
        else:
            # 尝试直接执行（需要有执行权限）
            return [str(path)] + base_args


# ============================================================
# Skill Tools — 将 Skill 操作封装为 LangChain Tool，实现三层渐进式加载
# ============================================================

def build_skill_tools(registry: SkillRegistry, loader: SkillLoader | None = None) -> List:
    """
    构建 Skill 相关的 LangChain Tool 列表。

    LLM 通过这些 tool 自主完成三层渐进式加载：
    1. activate_skill   — 看到 catalog 后，激活某个 skill，获取完整 content
    2. run_skill_script  — 根据 content 判断需要执行脚本，获取输出
    3. load_skill_reference — 根据 content 判断需要参考资料，按需读取

    Returns:
        List[BaseTool] — 可直接添加到 Agent 的 tools 列表
    """
    from langchain_core.tools import tool

    @tool
    def activate_skill(skill_name: str) -> str:
        """激活一个 Skill，返回其完整指令内容。
        当你判断用户的请求匹配某个 Available Skill 时，调用此工具获取该 Skill 的完整指令。
        获取后请严格按照指令内容执行。

        Args:
            skill_name: Skill 名称（来自 Available Skills 列表）
        """
        skill = registry.get(skill_name)
        if not skill:
            # 尝试从 loader 按需加载
            if loader:
                try:
                    skill = loader.load(skill_name)
                    registry.register(skill)
                except ValueError:
                    pass
        if not skill:
            available = [s.name for s in registry.invocable_skills]
            return f"Skill '{skill_name}' not found. Available skills: {available}"

        if skill.disable_model_invocation:
            return f"Skill '{skill_name}' is disabled for model invocation."

        parts = [f"# Skill: {skill.name}\n", skill.content]

        # 提示可用的 scripts 和 references
        if skill.scripts:
            parts.append(f"\n\n## Available Scripts\n可通过 run_skill_script 执行: {', '.join(skill.scripts.keys())}")
        if skill.references:
            parts.append(f"\n\n## Available References\n可通过 load_skill_reference 加载: {', '.join(skill.references.keys())}")

        return "\n".join(parts)

    @tool
    def run_skill_script(skill_name: str, script_name: str, script_args: str = "") -> str:
        """执行 Skill 关联的脚本，返回脚本输出。
        脚本已预定义在 Skill 目录中，你只需提供脚本名称和参数。

        Args:
            skill_name: Skill 名称
            script_name: 脚本文件名（如 check.py, helper.sh）
            script_args: 传给脚本的参数，多个参数用空格分隔
        """
        skill = registry.get(skill_name)
        if not skill:
            return f"Skill '{skill_name}' not found. Please activate it first using activate_skill."

        if not skill.scripts:
            return f"Skill '{skill_name}' has no scripts."

        if script_name not in skill.scripts:
            return f"Script '{script_name}' not found. Available: {list(skill.scripts.keys())}"

        args_list = script_args.split() if script_args.strip() else []
        try:
            output = SkillExecutor.execute_script(skill, script_name, args=args_list)
            return output if output.strip() else "(script produced no output)"
        except (ValueError, RuntimeError) as e:
            return f"Script execution failed: {e}"

    @tool
    def load_skill_reference(skill_name: str, reference_name: str) -> str:
        """按需加载 Skill 的参考资料文档。
        参考资料是 Skill 附带的补充文档（如 API 文档、风格指南等），只在你需要时才加载。

        Args:
            skill_name: Skill 名称
            reference_name: 参考资料文件名（如 api-doc.md, style-guide.md）
        """
        skill = registry.get(skill_name)
        if not skill:
            return f"Skill '{skill_name}' not found. Please activate it first using activate_skill."

        if not skill.references:
            return f"Skill '{skill_name}' has no references."

        if reference_name not in skill.references:
            return f"Reference '{reference_name}' not found. Available: {list(skill.references.keys())}"

        if not loader:
            return "Reference loading not available (no SkillLoader configured)."

        try:
            content = loader.load_reference(skill, reference_name)
            return content
        except (ValueError, OSError) as e:
            return f"Failed to load reference: {e}"

    return [activate_skill, run_skill_script, load_skill_reference]


# ============================================================
# 向后兼容 — SkillSelector（标记为 deprecated）
# ============================================================

class SkillSelector:
    """
    Skill 选择器（已弃用）

    保留用于向后兼容。新代码请使用 SkillRegistry。
    """

    # 匹配 "使用 xxx 技能/skill" 的模式
    SKILL_REFERENCE_PATTERN = re.compile(
        r"使用\s+['\"`]?([a-zA-Z0-9_-]+)['\"`]?\s*(技能|skill)",
        re.IGNORECASE
    )

    @classmethod
    def parse_skill_reference(cls, query: str) -> Optional[str]:
        """解析 prompt 中的技能引用，返回技能名或 None"""
        match = cls.SKILL_REFERENCE_PATTERN.search(query)
        if match:
            return match.group(1).lower().replace("-", "_")
        return None

    @classmethod
    def select_relevant_skills(cls, query: str, skills: List[Skill]) -> List[Skill]:
        """已弃用 — 仅保留显式引用匹配"""
        if not skills:
            return []

        skill_name = cls.parse_skill_reference(query)
        if skill_name:
            for skill in skills:
                if skill.name.lower().replace("-", "_") == skill_name:
                    return [skill]

        return []

    @classmethod
    def build_system_prompt_with_skills(
        cls,
        skills: List[Skill],
        base_prompt: str = ""
    ) -> str:
        """已弃用 — 请使用 SkillRegistry.build_active_skills_prompt"""
        parts = [base_prompt] if base_prompt else []

        if skills:
            parts.append("\n\n# Active Skills\n")
            parts.append("Follow the instructions in these skills:\n")
            for skill in skills:
                parts.append(f"\n---\n## Skill: {skill.name}\n")
                parts.append(skill.content)

        return "\n".join(parts)
