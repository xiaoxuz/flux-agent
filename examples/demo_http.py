#!/usr/bin/env python3
"""
HTTPRequestNode 示例

演示 HTTP API 调用
"""
import sys
from pathlib import Path


from auto_agent import WorkflowRunner

def main():
    config = {
        "workflow": {"name": "http-demo"},
        "nodes": [
            {
                "id": "get_posts",
                "type": "HTTPRequestNode",
                "config": {
                    "url": "https://jsonplaceholder.typicode.com/posts/1",
                    "method": "GET",
                    "output_key": "data.post",
                    "timeout": 10
                }
            },
            {
                "id": "get_users",
                "type": "HTTPRequestNode",
                "config": {
                    "url": "https://jsonplaceholder.typicode.com/users/1",
                    "method": "GET",
                    "output_key": "data.user",
                    "timeout": 10
                }
            }
        ],
        "edges": [
            {"from": "START", "to": "get_posts"},
            {"from": "get_posts", "to": "get_users"},
            {"from": "get_users", "to": "END"}
        ]
    }

    print("=" * 50)
    print("HTTPRequestNode 示例：HTTP API 调用")
    print("=" * 50)

    runner = WorkflowRunner(config_dict=config)
    result = runner.invoke({"data": {}})

    data = result.get("data", {})
    post = data.get("post", {})
    user = data.get("user", {})

    print(f"文章标题: {post.get('title', 'N/A')[:50]}...")
    print(f"用户名: {user.get('name', 'N/A')}")
    print(f"邮箱: {user.get('email', 'N/A')}")
    print("=" * 50)

if __name__ == "__main__":
    main()
