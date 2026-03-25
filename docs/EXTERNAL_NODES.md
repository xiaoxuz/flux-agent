# 外部节点开发指南

## 一、概述

将业务节点作为独立 Python 包开发，通过 `entry_points` 自动注册到 auto-agent。

**优势：**
- 独立版本管理
- 多项目复用
- 独立发布周期

---

## 二、项目结构

```
my-business-nodes/
├── pyproject.toml
├── README.md
└── my_nodes/
    ├── __init__.py
    └── video_process.py
```

---

## 三、编写节点

```python
# my_nodes/video_process.py
from flux_agent.nodes.base import BaseNode, NodeConfig
from dataclasses import dataclass
from typing import Any, Dict

@dataclass
class VideoProcessConfig(NodeConfig):
    output_format: str = "mp4"

class VideoProcessNode(BaseNode):
    node_type = "video_process"
    config_class = VideoProcessConfig
    
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        video_url = self._get_nested(state, "data.video_url")
        result = self._process(video_url)
        return self._set_nested({}, "data.result", result)
    
    def _process(self, url: str) -> Dict:
        return {"url": url, "format": self.config.output_format}
```

---

## 四、配置 pyproject.toml

```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "my-business-nodes"
version = "1.0.0"
dependencies = ["auto-agent>=0.1.0"]

# 关键：注册节点
[project.entry-points."flux_agent.nodes"]
video_process = "my_nodes.video_process:VideoProcessNode"

[tool.setuptools.packages.find]
where = ["."]
include = ["my_nodes*"]
```

---

## 五、安装使用

```bash
# 开发模式
pip install -e .

# 从 PyPI 安装
pip install my-business-nodes
```

使用：

```python
from flux_agent import WorkflowRunner

# 节点已自动注册
config = {
    "nodes": [
        {"id": "process", "type": "video_process", "config": {"output_format": "mp4"}}
    ]
}

runner = WorkflowRunner(config_dict=config)
result = runner.invoke({"data": {"video_url": "https://..."}})
```

---

## 六、调试

```bash
# 安装框架
pip install -e /path/to/auto-agent

# 安装业务节点
pip install -e .

# 验证注册
python -c "
from flux_agent.core.registry import NodeRegistry
print(NodeRegistry().list_types())
"
```

---

## 七、发布

```bash
pip install build twine
python -m build
twine upload dist/*
```
