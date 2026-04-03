#!/usr/bin/env python3
"""
LLMNode Structured Output 示例

演示 LLMNode 的 JSON Schema 功能：
1. 基础 JSON Schema 使用
2. 嵌套结构
3. 数组类型
4. 枚举类型

使用说明：
- 需要配置 api_key 和 base_url，或设置环境变量 OPENAI_API_KEY
- 示例使用代理配置，如不需要可移除 base_url 和 api_key
"""

from flux_agent import WorkflowRunner

# 默认 API 配置（可修改为自己的）
DEFAULT_BASE_URL = ""
DEFAULT_API_KEY = ""


def demo_json_schema_basic():
    """示例1：基础 JSON Schema - 提取用户信息"""
    print("=" * 60)
    print("示例1: 基础 JSON Schema - 提取用户信息")
    print("=" * 60)

    config = {
        "workflow": {"name": "llm-json-schema-basic"},
        "nodes": [
            {
                "id": "init",
                "type": "transform",
                "config": {
                    "transforms": [
                        {
                            "action": "set",
                            "key": "data.input",
                            "value": "用户张三，25岁，邮箱 zhangsan@example.com",
                        }
                    ]
                },
            },
            {
                "id": "extract",
                "type": "llm",
                "config": {
                    "model_name": "gpt-4o",
                    "user_prompt": "从以下文本提取用户信息：${data.input}",
                    "output_key": "data.user_info",
                    "base_url": DEFAULT_BASE_URL,
                    "api_key": DEFAULT_API_KEY,
                    "json_schema": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "用户名"},
                            "age": {"type": "integer", "description": "年龄"},
                            "email": {"type": "string", "description": "邮箱"},
                        },
                        "required": ["name", "age"],
                    },
                },
            },
        ],
        "edges": [
            {"from": "START", "to": "init"},
            {"from": "init", "to": "extract"},
            {"from": "extract", "to": "END"},
        ],
    }

    runner = WorkflowRunner(config_dict=config)
    result = runner.invoke({"data": {}})

    data = result.get("data", {})
    user_info = data.get("user_info", {})

    print(f"输入: {data.get('input')}")
    print(data)
    print(f"提取结果:")
    print(f"  name: {user_info.get('name')}")
    print(f"  age: {user_info.get('age')}")
    print(f"  email: {user_info.get('email')}")
    print()


def demo_json_schema_nested():
    """示例2：嵌套结构 - 提取订单信息"""
    print("=" * 60)
    print("示例2: 嵌套结构 - 提取订单信息")
    print("=" * 60)

    config = {
        "workflow": {"name": "llm-json-schema-nested"},
        "nodes": [
            {
                "id": "init",
                "type": "transform",
                "config": {
                    "transforms": [
                        {
                            "action": "set",
                            "key": "data.input",
                            "value": "订单号 ORDER-12345，商品 iPhone 15 Pro，价格 8999 元，数量 2 件，收件人李四，电话 13800138000",
                        }
                    ]
                },
            },
            {
                "id": "extract",
                "type": "llm",
                "config": {
                    "model_name": "gpt-4o",
                    "user_prompt": "从以下文本提取订单信息：${data.input}",
                    "output_key": "data.order",
                    "base_url": DEFAULT_BASE_URL,
                    "api_key": DEFAULT_API_KEY,
                    "json_schema": {
                        "type": "object",
                        "properties": {
                            "order_id": {"type": "string", "description": "订单号"},
                            "items": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string", "description": "商品名称"},
                                        "price": {"type": "number", "description": "单价"},
                                        "quantity": {"type": "integer", "description": "数量"},
                                    },
                                },
                            },
                            "contact": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string", "description": "收件人"},
                                    "phone": {"type": "string", "description": "电话"},
                                },
                            },
                        },
                        "required": ["order_id", "items"],
                    },
                },
            },
        ],
        "edges": [
            {"from": "START", "to": "init"},
            {"from": "init", "to": "extract"},
            {"from": "extract", "to": "END"},
        ],
    }

    runner = WorkflowRunner(config_dict=config)
    result = runner.invoke({"data": {}})

    data = result.get("data", {})
    order = data.get("order", {})

    print(f"输入: {data.get('input')}")
    print(f"提取结果:")
    print(f"  order_id: {order.get('order_id')}")
    print(f"  items: {order.get('items')}")
    print(f"  contact: {order.get('contact')}")
    print()


