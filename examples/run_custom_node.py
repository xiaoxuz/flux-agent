#!/usr/bin/env python3
"""
示例：自定义节点

使用方法：
    ./venv/bin/python examples/run_custom_node.py
"""
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Any, Dict, Optional
import logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S"
)
example_dir = Path(__file__).parent

from auto_agent import WorkflowRunner
from auto_agent.nodes.base import BaseNode, NodeConfig
from auto_agent.core.registry import NodeRegistry

def example_input_hook(node_id, state):
    # print(f"[IN]>>>>>>>>>>>>>> {node_id}: {state.get('data', {})}")
    pass
    # return state  # 可修改后返回

def example_output_hook(node_id, state, output):
    # print(f"[OUT]<<<<<<<<<<<<< {node_id}: {output}")
    pass

def main():
    # NodeRegistry.register_node("save_answer", SaveAnswerNode)

    runner = WorkflowRunner(
        config_path=str(example_dir / "custom_nodes.json"), 
        on_node_input=example_input_hook,
        on_node_output=example_output_hook,
        custom_nodes={"SaveAnswer": SaveAnswerNode}
    )

    result = runner.invoke(
        {"data": {"question": "蓝、白、棕三个颜色鞋子，左右脚各穿一个颜色，一共有多少种搭配方式？"}, "context":{"task_id":"17441004694569588072"}}
    )

    print(result.get("data", {}).get("answer", ""))

@dataclass
class SaveAnswerConfig(NodeConfig):
    output_key: str = ""
    input_key: str = ""
    saver_name:str = "尕小"

class SaveAnswerNode(BaseNode):
    node_type = "SaveAnswer"
    config_class = SaveAnswerConfig

    def execute(
        self, state: Dict[str, Any]
    ) -> Dict[str, Any]:
        logging.info(f"SaveAnswerNode 开始执行，输出 key: {self.config.output_key} 输入key: {self.config.input_key}")

        answer_data= self._get_nested(state, self.config.input_key, "")

        if not answer_data:
            raise Exception("未找到答案数据")

        

        # 使用 'with' 语句可以确保文件在操作完成后自动关闭
        with open("test_answer_info.txt", "w", encoding="utf-8") as f:
            f.write(answer_data)

        return self._set_nested({}, self.config.output_key, answer_data)

if __name__ == "__main__":
    main()
