from langchain_core.load import dumps

def pretty_state(state: dict, indent: int = 2) -> str:
    """Pretty print a state"""
    return dumps(state, indent=indent)