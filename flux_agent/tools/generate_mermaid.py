"""
通用 Workflow JSON → Mermaid 转换器

支持的节点类型：自动识别，无需硬编码
支持的边类型：普通边、条件边
"""

import json
import sys
from typing import Any, Dict, List, Optional


# 节点类型对应的图标和形状
NODE_TYPE_ICONS = {
    "TransformNode": "🔄",
    "HTTPRequestNode": "🌐",
    "LLMNode": "🤖",
    "ConditionNode": "🔀",
    "ToolNode": "🔧",
    "HumanNode": "👤",
    "SubGraphNode": "📦",
}

# 节点类型对应的颜色
NODE_TYPE_COLORS = {
    "TransformNode": "#2196F3",
    "HTTPRequestNode": "#FF9800",
    "LLMNode": "#4CAF50",
    "ConditionNode": "#9C27B0",
    "ToolNode": "#795548",
    "HumanNode": "#E91E63",
    "SubGraphNode": "#607D8B",
}


def get_node_icon(node_type: str) -> str:
    """获取节点图标"""
    return NODE_TYPE_ICONS.get(node_type, "📌")


def get_node_color(node_type: str) -> str:
    """获取节点颜色"""
    return NODE_TYPE_COLORS.get(node_type, "#666666")


def get_node_description(node: Dict[str, Any]) -> str:
    """从节点配置中提取简要描述"""
    node_type = node.get("type", "")
    config = node.get("config", {})
    parts = []

    if node_type == "TransformNode":
        transforms = config.get("transforms", [])
        for t in transforms[:3]:  # 最多显示3个
            action = t.get("action", "")
            key = t.get("key", "").split(".")[-1]  # 取最后一段
            if action == "set":
                value = t.get("value", "")
                if isinstance(value, str) and len(value) > 15:
                    value = value[:15] + "..."
                elif isinstance(value, (list, dict)):
                    value = str(value)[:15] + "..."
                parts.append(f"{action} {key}={value}")
            else:
                parts.append(f"{action} {key}")
        if len(transforms) > 3:
            parts.append(f"...共{len(transforms)}项")

    elif node_type == "LLMNode":
        model = config.get("model_name", config.get("model", ""))
        if model:
            parts.append(f"模型: {model}")
        output = config.get("output_key", "")
        if output:
            parts.append(f"输出: {output.split('.')[-1]}")
        tools = config.get("tools", [])
        if tools:
            parts.append(f"工具: {', '.join(tools)}")

    elif node_type == "HTTPRequestNode":
        method = config.get("method", "GET")
        url = config.get("url", "")
        # 只取路径部分
        if "/" in url:
            path = "/" + "/".join(url.split("/")[-2:])
        else:
            path = url
        parts.append(f"{method} {path}")
        output = config.get("output_key", "")
        if output:
            parts.append(f"输出: {output.split('.')[-1]}")

    elif node_type == "ConditionNode":
        branches = config.get("branches", [])
        for b in branches[:3]:
            cond = b.get("condition", "")
            target = b.get("target", "")
            if cond == "default":
                parts.append(f"default → {target}")
            else:
                # 简化条件表达式
                short_cond = cond.replace("data.", "").replace("context.", "")
                if len(short_cond) > 25:
                    short_cond = short_cond[:25] + "..."
                parts.append(f"{short_cond} → {target}")

    elif node_type == "ToolNode":
        tool = config.get("tool_name", "")
        if tool:
            parts.append(f"工具: {tool}")
        output = config.get("output_key", "")
        if output:
            parts.append(f"输出: {output.split('.')[-1]}")

    return "<br/>".join(parts) if parts else node_type

    
def sanitize_id(node_id: str) -> str:
    """清理节点ID，确保 mermaid 兼容"""
    return node_id.replace("-", "_").replace(" ", "_")


