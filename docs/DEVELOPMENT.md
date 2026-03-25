# 开发、测试、发布指南

本文档详细说明 auto-agent 模块的开发、测试和发布流程。

---

## 一、开发环境搭建

### 1.1 克隆项目

```bash
git clone https://github.com/xiaoxuz/auto-agent.git
cd auto-agent
```

### 1.2 创建虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 1.3 安装开发依赖

```bash
# 可编辑模式安装（代码修改立即生效）
pip install -e ".[dev]"
```

### 1.4 验证安装

```bash
python -c "from flux_agent import WorkflowRunner; print('✅ 安装成功')"
```

---

## 二、本地开发工作流

### 2.1 目录结构

```
auto-agent/
├── flux_agent/          # 包代码（修改这里）
│   ├── __init__.py
│   ├── core/
│   ├── nodes/
│   └── utils/
├── examples/            # 示例脚本（本地测试用）
├── tests/               # 单元测试
├── docs/                # 文档
├── pyproject.toml       # 包配置
└── venv/                # 虚拟环境
```

### 2.2 修改代码

```bash
# 编辑 flux_agent/ 下的文件
vim flux_agent/core/executor.py
```

### 2.3 本地测试

**方式1：运行示例脚本**

```bash
./venv/bin/python examples/demo_llm.py
./venv/bin/python examples/test_condition_end.py
```

**方式2：Python 交互测试**

```python
from flux_agent import WorkflowRunner

config = {
    "workflow": {"name": "test"},
    "nodes": [...],
    "edges": [...]
}

runner = WorkflowRunner(config_dict=config)
result = runner.invoke({"data": {}})
print(result)
```

**方式3：运行单元测试**

```bash
pytest tests/
pytest tests/test_executor.py -v
```

### 2.4 代码检查

```bash
# 格式化
black flux_agent/

# Lint
ruff check flux_agent/ --fix

# 类型检查
mypy flux_agent/
```

---

## 三、测试方法

### 3.1 在 examples/ 目录创建测试脚本

```python
# examples/test_my_feature.py
from flux_agent import WorkflowRunner

def test_something():
    config = {
        "workflow": {"name": "test"},
        "nodes": [...],
        "edges": [...]
    }
    
    runner = WorkflowRunner(config_dict=config)
    result = runner.invoke({"data": {"input": "test"}})
    
    assert result["data"]["result"] == "expected"
    print("✅ 测试通过")

if __name__ == "__main__":
    test_something()
```

运行测试：

```bash
./venv/bin/python examples/test_my_feature.py
```

### 3.2 编写单元测试

```python
# tests/test_executor.py
import pytest
from flux_agent import WorkflowRunner

def test_simple_workflow():
    config = {
        "workflow": {"name": "test"},
        "nodes": [
            {
                "id": "transform",
                "type": "TransformNode",
                "config": {
                    "transforms": [
                        {"action": "set", "key": "data.value", "value": 42}
                    ]
                }
            }
        ],
        "edges": [
            {"from": "START", "to": "transform"},
            {"from": "transform", "to": "END"}
        ]
    }
    
    runner = WorkflowRunner(config_dict=config)
    result = runner.invoke({"data": {}})
    
    assert result["data"]["value"] == 42
```

运行：

```bash
pytest tests/test_executor.py -v
```

### 3.3 测试新节点

```python
# examples/test_custom_node.py
from flux_agent import WorkflowRunner
from flux_agent.nodes.base import BaseNode, NodeConfig
from dataclasses import dataclass
from typing import Any, Dict

@dataclass
class MyNodeConfig(NodeConfig):
    prefix: str = ""

class MyNode(BaseNode):
    node_type = "my_node"
    config_class = MyNodeConfig
    
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        value = self._get_nested(state, "data.input", "")
        result = f"{self.config.prefix}{value}"
        return {"data": {"result": result}}

# 测试
config = {
    "workflow": {"name": "test"},
    "nodes": [
        {
            "id": "process",
            "type": "my_node",
            "config": {"prefix": "Hello, "}
        }
    ],
    "edges": [
        {"from": "START", "to": "process"},
        {"from": "process", "to": "END"}
    ]
}

runner = WorkflowRunner(
    config_dict=config,
    custom_nodes={"my_node": MyNode}
)

result = runner.invoke({"data": {"input": "World"}})
print(result)  # {"data": {"input": "World", "result": "Hello, World"}}
```

---

## 四、版本管理

### 4.1 版本号规则

