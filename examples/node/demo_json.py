#!/usr/bin/env python3
"""
JsonNode 示例

演示 JSON 编码和解码功能：
1. 基础 encode/decode
2. 中文处理
3. 嵌套结构
4. 错误处理
5. 与其他节点配合使用
"""

from flux_agent import WorkflowRunner


def demo_basic_encode():
    """示例1：基础编码 - 对象转 JSON 字符串"""
    print("=" * 60)
    print("示例1: 基础编码 - 对象转 JSON")
    print("=" * 60)

    config = {
        "workflow": {"name": "json-encode-demo"},
        "nodes": [
            {
                "id": "init",
                "type": "transform",
                "config": {
                    "transforms": [
                        {
                            "action": "set",
                            "key": "data.user",
                            "value": {"name": "张三", "age": 25, "city": "北京"},
                        }
                    ]
                },
            },
            {
                "id": "encode",
                "type": "json",
                "config": {
                    "action": "encode",
                    "input_key": "data.user",
                    "output_key": "data.json_str",
                    "indent": 2,
                    "ensure_ascii": False,
                },
            },
        ],
        "edges": [
            {"from": "START", "to": "init"},
            {"from": "init", "to": "encode"},
            {"from": "encode", "to": "END"},
        ],
    }

    runner = WorkflowRunner(config_dict=config)
    result = runner.invoke({"data": {}})

    data = result.get("data", {})
    print(f"原始对象: {data.get('user')}")
    print(f"JSON 字符串:\n{data.get('json_str')}")
    print()


def demo_basic_decode():
    """示例2：基础解码 - JSON 字符串转对象"""
    print("=" * 60)
    print("示例2: 基础解码 - JSON 字符串转对象")
    print("=" * 60)

    config = {
        "workflow": {"name": "json-decode-demo"},
        "nodes": [
            {
                "id": "init",
                "type": "transform",
                "config": {
                    "transforms": [
                        {
                            "action": "set",
                            "key": "data.json_str",
                            "value": '{"name": "李四", "age": 30, "skills": ["Python", "JavaScript"]}',
                        }
                    ]
                },
            },
            {
                "id": "decode",
                "type": "json",
                "config": {
                    "action": "decode",
                    "input_key": "data.json_str",
                    "output_key": "data.obj",
                },
            },
        ],
        "edges": [
            {"from": "START", "to": "init"},
            {"from": "init", "to": "decode"},
            {"from": "decode", "to": "END"},
        ],
    }

    runner = WorkflowRunner(config_dict=config)
    result = runner.invoke({"data": {}})

    data = result.get("data", {})
    print(f"JSON 字符串: {data.get('json_str')}")
    print(f"解码对象: {data.get('obj')}")
    print(f"name: {data.get('obj', {}).get('name')}")
    print(f"skills: {data.get('obj', {}).get('skills')}")
    print()


def demo_chinese_encoding():
    """示例3：中文编码处理"""
    print("=" * 60)
    print("示例3: 中文编码处理")
    print("=" * 60)

    config = {
        "workflow": {"name": "json-chinese-demo"},
        "nodes": [
            {
                "id": "init",
                "type": "transform",
                "config": {
                    "transforms": [
                        {
                            "action": "set",
                            "key": "data.info",
                            "value": {
                                "标题": "中文标题",
                                "内容": "这是一段中文内容",
                                "标签": ["标签1", "标签2"],
                            },
                        }
                    ]
                },
            },
            {
                "id": "encode_ascii",
                "type": "json",
                "config": {
                    "action": "encode",
                    "input_key": "data.info",
                    "output_key": "data.json_ascii",
                    "ensure_ascii": True,  # 转义中文
                },
            },
            {
                "id": "encode_utf8",
                "type": "json",
                "config": {
                    "action": "encode",
                    "input_key": "data.info",
                    "output_key": "data.json_utf8",
                    "ensure_ascii": False,  # 保留中文
                },
            },
        ],
        "edges": [
            {"from": "START", "to": "init"},
            {"from": "init", "to": "encode_ascii"},
            {"from": "encode_ascii", "to": "encode_utf8"},
            {"from": "encode_utf8", "to": "END"},
        ],
    }

    runner = WorkflowRunner(config_dict=config)
    result = runner.invoke({"data": {}})

    data = result.get("data", {})
    print(f"ensure_ascii=True:\n{data.get('json_ascii')}\n")
    print(f"ensure_ascii=False:\n{data.get('json_utf8')}")
    print()


