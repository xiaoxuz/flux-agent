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

from auto_agent.nodes.base import BaseNode, NodeConfig

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

                try:
                    from langchain.messages import ToolMessage

                    messages.append(
                        ToolMessage(content=str(tool_result), tool_call_id=tool_call.get("id", ""))
                    )
                except ImportError:
                    messages.append(
                        {
                            "role": "tool",
                            "content": str(tool_result),
                            "tool_call_id": tool_call.get("id", ""),
                        }
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
            user_content = self._interpolate(self.config.user_prompt, state)
            assistant_content = (
                result if isinstance(result, str) else json.dumps(result, ensure_ascii=False)
            )
            if "messages" not in output:
                output["messages"] = []
            output["messages"].append({"role": "user", "content": user_content})
            output["messages"].append({"role": "assistant", "content": assistant_content})

        return output

    def _build_messages(self, state: Dict[str, Any]) -> List:
        """构建消息列表"""
        messages = []

        existing_messages = state.get("messages", [])
        if existing_messages:
            messages.extend(existing_messages)

        if self.config.system_prompt:
            try:
                from langchain.messages import SystemMessage

                system_content = self._interpolate(self.config.system_prompt, state)
                messages.append(SystemMessage(content=system_content))
            except ImportError:
                messages.append(
                    {
                        "role": "system",
                        "content": self._interpolate(self.config.system_prompt, state),
                    }
                )

        if self.config.user_prompt:
            user_content = self._interpolate(self.config.user_prompt, state)
            try:
                from langchain.messages import HumanMessage

                messages.append(HumanMessage(content=user_content))
            except ImportError:
                messages.append({"role": "user", "content": user_content})

        return messages