遵循 [Semantic Versioning](https://semver.org/)：

```
MAJOR.MINOR.PATCH

MAJOR - 不兼容的 API 变更
MINOR - 向后兼容的新功能
PATCH - 向后兼容的 bug 修复
```

### 4.2 更新版本号

**位置1：pyproject.toml**

```toml
[project]
name = "auto-agent"
version = "0.1.1"  # 修改这里
```

**位置2：flux_agent/__init__.py**

```python
__version__ = "0.1.1"  # 修改这里
```

### 4.3 更新 CHANGELOG.md

```markdown
# Changelog

## [0.1.1] - 2025-03-25

### Added
- 新增 XXX 功能

### Fixed
- 修复 XXX 问题

### Changed
- 优化 XXX 性能
```

---

## 五、发布流程

### 5.1 发布前检查清单

```bash
# 1. 确保所有测试通过
pytest tests/

# 2. 运行示例验证
./venv/bin/python examples/demo_llm.py

# 3. 代码格式化
black flux_agent/
ruff check flux_agent/ --fix

# 4. 更新版本号
#    - pyproject.toml
#    - flux_agent/__init__.py

# 5. 更新 CHANGELOG.md

# 6. 提交代码
git add .
git commit -m "chore: release v0.1.1"
```

### 5.2 构建包

```bash
# 清理旧构建
rm -rf dist/ build/ *.egg-info

# 安装构建工具
pip install build twine

# 构建
python -m build
```

构建完成后会在 `dist/` 目录生成：

```
dist/
├── flux_agent-0.1.1-py3-none-any.whl
└── flux_agent-0.1.1.tar.gz
```

### 5.3 检查构建

```bash
# 检查包内容
tar -tzf dist/flux_agent-0.1.1.tar.gz | head -20

# 检查 wheel
unzip -l dist/flux_agent-0.1.1-py3-none-any.whl | head -20

# 验证元数据
twine check dist/*
```

### 5.4 本地安装测试

```bash
# 卸载当前版本
pip uninstall auto-agent -y

# 安装构建的包
pip install dist/flux_agent-0.1.1-py3-none-any.whl

# 验证
python -c "
from flux_agent import WorkflowRunner
print('版本:', __import__('flux_agent').__version__)
runner = WorkflowRunner(config_dict={'workflow': {'name': 'test'}, 'nodes': [], 'edges': []})
print('✅ 安装成功')
"
```

### 5.5 发布到 TestPyPI（测试）

```bash
# 上传到 TestPyPI
twine upload --repository testpypi dist/*

# 从 TestPyPI 安装测试
pip install --index-url https://test.pypi.org/simple/ auto-agent
```

### 5.6 发布到 PyPI（正式）

```bash
# 上传到 PyPI
twine upload dist/*
```

### 5.7 验证发布

```bash
# 等待几分钟让 PyPI 索引更新

# 创建新的虚拟环境测试
python -m venv test_env
source test_env/bin/activate

# 从 PyPI 安装
pip install auto-agent

# 验证
python -c "
from flux_agent import WorkflowRunner
print('版本:', __import__('flux_agent').__version__)
"

# 清理测试环境
deactivate
rm -rf test_env
```

### 5.8 打 Git Tag

```bash
git tag -a v0.1.1 -m "Release v0.1.1"
git push origin v0.1.1
```

---

## 六、迭代开发流程

### 6.1 修改代码

```bash
# 切换到主分支
git checkout main
git pull origin main

# 创建开发分支
git checkout -b feature/new-feature

# 修改代码...
vim flux_agent/core/executor.py
```

### 6.2 本地测试

```bash
# 运行测试
pytest tests/

# 运行示例
./venv/bin/python examples/demo_llm.py
```

### 6.3 提交代码

```bash
git add .
git commit -m "feat: add new feature"
git push origin feature/new-feature
```

### 6.4 合并到主分支

```bash
git checkout main
git merge feature/new-feature
git push origin main
```

### 6.5 发布新版本

重复「五、发布流程」

---

## 七、常见问题

### Q1: 如何在不发布的情况下测试？

```bash
# 可编辑模式安装，代码修改立即生效
pip install -e .

# 然后直接运行测试
./venv/bin/python examples/test_xxx.py
```

### Q2: 如何测试发布后的包？

```bash
# 创建干净的环境
python -m venv clean_env
source clean_env/bin/activate

# 从 PyPI 安装
pip install auto-agent

# 测试
python -c "from flux_agent import WorkflowRunner; print('OK')"
```

### Q3: 发布失败怎么办？

```bash
# 检查版本号是否已存在
curl -s https://pypi.org/pypi/auto-agent/json | grep version

# 如果版本已存在，需要更新版本号
# 修改 pyproject.toml 和 __init__.py
```

### Q4: 如何撤销发布？

PyPI 不支持撤销已发布的版本，只能发布新版本修复。TestPyPI 可以删除：

```bash
# 需要在 PyPI 网站上操作
# https://test.pypi.org/manage/project/auto-agent/releases/
```

### Q5: 如何在业务项目中测试开发中的 auto-agent？

```bash
# 方式1：本地路径安装
pip install -e /path/to/auto-agent

# 方式2：Git 安装
pip install git+https://github.com/xiaoxuz/auto-agent.git@main

# 方式3：指定分支
pip install git+https://github.com/xiaoxuz/auto-agent.git@feature/xxx
```

---

## 八、完整示例：从开发到发布

```bash
# ========== 1. 开发 ==========
# 修改代码
vim flux_agent/core/executor.py

# 本地测试
./venv/bin/python examples/demo_llm.py

# ========== 2. 提交 ==========
git add .
git commit -m "feat: add new feature"
git push origin main

# ========== 3. 更新版本 ==========
# 修改 pyproject.toml: version = "0.1.1"
# 修改 flux_agent/__init__.py: __version__ = "0.1.1"
# 更新 CHANGELOG.md

# ========== 4. 构建 ==========
rm -rf dist/ build/
python -m build

# ========== 5. 本地验证 ==========
pip uninstall auto-agent -y
pip install dist/flux_agent-0.1.1-py3-none-any.whl
./venv/bin/python examples/demo_llm.py

# ========== 6. 发布 ==========
twine upload dist/*

# ========== 7. 打 Tag ==========
git tag -a v0.1.1 -m "Release v0.1.1"
git push origin v0.1.1

# ========== 8. 验证发布 ==========
pip install auto-agent --upgrade
python -c "from flux_agent import WorkflowRunner; print('OK')"
```

---

## 九、快速参考命令

```bash
# 开发
pip install -e ".[dev]"        # 安装开发依赖
pytest tests/                  # 运行测试
black flux_agent/              # 格式化
ruff check flux_agent/ --fix   # Lint

# 构建
python -m build                # 构建
twine check dist/*             # 检查

# 发布
twine upload dist/*            # 发布到 PyPI
twine upload --repository testpypi dist/*  # 发布到 TestPyPI

# Git
git tag -a v0.1.0 -m "Release v0.1.0"
git push origin v0.1.0
```
