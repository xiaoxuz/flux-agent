# gvideo-nodes

Auto-Agent 外部节点示例包。

## 安装

```bash
cd examples/external_nodes_example
pip install -e .
```

## 验证

```bash
python -c "from core.registry import NodeRegistry; r = NodeRegistry(); print(r.list_types())"
# 应该看到 'video_render' 节点
```

## 使用

安装后，`video_render` 节点自动注册到框架，可在 JSON 配置中直接使用：

```json
{
  "nodes": [
    {
      "id": "render",
      "type": "video_render",
      "config": {
        "output_format": "mp4",
        "resolution": "4k",
        "quality": "high"
      }
    }
  ]
}
```

## 工作原理

```
pyproject.toml 中的配置：

[project.entry-points."auto_agent.nodes"]
video_render = "gvideo_nodes.video_render:VideoRenderNode"

↓ 安装后自动注册到 NodeRegistry
↓ 框架启动时扫描 entry_points
↓ 用户在 JSON 中直接使用 "type": "video_render"
```
