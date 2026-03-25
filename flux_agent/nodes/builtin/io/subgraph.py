# nodes/subgraph.py
"""
子图节点

将其他工作流作为子图嵌入。
"""
from __future__ import annotations
from typing import Any, Dict, Optional
from dataclasses import dataclass, field
import json
from pathlib import Path

from flux_agent.nodes.base import BaseNode, NodeConfig


@dataclass
class SubgraphNodeConfig(NodeConfig):
    """子图节点配置"""
    workflow_path: str = ""
    workflow: Dict[str, Any] = field(default_factory=dict)
    input_mapping: Dict[str, str] = field(default_factory=dict)
    output_mapping: Dict[str, str] = field(default_factory=dict)
    checkpointer: str = "inherit"
    thread_id_prefix: str = "sub_"


class SubgraphNode(BaseNode):
    """子图节点"""
    
    node_type = "subgraph"
    config_class = SubgraphNodeConfig
    
    def __init__(self, config: Dict[str, Any], **kwargs):
        super().__init__(config, **kwargs)
        self._subgraph = None
        self._subgraph_config = None
    
    def _load_subgraph_config(self) -> Dict[str, Any]:
        """加载子图配置"""
        if self._subgraph_config:
            return self._subgraph_config
        
        if self.config.workflow:
            self._subgraph_config = self.config.workflow
        elif self.config.workflow_path:
            path = Path(self.config.workflow_path)
            if not path.exists():
                raise FileNotFoundError(f"子图配置文件不存在: {path}")
            self._subgraph_config = json.loads(path.read_text(encoding="utf-8"))
        else:
            raise ValueError("必须提供 workflow_path 或 workflow 配置")
        
        return self._subgraph_config
    
    def execute(
        self,
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        subgraph_config = self._load_subgraph_config()
        
        subgraph_input = {}
        for dest_key, src_key in self.config.input_mapping.items():
            value = self._get_nested(state, src_key)
            if value is not None:
                subgraph_input[dest_key] = value
        
        return {
            "_subgraph": {
                "config": subgraph_config,
                "input": subgraph_input,
                "output_mapping": self.config.output_mapping,
                "checkpointer": self.config.checkpointer
            }
        }
