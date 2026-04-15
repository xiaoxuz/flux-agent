"""
flux_agent/agents/utils/token_usage.py
Token 使用计量辅助函数
"""
from langchain_core.messages import AIMessage

from ..base import TokenUsageDetail, TokenUsageSummary


def extract_usage_from_message(
    msg: AIMessage,
    step_index: int = -1,
    operation: str = "",
) -> TokenUsageDetail | None:
    """从 AIMessage 提取 usage_metadata，返回 TokenUsageDetail"""
    usage = getattr(msg, "usage_metadata", None)
    if not usage:
        return None
    return TokenUsageDetail(
        step_index=step_index,
        operation=operation,
        input_tokens=usage.get("input_tokens", 0),
        output_tokens=usage.get("output_tokens", 0),
        total_tokens=usage.get("total_tokens", 0),
    )


def aggregate_details_to_summary(details: list[TokenUsageDetail]) -> TokenUsageSummary:
    """从明细列表聚合为汇总对象"""
    total_input = sum(d.input_tokens for d in details)
    total_output = sum(d.output_tokens for d in details)
    total = sum(d.total_tokens for d in details)
    return TokenUsageSummary(
        input_tokens=total_input,
        output_tokens=total_output,
        total_tokens=total,
        details=details,
    )


def merge_usage_summaries(a: TokenUsageSummary, b: TokenUsageSummary) -> TokenUsageSummary:
    """合并两个 TokenUsageSummary（Supervisor 聚合 worker 用）"""
    return TokenUsageSummary(
        input_tokens=a.input_tokens + b.input_tokens,
        output_tokens=a.output_tokens + b.output_tokens,
        total_tokens=a.total_tokens + b.total_tokens,
        details=a.details + b.details,
    )


def usage_to_dict(usage: TokenUsageSummary | None) -> dict:
    """序列化辅助"""
    if usage is None:
        return {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "details": []}
    return {
        "input_tokens": usage.input_tokens,
        "output_tokens": usage.output_tokens,
        "total_tokens": usage.total_tokens,
        "details": [
            {
                "step_index": d.step_index,
                "operation": d.operation,
                "input_tokens": d.input_tokens,
                "output_tokens": d.output_tokens,
                "total_tokens": d.total_tokens,
            }
            for d in usage.details
        ],
    }
