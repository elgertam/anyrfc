"""IMAP message handling per RFC 9051."""
# CRITICAL: ALL I/O OPERATIONS MUST USE ANYIO - NO ASYNCIO IMPORTS ALLOWED
from typing import Dict, List, Optional, Any, Set, Union
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import email
import email.parser
import email.policy
from email.message import EmailMessage


class MessageFlag(Enum):
    """IMAP message flags per RFC 9051 Section 2.3.2."""
    # System flags
    SEEN = "\\Seen"
    ANSWERED = "\\Answered"
    FLAGGED = "\\Flagged"
    DELETED = "\\Deleted"
    DRAFT = "\\Draft"
    RECENT = "\\Recent"


@dataclass
class MessageEnvelope:
    """IMAP message envelope structure per RFC 9051."""
    date: Optional[str] = None
    subject: Optional[str] = None
    from_: Optional[List[Dict[str, str]]] = None
    sender: Optional[List[Dict[str, str]]] = None
    reply_to: Optional[List[Dict[str, str]]] = None
    to: Optional[List[Dict[str, str]]] = None
    cc: Optional[List[Dict[str, str]]] = None
    bcc: Optional[List[Dict[str, str]]] = None
    in_reply_to: Optional[str] = None
    message_id: Optional[str] = None


@dataclass
class MessageBodyStructure:
    """IMAP message body structure per RFC 9051."""
    media_type: str
    media_subtype: str
    parameters: Dict[str, str]
    content_id: Optional[str] = None
    content_description: Optional[str] = None
    content_encoding: Optional[str] = None
    size: Optional[int] = None
    parts: Optional[List['MessageBodyStructure']] = None
    
    @property
    def is_multipart(self) -> bool:
        """Check if this is a multipart body structure."""
        return self.parts is not None and len(self.parts) > 0
    
    @property
    def content_type(self) -> str:
        """Get full content type."""
        return f"{self.media_type}/{self.media_subtype}"


@dataclass
class MessageInfo:
    """IMAP message information."""
    message_number: int
    uid: Optional[int] = None
    flags: Set[str] = None
    internal_date: Optional[datetime] = None
    size: Optional[int] = None
    envelope: Optional[MessageEnvelope] = None
    body_structure: Optional[MessageBodyStructure] = None
    modseq: Optional[int] = None  # For CONDSTORE
    
    def __post_init__(self):
        if self.flags is None:
            self.flags = set()
    
    def has_flag(self, flag: Union[MessageFlag, str]) -> bool:
        """Check if message has specific flag."""
        flag_str = flag.value if isinstance(flag, MessageFlag) else flag
        return flag_str in self.flags
    
    @property
    def is_seen(self) -> bool:
        return self.has_flag(MessageFlag.SEEN)
    
    @property
    def is_flagged(self) -> bool:
        return self.has_flag(MessageFlag.FLAGGED)
    
    @property
    def is_answered(self) -> bool:
        return self.has_flag(MessageFlag.ANSWERED)
    
    @property
    def is_deleted(self) -> bool:
        return self.has_flag(MessageFlag.DELETED)
    
    @property
    def is_draft(self) -> bool:
        return self.has_flag(MessageFlag.DRAFT)
    
    @property
    def is_recent(self) -> bool:
        return self.has_flag(MessageFlag.RECENT)


