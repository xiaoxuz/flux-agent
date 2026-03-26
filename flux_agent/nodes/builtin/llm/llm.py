# nodes/llm.py
"""
LLM 节点

调用大语言模型的节点实现。
支持工具绑定和自动执行 tool_calls。
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
import json
import logging
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage

from flux_agent.nodes.base import BaseNode, NodeConfig

logger = logging.getLogger(__name__)


@dataclass
class LLMNodeConfig(NodeConfig):
    """LLM 节点配置"""

    model_name: str = "gpt-4o"
    system_prompt: str = ""
    user_prompt: str = ""
    output_key: str = "data.output"
    temperature: float = 0.0
    max_tokens: int = 4096
    tools: List[str] = field(default_factory=list)
    image_list: List[str] = field(default_factory=list)  # 图片 URL 列表
    video_list: List[str] = field(default_factory=list)  # 视频 URL 列表（仅 mp4）
    tool_choice: str = "auto"
    parallel_tool_calls: bool = True
    response_format: Optional[Dict] = None
    stream: bool = False
    base_url: str = ""
    api_key: str = ""
    save_to_messages: bool = True
    max_tool_iterations: int = 10


class LLMNode(BaseNode):
    """
    LLM 调用节点

    支持多种模型提供商：
    - OpenAI (gpt-4o, gpt-4o-mini, etc.)
    - Anthropic (claude-sonnet-4-6, claude-haiku-4-5, etc.)
    - Google (gemini-2.0-flash, gemini-2.0-pro, etc.)

    支持工具调用：
    - 自动绑定工具到 LLM
    - 自动执行 tool_calls 并循环直到完成
    """

    node_type = "llm"
    config_class = LLMNodeConfig

    def __init__(self, config: Dict[str, Any], **kwargs):
        super().__init__(config, **kwargs)
        self._llm = None
        self._bound_tools = None
        self._tools_by_name = {}

    def _get_llm(self):
        """获取 LLM 实例"""
        if self._llm is None:
            try:
                from langchain_openai import ChatOpenAI
            except ImportError:
                raise ImportError("请安装 langchain: pip install langchain")

            model_kwargs = {}
            if self.config.response_format:
                rf_type = self.config.response_format.get("type")
                if rf_type == "json_object":
                    model_kwargs["response_format"] = {"type": "json_object"}
                elif rf_type == "json_schema":
                    model_kwargs["response_format"] = self.config.response_format

            llm_params = {
                "model": self.config.model_name,
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens,
            }

            if self.config.api_key:
                llm_params["api_key"] = self.config.api_key
            if self.config.base_url:
                llm_params["base_url"] = self.config.base_url
            if model_kwargs:
                llm_params["model_kwargs"] = model_kwargs

            self._llm = ChatOpenAI(**llm_params)

        return self._llm

    def _wrap_tool(self, func: callable, name: str = None) -> Any:
        """将普通函数包装为 LangChain Tool"""
        from langchain_core.tools import StructuredTool

        tool_name = name or func.__name__
        tool_description = func.__doc__ or f"Execute {tool_name}"

        wrapped = StructuredTool.from_function(
            func=func, name=tool_name, description=tool_description
        )

        return wrapped

    def _bind_tools(self, llm):
        """绑定工具到 LLM"""
        if not self.tools:
            return llm

        tools_to_bind = []
        for tool_name in self.config.tools:
            if tool_name not in self.tools:
                logger.warning(f"工具 {tool_name} 未注册")
                continue

            tool_def = self.tools[tool_name]

            if hasattr(tool_def, "invoke"):
                tools_to_bind.append(tool_def)
                self._tools_by_name[tool_name] = tool_def
            elif callable(tool_def):
                wrapped = self._wrap_tool(tool_def, tool_name)
                tools_to_bind.append(wrapped)
                self._tools_by_name[tool_name] = wrapped
            elif isinstance(tool_def, dict):
                impl = tool_def.get("implementation")
                if callable(impl):
                    wrapped = self._wrap_tool(impl, tool_name)
                    tools_to_bind.append(wrapped)
                    self._tools_by_name[tool_name] = wrapped

        if tools_to_bind:
            self._bound_tools = llm.bind_tools(tools_to_bind)
            return self._bound_tools

        return llm

    def _execute_tool_call(self, tool_call: Dict) -> Any:
        """执行单个工具调用"""
        tool_name = tool_call.get("name") or tool_call.get("function", {}).get("name")
        tool_args = tool_call.get("args") or tool_call.get("function", {}).get("arguments", {})

        if isinstance(tool_args, str):
            try:
                tool_args = json.loads(tool_args)
            except json.JSONDecodeError:
                tool_args = {}

        if tool_name not in self._tools_by_name:
            return f"Error: Tool {tool_name} not found"

        tool = self._tools_by_name[tool_name]

        try:
            result = tool.invoke(tool_args)
            return result
        except Exception as e:
            return f"Error executing {tool_name}: {str(e)}"

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """执行 LLM 调用，支持工具自动执行"""
        llm = self._get_llm()

        if self.config.tools and self._bound_tools is None:
            llm = self._bind_tools(llm)

        messages = self._build_messages(state)

        max_iterations = getattr(self.config, "max_tool_iterations", 10)
        iteration = 0

        while iteration < max_iterations:
            response = llm.invoke(messages)

            if not response.tool_calls:
                break

            iteration += 1

            messages.append(response)

            for tool_call in response.tool_calls:
                tool_result = self._execute_tool_call(tool_call)
                messages.append(
                    ToolMessage(content=str(tool_result), tool_call_id=tool_call.get("id", ""))
                )

        if hasattr(response, "content"):
            result = response.content
        else:
            result = str(response)

        if self.config.response_format and self.config.response_format.get("type") == "json_object":
            if isinstance(result, str):
                try:
                    result = json.loads(result)
                except json.JSONDecodeError:
                    pass

        output = self._set_nested({}, self.config.output_key, result)

        if getattr(self.config, "save_to_messages", True):
            assistant_content = (
                result if isinstance(result, str) else json.dumps(result, ensure_ascii=False)
            )
            if "messages" not in output:
                output["messages"] = []
            output["messages"].extend(messages)
            output["messages"].append({"role": "assistant", "content": assistant_content})

        return output

    def _is_base64(self, s: str) -> bool:
        """检查是否是纯 base64 字符串"""
        import base64

        try:
            if len(s) < 100:
                sample = s
            else:
                sample = s[:100]
            base64.b64decode(sample, validate=True)
            return True
        except Exception:
            return False

    def _guess_mime_type_from_url(self, url: str, default: str = "image/jpeg") -> str:
        """从 URL 推断 MIME type"""
        import mimetypes

        mime_type, _ = mimetypes.guess_type(url)
        return mime_type or default

    def _guess_mime_type_from_path(self, path: str, default: str = "image/jpeg") -> str:
        """从文件路径推断 MIME type"""
        import mimetypes

        mime_type, _ = mimetypes.guess_type(path)
        return mime_type or default

    def _download_to_base64(self, url: str, default_mime: str = "image/jpeg") -> tuple:
        """下载文件并转 base64"""
        import base64

        try:
            import httpx
        except ImportError:
            raise ImportError("请安装 httpx: pip install httpx")

        response = httpx.get(url, timeout=30, follow_redirects=True)
        response.raise_for_status()
        data = base64.b64encode(response.content).decode("utf-8")
        mime_type = self._guess_mime_type_from_url(url, default_mime)
        return data, mime_type

    def _read_local_file_to_base64(self, file_path: str, default_mime: str = "image/jpeg") -> tuple:
        """读取本地文件转 base64"""
        import base64
        import os

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        with open(file_path, "rb") as f:
            data = base64.b64encode(f.read()).decode("utf-8")
        mime_type = self._guess_mime_type_from_path(file_path, default_mime)
        return data, mime_type

    def _process_image(self, image_input: str, state: Dict[str, Any]) -> Dict:
        """
        处理图片输入，统一返回 base64 格式

        支持:
        - URL (http/https) -> 下载转 base64
        - data URI (data:image/...) -> 直接用
        - 本地文件路径 -> 读取转 base64
        - 纯 base64 字符串 -> 补充 MIME type

        返回: {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}}
        """
        import os

        value = self._interpolate(image_input, state)

        if value.startswith("data:image"):
            return {"type": "image_url", "image_url": {"url": value}}

        if value.startswith("http://") or value.startswith("https://"):
            image_data, mime_type = self._download_to_base64(value, "image/jpeg")
            return {
                "type": "image_url",
                "image_url": {"url": f"data:{mime_type};base64,{image_data}"},
            }

        if os.path.exists(value):
            image_data, mime_type = self._read_local_file_to_base64(value, "image/jpeg")
            return {
                "type": "image_url",
                "image_url": {"url": f"data:{mime_type};base64,{image_data}"},
            }

        if self._is_base64(value):
            mime_type = self._guess_mime_type_from_url(value, "image/jpeg")
            return {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{value}"}}

        return {"type": "image_url", "image_url": {"url": value}}

    def _process_video(self, video_input: str, state: Dict[str, Any]) -> Dict:
        """
        处理视频输入

        支持:
        - URL (http/https) -> 直接用 URL
        - data URI (data:video/...) -> 提取 base64
        - 本地文件路径 -> 读取转 base64
        - 纯 base64 字符串 -> 补充 MIME type (video/mp4)

        返回: {"type": "video", "url": "..."} 或 {"type": "video", "base64": "...", "mime_type": "..."}
        """
        import os

        value = self._interpolate(video_input, state)

        if value.startswith("http://") or value.startswith("https://"):
            return {"type": "video", "url": value}

        if value.startswith("data:video"):
            parts = value.split(",", 1)
            if len(parts) == 2:
                base64_data = parts[1]
                mime_part = parts[0].split(":")[1].split(";")[0]
                return {"type": "video", "base64": base64_data, "mime_type": mime_part}
            return {"type": "video", "url": value}

        if os.path.exists(value):
            video_data, mime_type = self._read_local_file_to_base64(value, "video/mp4")
            return {"type": "video", "base64": video_data, "mime_type": mime_type}

        if self._is_base64(value):
            return {"type": "video", "base64": value, "mime_type": "video/mp4"}

        return {"type": "video", "url": value}

    def _build_messages(self, state: Dict[str, Any]) -> List:
        """构建消息列表，支持多模态"""
        messages = []

        existing_messages = state.get("messages", [])
        if existing_messages:
            messages.extend(existing_messages)

        if self.config.system_prompt:
            content = [
                {"type": "text", "text": self._interpolate(self.config.system_prompt, state)}
            ]
            messages.append(SystemMessage(content=content))

        human_content = []

        if self.config.user_prompt:
            text = self._interpolate(self.config.user_prompt, state)
            human_content.append({"type": "text", "text": text})

        for image_input in self.config.image_list:
            human_content.append(self._process_image(image_input, state))

        for video_input in self.config.video_list:
            human_content.append(self._process_video(video_input, state))

        if human_content:
            messages.append(HumanMessage(content=human_content))

        return messages
