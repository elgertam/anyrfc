"""IMAP extensions implementation per various RFCs."""
# CRITICAL: ALL I/O OPERATIONS MUST USE ANYIO - NO ASYNCIO IMPORTS ALLOWED
import anyio
from typing import Dict, List, Optional, Any, AsyncIterator, Callable
from enum import Enum
from abc import ABC, abstractmethod

from .commands import IMAPCommand, IMAPCommandType, IMAPCommandBuilder
from .responses import IMAPResponse, IMAPResponseParser


class IMAPExtension(ABC):
    """Base class for IMAP extensions."""
    
    @abstractmethod
    def get_capability_name(self) -> str:
        """Return the capability name for this extension."""
    
    @abstractmethod
    def get_rfc_number(self) -> str:
        """Return the RFC number that defines this extension."""
    
    @abstractmethod
    async def validate_server_support(self, capabilities: set[str]) -> bool:
        """Check if server supports this extension."""


class IdleExtension(IMAPExtension):
    """IDLE extension per RFC 2177."""
    
    def __init__(self, client):
        self.client = client
        self._idle_active = False
        self._idle_task: Optional[anyio.abc.TaskGroup] = None
    
    def get_capability_name(self) -> str:
        return "IDLE"
    
    def get_rfc_number(self) -> str:
        return "RFC 2177"
    
    async def validate_server_support(self, capabilities: set[str]) -> bool:
        return "IDLE" in capabilities
    
    async def start_idle(self, callback: Optional[Callable[[IMAPResponse], None]] = None) -> None:
        """Start IDLE mode per RFC 2177."""
        if self._idle_active:
            raise RuntimeError("IDLE already active")
        
        if not await self.validate_server_support(self.client.capabilities):
            raise RuntimeError("Server does not support IDLE")
        
        # Send IDLE command
        command = IMAPCommandBuilder.idle()
        await self.client._send_command_no_wait(command)
        
        # Read continuation response
        response = await self.client._read_response()
        if response.response_type.value != "continuation":
            raise RuntimeError(f"Expected continuation, got: {response.message}")
        
        self._idle_active = True
        
        # Start monitoring for updates if callback provided
        if callback:
            async with anyio.create_task_group() as tg:
                self._idle_task = tg
                tg.start_soon(self._monitor_idle_responses, callback)
    
    async def stop_idle(self) -> None:
        """Stop IDLE mode per RFC 2177."""
        if not self._idle_active:
            return
        
        # Send DONE to exit IDLE
        await self.client._stream.send(b"DONE\r\n")
        
        # Read completion response
        response = await self.client._read_response()
        
        self._idle_active = False
        if self._idle_task:
            self._idle_task.cancel_scope.cancel()
            self._idle_task = None
    
    async def _monitor_idle_responses(self, callback: Callable[[IMAPResponse], None]) -> None:
        """Monitor for IDLE responses using AnyIO."""
        while self._idle_active:
            try:
                response = await self.client._read_response()
                callback(response)
                
                # Handle expunge, exists, recent updates
                if any(keyword in response.message for keyword in ["EXISTS", "RECENT", "EXPUNGE", "FETCH"]):
                    # Mailbox state changed
                    pass
                    
            except anyio.get_cancelled_exc_class():
                break
            except Exception as e:
                # Log error and continue
                print(f"IDLE monitoring error: {e}")


class SortExtension(IMAPExtension):
    """SORT extension per RFC 5256."""
    
    def __init__(self, client):
        self.client = client
    
    def get_capability_name(self) -> str:
        return "SORT"
    
    def get_rfc_number(self) -> str:
        return "RFC 5256"
    
    async def validate_server_support(self, capabilities: set[str]) -> bool:
        return "SORT" in capabilities
    
    async def sort_messages(self, sort_criteria: List[str], search_criteria: str, 
                          charset: str = "UTF-8") -> List[int]:
        """SORT messages per RFC 5256."""
        if not await self.validate_server_support(self.client.capabilities):
            raise RuntimeError("Server does not support SORT")
        
        # Build SORT command
        criteria_str = f"({' '.join(sort_criteria)})"
        args = [criteria_str, charset, search_criteria]
        command = IMAPCommand(IMAPCommandType.SORT, args)
        
        response = await self.client._send_command(command)
        
        if response.status.value == "OK":
            # Parse SORT response
            for resp in self.client._pending_responses:
                if resp.message.startswith("SORT"):
                    parts = resp.message.split()
                    if len(parts) > 1:
                        return [int(num) for num in parts[1:]]
            return []
        else:
            raise RuntimeError(f"SORT failed: {response.message}")


class ThreadExtension(IMAPExtension):
    """THREAD extension per RFC 5256."""
    
    def __init__(self, client):
        self.client = client
    
    def get_capability_name(self) -> str:
        return "THREAD"
    
    def get_rfc_number(self) -> str:
        return "RFC 5256"
    
    async def validate_server_support(self, capabilities: set[str]) -> bool:
        return any("THREAD=" in cap for cap in capabilities)
    
    async def thread_messages(self, algorithm: str, search_criteria: str,
                            charset: str = "UTF-8") -> List[Dict[str, Any]]:
        """THREAD messages per RFC 5256."""
        if not await self.validate_server_support(self.client.capabilities):
            raise RuntimeError("Server does not support THREAD")
        
        # Build THREAD command
        args = [algorithm, charset, search_criteria]
        command = IMAPCommand(IMAPCommandType.THREAD, args)
        
        response = await self.client._send_command(command)
        
        if response.status.value == "OK":
            # Parse THREAD response - simplified implementation
            threads = []
            for resp in self.client._pending_responses:
                if resp.message.startswith("THREAD"):
                    # Parse thread structure (simplified)
                    threads.append({"raw": resp.message})
            return threads
        else:
            raise RuntimeError(f"THREAD failed: {response.message}")