class MessageManager:
    """IMAP message management helper."""
    
    def __init__(self, client):
        self.client = client
    
    async def get_message_info(self, message_nums: Union[int, str], 
                             use_uid: bool = False) -> List[MessageInfo]:
        """Get message information using FETCH."""
        if isinstance(message_nums, int):
            sequence_set = str(message_nums)
        else:
            sequence_set = message_nums
        
        # Fetch basic message info
        items = "FLAGS UID INTERNALDATE RFC822.SIZE ENVELOPE BODYSTRUCTURE"
        messages = await self.client.fetch_messages(sequence_set, items, use_uid)
        
        return [self._parse_message_info(msg) for msg in messages]
    
    async def get_message_headers(self, message_nums: Union[int, str],
                                headers: Optional[List[str]] = None,
                                use_uid: bool = False) -> List[Dict[str, Any]]:
        """Get message headers."""
        if isinstance(message_nums, int):
            sequence_set = str(message_nums)
        else:
            sequence_set = message_nums
        
        if headers:
            header_list = " ".join(headers)
            items = f"BODY.PEEK[HEADER.FIELDS ({header_list})]"
        else:
            items = "BODY.PEEK[HEADER]"
        
        messages = await self.client.fetch_messages(sequence_set, items, use_uid)
        return messages
    
    async def get_message_body(self, message_num: int, section: str = "",
                             use_uid: bool = False) -> Optional[bytes]:
        """Get message body or body section."""
        if section:
            items = f"BODY.PEEK[{section}]"
        else:
            items = "BODY.PEEK[]"
        
        messages = await self.client.fetch_messages(str(message_num), items, use_uid)
        
        if messages:
            # Extract body data from fetch response
            # This is simplified - production would need more robust parsing
            fetch_data = messages[0].get('fetch_data', '')
            # Parse body data from parenthesized list
            # Implementation would extract the literal data
            return b""  # Placeholder
        
        return None
    
    async def get_message_text(self, message_num: int, use_uid: bool = False) -> Optional[str]:
        """Get message as text."""
        body_data = await self.get_message_body(message_num, "", use_uid)
        if body_data:
            try:
                return body_data.decode('utf-8')
            except UnicodeDecodeError:
                return body_data.decode('utf-8', errors='replace')
        return None
    
    async def parse_message(self, message_num: int, use_uid: bool = False) -> Optional[EmailMessage]:
        """Parse message into EmailMessage object."""
        body_data = await self.get_message_body(message_num, "", use_uid)
        if body_data:
            parser = email.parser.BytesParser(policy=email.policy.default)
            return parser.parsebytes(body_data)
        return None
    
    async def set_message_flags(self, message_nums: Union[int, str], 
                              flags: List[str], action: str = "REPLACE",
                              use_uid: bool = False) -> bool:
        """Set message flags using STORE command."""
        if isinstance(message_nums, int):
            sequence_set = str(message_nums)
        else:
            sequence_set = message_nums
        
        # Build STORE command
        flags_str = f"({' '.join(flags)})"
        
        if action == "ADD":
            item = "+FLAGS"
        elif action == "REMOVE":
            item = "-FLAGS"
        else:  # REPLACE
            item = "FLAGS"
        
        from .commands import IMAPCommand, IMAPCommandType
        if use_uid:
            command = IMAPCommand(IMAPCommandType.STORE, ["UID", sequence_set, item, flags_str])
        else:
            command = IMAPCommand(IMAPCommandType.STORE, [sequence_set, item, flags_str])
        
        response = await self.client._send_command(command)
        return response.status.value == "OK"
    
    async def mark_seen(self, message_nums: Union[int, str], 
                       use_uid: bool = False) -> bool:
        """Mark messages as seen."""
        return await self.set_message_flags(
            message_nums, [MessageFlag.SEEN.value], "ADD", use_uid
        )
    
    async def mark_unseen(self, message_nums: Union[int, str],
                         use_uid: bool = False) -> bool:
        """Mark messages as unseen."""
        return await self.set_message_flags(
            message_nums, [MessageFlag.SEEN.value], "REMOVE", use_uid
        )
    
    async def mark_flagged(self, message_nums: Union[int, str],
                          use_uid: bool = False) -> bool:
        """Mark messages as flagged."""
        return await self.set_message_flags(
            message_nums, [MessageFlag.FLAGGED.value], "ADD", use_uid
        )
    
    async def mark_deleted(self, message_nums: Union[int, str],
                          use_uid: bool = False) -> bool:
        """Mark messages as deleted."""
        return await self.set_message_flags(
            message_nums, [MessageFlag.DELETED.value], "ADD", use_uid
        )
    
    async def copy_messages(self, message_nums: Union[int, str], 
                          destination: str, use_uid: bool = False) -> bool:
        """Copy messages to destination mailbox."""
        if isinstance(message_nums, int):
            sequence_set = str(message_nums)
        else:
            sequence_set = message_nums
        
        from .commands import IMAPCommand, IMAPCommandType, IMAPQuotedString
        mailbox_quoted = IMAPQuotedString(destination).to_imap_string()
        
        if use_uid:
            command = IMAPCommand(IMAPCommandType.COPY, ["UID", sequence_set, mailbox_quoted])
        else:
            command = IMAPCommand(IMAPCommandType.COPY, [sequence_set, mailbox_quoted])
        
        response = await self.client._send_command(command)
        return response.status.value == "OK"
    
    async def move_messages(self, message_nums: Union[int, str],
                          destination: str, use_uid: bool = False) -> bool:
        """Move messages to destination mailbox (if server supports MOVE)."""
        if not self.client.has_capability("MOVE"):
            # Fallback to COPY + STORE +FLAGS \\Deleted + EXPUNGE
            success = await self.copy_messages(message_nums, destination, use_uid)
            if success:
                await self.mark_deleted(message_nums, use_uid)
                await self.expunge_messages()
            return success
        
        if isinstance(message_nums, int):
            sequence_set = str(message_nums)
        else:
            sequence_set = message_nums
        
        from .commands import IMAPCommand, IMAPCommandType, IMAPQuotedString
        mailbox_quoted = IMAPQuotedString(destination).to_imap_string()
        
        if use_uid:
            command = IMAPCommand(IMAPCommandType.MOVE, ["UID", sequence_set, mailbox_quoted])
        else:
            command = IMAPCommand(IMAPCommandType.MOVE, [sequence_set, mailbox_quoted])
        
        response = await self.client._send_command(command)
        return response.status.value == "OK"
    
    async def expunge_messages(self) -> List[int]:
        """Expunge deleted messages from current mailbox."""
        from .commands import IMAPCommandBuilder
        command = IMAPCommandBuilder.expunge()
        response = await self.client._send_command(command)
        
        if response.status.value == "OK":
            # Parse EXPUNGE responses
            expunged = []
            for resp in self.client._pending_responses:
                if " EXPUNGE" in resp.message:
                    parts = resp.message.split()
                    if len(parts) >= 2 and parts[0] == "*":
                        try:
                            expunged.append(int(parts[1]))
                        except ValueError:
                            pass
            
            self.client._pending_responses = []
            return expunged
        else:
            raise RuntimeError(f"EXPUNGE failed: {response.message}")
    
    async def search_messages(self, criteria: str, use_uid: bool = False) -> List[int]:
        """Search for messages matching criteria."""
        return await self.client.search_messages(criteria, use_uid)
    
    async def append_message(self, mailbox: str, message: Union[str, bytes],
                           flags: Optional[List[str]] = None,
                           internal_date: Optional[datetime] = None) -> bool:
        """Append message to mailbox."""
        from .commands import IMAPCommand, IMAPCommandType, IMAPQuotedString, IMAPLiteral
        
        args = []
        
        # Mailbox name
        mailbox_quoted = IMAPQuotedString(mailbox).to_imap_string()
        args.append(mailbox_quoted)
        
        # Optional flags
        if flags:
            flags_str = f"({' '.join(flags)})"
            args.append(flags_str)
        
        # Optional internal date
        if internal_date:
            date_str = internal_date.strftime('"%d-%b-%Y %H:%M:%S %z"')
            args.append(date_str)
        
        # Message literal
        if isinstance(message, str):
            message = message.encode('utf-8')
        
        literal = IMAPLiteral(message)
        args.append(literal.to_imap_string())
        
        command = IMAPCommand(IMAPCommandType.APPEND, args)
        
        # For APPEND with literal, we need special handling
        # This is simplified - production would handle the literal continuation
        response = await self.client._send_command(command)
        return response.status.value == "OK"
    
    def _parse_message_info(self, fetch_data: Dict[str, Any]) -> MessageInfo:
        """Parse FETCH response into MessageInfo."""
        info = MessageInfo(
            message_number=fetch_data.get('message_number', 0)
        )
        
        # This is simplified parsing - production would need more robust parsing
        # of the actual FETCH response format
        raw_data = fetch_data.get('fetch_data', '')
        
        # Parse basic fields from fetch_data
        # Implementation would extract UID, FLAGS, INTERNALDATE, etc.
        # from the parenthesized response
        
        return info