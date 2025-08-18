"""IMAP client implementation per RFC 9051."""

from .client import IMAPClient, IMAPState
from .commands import IMAPCommandBuilder, IMAPCommand, IMAPSequenceSet
from .responses import IMAPResponseParser, IMAPResponse, IMAPStatus
from .mailbox import MailboxManager, MailboxInfo, MailboxAttribute
from .messages import (
    MessageManager,
    MessageInfo,
    MessageFlag,
    FetchItem,
    StoreAction,
    SearchCriteria,
    build_fetch_items,
    build_flag_list,
    build_search_criteria,
)
from .extensions import ExtensionManager, IdleExtension, SortExtension
from .compliance import RFC9051Compliance

__all__ = [
    "IMAPClient",
    "IMAPState",
    "IMAPCommandBuilder",
    "IMAPCommand",
    "IMAPSequenceSet",
    "IMAPResponseParser",
    "IMAPResponse",
    "IMAPStatus",
    "MailboxManager",
    "MailboxInfo",
    "MailboxAttribute",
    "MessageManager",
    "MessageInfo",
    "MessageFlag",
    "FetchItem",
    "StoreAction",
    "SearchCriteria",
    "build_fetch_items",
    "build_flag_list",
    "build_search_criteria",
    "ExtensionManager",
    "IdleExtension",
    "SortExtension",
    "RFC9051Compliance",
]