class CondstoreExtension(IMAPExtension):
    """CONDSTORE extension per RFC 7162."""
    
    def __init__(self, client):
        self.client = client
    
    def get_capability_name(self) -> str:
        return "CONDSTORE"
    
    def get_rfc_number(self) -> str:
        return "RFC 7162"
    
    async def validate_server_support(self, capabilities: set[str]) -> bool:
        return "CONDSTORE" in capabilities
    
    async def fetch_changed_since(self, sequence_set: str, modseq: int, 
                                items: str) -> List[Dict[str, Any]]:
        """Fetch messages changed since MODSEQ per RFC 7162."""
        if not await self.validate_server_support(self.client.capabilities):
            raise RuntimeError("Server does not support CONDSTORE")
        
        # Build FETCH command with CHANGEDSINCE
        args = [sequence_set, items, f"(CHANGEDSINCE {modseq})"]
        command = IMAPCommand(IMAPCommandType.FETCH, args)
        
        response = await self.client._send_command(command)
        
        if response.status.value == "OK":
            messages = []
            for resp in self.client._pending_responses:
                if " FETCH " in resp.message:
                    fetch_data = IMAPResponseParser.parse_fetch_response(resp.raw_line)
                    if fetch_data:
                        messages.append(fetch_data)
            return messages
        else:
            raise RuntimeError(f"FETCH CHANGEDSINCE failed: {response.message}")


class QresyncExtension(IMAPExtension):
    """QRESYNC extension per RFC 7162."""
    
    def __init__(self, client):
        self.client = client
    
    def get_capability_name(self) -> str:
        return "QRESYNC"
    
    def get_rfc_number(self) -> str:
        return "RFC 7162"
    
    async def validate_server_support(self, capabilities: set[str]) -> bool:
        return "QRESYNC" in capabilities
    
    async def select_with_qresync(self, mailbox: str, uidvalidity: int, 
                                 modseq: int, known_uids: Optional[str] = None,
                                 seq_match_data: Optional[str] = None) -> Dict[str, Any]:
        """SELECT with QRESYNC per RFC 7162."""
        if not await self.validate_server_support(self.client.capabilities):
            raise RuntimeError("Server does not support QRESYNC")
        
        # Build SELECT command with QRESYNC
        qresync_params = [str(uidvalidity), str(modseq)]
        if known_uids:
            qresync_params.append(known_uids)
        if seq_match_data:
            qresync_params.append(seq_match_data)
        
        qresync_str = f"(QRESYNC ({' '.join(qresync_params)}))"
        
        from .commands import IMAPQuotedString
        mailbox_quoted = IMAPQuotedString(mailbox).to_imap_string()
        args = [mailbox_quoted, qresync_str]
        command = IMAPCommand(IMAPCommandType.SELECT, args)
        
        response = await self.client._send_command(command)
        
        if response.status.value == "OK":
            return self.client._parse_select_response()
        else:
            raise RuntimeError(f"SELECT QRESYNC failed: {response.message}")


class AppendLimitExtension(IMAPExtension):
    """APPENDLIMIT extension per RFC 7889."""
    
    def __init__(self, client):
        self.client = client
    
    def get_capability_name(self) -> str:
        return "APPENDLIMIT"
    
    def get_rfc_number(self) -> str:
        return "RFC 7889"
    
    async def validate_server_support(self, capabilities: set[str]) -> bool:
        return any("APPENDLIMIT" in cap for cap in capabilities)
    
    def get_append_limit(self, capabilities: set[str]) -> Optional[int]:
        """Get APPENDLIMIT value from capabilities."""
        for cap in capabilities:
            if cap.startswith("APPENDLIMIT="):
                try:
                    return int(cap.split("=")[1])
                except (IndexError, ValueError):
                    pass
        return None


class ExtensionManager:
    """Manager for IMAP extensions."""
    
    def __init__(self, client):
        self.client = client
        self.extensions: Dict[str, IMAPExtension] = {}
        
        # Register standard extensions
        self.register_extension(IdleExtension(client))
        self.register_extension(SortExtension(client))
        self.register_extension(ThreadExtension(client))
        self.register_extension(CondstoreExtension(client))
        self.register_extension(QresyncExtension(client))
        self.register_extension(AppendLimitExtension(client))
    
    def register_extension(self, extension: IMAPExtension) -> None:
        """Register an IMAP extension."""
        self.extensions[extension.get_capability_name()] = extension
    
    def get_extension(self, name: str) -> Optional[IMAPExtension]:
        """Get extension by capability name."""
        return self.extensions.get(name)
    
    async def get_supported_extensions(self) -> List[str]:
        """Get list of supported extensions based on server capabilities."""
        supported = []
        capabilities = self.client.capabilities
        
        for name, extension in self.extensions.items():
            if await extension.validate_server_support(capabilities):
                supported.append(name)
        
        return supported
    
    def has_extension(self, name: str) -> bool:
        """Check if extension is supported by server."""
        extension = self.get_extension(name)
        if not extension:
            return False
        
        # Synchronous check - use cached capabilities
        capabilities = self.client.capabilities
        
        # Simple capability check for basic extensions
        if name == "IDLE":
            return "IDLE" in capabilities
        elif name == "SORT":
            return "SORT" in capabilities
        elif name == "THREAD":
            return any("THREAD=" in cap for cap in capabilities)
        elif name == "CONDSTORE":
            return "CONDSTORE" in capabilities
        elif name == "QRESYNC":
            return "QRESYNC" in capabilities
        elif name == "APPENDLIMIT":
            return any("APPENDLIMIT" in cap for cap in capabilities)
        
        return False