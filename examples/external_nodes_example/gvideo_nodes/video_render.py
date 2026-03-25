# gvideo_nodes/video_render.py
"""视频渲染节点示例"""

from nodes.base import BaseNode, NodeConfig
from dataclasses import dataclass
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class VideoRenderConfig(NodeConfig):
    """视频渲染配置"""

    output_format: str = "mp4"
    resolution: str = "1080p"
    quality: str = "high"


class VideoRenderNode(BaseNode):
    """
    视频渲染节点

    功能：模拟视频渲染流程
    - 接收脚本 JSON
    - 返回渲染任务信息
    """

    node_type = "video_render"
    config_class = VideoRenderConfig

    def execute(
        self, state: Dict[str, Any], config: Optional[Any] = None, runtime: Optional[Any] = None
    ) -> Dict[str, Any]:
        logger.info(f"VideoRenderNode 开始执行，格式: {self.config.output_format}")

        script_data = self._get_nested(state, "data.script", {})
        tid = self._get_nested(state, "data.tid", "unknown")

        if not script_data:
            return {"errors": ["缺少 script 数据"], "data": {"render_status": "failed"}}

        render_result = {
            "task_id": f"task_{tid}",
            "status": "rendering",
            "config": {
                "format": self.config.output_format,
                "resolution": self.config.resolution,
                "quality": self.config.quality,
            },
            "script_preview": str(script_data)[:100] + "..."
            if len(str(script_data)) > 100
            else script_data,
        }

        logger.info(f"渲染任务已创建: {render_result['task_id']}")

        return self._set_nested({}, "data.render_result", render_result)
