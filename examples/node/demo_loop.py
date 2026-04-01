#!/usr/bin/env python3
"""
LoopNode v3 示例 - 基于子图的循环迭代

演示功能：
1. 简单遍历：数组每项执行子图，收集结果
2. 并行执行：多线程并行处理
3. 复杂子图：子图内多节点 + 条件分支
4. 错误处理：on_error = skip 跳过失败项
"""

from flux_agent import WorkflowRunner
from flux_agent import utils
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)


def demo_simple_loop():
    """示例1：遍历列表，子图对每个元素做简单变换"""
    print("=" * 60)
    print("示例1: 简单循环 - 遍历并转换数据")
    print("=" * 60)

    config = {
        "workflow": {"name": "loop-demo-simple"},
        "nodes": [
            # ① 初始化：准备待遍历数组
            {
                "id": "init",
                "type": "transform",
                "config": {
                    "transforms": [
                        {
                            "action": "set",
                            "key": "data.items",
                            "value": [1, 2, 3, 4, 5],
                        },
                    ]
                },
            },
            # ② 循环节点
            {
                "id": "process_loop",
                "type": "loop",
                "config": {
                    # 从主 state 取数组
                    "input_key": "data.items",
                    # 结果写回主 state 的路径
                    "results_key": "data.results",
                    # 子图中通过 state["data"]["item"] 拿到当前元素
                    "subgraph_item_key": "data.item",
                    # 子图中通过 state["data"]["meta"] 拿到循环元信息
                    "subgraph_meta_key": "data.meta",
                    # 从子图最终 state 中提取 result 字段作为本轮结果
                    "subgraph_result_path": "data.result",

                    # --- 子图定义 ---
                    "body_nodes": [
                        {
                            "id": "double",
                            "type": "transform",
                            "config": {
                                "transforms": [
                                    {
                                        "action": "set",
                                        "key": "data.result",
                                        "value": "${data.item} * 2",
                                    }
                                ]
                            },
                        }
                    ],
                    "body_edges": [
                        {"from": "START", "to": "double"},
                        {"from": "double", "to": "END"},
                    ],
                    "body_entry_point": "double",
                },
            },
            # ③ 后续处理
            {
                "id": "done",
                "type": "transform",
                "config": {
                    "transforms": [
                        {"action": "set", "key": "data.status", "value": "完成"},
                    ]
                },
            },
        ],
        "edges": [
            {"from": "START", "to": "init"},
            {"from": "init", "to": "process_loop"},
            {"from": "process_loop", "to": "done"},
            {"from": "done", "to": "END"},
        ],
    }

    runner = WorkflowRunner(config_dict=config)
    result = runner.invoke({"data": {}})
    print(utils.pretty_state(result))
    data = result.get("data", {})
    print(f"输入: [1, 2, 3, 4, 5]")
    print(f"结果: {data.get('results', [])}")
    print(f"状态: {data.get('status')}")
    print()


def demo_parallel_loop():
    """示例2：并行遍历"""
    print("=" * 60)
    print("示例2: 并行循环 - 多线程处理")
    print("=" * 60)

    config = {
        "workflow": {"name": "loop-demo-parallel"},
        "nodes": [
            {
                "id": "init",
                "type": "transform",
                "config": {
                    "transforms": [
                        {
                            "action": "set",
                            "key": "data.items",
                            "value": ["苹果", "香蕉", "橙子", "葡萄", "西瓜"],
                        },
                    ]
                },
            },
            {
                "id": "process_loop",
                "type": "loop",
                "config": {
                    "input_key": "data.items",
                    "results_key": "data.results",
                    "subgraph_item_key": "data.item",
                    "subgraph_meta_key": "data.meta",
                    "subgraph_result_path": "data.output",
                    # 并行配置
                    "parallel": True,
                    "parallel_max_workers": 3,

                    "body_nodes": [
                        {
                            "id": "describe",
                            "type": "transform",
                            "config": {
                                "transforms": [
                                    {
                                        "action": "set",
                                        "key": "data.output",
                                        "value": "处理: ${data.item} (第 ${data.meta.index} 项，共 ${data.meta.total} 项)",
                                    }
                                ]
                            },
                        }
                    ],
                    "body_edges": [
                        {"from": "START", "to": "describe"},
                        {"from": "describe", "to": "END"},
                    ],
                    "body_entry_point": "describe",
                },
            },
        ],
        "edges": [
            {"from": "START", "to": "init"},
            {"from": "init", "to": "process_loop"},
            {"from": "process_loop", "to": "END"},
        ],
    }

    runner = WorkflowRunner(config_dict=config)
    result = runner.invoke({"data": {}})

    data = result.get("data", {})
    results = data.get("results", [])
    print(f"共处理 {len(results)} 项（并行）:")
    for i, r in enumerate(results):
        print(f"  {i + 1}. {r}")
    print()


