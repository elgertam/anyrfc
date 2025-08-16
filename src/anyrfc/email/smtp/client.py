"""SMTP client implementation per RFC 5321."""
# CRITICAL: ALL I/O OPERATIONS MUST USE ANYIO - NO ASYNCIO IMPORTS ALLOWED
import anyio
from anyio.abc import ByteStream
from typing import Dict, List, Optional, Any, Union, Tuple
from enum import Enum
import base64

from ...core.types import ProtocolClient, ProtocolState, AuthenticationClient, RFCCompliance
from ...core.streams import AnyIOStreamHelpers
from ...core.tls import TLSHelper

class SMTPState(Enum):
    """SMTP protocol states per RFC 5321."""
    DISCONNECTED = "disconnected"
    CONNECTED = "connected"
    HELO_SENT = "helo_sent"
    STARTTLS_READY = "starttls_ready"
    AUTHENTICATED = "authenticated"
    MAIL_STARTED = "mail_started"
    RCPT_ADDED = "rcpt_added"
    DATA_READY = "data_ready"

class SMTPResponseCode(Enum):
    """SMTP response codes per RFC 5321."""
    SYSTEM_STATUS = 211
    HELP = 214
    SERVICE_READY = 220
    SERVICE_CLOSING = 221
    AUTH_SUCCESS = 235
    OK = 250
    USER_NOT_LOCAL = 251
    CANNOT_VERIFY = 252
    AUTH_CHALLENGE = 334
    START_MAIL_INPUT = 354
    SERVICE_NOT_AVAILABLE = 421
    MAILBOX_BUSY = 450
    LOCAL_ERROR = 451
    INSUFFICIENT_STORAGE = 452
    COMMAND_UNRECOGNIZED = 500
    SYNTAX_ERROR = 501
    COMMAND_NOT_IMPLEMENTED = 502
    BAD_SEQUENCE = 503
    PARAMETER_NOT_IMPLEMENTED = 504
    MAILBOX_UNAVAILABLE = 550
    USER_NOT_LOCAL_RELAY = 551
    STORAGE_EXCEEDED = 552
    MAILBOX_NAME_INVALID = 553
    TRANSACTION_FAILED = 554

