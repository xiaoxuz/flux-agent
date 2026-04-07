def mock_search(query: str) -> str:
    """模拟搜索工具"""
    results = {
        "天气": "今天北京晴，气温18-25℃",
        "新闻": "今日头条：AI技术持续突破",
        "股票": "上证指数今日收盘3250点",
    }
    for key, value in results.items():
        if key in query:
            return value
    return f"未找到 '{query}' 的相关信息"
