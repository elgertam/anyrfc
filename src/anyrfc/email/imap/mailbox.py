"""IMAP mailbox management per RFC 9051."""
# CRITICAL: ALL I/O OPERATIONS MUST USE ANYIO - NO ASYNCIO IMPORTS ALLOWED
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from enum import Enum
from datetime import datetime


class MailboxAttribute(Enum):
    """Mailbox attributes per RFC 9051 Section 7.3.1."""
    # Standard attributes
    NOINFERIORS = "\\Noinferiors"
    NOSELECT = "\\Noselect"
    MARKED = "\\Marked"
    UNMARKED = "\\Unmarked"
    
    # Special-use mailbox attributes (RFC 6154)
    ALL = "\\All"
    ARCHIVE = "\\Archive" 
    DRAFTS = "\\Drafts"
    FLAGGED = "\\Flagged"
    JUNK = "\\Junk"
    SENT = "\\Sent"
    TRASH = "\\Trash"
    IMPORTANT = "\\Important"


@dataclass
class MailboxInfo:
    """IMAP mailbox information."""
    name: str
    attributes: Set[str]
    delimiter: str
    exists: Optional[int] = None
    recent: Optional[int] = None
    unseen: Optional[int] = None
    uidvalidity: Optional[int] = None
    uidnext: Optional[int] = None
    permanentflags: Set[str] = None
    flags: Set[str] = None
    
    def __post_init__(self):
        if self.permanentflags is None:
            self.permanentflags = set()
        if self.flags is None:
            self.flags = set()
    
    @property
    def is_selectable(self) -> bool:
        """Check if mailbox is selectable."""
        return MailboxAttribute.NOSELECT.value not in self.attributes
    
    @property
    def has_children(self) -> bool:
        """Check if mailbox can have children."""
        return MailboxAttribute.NOINFERIORS.value not in self.attributes
    
    @property
    def is_marked(self) -> bool:
        """Check if mailbox is marked."""
        return MailboxAttribute.MARKED.value in self.attributes
    
    def has_special_use(self, use: MailboxAttribute) -> bool:
        """Check if mailbox has specific special use."""
        return use.value in self.attributes


