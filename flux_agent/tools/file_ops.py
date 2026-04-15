"""
文件操作专用工具集

每个工具都针对常见文件操作场景做了优化，比直接写 bash 命令更安全、
更高效、更易调试。ALWAYS 使用本工具集中的工具，NEVER 通过 bash
执行对应的 find/grep/cat/head/tail/sed/awk/echo 命令。
"""
import glob
import os
from langchain_core.tools import tool


@tool
def glob_search(pattern: str, path: str = "") -> str:
    """文件路径模式匹配搜索。ALWAYS 使用本工具进行文件路径搜索。NEVER 通过 bash 执行 find 或 ls。

    支持通配符：* 匹配任意字符，? 匹配单个字符，** 递归匹配子目录。
    例如：
        "**/*.py" - 递归查找所有 Python 文件
        "src/**/*.ts" - 在 src 下查找所有 TypeScript 文件
        "*.md" - 当前目录下的 Markdown 文件

    Args:
        pattern: 文件路径匹配模式，支持通配符
        path: 搜索起始目录，默认为当前工作目录
    """
    search_path = os.path.join(path, pattern) if path else pattern
    results = glob.glob(search_path, recursive=True)
    if not results:
        return f"未找到匹配 '{pattern}' 的文件"
    return "\n".join(results)


@tool
def grep_search(
    pattern: str,
    path: str = "",
    case_sensitive: bool = True,
    max_results: int = 100,
) -> str:
    """文件内容全文搜索。ALWAYS 使用本工具进行文件内容搜索。NEVER 通过 bash 执行 grep 或 rg。

    在指定目录下的文本文件中搜索包含目标模式的行。
    适用于快速定位代码、日志或配置文件中的关键内容。

    Args:
        pattern: 搜索模式（字符串匹配，非正则）
        path: 搜索起始目录，默认为当前工作目录
        case_sensitive: 是否区分大小写，默认区分
        max_results: 最大返回结果数，默认 100
    """
    search_path = path or os.getcwd()
    results = []
    count = 0

    for root, _, files in os.walk(search_path):
        if count >= max_results:
            break
        for filename in files:
            filepath = os.path.join(root, filename)
            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    for line_num, line in enumerate(f, 1):
                        search_line = line if case_sensitive else line.lower()
                        search_pattern = pattern if case_sensitive else pattern.lower()
                        if search_pattern in search_line:
                            results.append(f"{filepath}:{line_num}:{line.rstrip()}")
                            count += 1
                            if count >= max_results:
                                break
            except (PermissionError, OSError):
                continue

    if not results:
        return f"未找到包含 '{pattern}' 的内容"
    return "\n".join(results[:max_results])


@tool
def file_read(file_path: str, max_lines: int = 200, offset: int = 0) -> str:
    """读取文件内容。ALWAYS 使用本工具读取文件内容。NEVER 通过 bash 执行 cat/head/tail。

    支持指定起始行和最大行数，适合查看大型文件的部分内容。
    输出包含行号，方便后续定位和编辑。

    Args:
        file_path: 文件路径
        max_lines: 最大读取行数，默认 200
        offset: 起始行偏移（从 0 开始），默认从文件开头读取
    """
    if not os.path.exists(file_path):
        return f"错误：文件不存在 '{file_path}'"

    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        total_lines = len(lines)
        end = min(offset + max_lines, total_lines)
        selected = lines[offset:end]

        if not selected:
            return f"文件 '{file_path}' 共 {total_lines} 行，偏移 {offset} 处无内容"

        output_lines = [f"文件: {file_path} (共 {total_lines} 行, 显示 {offset}-{end-1})"]
        for i, line in enumerate(selected, offset):
            output_lines.append(f"{i:4d} | {line.rstrip()}")
        return "\n".join(output_lines)
    except PermissionError:
        return f"错误：无权限读取 '{file_path}'"
    except Exception as e:
        return f"错误：读取文件失败 - {e}"


@tool
def file_edit(file_path: str, old_string: str, new_string: str) -> str:
    """精确替换文件内容。ALWAYS 使用本工具编辑文件内容。NEVER 通过 bash 执行 sed/awk。

    在文件中查找第一个精确匹配的字符串并替换为新内容。
    要求 old_string 必须与文件内容完全匹配（包括缩进和换行）。
    建议先使用 file_read 确认目标内容后再调用本工具。

    Args:
        file_path: 文件路径
        old_string: 需要被替换的原文字符串（必须精确匹配）
        new_string: 替换后的新字符串
    """
    if not os.path.exists(file_path):
        return f"错误：文件不存在 '{file_path}'"

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        if old_string not in content:
            return (
                f"错误：在 '{file_path}' 中未找到精确匹配的原文。\n"
                f"请先使用 file_read 查看文件内容，确认原文后再试。"
            )

        new_content = content.replace(old_string, new_string, 1)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)

        return f"成功：已将 '{file_path}' 中第一处匹配内容替换为新字符串"
    except PermissionError:
        return f"错误：无权限修改 '{file_path}'"
    except Exception as e:
        return f"错误：编辑文件失败 - {e}"


@tool
def file_write(file_path: str, content: str) -> str:
    """写入文件内容（覆盖或新建）。ALWAYS 使用本工具写入文件。NEVER 通过 bash 执行 echo>/cat<<EOF。

    如果文件已存在则覆盖内容，如果不存在则创建新文件（含自动创建中间目录）。
    适用于创建新文件或完全重写已有文件。如需部分修改请使用 file_edit。

    Args:
        file_path: 文件路径
        content: 要写入的完整内容
    """
    try:
        parent_dir = os.path.dirname(file_path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        action = "已创建" if not os.path.exists(file_path) else "已覆盖"
        lines = content.count("\n") + 1
        return f"成功：{action} '{file_path}'（{lines} 行）"
    except PermissionError:
        return f"错误：无权限写入 '{file_path}'"
    except Exception as e:
        return f"错误：写入文件失败 - {e}"
