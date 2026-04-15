"""
Bash 执行工具

核心职责：执行 bash/shell 命令并返回输出。

【什么时候推荐用 Bash】
- 系统命令：ls, mkdir, cp, mv, chmod, pip install 等
- Git 操作：git status, git diff, git log, git add, git commit 等
- GitHub CLI：gh pr view, gh issue list 等
- Python 脚本：python -c "..." 用于数据处理/计算/格式转换
  （当已有文件内容时，用 python -c 做 JSON 解析、CSV 处理、数学计算等）
- 进程管理：ps, kill, top, curl, wget 等
- 需要 shell 操作符的场景：&& 串联、| 管道、> 重定向
- 长时间运行的命令（需配合 timeout 参数）

【什么时候不用 Bash】
重要：避免使用本工具执行 find/grep/cat/head/tail/sed/awk/echo 命令，
除非用户明确要求或已确认无专用工具可用。请使用对应的专用工具：
- 文件搜索: 使用 glob_search（NOT find 或 ls）
- 内容搜索: 使用 grep_search（NOT grep 或 rg）
- 读取文件: 使用 file_read（NOT cat/head/tail）
- 编辑文件: 使用 file_edit（NOT sed/awk）
- 写入文件: 使用 file_write（NOT echo> / cat<<EOF）
- 输出文本: 直接输出（NOT echo/printf）

环境说明：
- 工作目录在多次调用间保持持久化，但 shell 状态（变量、cd 等）不持久
- 避免使用 cd 命令，改用绝对路径
- 含空格的路径请用双引号包裹
- 多条依赖命令用 && 串联（如：cd dir && ls）

安全限制：
- 自动拦截 rm -rf /、dd if=、mkfs 等危险操作
"""
import re
import subprocess
import locale
from langchain_core.tools import tool

# 危险命令模式 — 只要包含 rm 命令就拦截
_DANGEROUS_PATTERNS = [
    re.compile(r'\brm\s'),                 # 任何 rm 命令
    re.compile(r'\bsudo\s+rm\s'),          # sudo rm
    re.compile(r'\bdd\s+if='),             # dd 覆盘
    re.compile(r'\bmkfs\b'),               # 格式化文件系统
    re.compile(r'\s>\s*/dev/sd'),          # 直接写磁盘设备
]


def _is_dangerous(command: str) -> str | None:
    """检查命令是否包含危险操作，若是则返回拒绝理由，否则返回 None"""
    for pattern in _DANGEROUS_PATTERNS:
        if pattern.search(command):
            return f"错误：拒绝执行危险命令（可能删除/破坏系统数据）。模式: '{pattern.pattern}'"
    return None


@tool
def bash(command: str, timeout: int = 120, run_in_background: bool = False) -> str:
    """执行 bash/shell 命令并返回标准输出/错误。

    适用场景：系统命令（ls/mkdir/pip）、Git 操作、Python 单行脚本
    （python -c 做数据计算/格式转换）、进程管理、curl/wget 等。
    不适用场景：文件搜索/内容搜索/读取/编辑/写入，请使用专用工具。

    Args:
        command: 要执行的 shell 命令字符串
        timeout: 超时时间（秒），默认 120 秒
        run_in_background: 是否后台运行（当前版本不支持，设为 True 将直接报错）
    """
    if run_in_background:
        return "错误：当前版本不支持后台运行模式"

    # 安全检查：阻止危险操作
    reason = _is_dangerous(command)
    if reason:
        return reason

    system_encoding = locale.getpreferredencoding(False)

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding=system_encoding,
            errors="replace",
        )

        output_parts = []
        if result.stdout:
            output_parts.append(result.stdout.rstrip())
        if result.stderr:
            output_parts.append(f"stderr:\n{result.stderr.rstrip()}")
        if result.returncode != 0:
            output_parts.append(f"退出码: {result.returncode}")

        if not output_parts:
            return "（命令执行成功，无输出）"

        return "\n".join(output_parts)

    except subprocess.TimeoutExpired:
        return f"错误：命令执行超时（{timeout} 秒）"
    except Exception as e:
        return f"错误：执行命令失败 - {e}"
