# nodes/business/__init__.py
"""
业务节点目录

此目录用于存放项目特定的业务节点。

命名规范：
- 文件名：{业务域}_{动作}.py，如 order_analyze.py
- 类名：{业务域}{动作}Node，如 OrderAnalyzeNode

开发指南：
1. 继承 BaseNode 基类
2. 实现 run() 方法
3. 定义配置模型（如需要）
4. 在此文件中导出节点类
5. 在 BUSINESS_NODES 中注册

示例：
    # order_analyze.py
    from auto_agent.nodes.base import BaseNode, NodeConfig
    from pydantic import BaseModel

    class OrderAnalyzeConfig(NodeConfig):
        analyze_type: str = "basic"

    class OrderAnalyzeNode(BaseNode[OrderAnalyzeConfig]):
        @property
        def node_type(self) -> str:
            return "order_analyze"

        async def run(self) -> dict:
            # 实现业务逻辑
            return {"result": "analyzed"}
"""

from auto_agent.nodes.base import BaseNode

BUSINESS_NODES: dict[str, type[BaseNode]] = {}

__all__ = ["BUSINESS_NODES"]
