#!/usr/bin/env python3
"""
完整配置示例：智能客服工作流

演示以下功能：
- TransformNode: 数据初始化、状态更新
- LLMNode: 意图分类、智能回复（需要 API Key）
- ConditionNode: 意图路由、循环判断
- ToolNode: 创建工单
- HumanInputNode: 等待用户输入

流程图：
START → init → classify_intent → route_intent ─┬→ handle_query → increment_turn
                                               ├→ handle_complaint → create_ticket_if_needed → increment_turn
                                               └→ handle_other → increment_turn
                                                                                      ↓
                                                                            check_continue ─┬→ wait_input → classify_intent
                                                                                             └→ finalize → END
"""

import sys
import os
from pathlib import Path


from auto_agent import WorkflowRunner


def mock_search_knowledge_base(query: str, limit: int = 5) -> dict:
    """模拟知识库搜索工具"""
    knowledge_base = {
        "退款政策": "订单签收后7天内可申请退款，需保持商品完好。",
        "配送时间": "一线城市1-2天，二三线城市3-5天。",
        "会员权益": "会员享受9折优惠、优先发货、专属客服。",
    }

    results = []
    for key, value in knowledge_base.items():
        if query in key or key in query:
            results.append({"title": key, "content": value})

    return {"results": results[:limit], "total": len(results)}


def mock_create_ticket(user_id: str, issue: str) -> dict:
    """模拟创建工单工具"""
    import time

    ticket_id = f"TK{int(time.time())}"
    return {
        "ticket_id": ticket_id,
        "user_id": user_id,
        "issue": issue,
        "status": "open",
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }


