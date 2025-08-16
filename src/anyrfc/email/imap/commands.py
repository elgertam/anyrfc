"""IMAP command construction per RFC 9051."""
# CRITICAL: ALL I/O OPERATIONS MUST USE ANYIO - NO ASYNCIO IMPORTS ALLOWED
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import re

class IMAPCommandType(Enum):
    """IMAP command types per RFC 9051."""
    # Connection and authentication
    CAPABILITY = "CAPABILITY"
    NOOP = "NOOP"
    LOGOUT = "LOGOUT"
    STARTTLS = "STARTTLS"
    AUTHENTICATE = "AUTHENTICATE"
    LOGIN = "LOGIN"
    
    # Mailbox management
    SELECT = "SELECT"
    EXAMINE = "EXAMINE"
    CREATE = "CREATE"
    DELETE = "DELETE"
    RENAME = "RENAME"
    SUBSCRIBE = "SUBSCRIBE"
    UNSUBSCRIBE = "UNSUBSCRIBE"
    LIST = "LIST"
    NAMESPACE = "NAMESPACE"
    STATUS = "STATUS"
    
    # Message operations
    APPEND = "APPEND"
    CHECK = "CHECK"
    CLOSE = "CLOSE"
    EXPUNGE = "EXPUNGE"
    SEARCH = "SEARCH"
    FETCH = "FETCH"
    STORE = "STORE"
    COPY = "COPY"
    MOVE = "MOVE"
    
    # Extensions
    IDLE = "IDLE"
    SORT = "SORT"
    THREAD = "THREAD"

@dataclass
class IMAPCommand:
    """IMAP command representation."""
    command_type: IMAPCommandType
    arguments: List[str]
    
    def to_string(self) -> str:
        """Convert command to IMAP protocol string."""
        if self.arguments:
            return f"{self.command_type.value} {' '.join(self.arguments)}"
        else:
            return self.command_type.value

class IMAPLiteral:
    """IMAP literal string representation per RFC 9051 Section 4.3."""
    
    def __init__(self, data: Union[str, bytes]):
        if isinstance(data, str):
            self.data = data.encode('utf-8')
        else:
            self.data = data
    
    def __len__(self) -> int:
        return len(self.data)
    
    def to_imap_string(self) -> str:
        """Convert to IMAP literal format: {length}"""
        return f"{{{len(self.data)}}}"

class IMAPQuotedString:
    """IMAP quoted string per RFC 9051."""
    
    def __init__(self, value: str):
        self.value = value
    
    def to_imap_string(self) -> str:
        """Convert to IMAP quoted string format."""
        # Escape quotes and backslashes
        escaped = self.value.replace('\\', '\\\\').replace('"', '\\"')
        return f'"{escaped}"'