def workflow_to_mermaid(
    workflow_json: Dict[str, Any],
    direction: str = "TD",
    show_details: bool = True,
    show_styles: bool = True,
    show_subgraph: bool = False,
) -> str:
    """
    将 workflow JSON 转换为 Mermaid 流程图

    Args:
        workflow_json: workflow 配置 JSON
        direction: 流程图方向 TD(上到下) / LR(左到右)
        show_details: 是否显示节点详细信息
        show_styles: 是否添加样式
        show_subgraph: 是否按节点类型分组

    Returns:
        Mermaid 格式字符串
    """
    nodes = workflow_json.get("nodes", [])
    edges = workflow_json.get("edges", [])
    workflow_info = workflow_json.get("workflow", {})

    # 构建节点映射
    node_map: Dict[str, Dict[str, Any]] = {}
    for node in nodes:
        node_map[node["id"]] = node

    lines: List[str] = []

    # 标题注释
    workflow_name = workflow_info.get("name", "workflow")
    workflow_desc = workflow_info.get("description", "")
    lines.append(f"---")
    lines.append(f"title: {workflow_name}")
    lines.append(f"---")

    lines.append(f"graph {direction}")

    # ===== 节点定义 =====
    lines.append("")
    lines.append("    %% === 节点定义 ===")

    for node in nodes:
        nid = sanitize_id(node["id"])
        node_type = node.get("type", "Unknown")
        icon = get_node_icon(node_type)

        if show_details:
            desc = get_node_description(node)
            label = f"{icon} {node['id']}<br/><small>{node_type}</small><br/>{desc}"
        else:
            label = f"{icon} {node['id']}<br/>{node_type}"

        # ConditionNode 用菱形，其他用方框
        if node_type == "ConditionNode":
            lines.append(f'    {nid}{{"{label}"}}')
        else:
            lines.append(f'    {nid}["{label}"]')

    # ===== 边定义 =====
    lines.append("")
    lines.append("    %% === 边定义 ===")

    for edge in edges:
        from_id = sanitize_id(edge["from"])
        
        # 处理 START / END 特殊节点
        if edge["from"] == "START":
            from_id = "START"
            lines.append(f'    START(["🚀 START"])')
        
        # 普通边
        if "to" in edge:
            to_id = sanitize_id(edge["to"])
            if edge["to"] == "END":
                to_id = "END"
                # 确保 END 节点被定义（去重由 mermaid 处理）
                lines.append(f'    END(["🏁 END"])')
            lines.append(f"    {from_id} --> {to_id}")

        # 条件边
        elif "condition_map" in edge:
            condition_map = edge["condition_map"]

            # 同时从节点配置中获取条件详情
            from_node = node_map.get(edge["from"], {})
            branches = from_node.get("config", {}).get("branches", [])
            
            # 构建 target → condition 的映射
            target_to_condition = {}
            for branch in branches:
                target = branch.get("target", "")
                condition = branch.get("condition", "")
                target_to_condition[target] = condition

            for label, target in condition_map.items():
                to_id = sanitize_id(target)
                if target == "END":
                    to_id = "END"
                    lines.append(f'    END(["🏁 END"])')
                
                # 尝试获取更详细的条件描述
                condition_text = target_to_condition.get(target, label)
                if condition_text == "default":
                    lines.append(f"    {from_id} -. \"{condition_text}\" .-> {to_id}")
                else:
                    # 简化条件文字
                    short = condition_text.replace("data.", "").replace("context.", "")
                    if len(short) > 30:
                        short = short[:30] + "..."
                    lines.append(f'    {from_id} -- "{short}" --> {to_id}')

            # 补充 condition_map 中没有但 branches 中有的 default 分支
            for branch in branches:
                target = branch.get("target", "")
                condition = branch.get("condition", "")
                if condition == "default" and target not in condition_map.values():
                    to_id = sanitize_id(target)
                    if target == "END":
                        to_id = "END"
                        lines.append(f'    END(["🏁 END"])')
                    lines.append(f'    {from_id} -. "default" .-> {to_id}')

    # ===== 样式 =====
    if show_styles:
        lines.append("")
        lines.append("    %% === 样式 ===")
        lines.append("    style START fill:#4CAF50,color:#fff,stroke:#388E3C")
        lines.append("    style END fill:#f44336,color:#fff,stroke:#D32F2F")
        
        for node in nodes:
            nid = sanitize_id(node["id"])
            color = get_node_color(node.get("type", ""))
            lines.append(f"    style {nid} fill:{color},color:#fff,stroke:{color}")

    return "\n".join(lines)


