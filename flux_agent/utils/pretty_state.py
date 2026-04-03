import json
import re
from langchain_core.load import dumps

def pretty_state(state: dict, indent: int = 2) -> str:
    """Pretty print a state，截断 base64"""
    
    # 先用 langchain 的 dumps 序列化成 JSON 字符串
    raw = dumps(state, indent=indent)
    
    # 再解析成 dict 进行截断
    parsed = json.loads(raw)
    
    def truncate_base64(obj):
        if isinstance(obj, str):
            if obj.startswith("data:image"):
                prefix = obj[:obj.index(",") + 1] if "," in obj else ""
                return f"{prefix}[base64...truncated, len={len(obj)}]"
            if len(obj) > 200 and re.match(r'^[A-Za-z0-9+/=]+$', obj[:100]):
                return f"[base64...truncated, len={len(obj)}]"
            return obj
        elif isinstance(obj, dict):
            return {k: truncate_base64(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [truncate_base64(item) for item in obj]
        return obj
    
    truncated = truncate_base64(parsed)
    return json.dumps(truncated, indent=indent, ensure_ascii=False)