def main():
    import logging

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S"
    )

    config = {
        "workflow": {
            "name": "smart-customer-service",
            "description": "智能客服工作流",
            "version": "2.0.0",
        },
        "tools": [
            {
                "name": "search_knowledge_base",
                "description": "搜索知识库",
                "implementation": mock_search_knowledge_base,
            },
            {
                "name": "create_ticket",
                "description": "创建工单",
                "implementation": mock_create_ticket,
            },
        ],
        "nodes": [
            {
                "id": "init",
                "type": "TransformNode",
                "config": {
                    "transforms": [
                        {"action": "set", "key": "data.status", "value": "processing"},
                        {"action": "set", "key": "data.turn_count", "value": 0},
                        {"action": "set", "key": "data.user_id", "value": "user_001"},
                    ]
                },
            },
            {
                "id": "classify_intent",
                "type": "LLMNode",
                "config": {
                    "model_name": "gpt-4o",
                    "system_prompt": '你是一个意图分类专家。请根据用户输入分类意图。\n\n可能的类别：\n- query: 用户咨询问题\n- complaint: 用户投诉或不满\n- feedback: 用户反馈或建议\n\n请只返回 JSON 格式：{"category": "类别", "confidence": 0.0-1.0}',
                    "user_prompt": "用户输入：${data.user_input}",
                    "response_format": {"type": "json_object"},
                    "output_key": "data.intent",
                    "temperature": 0.3,
                    "base_url": "",
                    "api_key": "",
                },
            },
            {
                "id": "route_intent",
                "type": "ConditionNode",
                "config": {
                    "branches": [
                        {
                            "condition": "data.intent.category == 'complaint'",
                            "target": "handle_complaint",
                        },
                        {"condition": "data.intent.category == 'query'", "target": "handle_query"},
                        {"condition": "default", "target": "handle_other"},
                    ]
                },
            },
            {
                "id": "handle_query",
                "type": "TransformNode",
                "config": {
                    "transforms": [
                        {
                            "action": "set",
                            "key": "data.response",
                            "value": "感谢您的咨询，已为您查询相关信息。",
                        },
                        {
                            "action": "set",
                            "key": "data.knowledge_result",
                            "value": {"found": True, "items": ["退款政策", "配送时间"]},
                        },
                    ]
                },
            },
            {
                "id": "handle_complaint",
                "type": "TransformNode",
                "config": {
                    "transforms": [
                        {"action": "set", "key": "data.need_escalation", "value": True},
                        {
                            "action": "set",
                            "key": "data.response",
                            "value": "非常抱歉给您带来不便，已为您创建工单。",
                        },
                    ]
                },
            },
            {
                "id": "create_ticket_if_needed",
                "type": "ToolNode",
                "config": {
                    "tool_name": "create_ticket",
                    "args": {"user_id": "${data.user_id}", "issue": "${data.user_input}"},
                    "output_key": "data.ticket",
                },
            },
            {
                "id": "handle_other",
                "type": "TransformNode",
                "config": {
                    "transforms": [
                        {
                            "action": "set",
                            "key": "data.response",
                            "value": "感谢您的反馈，我们会持续改进。",
                        }
                    ]
                },
            },
            {
                "id": "increment_turn",
                "type": "TransformNode",
                "config": {"transforms": [{"action": "increment", "key": "data.turn_count"}]},
            },
            {
                "id": "check_continue",
                "type": "ConditionNode",
                "config": {
                    "branches": [
                        {"condition": "data.turn_count >= 3", "target": "finalize"},
                        {"condition": "data.user_input == '退出'", "target": "finalize"},
                        {"condition": "data.user_input == 'done'", "target": "finalize"},
                        {"condition": "default", "target": "wait_input"},
                    ]
                },
            },
            {
                "id": "wait_input",
                "type": "HumanInputNode",
                "config": {
                    "prompt": "还有其他问题吗？(输入 '退出' 或 'done' 结束)",
                    "output_key": "data.user_input",
                    "timeout": 300,
                },
            },
            {
                "id": "finalize",
                "type": "TransformNode",
                "config": {
                    "transforms": [{"action": "set", "key": "data.status", "value": "completed"}]
                },
            },
        ],
        "edges": [
            {"from": "START", "to": "init"},
            {"from": "init", "to": "classify_intent"},
            {"from": "classify_intent", "to": "route_intent"},
            {
                "from": "route_intent",
                "condition_map": {
                    "handle_query": "handle_query",
                    "handle_complaint": "handle_complaint",
                    "handle_other": "handle_other",
                },
            },
            {"from": "handle_query", "to": "increment_turn"},
            {"from": "handle_complaint", "to": "create_ticket_if_needed"},
            {"from": "create_ticket_if_needed", "to": "increment_turn"},
            {"from": "handle_other", "to": "increment_turn"},
            {"from": "increment_turn", "to": "check_continue"},
            {
                "from": "check_continue",
                "condition_map": {"wait_input": "wait_input", "finalize": "finalize"},
            },
            {"from": "wait_input", "to": "classify_intent"},
            {"from": "finalize", "to": "END"},
        ],
    }

    print("=" * 60)
    print("智能客服工作流示例")
    print("=" * 60)
    print()

    # 获取初始问题
    print("请输入您的问题（输入 '退出' 结束）:")
    user_input = input("> ").strip()

    if not user_input or user_input.lower() in ("退出", "exit", "quit"):
        print("再见！")
        return

    print("-" * 60)

    import logging

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S"
    )

    runner = WorkflowRunner(config_dict=config)

    initial_input = {"data": {"user_input": user_input, "user_id": "user_001"}}

    thread_id = "customer-service-1"
    result = runner.invoke(initial_input, thread_id=thread_id)

    # 循环处理人工输入
    while "__interrupt__" in result:
        interrupt_info = result["__interrupt__"][0]
        interrupt_value = (
            interrupt_info.value if hasattr(interrupt_info, "value") else interrupt_info
        )

        if isinstance(interrupt_value, dict):
            prompt = interrupt_value.get("prompt", "请输入:")
            print(f"\n{prompt}")

        user_input = input("> ").strip()

        if user_input.lower() in ("退出", "exit", "quit", "done"):
            print("\n结束对话。")
            break

        result = runner.resume(thread_id, user_input)

    print()
    print("-" * 60)
    print("执行完成!")
    print("-" * 60)

    data = result.get("data", {})

    print(f"状态: {data.get('status')}")
    print(f"对话轮次: {data.get('turn_count')}")
    print()

    if data.get("intent"):
        print(f"意图分类: {data.get('intent', {}).get('category')}")

    if data.get("response"):
        print(f"系统回复: {data.get('response')}")

    if data.get("ticket"):
        print(f"工单信息: {data.get('ticket')}")

    print()
    print("=" * 60)


if __name__ == "__main__":
    main()
