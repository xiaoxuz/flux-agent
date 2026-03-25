# nodes/base/config.py
"""
节点配置基类

定义节点的配置、重试策略、缓存策略等。
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class NodeConfig:
    """节点配置基类"""

    input_keys: List[str] = field(default_factory=list)
    output_keys: List[str] = field(default_factory=list)
    timeout: Optional[int] = None
    on_error: str = "stop"


@dataclass
class RetryPolicy:
    """重试策略"""

    max_attempts: int = 3
    initial_interval: float = 1.0
    max_interval: float = 10.0
    backoff_multiplier: float = 2.0
    retry_on: List[str] = field(default_factory=list)


@dataclass
class CachePolicy:
    """缓存策略"""

    enabled: bool = True
    ttl: int = 300
    key_template: str = ""
    scope: str = "thread"
