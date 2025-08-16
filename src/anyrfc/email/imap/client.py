"""IMAP client implementation per RFC 9051."""
# CRITICAL: ALL I/O OPERATIONS MUST USE ANYIO - NO ASYNCIO IMPORTS ALLOWED
import anyio
from anyio.abc import ByteStream
from typing import AsyncIterator, Dict, List, Optional, Any, Union, Set
from enum import Enum

from ...core.types import ProtocolClient, ProtocolState, AuthenticationClient, RFCCompliance
from ...core.streams import AnyIOStreamHelpers
from ...core.tls import TLSHelper
from .commands import IMAPCommand, IMAPCommandBuilder, IMAPSequenceSet
from .responses import IMAPResponse, IMAPResponseParser, IMAPStatus, IMAPResponseType
from .extensions import ExtensionManager
from .mailbox import MailboxManager
from .messages import MessageManager

class IMAPState(Enum):
    """IMAP protocol states per RFC 9051."""
    NOT_AUTHENTICATED = "not_authenticated"
    AUTHENTICATED = "authenticated" 
    SELECTED = "selected"
    LOGOUT = "logout"

class IMAPClient(ProtocolClient[IMAPCommand], AuthenticationClient, RFCCompliance):
    """RFC 9051 compliant IMAP4rev2 client using ONLY AnyIO for I/O."""
    
    def __init__(self, hostname: str, port: int = 993, *, use_tls: bool = True):
        super().__init__()
        self.hostname = hostname
        self.port = port
        self.use_tls = use_tls
        self._stream: Optional[ByteStream] = None  # AnyIO ByteStream only
        self._imap_state = IMAPState.NOT_AUTHENTICATED
        self._tag_counter = 0
        self._capabilities: Set[str] = set()
        self._selected_mailbox: Optional[str] = None
        self._selected_mailbox_info: Dict[str, Any] = {}
        
        # Response handling
        self._pending_responses: List[IMAPResponse] = []
        self._idle_mode = False
        
        # Managers
        self.extensions = ExtensionManager(self)
        self.mailbox = MailboxManager(self)
        self.messages = MessageManager(self)
        
    def get_rfc_number(self) -> str:
        return "RFC 9051"
    
    async def validate_compliance(self) -> Dict[str, bool]:
        """Validate RFC 9051 compliance."""
        from .compliance import RFC9051Compliance
        compliance = RFC9051Compliance(self)
        return await compliance.validate_compliance()
    
    def get_test_vectors(self) -> Dict[str, Any]:
        """Return RFC 9051 test vectors."""
        from .compliance import RFC9051Compliance
        compliance = RFC9051Compliance(self)
        return compliance.get_test_vectors()
    
    @property
    def imap_state(self) -> IMAPState:
        """Get current IMAP protocol state."""
        return self._imap_state
    
    @property
    def capabilities(self) -> Set[str]:
        """Get server capabilities."""
        return self._capabilities.copy()
    
    @property
    def selected_mailbox(self) -> Optional[str]:
        """Get currently selected mailbox."""
        return self._selected_mailbox
    
    def has_capability(self, capability: str) -> bool:
        """Check if server has specific capability."""
        return capability.upper() in {cap.upper() for cap in self._capabilities}
    
    async def connect(self) -> None:
        """Establish IMAP connection per RFC 9051 using AnyIO."""
        await self._transition_state(ProtocolState.CONNECTING)
        
        try:
            # CRITICAL: Use ONLY AnyIO for network I/O
            if self.use_tls:
                tls_context = TLSHelper.create_default_client_context()
                self._stream = await anyio.connect_tcp(self.hostname, self.port, tls=True, ssl_context=tls_context)
            else:
                self._stream = await anyio.connect_tcp(self.hostname, self.port)
            
            # Read greeting per RFC 9051 Section 7.1.1
            greeting = await self._read_response()
            if greeting.status != IMAPStatus.OK and greeting.status != IMAPStatus.PREAUTH:
                raise ValueError(f"IMAP server greeting failed: {greeting.message}")
            
            # Check if pre-authenticated
            if greeting.status == IMAPStatus.PREAUTH:
                self._imap_state = IMAPState.AUTHENTICATED
                await self._transition_state(ProtocolState.AUTHENTICATED)
            else:
                await self._transition_state(ProtocolState.CONNECTED)
            
            # Get capabilities per RFC 9051
            await self._get_capabilities()
            
        except Exception as e:
            await self._transition_state(ProtocolState.ERROR)
            if self._stream:
                await self._cleanup_connection()
            raise
    
    async def disconnect(self) -> None:
        """Gracefully close IMAP connection per RFC 9051."""
        if self.state in {ProtocolState.CONNECTED, ProtocolState.AUTHENTICATED}:
            try:
                # Send LOGOUT command
                await self._send_command(IMAPCommandBuilder.logout())
                self._imap_state = IMAPState.LOGOUT
            except Exception:
                # Ignore logout errors
                pass
        
        await self._cleanup_connection()
        await self._transition_state(ProtocolState.DISCONNECTED)
    
    async def authenticate(self, credentials: Dict[str, Any]) -> bool:
        """Perform IMAP authentication per RFC 9051."""
        if self.state != ProtocolState.CONNECTED:
            raise RuntimeError("Must be connected before authentication")
        
        await self._transition_state(ProtocolState.AUTHENTICATING)
        
        username = credentials.get('username')
        password = credentials.get('password')
        auth_method = credentials.get('method', 'LOGIN')
        
        try:
            if auth_method == 'LOGIN':
                success = await self._login(username, password)
            else:
                # Implement other SASL methods per RFC 4422
                success = await self._sasl_authenticate(auth_method, credentials)
            
            if success:
                self._imap_state = IMAPState.AUTHENTICATED
                await self._transition_state(ProtocolState.AUTHENTICATED)
            else:
                await self._transition_state(ProtocolState.CONNECTED)
            
            return success
            
        except Exception as e:
            await self._transition_state(ProtocolState.ERROR)
            raise
    
    async def refresh_credentials(self) -> bool:
        """Refresh authentication credentials if supported."""
        # IMAP doesn't typically support credential refresh
        return False
    
    async def send(self, message: IMAPCommand) -> None:
        """Send IMAP command following RFC encoding rules."""
        await self._send_command(message)
    
    async def receive(self) -> AsyncIterator[IMAPCommand]:
        """Receive responses following RFC parsing rules."""
        # IMAP is request-response, so this iterator doesn't make as much sense
        # But we implement it for interface compliance
        while self.state in {ProtocolState.CONNECTED, ProtocolState.AUTHENTICATED}:
            response = await self._read_response()
            if response.response_type == IMAPResponseType.UNTAGGED:
                # Convert response to command-like object for interface compliance
                # In practice, you'd use specific methods to get responses
                yield response  # type: ignore
    
    async def _login(self, username: str, password: str) -> bool:
        """Perform LOGIN authentication using AnyIO I/O."""
        command = IMAPCommandBuilder.login(username, password)
        response = await self._send_command(command)
        return response.status == IMAPStatus.OK
    
    async def _sasl_authenticate(self, method: str, credentials: Dict[str, Any]) -> bool:
        """Perform SASL authentication per RFC 4422."""
        # Implementation of SASL authentication mechanisms
        # For now, return False (not implemented)
        return False
    
    async def _get_capabilities(self) -> None:
        """Get server capabilities per RFC 9051 Section 6.1.1."""
        command = IMAPCommandBuilder.capability()
        response = await self._send_command(command)
        
        if response.status == IMAPStatus.OK:
            # Look for CAPABILITY response in untagged responses
            for resp in self._pending_responses:
                if resp.message.startswith("CAPABILITY"):
                    capabilities = IMAPResponseParser.parse_capability_response(resp.raw_line)
                    self._capabilities = set(capabilities)
                    break
            
            # Clear processed responses
            self._pending_responses = []
    
    async def select_mailbox(self, mailbox: str = "INBOX") -> Dict[str, Any]:
        """Select mailbox per RFC 9051 Section 6.3.1."""
        if self._imap_state != IMAPState.AUTHENTICATED:
            raise RuntimeError("Must be authenticated to select mailbox")
        
        command = IMAPCommandBuilder.select(mailbox)
        response = await self._send_command(command)
        
        if response.status == IMAPStatus.OK:
            self._selected_mailbox = mailbox
            self._imap_state = IMAPState.SELECTED
            
            # Parse SELECT response data
            mailbox_info = self._parse_select_response()
            self._selected_mailbox_info = mailbox_info
            
            return mailbox_info
        else:
            raise ValueError(f"Failed to select mailbox {mailbox}: {response.message}")
    
    async def list_mailboxes(self, reference: str = "", pattern: str = "*") -> List[Dict[str, Any]]:
        """List mailboxes per RFC 9051 Section 6.3.9."""
        if self._imap_state not in {IMAPState.AUTHENTICATED, IMAPState.SELECTED}:
            raise RuntimeError("Must be authenticated to list mailboxes")
        
        command = IMAPCommandBuilder.list(reference, pattern)
        response = await self._send_command(command)
        
        if response.status == IMAPStatus.OK:
            mailboxes = []
            for resp in self._pending_responses:
                if resp.message.startswith("LIST"):
                    mailbox_data = IMAPResponseParser.parse_list_response(resp.raw_line)
                    if mailbox_data:
                        mailboxes.append(mailbox_data)
            
            self._pending_responses = []
            return mailboxes
        else:
            raise ValueError(f"Failed to list mailboxes: {response.message}")
    
    async def search_messages(self, criteria: str, use_uid: bool = False) -> List[int]:
        """Search messages per RFC 9051 Section 6.4.4."""
        if self._imap_state != IMAPState.SELECTED:
            raise RuntimeError("Must have mailbox selected to search messages")
        
        # For UID SEARCH, prepend UID to command
        if use_uid:
            from .commands import IMAPCommandType
            command = IMAPCommand(IMAPCommandType.SEARCH, ["UID", criteria])
        else:
            command = IMAPCommandBuilder.search(criteria)
        
        response = await self._send_command(command)
        
        if response.status == IMAPStatus.OK:
            for resp in self._pending_responses:
                if resp.message.startswith("SEARCH"):
                    message_nums = IMAPResponseParser.parse_search_response(resp.raw_line)
                    self._pending_responses = []
                    return message_nums
            
            self._pending_responses = []
            return []
        else:
            raise ValueError(f"Failed to search messages: {response.message}")
    
    async def fetch_messages(self, sequence_set: str, items: str, use_uid: bool = False) -> List[Dict[str, Any]]:
        """Fetch messages per RFC 9051 Section 6.4.5."""
        if self._imap_state != IMAPState.SELECTED:
            raise RuntimeError("Must have mailbox selected to fetch messages")
        
        # For UID FETCH, prepend UID to command
        if use_uid:
            from .commands import IMAPCommand, IMAPCommandType
            command = IMAPCommand(IMAPCommandType.FETCH, ["UID", sequence_set, items])
        else:
            command = IMAPCommandBuilder.fetch(sequence_set, items)
        
        response = await self._send_command(command)
        
        if response.status == IMAPStatus.OK:
            messages = []
            for resp in self._pending_responses:
                if " FETCH " in resp.message:
                    fetch_data = IMAPResponseParser.parse_fetch_response(resp.raw_line)
                    if fetch_data:
                        messages.append(fetch_data)
            
            self._pending_responses = []
            return messages
        else:
            raise ValueError(f"Failed to fetch messages: {response.message}")
    
    async def _send_command(self, command: IMAPCommand) -> IMAPResponse:
        """Send tagged IMAP command per RFC 9051 using AnyIO."""
        if not self._stream:
            raise RuntimeError("Not connected")
        
        tag = f"A{self._tag_counter:04d}"
        self._tag_counter += 1
        
        command_line = f"{tag} {command.to_string()}\\r\\n"
        
        # CRITICAL: Use AnyIO stream send only
        await AnyIOStreamHelpers.send_all(self._stream, command_line)
        
        # Read responses until we get the tagged response
        while True:
            response = await self._read_response()
            
            if response.response_type == IMAPResponseType.TAGGED and response.tag == tag:
                return response
            elif response.response_type == IMAPResponseType.UNTAGGED:
                # Store untagged responses for processing
                self._pending_responses.append(response)
            elif response.response_type == IMAPResponseType.CONTINUATION:
                # Handle continuation responses (for literals, authentication, etc.)
                # For now, just continue reading
                continue
    
    async def _send_command_no_wait(self, command: IMAPCommand) -> str:
        """Send IMAP command without waiting for completion response."""
        if not self._stream:
            raise RuntimeError("Not connected")
        
        tag = f"A{self._tag_counter:04d}"
        self._tag_counter += 1
        
        command_line = f"{tag} {command.to_string()}\\r\\n"
        
        # CRITICAL: Use AnyIO stream send only
        await AnyIOStreamHelpers.send_all(self._stream, command_line)
        
        return tag
    
    async def _read_response(self) -> IMAPResponse:
        """Read IMAP response per RFC 9051 Section 7 using AnyIO."""
        if not self._stream:
            raise RuntimeError("Not connected")
        
        line = await AnyIOStreamHelpers.read_line(self._stream)
        return IMAPResponseParser.parse(line)
    
    def _parse_select_response(self) -> Dict[str, Any]:
        """Parse SELECT response data per RFC 9051."""
        mailbox_info = {}
        
        for resp in self._pending_responses:
            # Parse various SELECT response data
            if resp.message.endswith(" EXISTS"):
                parts = resp.message.split()
                if len(parts) >= 2:
                    mailbox_info['exists'] = int(parts[0])
            elif resp.message.endswith(" RECENT"):
                parts = resp.message.split()
                if len(parts) >= 2:
                    mailbox_info['recent'] = int(parts[0])
            elif "FLAGS" in resp.message:
                # Parse flags - simple implementation
                mailbox_info['flags'] = resp.message
            elif resp.status == IMAPStatus.OK:
                # Parse response codes from OK responses
                if '[' in resp.message and ']' in resp.message:
                    start = resp.message.find('[') + 1
                    end = resp.message.find(']')
                    if start > 0 and end > start:
                        response_code = resp.message[start:end]
                        if response_code.startswith('UIDVALIDITY '):
                            mailbox_info['uidvalidity'] = int(response_code.split()[1])
                        elif response_code.startswith('UIDNEXT '):
                            mailbox_info['uidnext'] = int(response_code.split()[1])
        
        return mailbox_info
    
    async def _cleanup_connection(self) -> None:
        """Clean up connection resources."""
        if self._stream:
            try:
                await self._stream.aclose()
            except Exception:
                # Ignore cleanup errors
                pass
            finally:
                self._stream = None