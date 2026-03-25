#!/usr/bin/env python
"""
测试外部节点注册

运行方式：
  ./venv/bin/python test_external_node.py

步骤：
1. 先安装外部节点包：./venv/bin/pip install -e examples/external_nodes_example/
2. 再运行此脚本
"""

import sys


def test_external_node():
    print("=" * 50)
    print("测试外部节点注册")
    print("=" * 50)

    # 1. 检查注册表
    from core.registry import NodeRegistry

    registry = NodeRegistry()
    all_types = registry.list_types()

    print(f"\n已注册节点数量: {len(all_types)}")
    print(f"节点列表: {all_types}")

    if "video_render" in all_types:
        print("\n✅ video_render 节点已注册!")
    else:
        print("\n❌ video_render 节点未注册")
        print("请先安装: ./venv/bin/pip install -e examples/external_nodes_example/")
        sys.exit(1)

    # 2. 直接导入测试
    print("\n" + "-" * 50)
    print("直接导入节点类")
    print("-" * 50)

    from gvideo_nodes.video_render import VideoRenderNode, VideoRenderConfig

    config = {
        "output_format": "mp4",
        "resolution": "4k",
        "quality": "high",
    }

    node = VideoRenderNode(config)
    print(f"节点类型: {node.node_type}")
    print(f"配置: {node.config}")

    # 3. 执行测试
    print("\n" + "-" * 50)
    print("执行节点")
    print("-" * 50)

    state = {
        "data": {
            "tid": "test_001",
            "script": {"scenes": [{"text": "Hello World"}]},
        }
    }

    result = node.execute(state)
    print(f"执行结果: {result}")

    # 4. 工作流集成测试
    print("\n" + "-" * 50)
    print("工作流集成测试")
    print("-" * 50)

    from auto_agent import WorkflowRunner

    workflow_config = {
        "workflow": {"name": "test-external-node"},
        "nodes": [
            {
                "id": "render",
                "type": "video_render",
                "config": {
                    "output_format": "webm",
                    "resolution": "720p",
                },
            }
        ],
        "edges": [
            {"from": "START", "to": "render"},
            {"from": "render", "to": "END"},
        ],
    }

    runner = WorkflowRunner(config_dict=workflow_config)
    result = runner.invoke({"data": {"tid": "wf_001", "script": {"test": True}}})

    print(f"工作流结果: {result['data']['render_result']}")

    print("\n" + "=" * 50)
    print("✅ 所有测试通过!")
    print("=" * 50)


if __name__ == "__main__":
    test_external_node()