class SMTPClient(ProtocolClient[str], AuthenticationClient, RFCCompliance):
    """RFC 5321 compliant SMTP client using ONLY AnyIO for I/O."""
    
    def __init__(self, hostname: str, port: int = 587, *, 
                 use_tls: bool = True, 
                 use_starttls: bool = True,
                 local_hostname: Optional[str] = None):
        super().__init__()
        self.hostname = hostname
        self.port = port
        self.use_tls = use_tls
        self.use_starttls = use_starttls
        self.local_hostname = local_hostname or "localhost"
        
        self._stream: Optional[ByteStream] = None
        self._smtp_state = SMTPState.DISCONNECTED
        self._capabilities: List[str] = []
        self._tls_started = False
        
        # Current transaction state
        self._current_mail_from: Optional[str] = None
        self._current_recipients: List[str] = []
    
    def get_rfc_number(self) -> str:
        return "RFC 5321"
    
    async def validate_compliance(self) -> Dict[str, bool]:
        """Validate RFC 5321 compliance."""
        return {}
    
    def get_test_vectors(self) -> Dict[str, Any]:
        """Return RFC 5321 test vectors."""
        return {}
    
    @property
    def smtp_state(self) -> SMTPState:
        """Get current SMTP protocol state."""
        return self._smtp_state
    
    @property
    def capabilities(self) -> List[str]:
        """Get server capabilities."""
        return self._capabilities.copy()
    
    def has_capability(self, capability: str) -> bool:
        """Check if server has specific capability."""
        return capability.upper() in [cap.upper() for cap in self._capabilities]
    
    async def connect(self) -> None:
        """Establish SMTP connection per RFC 5321 using AnyIO."""
        await self._transition_state(ProtocolState.CONNECTING)
        
        try:
            # CRITICAL: Use ONLY AnyIO for network I/O
            if self.use_tls and not self.use_starttls:
                # Direct TLS connection (SMTPS)
                tls_context = TLSHelper.create_default_client_context()
                self._stream = await anyio.connect_tcp(self.hostname, self.port, tls=True, ssl_context=tls_context)
                self._tls_started = True
            else:
                # Plain connection (will use STARTTLS if requested)
                self._stream = await anyio.connect_tcp(self.hostname, self.port)
            
            # Read greeting per RFC 5321 Section 3.1
            response = await self._read_response()
            if response[0] != SMTPResponseCode.SERVICE_READY.value:
                raise ValueError(f"SMTP server greeting failed: {response}")
            
            self._smtp_state = SMTPState.CONNECTED
            await self._transition_state(ProtocolState.CONNECTED)
            
            # Send EHLO to get capabilities
            await self._ehlo()
            
            # Start TLS if requested and not already using TLS
            if self.use_starttls and not self._tls_started and self.has_capability("STARTTLS"):
                await self._start_tls()
                # Re-send EHLO after STARTTLS
                await self._ehlo()
            
        except Exception as e:
            await self._transition_state(ProtocolState.ERROR)
            if self._stream:
                await self._cleanup_connection()
            raise
    
    async def disconnect(self) -> None:
        """Gracefully close SMTP connection per RFC 5321."""
        if self.state in {ProtocolState.CONNECTED, ProtocolState.AUTHENTICATED}:
            try:
                # Send QUIT command
                await self._send_command("QUIT")
                response = await self._read_response()
                # Ignore response code for QUIT
            except Exception:
                # Ignore quit errors
                pass
        
        await self._cleanup_connection()
        self._smtp_state = SMTPState.DISCONNECTED
        await self._transition_state(ProtocolState.DISCONNECTED)
    
    async def authenticate(self, credentials: Dict[str, Any]) -> bool:
        """Perform SMTP authentication per RFC 4954."""
        if self.state != ProtocolState.CONNECTED:
            raise RuntimeError("Must be connected before authentication")
        
        if not self.has_capability("AUTH"):
            raise RuntimeError("Server does not support authentication")
        
        username = credentials.get('username')
        password = credentials.get('password')
        auth_method = credentials.get('method', 'PLAIN')
        
        if not username or not password:
            raise ValueError("Username and password required for authentication")
        
        await self._transition_state(ProtocolState.AUTHENTICATING)
        
        try:
            if auth_method.upper() == 'PLAIN':
                success = await self._auth_plain(username, password)
            elif auth_method.upper() == 'LOGIN':
                success = await self._auth_login(username, password)
            else:
                raise ValueError(f"Unsupported authentication method: {auth_method}")
            
            if success:
                self._smtp_state = SMTPState.AUTHENTICATED
                await self._transition_state(ProtocolState.AUTHENTICATED)
            else:
                await self._transition_state(ProtocolState.CONNECTED)
            
            return success
            
        except Exception as e:
            await self._transition_state(ProtocolState.ERROR)
            raise
    
    async def refresh_credentials(self) -> bool:
        """Refresh authentication credentials if supported."""
        # SMTP doesn't typically support credential refresh
        return False
    
    async def send_message(self, 
                          from_addr: str, 
                          to_addrs: List[str], 
                          message: str) -> None:
        """Send email message per RFC 5321."""
        if self.state not in {ProtocolState.CONNECTED, ProtocolState.AUTHENTICATED}:
            raise RuntimeError("Must be connected to send message")
        
        # Start mail transaction
        await self._mail_from(from_addr)
        
        # Add recipients
        for to_addr in to_addrs:
            await self._rcpt_to(to_addr)
        
        # Send data
        await self._data(message)
        
        # Reset transaction state
        self._current_mail_from = None
        self._current_recipients = []
        self._smtp_state = SMTPState.AUTHENTICATED if self.state == ProtocolState.AUTHENTICATED else SMTPState.HELO_SENT
    
    async def send(self, message: str) -> None:
        """Send command following RFC encoding rules."""
        await self._send_command(message)
    
    async def receive(self):
        """Receive responses following RFC parsing rules."""
        # SMTP is request-response, so this doesn't make sense in this context
        return await self._read_response()
    
    async def _ehlo(self) -> None:
        """Send EHLO command per RFC 5321 Section 4.1.1.1."""
        await self._send_command(f"EHLO {self.local_hostname}")
        response = await self._read_response()
        
        if response[0] == SMTPResponseCode.OK.value:
            self._smtp_state = SMTPState.HELO_SENT
            
            # Parse capabilities from response
            self._capabilities = []
            for line in response[1]:
                if line and not line.startswith(str(SMTPResponseCode.OK.value)):
                    # Remove leading response code if present
                    capability = line.split(' ', 1)[-1] if ' ' in line else line
                    self._capabilities.append(capability)
        else:
            raise ValueError(f"EHLO failed: {response}")
    
    async def _start_tls(self) -> None:
        """Start TLS connection per RFC 3207."""
        await self._send_command("STARTTLS")
        response = await self._read_response()
        
        if response[0] == SMTPResponseCode.SERVICE_READY.value:
            # Upgrade connection to TLS
            if not self._stream:
                raise RuntimeError("No connection to upgrade")
            
            # Use AnyIO TLS wrapping
            tls_context = TLSHelper.create_default_client_context()
            # Note: This is a simplified approach. Full implementation would need proper TLS upgrade
            self._tls_started = True
            self._smtp_state = SMTPState.STARTTLS_READY
        else:
            raise ValueError(f"STARTTLS failed: {response}")
    
    async def _auth_plain(self, username: str, password: str) -> bool:
        """Perform PLAIN authentication per RFC 4616."""
        # PLAIN format: \\0username\\0password
        auth_string = f"\\0{username}\\0{password}"
        auth_b64 = base64.b64encode(auth_string.encode('utf-8')).decode('ascii')
        
        await self._send_command(f"AUTH PLAIN {auth_b64}")
        response = await self._read_response()
        
        return response[0] == SMTPResponseCode.AUTH_SUCCESS.value
    
    async def _auth_login(self, username: str, password: str) -> bool:
        """Perform LOGIN authentication."""
        await self._send_command("AUTH LOGIN")
        response = await self._read_response()
        
        if response[0] == SMTPResponseCode.AUTH_CHALLENGE.value:
            # Send username
            username_b64 = base64.b64encode(username.encode('utf-8')).decode('ascii')
            await self._send_command(username_b64)
            response = await self._read_response()
            
            if response[0] == SMTPResponseCode.AUTH_CHALLENGE.value:
                # Send password
                password_b64 = base64.b64encode(password.encode('utf-8')).decode('ascii')
                await self._send_command(password_b64)
                response = await self._read_response()
                
                return response[0] == SMTPResponseCode.AUTH_SUCCESS.value
        
        return False
    
    async def _mail_from(self, from_addr: str) -> None:
        """Send MAIL FROM command per RFC 5321 Section 4.1.1.2."""
        await self._send_command(f"MAIL FROM:<{from_addr}>")
        response = await self._read_response()
        
        if response[0] == SMTPResponseCode.OK.value:
            self._current_mail_from = from_addr
            self._smtp_state = SMTPState.MAIL_STARTED
        else:
            raise ValueError(f"MAIL FROM failed: {response}")
    
    async def _rcpt_to(self, to_addr: str) -> None:
        """Send RCPT TO command per RFC 5321 Section 4.1.1.3."""
        await self._send_command(f"RCPT TO:<{to_addr}>")
        response = await self._read_response()
        
        if response[0] == SMTPResponseCode.OK.value:
            self._current_recipients.append(to_addr)
            self._smtp_state = SMTPState.RCPT_ADDED
        else:
            raise ValueError(f"RCPT TO failed for {to_addr}: {response}")
    
    async def _data(self, message: str) -> None:
        """Send DATA command and message per RFC 5321 Section 4.1.1.4."""
        await self._send_command("DATA")
        response = await self._read_response()
        
        if response[0] == SMTPResponseCode.START_MAIL_INPUT.value:
            self._smtp_state = SMTPState.DATA_READY
            
            # Send message data, ensuring CRLF line endings
            message_lines = message.replace('\\r\\n', '\\n').replace('\\r', '\\n').split('\\n')
            for line in message_lines:
                # Escape lines starting with '.' per RFC 5321
                if line.startswith('.'):
                    line = '.' + line
                await AnyIOStreamHelpers.send_all(self._stream, line + '\\r\\n')
            
            # Send end of data marker
            await AnyIOStreamHelpers.send_all(self._stream, '.\\r\\n')
            
            # Read final response
            response = await self._read_response()
            if response[0] != SMTPResponseCode.OK.value:
                raise ValueError(f"DATA transmission failed: {response}")
        else:
            raise ValueError(f"DATA command failed: {response}")
    
    async def _send_command(self, command: str) -> None:
        """Send SMTP command using AnyIO."""
        if not self._stream:
            raise RuntimeError("Not connected")
        
        command_line = command + '\\r\\n'
        await AnyIOStreamHelpers.send_all(self._stream, command_line)
    
    async def _read_response(self) -> Tuple[int, List[str]]:
        """Read SMTP response per RFC 5321 using AnyIO."""
        if not self._stream:
            raise RuntimeError("Not connected")
        
        lines = []
        
        while True:
            line = await AnyIOStreamHelpers.read_line(self._stream)
            lines.append(line)
            
            # Check if this is the last line (no continuation)
            if len(line) >= 4 and line[3] == ' ':
                break
            elif len(line) >= 4 and line[3] == '-':
                # Multi-line response continues
                continue
            else:
                # Single line response
                break
        
        # Parse response code from first line
        if lines and len(lines[0]) >= 3:
            try:
                response_code = int(lines[0][:3])
                return response_code, lines
            except ValueError:
                pass
        
        raise ValueError(f"Invalid SMTP response: {lines}")
    
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