def demo_complex_subgraph():
    """示例3：复杂子图 - 多节点 + 条件分支"""
    print("=" * 60)
    print("示例3: 复杂子图 - 多节点 + 条件分支")
    print("=" * 60)

    config = {
        "workflow": {"name": "loop-demo-complex"},
        "nodes": [
            {
                "id": "init",
                "type": "transform",
                "config": {
                    "transforms": [
                        {
                            "action": "set",
                            "key": "data.items",
                            "value": [10, 25, 30, 45, 60],
                        },
                    ]
                },
            },
            {
                "id": "process_loop",
                "type": "loop",
                "config": {
                    "input_key": "data.items",
                    "results_key": "data.results",
                    "subgraph_item_key": "data.item",
                    "subgraph_meta_key": "data.meta",
                    # 提取子图 state 中整个 result 对象
                    "subgraph_result_path": "data.result",

                    "body_nodes": [
                        # 节点1：读取当前值
                        {
                            "id": "read_value",
                            "type": "transform",
                            "config": {
                                "transforms": [
                                    {
                                        "action": "set",
                                        "key": "data.step_value",
                                        "value": "${data.item}",
                                    }
                                ]
                            },
                        },
                        # 节点2：条件判断
                        {
                            "id": "evaluate",
                            "type": "condition",
                            "config": {
                                "branches": [
                                    {
                                        "condition": "data.step_value > 40",
                                        "target": "mark_high",
                                    },
                                    {
                                        "condition": "default",
                                        "target": "mark_normal",
                                    },
                                ]
                            },
                        },
                        # 节点3a：高值标记
                        {
                            "id": "mark_high",
                            "type": "transform",
                            "config": {
                                "transforms": [
                                    {
                                        "action": "set",
                                        "key": "data.result.value",
                                        "value": "${data.item}",
                                    },
                                    {
                                        "action": "set",
                                        "key": "data.result.level",
                                        "value": "高",
                                    },
                                ]
                            },
                        },
                        # 节点3b：正常标记
                        {
                            "id": "mark_normal",
                            "type": "transform",
                            "config": {
                                "transforms": [
                                    {
                                        "action": "set",
                                        "key": "data.result.value",
                                        "value": "${data.item}",
                                    },
                                    {
                                        "action": "set",
                                        "key": "data.result.level",
                                        "value": "正常",
                                    },
                                ]
                            },
                        },
                    ],
                    "body_edges": [
                        {"from": "START", "to": "read_value"},
                        {"from": "read_value", "to": "evaluate"},
                        {
                            "from": "evaluate",
                            "condition_map": {
                                "mark_high": "mark_high",
                                "mark_normal": "mark_normal",
                            }
                        },
                        {"from": "mark_high", "to": "END"},
                        {"from": "mark_normal", "to": "END"},
                    ],
                    "body_entry_point": "read_value",
                },
            },
        ],
        "edges": [
            {"from": "START", "to": "init"},
            {"from": "init", "to": "process_loop"},
            {"from": "process_loop", "to": "END"},
        ],
    }

    runner = WorkflowRunner(config_dict=config)
    result = runner.invoke({"data": {}})

    data = result.get("data", {})
    results = data.get("results", [])
    print(f"输入: [10, 25, 30, 45, 60]")
    print(f"结果:")
    for i, r in enumerate(results):
        print(f"  {i + 1}. {r}")
    print()