class IMAPCommandBuilder:
    """Builder for IMAP commands per RFC 9051."""
    
    @staticmethod
    def capability() -> IMAPCommand:
        """Build CAPABILITY command per RFC 9051 Section 6.1.1."""
        return IMAPCommand(IMAPCommandType.CAPABILITY, [])
    
    @staticmethod
    def noop() -> IMAPCommand:
        """Build NOOP command per RFC 9051 Section 6.1.2."""
        return IMAPCommand(IMAPCommandType.NOOP, [])
    
    @staticmethod
    def logout() -> IMAPCommand:
        """Build LOGOUT command per RFC 9051 Section 6.1.3."""
        return IMAPCommand(IMAPCommandType.LOGOUT, [])
    
    @staticmethod
    def starttls() -> IMAPCommand:
        """Build STARTTLS command per RFC 8314."""
        return IMAPCommand(IMAPCommandType.STARTTLS, [])
    
    @staticmethod
    def login(username: str, password: str) -> IMAPCommand:
        """Build LOGIN command per RFC 9051 Section 6.2.3."""
        # Use quoted strings for username and password
        username_quoted = IMAPQuotedString(username).to_imap_string()
        password_quoted = IMAPQuotedString(password).to_imap_string()
        return IMAPCommand(IMAPCommandType.LOGIN, [username_quoted, password_quoted])
    
    @staticmethod
    def authenticate(mechanism: str, initial_response: Optional[str] = None) -> IMAPCommand:
        """Build AUTHENTICATE command per RFC 9051 Section 6.2.2."""
        args = [mechanism]
        if initial_response:
            args.append(initial_response)
        return IMAPCommand(IMAPCommandType.AUTHENTICATE, args)
    
    @staticmethod
    def select(mailbox: str) -> IMAPCommand:
        """Build SELECT command per RFC 9051 Section 6.3.1."""
        mailbox_quoted = IMAPQuotedString(mailbox).to_imap_string()
        return IMAPCommand(IMAPCommandType.SELECT, [mailbox_quoted])
    
    @staticmethod
    def examine(mailbox: str) -> IMAPCommand:
        """Build EXAMINE command per RFC 9051 Section 6.3.2."""
        mailbox_quoted = IMAPQuotedString(mailbox).to_imap_string()
        return IMAPCommand(IMAPCommandType.EXAMINE, [mailbox_quoted])
    
    @staticmethod
    def create(mailbox: str) -> IMAPCommand:
        """Build CREATE command per RFC 9051 Section 6.3.3."""
        mailbox_quoted = IMAPQuotedString(mailbox).to_imap_string()
        return IMAPCommand(IMAPCommandType.CREATE, [mailbox_quoted])
    
    @staticmethod
    def delete(mailbox: str) -> IMAPCommand:
        """Build DELETE command per RFC 9051 Section 6.3.4."""
        mailbox_quoted = IMAPQuotedString(mailbox).to_imap_string()
        return IMAPCommand(IMAPCommandType.DELETE, [mailbox_quoted])
    
    @staticmethod
    def rename(old_mailbox: str, new_mailbox: str) -> IMAPCommand:
        """Build RENAME command per RFC 9051 Section 6.3.5."""
        old_quoted = IMAPQuotedString(old_mailbox).to_imap_string()
        new_quoted = IMAPQuotedString(new_mailbox).to_imap_string()
        return IMAPCommand(IMAPCommandType.RENAME, [old_quoted, new_quoted])
    
    @staticmethod
    def list(reference: str = "", mailbox_pattern: str = "*") -> IMAPCommand:
        """Build LIST command per RFC 9051 Section 6.3.9."""
        ref_quoted = IMAPQuotedString(reference).to_imap_string()
        pattern_quoted = IMAPQuotedString(mailbox_pattern).to_imap_string()
        return IMAPCommand(IMAPCommandType.LIST, [ref_quoted, pattern_quoted])
    
    @staticmethod
    def status(mailbox: str, items: List[str]) -> IMAPCommand:
        """Build STATUS command per RFC 9051 Section 6.3.10."""
        mailbox_quoted = IMAPQuotedString(mailbox).to_imap_string()
        items_str = f"({' '.join(items)})"
        return IMAPCommand(IMAPCommandType.STATUS, [mailbox_quoted, items_str])
    
    @staticmethod
    def fetch(sequence_set: str, items: str) -> IMAPCommand:
        """Build FETCH command per RFC 9051 Section 6.4.5."""
        return IMAPCommand(IMAPCommandType.FETCH, [sequence_set, items])
    
    @staticmethod
    def store(sequence_set: str, item: str, value: str) -> IMAPCommand:
        """Build STORE command per RFC 9051 Section 6.4.6."""
        return IMAPCommand(IMAPCommandType.STORE, [sequence_set, item, value])
    
    @staticmethod
    def search(criteria: str, charset: Optional[str] = None) -> IMAPCommand:
        """Build SEARCH command per RFC 9051 Section 6.4.4."""
        args = []
        if charset:
            args.extend(["CHARSET", charset])
        args.append(criteria)
        return IMAPCommand(IMAPCommandType.SEARCH, args)
    
    @staticmethod
    def copy(sequence_set: str, mailbox: str) -> IMAPCommand:
        """Build COPY command per RFC 9051 Section 6.4.7."""
        mailbox_quoted = IMAPQuotedString(mailbox).to_imap_string()
        return IMAPCommand(IMAPCommandType.COPY, [sequence_set, mailbox_quoted])
    
    @staticmethod
    def move(sequence_set: str, mailbox: str) -> IMAPCommand:
        """Build MOVE command per RFC 6851."""
        mailbox_quoted = IMAPQuotedString(mailbox).to_imap_string()
        return IMAPCommand(IMAPCommandType.MOVE, [sequence_set, mailbox_quoted])
    
    @staticmethod
    def idle() -> IMAPCommand:
        """Build IDLE command per RFC 2177."""
        return IMAPCommand(IMAPCommandType.IDLE, [])
    
    @staticmethod
    def close() -> IMAPCommand:
        """Build CLOSE command per RFC 9051 Section 6.4.2."""
        return IMAPCommand(IMAPCommandType.CLOSE, [])
    
    @staticmethod
    def expunge() -> IMAPCommand:
        """Build EXPUNGE command per RFC 9051 Section 6.4.3."""
        return IMAPCommand(IMAPCommandType.EXPUNGE, [])

class IMAPSequenceSet:
    """IMAP sequence set utilities per RFC 9051 Section 9."""
    
    @staticmethod
    def single(num: int) -> str:
        """Create sequence set for single message."""
        return str(num)
    
    @staticmethod
    def range(start: int, end: int) -> str:
        """Create sequence set for range of messages."""
        return f"{start}:{end}"
    
    @staticmethod
    def from_list(numbers: List[int]) -> str:
        """Create sequence set from list of message numbers."""
        return ",".join(str(n) for n in numbers)
    
    @staticmethod
    def all_messages() -> str:
        """Create sequence set for all messages."""
        return "1:*"
    
    @staticmethod
    def last_n_messages(n: int) -> str:
        """Create sequence set for last N messages."""
        if n == 1:
            return "*"
        else:
            return f"*:{n}"