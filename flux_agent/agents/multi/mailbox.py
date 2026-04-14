"""
flux_agent/agents/multi/mailbox.py
Agent 间通信 — 邮箱抽象 + 内存/文件系统实现
"""
from __future__ import annotations

import os
import json
import time
import uuid
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Literal


MailboxType = Literal["task", "result", "signal", "chat"]


@dataclass
class MailboxMessage:
    """Agent 间传递的消息"""
    from_agent: str
    to_agent: str
    content: str
    type: MailboxType = "chat"
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metadata: dict = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "type": self.type,
            "content": self.content,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "MailboxMessage":
        return cls(
            id=d["id"],
            from_agent=d["from_agent"],
            to_agent=d["to_agent"],
            type=d.get("type", "chat"),
            content=d["content"],
            metadata=d.get("metadata", {}),
            timestamp=d.get("timestamp", time.time()),
        )


class Mailbox(ABC):
    """Agent 间消息传递的抽象基类"""

    @abstractmethod
    def send(self, message: MailboxMessage) -> None:
        """发送消息到目标 agent 的收件箱"""
        ...

    @abstractmethod
    def receive(self, agent_id: str) -> list[MailboxMessage]:
        """收取目标 agent 的所有未读消息（读取后清除）"""
        ...

    @abstractmethod
    def peek(self, agent_id: str) -> list[MailboxMessage]:
        """查看目标 agent 的未读消息（不清除）"""
        ...

    @abstractmethod
    def clear(self, agent_id: str) -> None:
        """清空目标 agent 的收件箱"""
        ...


class InMemoryMailbox(Mailbox):
    """内存邮箱 — 单进程内多 agent 协作"""

    def __init__(self) -> None:
        self._boxes: dict[str, list[MailboxMessage]] = {}
        self._lock = threading.Lock()

    def send(self, message: MailboxMessage) -> None:
        with self._lock:
            self._boxes.setdefault(message.to_agent, []).append(message)

    def receive(self, agent_id: str) -> list[MailboxMessage]:
        with self._lock:
            msgs = self._boxes.pop(agent_id, [])
            return msgs

    def peek(self, agent_id: str) -> list[MailboxMessage]:
        with self._lock:
            return list(self._boxes.get(agent_id, []))

    def clear(self, agent_id: str) -> None:
        with self._lock:
            self._boxes.pop(agent_id, None)


class FileMailbox(Mailbox):
    """文件邮箱 — 跨进程/持久化场景

    目录结构: {base_dir}/{agent_id}/inbox/{msg_id}.json
    """

    def __init__(self, base_dir: str = ".mailbox") -> None:
        self._base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)

    def _agent_inbox(self, agent_id: str) -> str:
        path = os.path.join(self._base_dir, agent_id, "inbox")
        os.makedirs(path, exist_ok=True)
        return path

    def send(self, message: MailboxMessage) -> None:
        inbox = self._agent_inbox(message.to_agent)
        filepath = os.path.join(inbox, f"{message.id}.json")
        tmp = filepath + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(message.to_dict(), f, ensure_ascii=False)
        os.replace(tmp, filepath)  # 原子写入

    def receive(self, agent_id: str) -> list[MailboxMessage]:
        inbox = self._agent_inbox(agent_id)
        msgs = []
        for fname in os.listdir(inbox):
            if not fname.endswith(".json"):
                continue
            fpath = os.path.join(inbox, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    msgs.append(MailboxMessage.from_dict(json.load(f)))
                os.remove(fpath)
            except (json.JSONDecodeError, OSError):
                pass
        return msgs

    def peek(self, agent_id: str) -> list[MailboxMessage]:
        inbox = self._agent_inbox(agent_id)
        msgs = []
        for fname in os.listdir(inbox):
            if not fname.endswith(".json"):
                continue
            fpath = os.path.join(inbox, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    msgs.append(MailboxMessage.from_dict(json.load(f)))
            except (json.JSONDecodeError, OSError):
                pass
        return msgs

    def clear(self, agent_id: str) -> None:
        inbox = self._agent_inbox(agent_id)
        for fname in os.listdir(inbox):
            if fname.endswith(".json"):
                os.remove(os.path.join(inbox, fname))