def demo_error_handling():
    """示例4：错误处理 - skip 模式跳过失败项"""
    print("=" * 60)
    print("示例4: 错误处理 - skip 跳过失败项")
    print("=" * 60)

    config = {
        "workflow": {"name": "loop-demo-error"},
        "nodes": [
            {
                "id": "init",
                "type": "transform",
                "config": {
                    "transforms": [
                        {
                            "action": "set",
                            "key": "data.items",
                            "value": ["ok_1", "fail", "ok_2", "fail", "ok_3"],
                        },
                    ]
                },
            },
            {
                "id": "process_loop",
                "type": "loop",
                "config": {
                    "input_key": "data.items",
                    "results_key": "data.results",
                    "subgraph_item_key": "data.item",
                    "subgraph_result_path": "data.output",
                    # 遇到错误跳过，继续处理后续项
                    "on_error": "raise",

                    "body_nodes": [
                        {
                            "id": "process",
                            "type": "transform",
                            "config": {
                                "transforms": [
                                    {
                                        "action": "set",
                                        "key": "data.output",
                                        "value": "已处理: ${data.item}",
                                    }
                                ]
                            },
                        }
                    ],
                    "body_edges": [
                        {"from": "START", "to": "process"},
                        {"from": "process", "to": "END"},
                    ],
                    "body_entry_point": "process",
                },
            },
        ],
        "edges": [
            {"from": "START", "to": "init"},
            {"from": "init", "to": "process_loop"},
            {"from": "process_loop", "to": "END"},
        ],
    }

    runner = WorkflowRunner(config_dict=config)
    result = runner.invoke({"data": {}})

    data = result.get("data", {})
    results = data.get("results", [])
    print(f"结果 ({len(results)} 项):")
    for i, r in enumerate(results):
        if isinstance(r, dict) and "_error" in r:
            print(f"  {i + 1}. ❌ 错误: {r['_error']}")
        else:
            print(f"  {i + 1}. ✅ {r}")
    print()


def demo_max_iterations():
    """示例5：max_iterations 限制"""
    print("=" * 60)
    print("示例5: max_iterations - 只处理前 N 项")
    print("=" * 60)

    config = {
        "workflow": {"name": "loop-demo-max"},
        "nodes": [
            {
                "id": "init",
                "type": "transform",
                "config": {
                    "transforms": [
                        {
                            "action": "set",
                            "key": "data.items",
                            "value": list(range(1, 101)),  # 1~100
                        },
                    ]
                },
            },
            {
                "id": "process_loop",
                "type": "loop",
                "config": {
                    "input_key": "data.items",
                    "results_key": "data.results",
                    "subgraph_item_key": "data.item",
                    "subgraph_result_path": "data.output",
                    # 只处理前 5 项
                    "max_iterations": 5,

                    "body_nodes": [
                        {
                            "id": "square",
                            "type": "transform",
                            "config": {
                                "transforms": [
                                    {
                                        "action": "set",
                                        "key": "data.output",
                                        "value": "${data.item} ^ 2",
                                    }
                                ]
                            },
                        }
                    ],
                    "body_edges": [
                        {"from": "START", "to": "square"},
                        {"from": "square", "to": "END"},
                    ],
                    "body_entry_point": "square",
                },
            },
        ],
        "edges": [
            {"from": "START", "to": "init"},
            {"from": "init", "to": "process_loop"},
            {"from": "process_loop", "to": "END"},
        ],
    }

    runner = WorkflowRunner(config_dict=config)
    result = runner.invoke({"data": {}})

    data = result.get("data", {})
    results = data.get("results", [])
    print(f"输入: 1~100 (共100项)")
    print(f"max_iterations: 5")
    print(f"实际处理: {len(results)} 项")
    print(f"结果: {results}")
    print()