def workflow_to_mermaid_simple(workflow_json: Dict[str, Any], direction: str = "TD") -> str:
    """
    简洁版：只显示节点名和类型，不显示详细配置
    """
    return workflow_to_mermaid(workflow_json, direction=direction, show_details=False, show_styles=False)


def save_mermaid_markdown(mermaid_str: str, output_path: str, title: str = "Workflow") -> None:
    """保存为 Markdown 文件"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n")
        f.write("```mermaid\n")
        f.write(mermaid_str)
        f.write("\n```\n")
    print(f"✅ Markdown 已保存到: {output_path}")


def save_mermaid_html(mermaid_str: str, output_path: str, title: str = "Workflow") -> None:
    """保存为可直接打开的 HTML 文件"""
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; padding: 20px; background: #f5f5f5; }}
        h1 {{ color: #333; }}
        .mermaid {{ background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <div class="mermaid">
{mermaid_str}
    </div>
    <script>mermaid.initialize({{startOnLoad: true, theme: 'default'}});</script>
</body>
</html>"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ HTML 已保存到: {output_path} (浏览器打开即可查看)")


def convert(
    input_path: str,
    output_path: Optional[str] = None,
    direction: str = "TD",
    format: str = "markdown",
    simple: bool = False,
) -> str:
    """
    主入口：读取 JSON 文件，转换为 Mermaid，保存到文件

    Args:
        input_path: 输入 JSON 文件路径
        output_path: 输出文件路径，默认根据 format 自动生成
        direction: TD(上到下) / LR(左到右)
        format: markdown / html / raw
        simple: 是否使用简洁模式
    
    Returns:
        Mermaid 字符串
    """
    with open(input_path, "r", encoding="utf-8") as f:
        workflow_json = json.load(f)

    workflow_name = workflow_json.get("workflow", {}).get("name", "workflow")

    if simple:
        mermaid_str = workflow_to_mermaid_simple(workflow_json, direction)
    else:
        mermaid_str = workflow_to_mermaid(workflow_json, direction)

    if output_path is None:
        ext = ".html" if format == "html" else ".md" if format == "markdown" else ".mmd"
        output_path = input_path.rsplit(".", 1)[0] + ext

    if format == "html":
        save_mermaid_html(mermaid_str, output_path, workflow_name)
    elif format == "markdown":
        save_mermaid_markdown(mermaid_str, output_path, workflow_name)
    else:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(mermaid_str)
        print(f"✅ Mermaid 已保存到: {output_path}")

    return mermaid_str


# ===== CLI =====
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Workflow JSON → Mermaid 转换器")
    parser.add_argument("input", help="输入 JSON 文件路径")
    parser.add_argument("-o", "--output", help="输出文件路径")
    parser.add_argument("-d", "--direction", default="TD", choices=["TD", "LR", "BT", "RL"],
                        help="流程图方向: TD(上到下)/LR(左到右)/BT(下到上)/RL(右到左)")
    parser.add_argument("-f", "--format", default="markdown", choices=["markdown", "html", "raw"],
                        help="输出格式: markdown/html/raw(纯mermaid)")
    parser.add_argument("-s", "--simple", action="store_true",
                        help="简洁模式，只显示节点名和类型")
    parser.add_argument("--print", action="store_true", dest="print_output",
                        help="同时打印到终端")

    args = parser.parse_args()

    mermaid_str = convert(
        input_path=args.input,
        output_path=args.output,
        direction=args.direction,
        format=args.format,
        simple=args.simple,
    )

    if args.print_output:
        print("\n" + "=" * 60)
        print(mermaid_str)
        print("=" * 60)