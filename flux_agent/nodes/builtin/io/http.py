# nodes/http.py
"""
HTTP 请求节点

执行 HTTP API 调用。
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
import json

from flux_agent.nodes.base import BaseNode, NodeConfig


@dataclass
class HTTPRequestNodeConfig(NodeConfig):
    """HTTP 请求节点配置"""

    url: str = ""
    method: str = "GET"
    headers: Dict[str, str] = field(default_factory=dict)
    params: Dict[str, Any] = field(default_factory=dict)
    body: Any = None
    response_key: str = ""
    output_key: str = "data.http_result"
    timeout: int = 30
    retry_on: List[int] = field(default_factory=list)
    parse_response: bool = True


class HTTPRequestNode(BaseNode):
    """HTTP 请求节点"""

    node_type = "http_request"
    config_class = HTTPRequestNodeConfig

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            import requests
        except ImportError:
            raise ImportError("请安装 requests: pip install requests")

        url = self._interpolate(self.config.url, state)
        headers = self._interpolate_dict(self.config.headers, state)
        params = self._interpolate_dict(self.config.params, state)
        body = self._interpolate_value(self.config.body, state)

        try:
            response = requests.request(
                method=self.config.method.upper(),
                url=url,
                headers=headers,
                params=params,
                json=body if body else None,
                timeout=self.config.timeout,
            )

            if response.status_code >= 400:
                return {
                    "errors": [f"HTTP {response.status_code}: {response.text[:500]}"],
                    self.config.output_key.split(".")[0]
                    if "." in self.config.output_key
                    else "data": {
                        "status_code": response.status_code,
                        "error": response.text[:500],
                    },
                }

            result = response.text

            if self.config.parse_response:
                try:
                    result = response.json()
                except json.JSONDecodeError:
                    pass

            if isinstance(result, dict) and self.config.response_key:
                result = self._interpolate_value(self.config.response_key, result)

            return self._set_nested({}, self.config.output_key, result)

        except Exception as e:
            return {"errors": [f"HTTP 请求失败: {e}"]}
