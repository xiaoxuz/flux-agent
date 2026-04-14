"""
flux_agent/agents/multi/__init__.py
多 Agent 协作模块
"""
from .mailbox import (
    Mailbox,
    MailboxMessage,
    InMemoryMailbox,
    FileMailbox,
    MailboxType,
)

__all__ = [
    "Mailbox",
    "MailboxMessage",
    "InMemoryMailbox",
    "FileMailbox",
    "MailboxType",
]