def demo_nested_data():
    """示例6：遍历复杂对象数组，子图提取并组装结构化结果"""
    print("=" * 60)
    print("示例6: 复杂对象数组 - 结构化输入输出")
    print("=" * 60)

    config = {
        "workflow": {"name": "loop-demo-nested"},
        "nodes": [
            {
                "id": "init",
                "type": "transform",
                "config": {
                    "transforms": [
                        {
                            "action": "set",
                            "key": "data.users",
                            "value": [
                                {"name": "Alice", "age": 30, "city": "北京"},
                                {"name": "Bob", "age": 25, "city": "上海"},
                                {"name": "Charlie", "age": 35, "city": "深圳"},
                            ],
                        },
                    ]
                },
            },
            {
                "id": "process_loop",
                "type": "loop",
                "config": {
                    "input_key": "data.users",
                    "results_key": "data.summaries",
                    "subgraph_item_key": "data.user",
                    "subgraph_meta_key": "data.meta",
                    "subgraph_result_path": "data.summary",

                    "body_nodes": [
                        {
                            "id": "build_summary",
                            "type": "transform",
                            "config": {
                                "transforms": [
                                    {
                                        "action": "set",
                                        "key": "data.summary.text",
                                        "value": "${data.user.name} (${data.user.age}岁) 来自${data.user.city}",
                                    },
                                    {
                                        "action": "set",
                                        "key": "data.summary.index",
                                        "value": "${data.meta.index}",
                                    },
                                ]
                            },
                        }
                    ],
                    "body_edges": [
                        {"from": "START", "to": "build_summary"},
                        {"from": "build_summary", "to": "END"},
                    ],
                    "body_entry_point": "build_summary",
                },
            },
        ],
        "edges": [
            {"from": "START", "to": "init"},
            {"from": "init", "to": "process_loop"},
            {"from": "process_loop", "to": "END"},
        ],
    }

    runner = WorkflowRunner(config_dict=config)
    result = runner.invoke({"data": {}})

    data = result.get("data", {})
    summaries = data.get("summaries", [])
    print(f"用户摘要 ({len(summaries)} 条):")
    for s in summaries:
        print(f"  - {s}")
    print()


def demo_downstream_usage():
    """示例7：循环结果被下游节点使用"""
    print("=" * 60)
    print("示例7: 下游节点消费循环结果")
    print("=" * 60)

    config = {
        "workflow": {"name": "loop-demo-downstream"},
        "nodes": [
            {
                "id": "init",
                "type": "transform",
                "config": {
                    "transforms": [
                        {
                            "action": "set",
                            "key": "data.numbers",
                            "value": [10, 20, 30],
                        },
                    ]
                },
            },
            {
                "id": "double_loop",
                "type": "loop",
                "config": {
                    "input_key": "data.numbers",
                    "results_key": "data.doubled",
                    "subgraph_item_key": "data.item",
                    "subgraph_result_path": "data.result",

                    "body_nodes": [
                        {
                            "id": "calc",
                            "type": "transform",
                            "config": {
                                "transforms": [
                                    {
                                        "action": "set",
                                        "key": "data.result",
                                        "value": "${data.item} * 2",
                                    }
                                ]
                            },
                        }
                    ],
                    "body_edges": [
                        {"from": "START", "to": "calc"},
                        {"from": "calc", "to": "END"},
                    ],
                    "body_entry_point": "calc",
                },
            },
            # 下游节点读取循环结果
            {
                "id": "aggregate",
                "type": "transform",
                "config": {
                    "transforms": [
                        {
                            "action": "set",
                            "key": "data.report",
                            "value": "翻倍结果: ${data.doubled}",
                        },
                    ]
                },
            },
        ],
        "edges": [
            {"from": "START", "to": "init"},
            {"from": "init", "to": "double_loop"},
            {"from": "double_loop", "to": "aggregate"},
            {"from": "aggregate", "to": "END"},
        ],
    }

    runner = WorkflowRunner(config_dict=config)
    result = runner.invoke({"data": {}})

    data = result.get("data", {})
    print(f"输入:     [10, 20, 30]")
    print(f"翻倍结果: {data.get('doubled', [])}")
    print(f"报告:     {data.get('report', '')}")
    print()


def main():
    print()
    print("=" * 60)
    print("  LoopNode v3 演示 - 纯 for-each 子图迭代")
    print("=" * 60)
    print()
    print("配置模型:")
    print("  input_key          → 主 state 中待遍历的数组路径")
    print("  subgraph_item_key   → 子图 state 中放置当前元素的 key")
    print("  subgraph_meta_key   → 子图 state 中放置循环元信息的 key")
    print("  subgraph_result_path→ 从子图 state 中提取结果的路径")
    print("  results_key        → 所有结果写回主 state 的路径")
    print()

    # demo_simple_loop()
    # demo_parallel_loop()
    # demo_complex_subgraph()
    # demo_error_handling()
    # demo_max_iterations()
    # demo_nested_data()
    demo_downstream_usage()

    print("=" * 60)
    print("  全部示例完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()