# core/registry.py
"""
节点注册表

管理所有可用节点类型的注册和查找。
支持内置节点和用户自定义节点。
"""
from __future__ import annotations
from typing import Any, Callable, Dict, Optional, Type
import importlib
import logging

logger = logging.getLogger(__name__)


class NodeRegistry:
    """
    节点注册表（单例模式）
    
    用于管理所有可用的节点类型：
    - 注册内置节点
    - 注册用户自定义节点
    - 通过类型名称查找节点类
    """
    
    _instance: Optional["NodeRegistry"] = None
    _initialized: bool = False
    
    def __new__(cls) -> "NodeRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._registry: Dict[str, Type] = {}
        self._factories: Dict[str, Callable] = {}
        self._load_entry_points()
        self._initialized = True
    
    def register(self, node_type: str, node_class: Type) -> None:
        """
        注册节点类型
        
        Args:
            node_type: 节点类型标识
            node_class: 节点类
        """
        if node_type in self._registry:
            logger.warning(f"节点类型 '{node_type}' 已存在，将被覆盖")
        self._registry[node_type] = node_class
        logger.debug(f"注册节点类型: {node_type} -> {node_class.__name__}")
    
    def register_factory(self, node_type: str, factory: Callable) -> None:
        """
        注册节点工厂函数
        
        Args:
            node_type: 节点类型标识
            factory: 工厂函数，接受配置参数返回节点实例
        """
        self._factories[node_type] = factory
        logger.debug(f"注册节点工厂: {node_type}")
    
    def register_all(self, nodes: Dict[str, Type]) -> None:
        """
        批量注册节点类型
        
        Args:
            nodes: 节点类型映射字典 {type_name: node_class}
        """
        for node_type, node_class in nodes.items():
            self.register(node_type, node_class)
    
    def get(self, node_type: str) -> Optional[Type]:
        """
        获取节点类
        
        Args:
            node_type: 节点类型标识
        
        Returns:
            节点类，如果不存在返回 None
        """
        if node_type in self._registry:
            return self._registry[node_type]
        
        if node_type in self._factories:
            return self._factories[node_type]
        
        return None
    
    def has(self, node_type: str) -> bool:
        """
        检查节点类型是否存在
        
        Args:
            node_type: 节点类型标识
        
        Returns:
            是否存在
        """
        return node_type in self._registry or node_type in self._factories
    
    def list_types(self) -> list[str]:
        """
        列出所有已注册的节点类型
        
        Returns:
            节点类型列表
        """
        return list(set(self._registry.keys()) | set(self._factories.keys()))
    
    def unregister(self, node_type: str) -> bool:
        """
        注销节点类型
        
        Args:
            node_type: 节点类型标识
        
        Returns:
            是否成功注销
        """
        removed = False
        if node_type in self._registry:
            del self._registry[node_type]
            removed = True
        if node_type in self._factories:
            del self._factories[node_type]
            removed = True
        return removed
    
    def clear(self) -> None:
        """清空注册表"""
        self._registry.clear()
        self._factories.clear()
    
    def _load_entry_points(self) -> None:
        """
        从入口点加载节点
        
        入口点定义在 pyproject.toml 中：
        [project.entry-points."flux_agent.nodes"]
        my_node = "my_package.nodes:MyNode"
        """
        try:
            import importlib.metadata as metadata
        except ImportError:
            import importlib_metadata as metadata
        
        try:
            entry_points = metadata.entry_points()
            if hasattr(entry_points, "select"):
                nodes_eps = entry_points.select(group="flux_agent.nodes")
            else:
                nodes_eps = entry_points.get("flux_agent.nodes", [])
            
            for ep in nodes_eps:
                try:
                    node_class = ep.load()
                    self.register(ep.name, node_class)
                    logger.info(f"从入口点加载节点: {ep.name}")
                except Exception as e:
                    logger.warning(f"加载入口点 {ep.name} 失败: {e}")
        except Exception as e:
            logger.debug(f"加载入口点时出错: {e}")


def register(node_type: str) -> Callable:
    """
    装饰器：注册节点类型
    
    Usage:
        @register("my_custom")
        class MyCustomNode(BaseNode):
            ...
    """
    def decorator(cls: Type) -> Type:
        registry = NodeRegistry()
        registry.register(node_type, cls)
        return cls
    return decorator


def get_registry() -> NodeRegistry:
    """获取全局注册表实例"""
    return NodeRegistry()


def load_node_class(import_path: str) -> Type:
    """
    从导入路径加载节点类
    
    Args:
        import_path: 导入路径，如 "my_package.nodes:MyNode"
    
    Returns:
        节点类
    """
    if ":" in import_path:
        module_path, class_name = import_path.rsplit(":", 1)
    else:
        parts = import_path.rsplit(".", 1)
        if len(parts) == 2:
            module_path, class_name = parts
        else:
            raise ValueError(f"无效的导入路径: {import_path}")
    
    module = importlib.import_module(module_path)
    node_class = getattr(module, class_name)
    return node_class