def demo_error_handling():
    """示例4：错误处理"""
    print("=" * 60)
    print("示例4: 错误处理 - 解码失败")
    print("=" * 60)

    config = {
        "workflow": {"name": "json-error-demo"},
        "nodes": [
            {
                "id": "init",
                "type": "transform",
                "config": {
                    "transforms": [
                        {"action": "set", "key": "data.bad_json", "value": "not a valid json"}
                    ]
                },
            },
            {
                "id": "decode_safe",
                "type": "json",
                "config": {
                    "action": "decode",
                    "input_key": "data.bad_json",
                    "output_key": "data.result",
                    "error_on_fail": False,  # 不抛出错误
                    "default": {"error": "解析失败"},
                },
            },
        ],
        "edges": [
            {"from": "START", "to": "init"},
            {"from": "init", "to": "decode_safe"},
            {"from": "decode_safe", "to": "END"},
        ],
    }

    runner = WorkflowRunner(config_dict=config)
    result = runner.invoke({"data": {}})

    data = result.get("data", {})
    print(f"输入: {data.get('bad_json')}")
    print(f"结果: {data.get('result')}")
    print()


def demo_with_llm():
    """示例5：与 LLM 配合 - 解析 LLM 返回的 JSON"""
    print("=" * 60)
    print("示例5: 与 LLM 配合 - 解析 JSON 响应")
    print("=" * 60)

    config = {
        "workflow": {"name": "json-llm-demo"},
        "nodes": [
            {
                "id": "mock_llm",
                "type": "transform",
                "config": {
                    "transforms": [
                        {
                            "action": "set",
                            "key": "data.llm_response",
                            "value": '{"thought": "用户想了解天气", "action": "query_weather", "params": {"city": "北京"}}',
                        }
                    ]
                },
            },
            {
                "id": "parse_response",
                "type": "json",
                "config": {
                    "action": "decode",
                    "input_key": "data.llm_response",
                    "output_key": "data.parsed",
                },
            },
            {
                "id": "use_parsed",
                "type": "transform",
                "config": {
                    "transforms": [
                        {
                            "action": "set",
                            "key": "data.report",
                            "value": "意图: ${data.parsed.action}, 城市: ${data.parsed.params.city}",
                        }
                    ]
                },
            },
        ],
        "edges": [
            {"from": "START", "to": "mock_llm"},
            {"from": "mock_llm", "to": "parse_response"},
            {"from": "parse_response", "to": "use_parsed"},
            {"from": "use_parsed", "to": "END"},
        ],
    }

    runner = WorkflowRunner(config_dict=config)
    result = runner.invoke({"data": {}})

    data = result.get("data", {})
    print(f"LLM 响应: {data.get('llm_response')}")
    print(f"解析结果: {data.get('parsed')}")
    print(f"报告: {data.get('report')}")
    print()


def demo_list_encoding():
    """示例6：列表编码"""
    print("=" * 60)
    print("示例6: 列表编码")
    print("=" * 60)

    config = {
        "workflow": {"name": "json-list-demo"},
        "nodes": [
            {
                "id": "init",
                "type": "transform",
                "config": {
                    "transforms": [
                        {
                            "action": "set",
                            "key": "data.items",
                            "value": [
                                {"id": 1, "name": "项目A"},
                                {"id": 2, "name": "项目B"},
                                {"id": 3, "name": "项目C"},
                            ],
                        }
                    ]
                },
            },
            {
                "id": "encode",
                "type": "json",
                "config": {
                    "action": "encode",
                    "input_key": "data.items",
                    "output_key": "data.json_array",
                    "indent": 4,
                },
            },
        ],
        "edges": [
            {"from": "START", "to": "init"},
            {"from": "init", "to": "encode"},
            {"from": "encode", "to": "END"},
        ],
    }

    runner = WorkflowRunner(config_dict=config)
    result = runner.invoke({"data": {}})

    data = result.get("data", {})
    print(f"JSON 数组:\n{data.get('json_array')}")
    print()


def main():
    print("\n" + "=" * 60)
    print("  JsonNode 演示 - JSON 编码/解码")
    print("=" * 60 + "\n")

    demo_basic_encode()
    demo_basic_decode()
    demo_chinese_encoding()
    demo_error_handling()
    demo_with_llm()
    demo_list_encoding()

    print("=" * 60)
    print("  全部示例完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