def demo_json_schema_array():
    """示例3：数组类型 - 提取多个联系人"""
    print("=" * 60)
    print("示例3: 数组类型 - 提取多个联系人")
    print("=" * 60)

    config = {
        "workflow": {"name": "llm-json-schema-array"},
        "nodes": [
            {
                "id": "init",
                "type": "transform",
                "config": {
                    "transforms": [
                        {
                            "action": "set",
                            "key": "data.input",
                            "value": "通讯录：张三 13800001111、李四 13800002222、王五 13800003333",
                        }
                    ]
                },
            },
            {
                "id": "extract",
                "type": "llm",
                "config": {
                    "model_name": "gpt-4o",
                    "user_prompt": "从以下文本提取联系人列表：${data.input}",
                    "output_key": "data.contacts",
                    "base_url": DEFAULT_BASE_URL,
                    "api_key": DEFAULT_API_KEY,
                    "json_schema": {
                        "type": "object",
                        "properties": {
                            "contacts": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string", "description": "姓名"},
                                        "phone": {"type": "string", "description": "电话"},
                                    },
                                    "required": ["name", "phone"],
                                },
                            }
                        },
                        "required": ["contacts"],
                    },
                },
            },
        ],
        "edges": [
            {"from": "START", "to": "init"},
            {"from": "init", "to": "extract"},
            {"from": "extract", "to": "END"},
        ],
    }

    runner = WorkflowRunner(config_dict=config)
    result = runner.invoke({"data": {}})

    data = result.get("data", {})
    contacts = data.get("contacts", {})

    print(f"输入: {data.get('input')}")
    print(f"提取结果: {contacts}")
    print()


def demo_json_schema_enum():
    """示例4：枚举类型 - 情感分析"""
    print("=" * 60)
    print("示例4: 枚举类型 - 情感分析")
    print("=" * 60)

    config = {
        "workflow": {"name": "llm-json-schema-enum"},
        "nodes": [
            {
                "id": "init",
                "type": "transform",
                "config": {
                    "transforms": [
                        {
                            "action": "set",
                            "key": "data.input",
                            "value": "这个产品太棒了，强烈推荐！",
                        }
                    ]
                },
            },
            {
                "id": "analyze",
                "type": "llm",
                "config": {
                    "model_name": "gpt-4o",
                    "user_prompt": "分析以下评论的情感：${data.input}",
                    "output_key": "data.sentiment",
                    "base_url": DEFAULT_BASE_URL,
                    "api_key": DEFAULT_API_KEY,
                    "json_schema": {
                        "type": "object",
                        "properties": {
                            "sentiment": {
                                "type": "string",
                                "enum": ["positive", "negative", "neutral"],
                                "description": "情感倾向",
                            },
                            "score": {"type": "number", "description": "置信度 0-1"},
                            "reason": {"type": "string", "description": "分析理由"},
                        },
                        "required": ["sentiment", "score"],
                    },
                },
            },
        ],
        "edges": [
            {"from": "START", "to": "init"},
            {"from": "init", "to": "analyze"},
            {"from": "analyze", "to": "END"},
        ],
    }

    runner = WorkflowRunner(config_dict=config)
    result = runner.invoke({"data": {}})

    data = result.get("data", {})
    sentiment = data.get("sentiment", {})

    print(f"输入: {data.get('input')}")
    print(f"分析结果:")
    print(f"  sentiment: {sentiment.get('sentiment')}")
    print(f"  score: {sentiment.get('score')}")
    print(f"  reason: {sentiment.get('reason')}")
    print()


def demo_json_schema_with_rag():
    """示例5：结合 RAG - 提取文档信息"""
    print("=" * 60)
    print("示例5: JSON Schema 结合其他功能")
    print("=" * 60)

    config = {
        "workflow": {"name": "llm-json-schema-complex"},
        "nodes": [
            {
                "id": "init",
                "type": "transform",
                "config": {
                    "transforms": [
                        {
                            "action": "set",
                            "key": "data.products",
                            "value": [
                                {"name": "iPhone 15", "price": 5999, "category": "手机"},
                                {"name": "MacBook Pro", "price": 14999, "category": "电脑"},
                                {"name": "AirPods Pro", "price": 1999, "category": "耳机"},
                            ],
                        }
                    ]
                },
            },
            {
                "id": "analyze",
                "type": "llm",
                "config": {
                    "model_name": "gpt-4o",
                    "user_prompt": "分析以下商品列表，提取分类统计信息：${data.products}",
                    "output_key": "data.analysis",
                    "base_url": DEFAULT_BASE_URL,
                    "api_key": DEFAULT_API_KEY,
                    "json_schema": {
                        "type": "object",
                        "properties": {
                            "total_count": {"type": "integer", "description": "商品总数"},
                            "total_value": {"type": "number", "description": "总价值"},
                            "categories": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "count": {"type": "integer"},
                                        "avg_price": {"type": "number"},
                                    },
                                },
                            },
                        },
                        "required": ["total_count", "categories"],
                    },
                },
            },
        ],
        "edges": [
            {"from": "START", "to": "init"},
            {"from": "init", "to": "analyze"},
            {"from": "analyze", "to": "END"},
        ],
    }

    runner = WorkflowRunner(config_dict=config)
    result = runner.invoke({"data": {}})

    data = result.get("data", {})
    analysis = data.get("analysis", {})

    print(f"商品列表: {data.get('products')}")
    print(f"分析结果:")
    print(f"  total_count: {analysis.get('total_count')}")
    print(f"  total_value: {analysis.get('total_value')}")
    print(f"  categories: {analysis.get('categories')}")
    print()


def main():
    print("\n" + "=" * 60)
    print("  LLMNode JSON Schema 演示 - Structured Output")
    print("=" * 60 + "\n")

    # demo_json_schema_basic()
    # demo_json_schema_nested()
    # demo_json_schema_array()
    # demo_json_schema_enum()
    demo_json_schema_with_rag()

    print("=" * 60)
    print("  全部示例完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