class MailboxManager:
    """IMAP mailbox management helper."""
    
    def __init__(self, client):
        self.client = client
        self._mailbox_cache: Dict[str, MailboxInfo] = {}
        self._hierarchy_delimiter: Optional[str] = None
    
    async def get_mailbox_list(self, reference: str = "", pattern: str = "*",
                             refresh_cache: bool = False) -> List[MailboxInfo]:
        """Get list of mailboxes with caching."""
        if refresh_cache or not self._mailbox_cache:
            await self._refresh_mailbox_cache(reference, pattern)
        
        return list(self._mailbox_cache.values())
    
    async def get_mailbox_info(self, mailbox: str, 
                             refresh: bool = False) -> Optional[MailboxInfo]:
        """Get information for specific mailbox."""
        if refresh or mailbox not in self._mailbox_cache:
            # Refresh cache for this specific mailbox
            mailboxes = await self.client.list_mailboxes("", mailbox)
            for mb_data in mailboxes:
                info = self._parse_mailbox_data(mb_data)
                if info:
                    self._mailbox_cache[info.name] = info
        
        return self._mailbox_cache.get(mailbox)
    
    async def get_mailbox_status(self, mailbox: str, 
                               items: List[str] = None) -> Dict[str, int]:
        """Get mailbox status information."""
        if items is None:
            items = ["MESSAGES", "RECENT", "UIDNEXT", "UIDVALIDITY", "UNSEEN"]
        
        from .commands import IMAPCommandBuilder
        command = IMAPCommandBuilder.status(mailbox, items)
        response = await self.client._send_command(command)
        
        if response.status.value == "OK":
            # Parse STATUS response
            for resp in self.client._pending_responses:
                if resp.message.startswith("STATUS"):
                    from .responses import IMAPResponseParser
                    status_data = IMAPResponseParser.parse_status_response(resp.raw_line)
                    if status_data:
                        return status_data
            return {}
        else:
            raise RuntimeError(f"STATUS failed: {response.message}")
    
    async def create_mailbox(self, mailbox: str) -> bool:
        """Create a new mailbox."""
        from .commands import IMAPCommandBuilder
        command = IMAPCommandBuilder.create(mailbox)
        response = await self.client._send_command(command)
        
        success = response.status.value == "OK"
        if success:
            # Invalidate cache
            self._mailbox_cache.clear()
        
        return success
    
    async def delete_mailbox(self, mailbox: str) -> bool:
        """Delete a mailbox."""
        from .commands import IMAPCommandBuilder
        command = IMAPCommandBuilder.delete(mailbox)
        response = await self.client._send_command(command)
        
        success = response.status.value == "OK"
        if success:
            # Remove from cache
            self._mailbox_cache.pop(mailbox, None)
        
        return success
    
    async def rename_mailbox(self, old_name: str, new_name: str) -> bool:
        """Rename a mailbox."""
        from .commands import IMAPCommandBuilder
        command = IMAPCommandBuilder.rename(old_name, new_name)
        response = await self.client._send_command(command)
        
        success = response.status.value == "OK"
        if success:
            # Update cache
            if old_name in self._mailbox_cache:
                info = self._mailbox_cache.pop(old_name)
                info.name = new_name
                self._mailbox_cache[new_name] = info
        
        return success
    
    async def subscribe_mailbox(self, mailbox: str) -> bool:
        """Subscribe to a mailbox."""
        from .commands import IMAPCommand, IMAPCommandType, IMAPQuotedString
        mailbox_quoted = IMAPQuotedString(mailbox).to_imap_string()
        command = IMAPCommand(IMAPCommandType.SUBSCRIBE, [mailbox_quoted])
        response = await self.client._send_command(command)
        
        return response.status.value == "OK"
    
    async def unsubscribe_mailbox(self, mailbox: str) -> bool:
        """Unsubscribe from a mailbox."""
        from .commands import IMAPCommand, IMAPCommandType, IMAPQuotedString
        mailbox_quoted = IMAPQuotedString(mailbox).to_imap_string()
        command = IMAPCommand(IMAPCommandType.UNSUBSCRIBE, [mailbox_quoted])
        response = await self.client._send_command(command)
        
        return response.status.value == "OK"
    
    async def get_subscribed_mailboxes(self, reference: str = "", 
                                     pattern: str = "*") -> List[MailboxInfo]:
        """Get list of subscribed mailboxes."""
        from .commands import IMAPCommand, IMAPCommandType, IMAPQuotedString
        ref_quoted = IMAPQuotedString(reference).to_imap_string()
        pattern_quoted = IMAPQuotedString(pattern).to_imap_string()
        command = IMAPCommand(IMAPCommandType.LIST, ["SUBSCRIBED", ref_quoted, pattern_quoted])
        response = await self.client._send_command(command)
        
        if response.status.value == "OK":
            mailboxes = []
            for resp in self.client._pending_responses:
                if resp.message.startswith("LIST"):
                    from .responses import IMAPResponseParser
                    mailbox_data = IMAPResponseParser.parse_list_response(resp.raw_line)
                    if mailbox_data:
                        info = self._parse_mailbox_data(mailbox_data)
                        if info:
                            mailboxes.append(info)
            
            self.client._pending_responses = []
            return mailboxes
        else:
            raise RuntimeError(f"LIST SUBSCRIBED failed: {response.message}")
    
    def get_hierarchy_delimiter(self) -> Optional[str]:
        """Get the hierarchy delimiter character."""
        return self._hierarchy_delimiter
    
    def get_parent_mailbox(self, mailbox: str) -> Optional[str]:
        """Get parent mailbox name."""
        if not self._hierarchy_delimiter:
            return None
        
        delimiter_pos = mailbox.rfind(self._hierarchy_delimiter)
        if delimiter_pos > 0:
            return mailbox[:delimiter_pos]
        return None
    
    def get_child_mailboxes(self, parent: str) -> List[str]:
        """Get direct child mailboxes."""
        if not self._hierarchy_delimiter:
            return []
        
        children = []
        prefix = parent + self._hierarchy_delimiter
        
        for mailbox_name in self._mailbox_cache:
            if mailbox_name.startswith(prefix):
                # Check if it's a direct child (no additional delimiters)
                remainder = mailbox_name[len(prefix):]
                if self._hierarchy_delimiter not in remainder:
                    children.append(mailbox_name)
        
        return children
    
    def build_mailbox_tree(self) -> Dict[str, Any]:
        """Build hierarchical mailbox tree."""
        tree = {}
        
        for mailbox_name, info in self._mailbox_cache.items():
            if not self._hierarchy_delimiter:
                tree[mailbox_name] = {"info": info, "children": {}}
                continue
            
            parts = mailbox_name.split(self._hierarchy_delimiter)
            current = tree
            
            for i, part in enumerate(parts):
                if part not in current:
                    current[part] = {"info": None, "children": {}}
                
                if i == len(parts) - 1:
                    current[part]["info"] = info
                
                current = current[part]["children"]
        
        return tree
    
    async def _refresh_mailbox_cache(self, reference: str, pattern: str) -> None:
        """Refresh the mailbox cache."""
        mailboxes = await self.client.list_mailboxes(reference, pattern)
        
        self._mailbox_cache.clear()
        
        for mailbox_data in mailboxes:
            info = self._parse_mailbox_data(mailbox_data)
            if info:
                self._mailbox_cache[info.name] = info
                
                # Update hierarchy delimiter
                if self._hierarchy_delimiter is None and info.delimiter:
                    self._hierarchy_delimiter = info.delimiter
    
    def _parse_mailbox_data(self, mailbox_data: Dict[str, Any]) -> Optional[MailboxInfo]:
        """Parse mailbox data from LIST response."""
        if not mailbox_data:
            return None
        
        name = mailbox_data.get('mailbox', '')
        attributes = set(mailbox_data.get('flags', []))
        delimiter = mailbox_data.get('delimiter', '')
        
        return MailboxInfo(
            name=name,
            attributes=attributes,
            delimiter=delimiter
        )
    
    def find_special_use_mailbox(self, use: MailboxAttribute) -> Optional[MailboxInfo]:
        """Find mailbox with specific special-use attribute."""
        for info in self._mailbox_cache.values():
            if info.has_special_use(use):
                return info
        return None
    
    def get_drafts_mailbox(self) -> Optional[MailboxInfo]:
        """Get the Drafts mailbox."""
        return self.find_special_use_mailbox(MailboxAttribute.DRAFTS)
    
    def get_sent_mailbox(self) -> Optional[MailboxInfo]:
        """Get the Sent mailbox.""" 
        return self.find_special_use_mailbox(MailboxAttribute.SENT)
    
    def get_trash_mailbox(self) -> Optional[MailboxInfo]:
        """Get the Trash mailbox."""
        return self.find_special_use_mailbox(MailboxAttribute.TRASH)
    
    def get_junk_mailbox(self) -> Optional[MailboxInfo]:
        """Get the Junk/Spam mailbox."""
        return self.find_special_use_mailbox(MailboxAttribute.JUNK)
    
    def get_archive_mailbox(self) -> Optional[MailboxInfo]:
        """Get the Archive mailbox."""
        return self.find_special_use_mailbox(MailboxAttribute.ARCHIVE)