# AnyIO RFC Client Implementation Plan

## Project Overview

This plan outlines the implementation of **complete, RFC-compliant client libraries** using Python AnyIO's structured concurrency. The focus is on application layer protocols (Layer 7) with **WebSockets, IMAP, and OAuth 2.0 as the top three priorities**, followed by secure file transfer protocols (SSH, SFTP, FTPS).

**Key Principles:**

- **RFC Compliance First**: Every implementation must pass comprehensive RFC compliance tests
- **Complete Implementation**: No partial implementations - each protocol must fully implement its RFC specification
- **Security by Default**: Modern TLS, secure authentication, and best practices throughout
- **Production Ready**: Real-world testing against major server implementations
- **Type Safety**: Full mypy compliance with strict typing

## Constraints & Assumptions

- **Given implementations**: TCP, UDP, TLS, HTTP(S), JSON (kernel + standard library)
- **AnyIO foundation**: Structured concurrency with nurseries and cancellation scopes
- **Application layer focus**: No custom transport or network layer implementations
- **Python ecosystem**: Type hints, `uv` package management, pytest-asyncio testing
- **RFC Compliance Mandate**: All implementations must achieve 100% compliance with their respective RFCs
- **Complete Implementation Requirement**: No partial or subset implementations - each protocol must fully implement the RFC specification
- **Security First**: All implementations must use modern security practices and pass security audits
- **Production Quality**: Must pass interoperability tests with major real-world server implementations

### ⚠️ CRITICAL I/O CONSTRAINT ⚠️

**ANYIO ONLY FOR ALL I/O OPERATIONS:**

- **ABSOLUTELY NO `asyncio` imports or references** anywhere in the codebase
- **ALL I/O operations MUST use AnyIO APIs exclusively**: `anyio.connect_tcp()`, `anyio.create_udp_socket()`, `anyio.create_task_group()`, etc.
- **Standard library is acceptable** for compute-bound operations (math, string processing, cryptographic operations, data parsing)
- **Print statements for debugging are allowed** but should be removed before production
- **NO exceptions** - if you need I/O, it must be through AnyIO

### Third-Party Dependencies

**Development Dependencies (Allowed):**

- Testing frameworks: `pytest`, `pytest-asyncio`, `mypy`, `ruff`
- Development tools: `coverage`, `black`, `isort`
- Mock servers and testing utilities
- Documentation generation: `sphinx`, `mkdocs`

**Production Dependencies (Require Approval):**

- **Every third-party dependency** in the final build must be explicitly approved
- **Justification required**: Each dependency must provide critical functionality not available in stdlib + AnyIO
- **Security review**: All dependencies subject to security and supply chain analysis
- **Minimal dependency principle**: Prefer stdlib solutions when possible

**Acceptable Production Dependencies (Pre-Approved):**

- `anyio` (required)
- Cryptographic libraries for protocols requiring specific algorithms not in `hashlib`/`secrets`
- Protocol-specific parsers only if no reasonable stdlib alternative exists

## Implementation Priorities

### Phase 1: WebSocket Foundation (Weeks 1-4)

**Priority 1A: WebSocket Client (RFC 6455) - COMPLETE RFC IMPLEMENTATION**

- **Full RFC 6455 compliance**: All frame types, opcodes, and protocol states
- **WebSocket extensions**: Per-message deflate (RFC 7692), WebSocket over HTTP/2
- **Complete handshake implementation**: Sec-WebSocket-Key generation, response validation
- **Connection management**: Auto-reconnection, graceful close sequences, timeout handling
- **Comprehensive testing**: RFC compliance test suite, edge case validation, malformed frame handling

**Priority 1B: Project Infrastructure & RFC Compliance Framework**

- Package structure with `uv` and pyproject.toml
- **RFC compliance testing framework**: Automated validation against RFC test vectors
- **Protocol state machine validation**: Formal verification of protocol state transitions
- **Interoperability testing infrastructure**: Real-server testing with major implementations
- Documentation generation with RFC cross-references

### Phase 2: Email Infrastructure (Weeks 5-8)

**Priority 2A: IMAP Client (RFC 9051) - COMPLETE RFC IMPLEMENTATION**

- **Full IMAP4rev2 compliance**: All mandatory commands, response parsing, protocol states
- **Backward compatibility**: IMAP4rev1 support for legacy servers
- **Advanced features**: IDLE support, large message streaming, mailbox synchronization
- **Extension support**: IMAP extensions (SORT, THREAD, CONDSTORE, QRESYNC)
- **Comprehensive testing**: RFC 9051 compliance tests, server compatibility matrix

**Priority 2B: SMTP Client (RFC 5321) - COMPLETE RFC IMPLEMENTATION**

- **Full ESMTP compliance**: All SMTP commands, response codes, state machine
- **Security features**: STARTTLS negotiation, SASL authentication mechanisms
- **Advanced features**: Pipelining, 8BITMIME, SIZE extension, DSN support
- **MIME integration**: Complete multipart message composition per RFC 2045-2049
- **Comprehensive testing**: SMTP server compatibility, authentication method validation

### Phase 3: Modern Authentication (Weeks 9-12)

**Priority 3A: OAuth 2.0 Client Framework (RFC 6749/6750) - COMPLETE RFC IMPLEMENTATION**

- **All OAuth 2.0 flows**: Authorization code, client credentials, device authorization (RFC 8628)
- **Token management**: Automatic refresh, secure storage, scope validation
- **PKCE support**: RFC 7636 Proof Key for Code Exchange for public clients
- **JWT integration**: RFC 7519 JSON Web Token parsing and validation
- **Provider integration**: Google, Microsoft, GitHub, Auth0 specific implementations
- **Comprehensive testing**: OAuth flow validation, security vulnerability testing

**Priority 3B: SASL Authentication Framework (RFC 4422)**

- **Complete SASL mechanism support**: PLAIN, CRAM-MD5, DIGEST-MD5, GSSAPI, OAUTH-BEARER
- **Pluggable architecture**: Easy addition of custom SASL mechanisms
- **Integration layer**: SMTP, IMAP, XMPP SASL authentication
- **Security compliance**: Proper credential handling, channel binding support

### Phase 4: Secure File Transfer (Weeks 13-16)

**Priority 4A: SSH Client Suite (RFC 4251-4254) - COMPLETE RFC IMPLEMENTATION**

- **SSH Transport Layer (RFC 4253)**: Key exchange, encryption, integrity, compression
- **SSH Authentication (RFC 4252)**: Password, public key, host-based, keyboard-interactive
- **SSH Connection Protocol (RFC 4254)**: Channel management, port forwarding, exec/shell
- **Advanced features**: SSH agent integration, connection multiplexing, keep-alive
- **Security focus**: Modern crypto algorithms, host key verification, security best practices

**Priority 4B: SFTP Client (Draft SFTP v6) - COMPLETE SPECIFICATION IMPLEMENTATION**

- **Full SFTP protocol**: File operations, directory management, symbolic links, permissions
- **Performance optimizations**: Parallel transfers, request pipelining, resume capability
- **Error handling**: Comprehensive error code handling, retry mechanisms
- **Integration**: Seamless integration with SSH client for transport security

### Phase 5: Legacy File Transfer (Weeks 17-20)

**Priority 5A: FTPS Client (RFC 4217) - COMPLETE RFC IMPLEMENTATION**

- **FTP over TLS**: Both explicit (FTPES) and implicit (FTPS) modes
- **Complete FTP protocol**: Active/passive modes, ASCII/binary transfers, resume
- **TLS security**: Certificate validation, cipher suite negotiation, data channel protection
- **Compatibility**: Legacy server support, various FTP server implementations

**Priority 5B: FTP Client (RFC 959) - COMPLETE RFC IMPLEMENTATION**

- **Classic FTP protocol**: All FTP commands, response parsing, state management
- **Data channel management**: Active and passive mode support
- **Transfer modes**: ASCII, binary, stream, block, compressed modes
- **Directory operations**: Recursive operations, listing parsing, path resolution

### Phase 6: Real-Time & Advanced Protocols (Weeks 21-24)

**Priority 6A: DNS Infrastructure**

- **DNS Client (RFC 1035)**: Complete DNS message parsing, all record types
- **DNS-over-HTTPS (RFC 8484)**: Encrypted DNS queries with caching
- **mDNS/DNS-SD (RFC 6762/6763)**: Zero-configuration service discovery

**Priority 6B: CoAP & IoT Protocols**

- **CoAP Client (RFC 7252)**: Constrained Application Protocol for IoT devices
- **XMPP Client (RFC 6120)**: Real-time messaging with extension support

## Technical Architecture

### Core Design Patterns

```python
# AnyIO structured concurrency pattern
async def protocol_client_lifecycle():
    async with anyio.create_task_group() as tg:
        # Connection management
        tg.start_soon(connection_manager)
        # Message processing
        tg.start_soon(message_processor)
        # Heartbeat/keepalive
        tg.start_soon(heartbeat_manager)
```

### Package Structure

```
anyrfc/
├── pyproject.toml              # uv package configuration
├── src/anyrfc/
│   ├── __init__.py
│   ├── core/                   # Shared utilities & RFC compliance framework
│   │   ├── __init__.py
│   │   ├── types.py           # Common type definitions
│   │   ├── streams.py         # AnyIO stream helpers
│   │   ├── uri.py             # RFC 3986 URI parsing
│   │   ├── tls.py             # TLS configuration helpers
│   │   ├── rfc_compliance.py  # RFC test vector validation
│   │   └── state_machine.py   # Protocol state machine base
│   ├── websocket/             # RFC 6455 WebSocket - COMPLETE IMPLEMENTATION
│   │   ├── __init__.py
│   │   ├── client.py          # Main client implementation
│   │   ├── frames.py          # Frame parsing/construction
│   │   ├── handshake.py       # WebSocket handshake protocol
│   │   ├── extensions.py      # WebSocket extensions (RFC 7692)
│   │   ├── state_machine.py   # WebSocket protocol states
│   │   ├── compliance.py      # RFC 6455 compliance testing
│   │   └── exceptions.py      # Protocol-specific exceptions
│   ├── email/                 # RFC 5321 SMTP / RFC 9051 IMAP - COMPLETE IMPLEMENTATIONS
│   │   ├── __init__.py
│   │   ├── smtp/              # RFC 5321 SMTP client
│   │   │   ├── __init__.py
│   │   │   ├── client.py      # SMTP client implementation
│   │   │   ├── commands.py    # SMTP command encoding
│   │   │   ├── responses.py   # SMTP response parsing
│   │   │   ├── extensions.py  # ESMTP extensions
│   │   │   └── compliance.py  # RFC 5321 compliance tests
│   │   ├── imap/              # RFC 9051 IMAP client
│   │   │   ├── __init__.py
│   │   │   ├── client.py      # IMAP client implementation
│   │   │   ├── commands.py    # IMAP command construction
│   │   │   ├── responses.py   # IMAP response parsing
│   │   │   ├── mailbox.py     # Mailbox management
│   │   │   ├── messages.py    # Message handling
│   │   │   ├── extensions.py  # IMAP extensions (IDLE, SORT, etc.)
│   │   │   └── compliance.py  # RFC 9051 compliance tests
│   │   ├── mime.py            # RFC 2045-2049 MIME handling
│   │   └── sasl.py            # RFC 4422 SASL authentication
│   ├── auth/                  # RFC 6749/6750 OAuth 2.0 - COMPLETE IMPLEMENTATION
│   │   ├── __init__.py
│   │   ├── oauth2/            # OAuth 2.0 framework
│   │   │   ├── __init__.py
│   │   │   ├── client.py      # OAuth 2.0 client implementation
│   │   │   ├── flows.py       # Authorization flows
│   │   │   ├── tokens.py      # Token management
│   │   │   ├── pkce.py        # RFC 7636 PKCE implementation
│   │   │   ├── device.py      # RFC 8628 device authorization
│   │   │   ├── jwt.py         # RFC 7519 JWT handling
│   │   │   └── compliance.py  # OAuth 2.0 compliance tests
│   │   ├── sasl/              # RFC 4422 SASL framework
│   │   │   ├── __init__.py
│   │   │   ├── mechanisms.py  # SASL mechanisms
│   │   │   ├── client.py      # SASL client implementation
│   │   │   └── compliance.py  # SASL compliance tests
│   │   └── providers.py       # OAuth provider configurations
│   ├── ssh/                   # RFC 4251-4254 SSH - COMPLETE IMPLEMENTATION
│   │   ├── __init__.py
│   │   ├── transport.py       # RFC 4253 SSH transport layer
│   │   ├── auth.py            # RFC 4252 SSH authentication
│   │   ├── connection.py      # RFC 4254 SSH connection protocol
│   │   ├── client.py          # High-level SSH client
│   │   ├── crypto.py          # SSH cryptographic operations
│   │   ├── kex.py             # Key exchange algorithms
│   │   ├── channels.py        # SSH channel management
│   │   ├── agent.py           # SSH agent integration
│   │   └── compliance.py      # SSH RFC compliance tests
│   ├── file_transfer/         # Secure & Legacy File Transfer
│   │   ├── __init__.py
│   │   ├── sftp/              # SSH File Transfer Protocol
│   │   │   ├── __init__.py
│   │   │   ├── client.py      # SFTP client implementation
│   │   │   ├── protocol.py    # SFTP protocol messages
│   │   │   ├── attributes.py  # File attribute handling
│   │   │   └── compliance.py  # SFTP compliance tests
│   │   ├── ftps/              # RFC 4217 FTP over TLS
│   │   │   ├── __init__.py
│   │   │   ├── client.py      # FTPS client implementation
│   │   │   ├── tls_control.py # TLS control channel
│   │   │   ├── tls_data.py    # TLS data channel
│   │   │   └── compliance.py  # RFC 4217 compliance tests
│   │   └── ftp/               # RFC 959 Classic FTP
│   │       ├── __init__.py
│   │       ├── client.py      # FTP client implementation
│   │       ├── commands.py    # FTP command encoding
│   │       ├── responses.py   # FTP response parsing
│   │       ├── data_channel.py # Data channel management
│   │       └── compliance.py  # RFC 959 compliance tests
│   ├── dns/                   # DNS Infrastructure
│   │   ├── __init__.py
│   │   ├── client.py          # RFC 1035 DNS client
│   │   ├── doh.py             # RFC 8484 DNS-over-HTTPS
│   │   ├── messages.py        # DNS message format
│   │   ├── records.py         # DNS record types
│   │   └── compliance.py      # DNS compliance tests
│   ├── discovery/             # Zero-configuration Discovery
│   │   ├── __init__.py
│   │   ├── mdns.py            # RFC 6762 Multicast DNS
│   │   ├── dns_sd.py          # RFC 6763 DNS Service Discovery
│   │   └── compliance.py      # mDNS/DNS-SD compliance tests
│   ├── iot/                   # IoT & Constrained Protocols
│   │   ├── __init__.py
│   │   ├── coap.py            # RFC 7252 CoAP client
│   │   ├── messages.py        # CoAP message format
│   │   ├── observe.py         # CoAP observe pattern
│   │   └── compliance.py      # CoAP compliance tests
│   └── realtime/              # Real-time Communication
│       ├── __init__.py
│       ├── xmpp.py            # RFC 6120 XMPP client
│       ├── stanzas.py         # XMPP stanza handling
│       ├── extensions.py      # XMPP extension (XEPs)
│       └── compliance.py      # XMPP compliance tests
├── tests/
│   ├── conftest.py            # pytest configuration
│   ├── rfc_compliance/        # RFC compliance test suites
│   │   ├── websocket/         # RFC 6455 test vectors
│   │   ├── imap/              # RFC 9051 test vectors
│   │   ├── smtp/              # RFC 5321 test vectors
│   │   ├── oauth2/            # OAuth 2.0 test vectors
│   │   ├── ssh/               # SSH RFC test vectors
│   │   └── common/            # Shared test utilities
│   ├── unit/                  # Unit tests per module
│   ├── integration/           # Integration tests
│   ├── interop/               # Interoperability tests
│   └── security/              # Security-focused tests
├── docs/
│   ├── rfc_compliance/        # RFC compliance documentation
│   ├── protocols/             # Protocol-specific guides
│   ├── examples/              # Usage examples
│   └── api/                   # API documentation
└── examples/                  # Standalone examples
    ├── websocket_realtime.py
    ├── email_full_client.py
    ├── oauth2_integration.py
    ├── ssh_file_manager.py
    ├── sftp_sync.py
    └── secure_file_transfer.py
```

### Core Interfaces with RFC Compliance

```python
# CRITICAL: ALL I/O OPERATIONS MUST USE ANYIO - NO ASYNCIO IMPORTS ALLOWED
import anyio
from anyio.abc import ByteStream, SocketStream  # AnyIO interfaces only
from abc import ABC, abstractmethod
from typing import AsyncIterator, Generic, TypeVar, Dict, Any, Optional
from enum import Enum

# Standard library imports for compute operations are acceptable
import hashlib
import secrets
import base64
from urllib.parse import urlparse

T = TypeVar('T')

class RFCCompliance(ABC):
    """Base class for RFC compliance validation."""

    @abstractmethod
    def get_rfc_number(self) -> str:
        """Return the primary RFC number implemented."""

    @abstractmethod
    async def validate_compliance(self) -> Dict[str, bool]:
        """Run RFC compliance tests and return results."""

    @abstractmethod
    def get_test_vectors(self) -> Dict[str, Any]:
        """Return RFC test vectors for validation."""

class ProtocolState(Enum):
    """Base protocol state enumeration."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    AUTHENTICATING = "authenticating"
    AUTHENTICATED = "authenticated"
    DISCONNECTING = "disconnecting"
    ERROR = "error"

class ProtocolClient(ABC, Generic[T], RFCCompliance):
    """Base interface for all RFC-compliant protocol clients."""

    def __init__(self):
        self._state = ProtocolState.DISCONNECTED
        self._state_lock = anyio.Lock()  # AnyIO lock, not asyncio.Lock

    @property
    def state(self) -> ProtocolState:
        """Current protocol state."""
        return self._state

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection per RFC specification."""

    @abstractmethod
    async def disconnect(self) -> None:
        """Gracefully close connection per RFC specification."""

    @abstractmethod
    async def send(self, message: T) -> None:
        """Send message following RFC encoding rules."""

    @abstractmethod
    async def receive(self) -> AsyncIterator[T]:
        """Receive messages following RFC parsing rules."""

    async def _transition_state(self, new_state: ProtocolState) -> None:
        """Thread-safe state transition using AnyIO primitives."""
        async with self._state_lock:
            old_state = self._state
            self._state = new_state
            await self._on_state_change(old_state, new_state)

    async def _on_state_change(self, old_state: ProtocolState, new_state: ProtocolState) -> None:
        """Override to handle state transitions."""
        pass

class MessageFrame(ABC):
    """Base class for RFC-compliant protocol message frames."""

    @abstractmethod
    def to_bytes(self) -> bytes:
        """Serialize frame to bytes per RFC specification."""

    @classmethod
    @abstractmethod
    def from_bytes(cls, data: bytes) -> 'MessageFrame':
        """Deserialize frame from bytes per RFC specification."""

    @abstractmethod
    def validate_rfc_compliance(self) -> bool:
        """Validate frame against RFC requirements."""

class AuthenticationClient(ABC):
    """Base interface for RFC-compliant authentication."""

    @abstractmethod
    async def authenticate(self, credentials: Dict[str, Any]) -> bool:
        """Perform authentication per RFC specification."""

    @abstractmethod
    async def refresh_credentials(self) -> bool:
        """Refresh authentication credentials if supported."""

class SecureClient(ProtocolClient[T]):
    """Base class for protocols requiring secure transport."""

    def __init__(self, require_tls: bool = True):
        super().__init__()
        self.require_tls = require_tls
        self._tls_context: Optional[Any] = None

    @abstractmethod
    async def start_tls(self) -> None:
        """Initiate TLS according to protocol specification."""
```

## Implementation Details

### WebSocket Client (RFC 6455) - Priority 1 - COMPLETE IMPLEMENTATION

```python
# anyrfc/websocket/client.py
# CRITICAL: ONLY ANYIO FOR ALL I/O - NO ASYNCIO IMPORTS ANYWHERE
import anyio
from anyio.abc import ByteStream  # AnyIO interfaces only
from typing import AsyncIterator, Optional, Union, Dict, List
from urllib.parse import urlparse  # stdlib for parsing is acceptable
import base64  # stdlib for compute operations is acceptable
import hashlib  # stdlib for crypto compute is acceptable
import secrets  # stdlib for secure random is acceptable

from ..core.types import ProtocolClient, ProtocolState, RFCCompliance
from .frames import WSFrame, OpCode
from .state_machine import WebSocketStateMachine
from .compliance import RFC6455Compliance

class WebSocketClient(ProtocolClient[Union[str, bytes]], RFC6455Compliance):
    """RFC 6455 compliant WebSocket client implementation using ONLY AnyIO for I/O."""

    def __init__(self, uri: str, *,
                 protocols: Optional[List[str]] = None,
                 extensions: Optional[List[str]] = None,
                 origin: Optional[str] = None):
        super().__init__()
        self.uri = uri
        self.protocols = protocols or []
        self.extensions = extensions or []
        self.origin = origin
        self._stream: Optional[ByteStream] = None
        self._state_machine = WebSocketStateMachine()
        self._sec_websocket_key = self._generate_websocket_key()

    def get_rfc_number(self) -> str:
        return "RFC 6455"

    async def validate_compliance(self) -> Dict[str, bool]:
        """Validate RFC 6455 compliance."""
        return await RFC6455Compliance.run_compliance_tests(self)

    def get_test_vectors(self) -> Dict[str, Any]:
        """Return RFC 6455 test vectors."""
        return RFC6455Compliance.get_test_vectors()

    async def connect(self) -> None:
        """Establish RFC 6455 compliant WebSocket connection using AnyIO."""
        await self._transition_state(ProtocolState.CONNECTING)

        parsed = urlparse(self.uri)
        if not parsed.hostname:
            raise ValueError("Invalid WebSocket URI")

        # CRITICAL: Use ONLY AnyIO for network I/O - NO asyncio.connect() etc.
        if parsed.scheme == 'wss':
            self._stream = await anyio.connect_tcp(
                parsed.hostname, parsed.port or 443, tls=True)
        elif parsed.scheme == 'ws':
            self._stream = await anyio.connect_tcp(
                parsed.hostname, parsed.port or 80)
        else:
            raise ValueError(f"Unsupported scheme: {parsed.scheme}")

        # Perform RFC 6455 compliant WebSocket handshake
        await self._perform_rfc_handshake(parsed)
        await self._transition_state(ProtocolState.CONNECTED)

    async def send_text(self, text: str) -> None:
        """Send text message per RFC 6455."""
        if self.state != ProtocolState.CONNECTED:
            raise RuntimeError("WebSocket not connected")

        frame = WSFrame(
            fin=True,
            opcode=OpCode.TEXT,
            payload=text.encode('utf-8'),
            masked=True  # Client frames must be masked per RFC 6455
        )
        await self._send_frame(frame)

    async def send_binary(self, data: bytes) -> None:
        """Send binary message per RFC 6455."""
        if self.state != ProtocolState.CONNECTED:
            raise RuntimeError("WebSocket not connected")

        frame = WSFrame(
            fin=True,
            opcode=OpCode.BINARY,
            payload=data,
            masked=True
        )
        await self._send_frame(frame)

    async def receive(self) -> AsyncIterator[Union[str, bytes]]:
        """Receive messages following RFC 6455 specification."""
        while self.state == ProtocolState.CONNECTED:
            try:
                frame = await self._receive_frame()

                # Handle control frames per RFC 6455
                if frame.opcode == OpCode.PING:
                    await self._send_pong(frame.payload)
                    continue
                elif frame.opcode == OpCode.PONG:
                    # Handle pong response
                    continue
                elif frame.opcode == OpCode.CLOSE:
                    await self._handle_close_frame(frame)
                    break

                # Handle data frames
                if frame.opcode == OpCode.TEXT:
                    yield frame.payload.decode('utf-8')
                elif frame.opcode == OpCode.BINARY:
                    yield frame.payload

            except Exception as e:
                await self._transition_state(ProtocolState.ERROR)
                raise

    def _generate_websocket_key(self) -> str:
        """Generate Sec-WebSocket-Key per RFC 6455 using stdlib crypto."""
        return base64.b64encode(secrets.token_bytes(16)).decode('ascii')

    async def _perform_rfc_handshake(self, parsed_uri) -> None:
        """Perform RFC 6455 Section 4.2.1 compliant handshake using AnyIO I/O."""
        # Construct handshake request
        request_lines = [
            f"GET {parsed_uri.path or '/'} HTTP/1.1",
            f"Host: {parsed_uri.hostname}:{parsed_uri.port or (443 if parsed_uri.scheme == 'wss' else 80)}",
            "Upgrade: websocket",
            "Connection: Upgrade",
            f"Sec-WebSocket-Key: {self._sec_websocket_key}",
            "Sec-WebSocket-Version: 13"
        ]

        if self.origin:
            request_lines.append(f"Origin: {self.origin}")

        if self.protocols:
            request_lines.append(f"Sec-WebSocket-Protocol: {', '.join(self.protocols)}")

        if self.extensions:
            request_lines.append(f"Sec-WebSocket-Extensions: {', '.join(self.extensions)}")

        request = '\r\n'.join(request_lines) + '\r\n\r\n'
        # CRITICAL: Use AnyIO stream send, not any asyncio methods
        await self._stream.send(request.encode('utf-8'))

        # Parse handshake response and validate per RFC 6455
        response = await self._read_http_response()
        await self._validate_handshake_response(response)

    async def _read_http_response(self) -> str:
        """Read HTTP response using AnyIO stream receive."""
        buffer = b''
        while True:
            # CRITICAL: Use AnyIO stream receive, not asyncio methods
            chunk = await self._stream.receive(1024)
            if not chunk:
                break
            buffer += chunk
            # Look for end of HTTP headers
            if b'\r\n\r\n' in buffer:
                break
        return buffer.decode('utf-8')

    async def _validate_handshake_response(self, response: str) -> None:
        """Validate handshake response per RFC 6455 Section 4.2.2."""
        lines = response.split('\r\n')
        status_line = lines[0]

        if not status_line.startswith('HTTP/1.1 101'):
            raise ValueError(f"Invalid handshake response: {status_line}")

        headers = {}
        for line in lines[1:]:
            if ':' in line:
                key, value = line.split(':', 1)
                headers[key.strip().lower()] = value.strip()

        # Validate required headers per RFC 6455
        required_headers = {
            'upgrade': 'websocket',
            'connection': 'upgrade'
        }

        for header, expected_value in required_headers.items():
            if header not in headers:
                raise ValueError(f"Missing required header: {header}")
            if headers[header].lower() != expected_value:
                raise ValueError(f"Invalid {header} header: {headers[header]}")

        # Validate Sec-WebSocket-Accept per RFC 6455
        if 'sec-websocket-accept' not in headers:
            raise ValueError("Missing Sec-WebSocket-Accept header")

        expected_accept = self._calculate_websocket_accept(self._sec_websocket_key)
        if headers['sec-websocket-accept'] != expected_accept:
            raise ValueError("Invalid Sec-WebSocket-Accept header")

    def _calculate_websocket_accept(self, websocket_key: str) -> str:
        """Calculate Sec-WebSocket-Accept per RFC 6455 using stdlib crypto."""
        magic_string = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
        combined = websocket_key + magic_string
        sha1_hash = hashlib.sha1(combined.encode('utf-8')).digest()
        return base64.b64encode(sha1_hash).decode('ascii')

    async def _send_frame(self, frame: WSFrame) -> None:
        """Send WebSocket frame with RFC 6455 compliance validation using AnyIO."""
        if not frame.validate_rfc_compliance():
            raise ValueError("Frame violates RFC 6455 requirements")
        # CRITICAL: Use AnyIO stream send only
        await self._stream.send(frame.to_bytes())

    async def _receive_frame(self) -> WSFrame:
        """Receive and parse WebSocket frame per RFC 6455 using AnyIO."""
        # CRITICAL: Use AnyIO stream receive only
        header = await self._stream.receive(2)
        if len(header) < 2:
            raise ConnectionError("Unexpected end of stream")

        # Parse frame according to RFC 6455 Section 5.2
        frame = WSFrame.from_bytes(header + await self._read_frame_payload(header))

        if not frame.validate_rfc_compliance():
            raise ValueError("Received frame violates RFC 6455")

        return frame

    async def _read_frame_payload(self, header: bytes) -> bytes:
        """Read frame payload using AnyIO stream receive."""
        # Implementation of payload length parsing per RFC 6455
        # CRITICAL: All I/O must use self._stream.receive() (AnyIO)
        payload_len = header[1] & 0x7F

        if payload_len == 126:
            length_bytes = await self._stream.receive(2)
            payload_len = int.from_bytes(length_bytes, 'big')
        elif payload_len == 127:
            length_bytes = await self._stream.receive(8)
            payload_len = int.from_bytes(length_bytes, 'big')

        # Read masking key if present
        mask_bytes = b''
        if header[1] & 0x80:  # MASK bit set
            mask_bytes = await self._stream.receive(4)

        # Read payload
        payload = await self._stream.receive(payload_len)

        return length_bytes + mask_bytes + payload if payload_len > 125 else mask_bytes + payload
```

### IMAP Client (RFC 9051) - Priority 2 - COMPLETE IMPLEMENTATION

```python
# anyrfc/email/imap/client.py
# CRITICAL: ONLY ANYIO FOR ALL I/O - NO ASYNCIO IMPORTS ANYWHERE
import anyio
from anyio.abc import ByteStream  # AnyIO interfaces only
from typing import AsyncIterator, Dict, List, Optional, Any, Union, Set
from enum import Enum
import re  # stdlib for parsing is acceptable

from ...core.types import ProtocolClient, ProtocolState, AuthenticationClient
from .commands import IMAPCommand, IMAPCommandBuilder
from .responses import IMAPResponse, IMAPResponseParser
from .compliance import RFC9051Compliance

class IMAPState(Enum):
    """IMAP protocol states per RFC 9051."""
    NOT_AUTHENTICATED = "not_authenticated"
    AUTHENTICATED = "authenticated"
    SELECTED = "selected"
    LOGOUT = "logout"

class IMAPClient(ProtocolClient[IMAPCommand], AuthenticationClient, RFC9051Compliance):
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

    def get_rfc_number(self) -> str:
        return "RFC 9051"

    async def validate_compliance(self) -> Dict[str, bool]:
        """Validate RFC 9051 compliance."""
        return await RFC9051Compliance.run_compliance_tests(self)

    async def connect(self) -> None:
        """Establish IMAP connection per RFC 9051 using AnyIO."""
        await self._transition_state(ProtocolState.CONNECTING)

        # CRITICAL: Use ONLY AnyIO for network I/O
        if self.use_tls:
            self._stream = await anyio.connect_tcp(self.hostname, self.port, tls=True)
        else:
            self._stream = await anyio.connect_tcp(self.hostname, self.port)

        # Read greeting per RFC 9051 Section 7.1.1
        greeting = await self._read_response()
        if not greeting.status == 'OK':
            raise ValueError(f"IMAP server greeting failed: {greeting}")

        # Get capabilities per RFC 9051
        await self._capability()
        await self._transition_state(ProtocolState.CONNECTED)

    async def authenticate(self, credentials: Dict[str, Any]) -> bool:
        """Perform IMAP authentication per RFC 9051."""
        if self.state != ProtocolState.CONNECTED:
            raise RuntimeError("Must be connected before authentication")

        await self._transition_state(ProtocolState.AUTHENTICATING)

        username = credentials.get('username')
        password = credentials.get('password')
        auth_method = credentials.get('method', 'LOGIN')

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

    async def _login(self, username: str, password: str) -> bool:
        """Perform LOGIN authentication using AnyIO I/O."""
        command = IMAPCommandBuilder.login(username, password)
        response = await self._send_command(command)
        return response.status == 'OK'

    async def select_mailbox(self, mailbox: str = "INBOX") -> Dict[str, Any]:
        """Select mailbox per RFC 9051 Section 6.3.1."""
        if self._imap_state != IMAPState.AUTHENTICATED:
            raise RuntimeError("Must be authenticated to select mailbox")

        command = IMAPCommandBuilder.select(mailbox)
        response = await self._send_command(command)

        if response.status == 'OK':
            self._selected_mailbox = mailbox
            self._imap_state = IMAPState.SELECTED
            return self._parse_select_response(response)
        else:
            raise ValueError(f"Failed to select mailbox {mailbox}: {response}")

    async def fetch_messages(self, sequence_set: str, items: str) -> AsyncIterator[Dict[str, Any]]:
        """Fetch messages per RFC 9051 Section 6.4.5."""
        if self._imap_state != IMAPState.SELECTED:
            raise RuntimeError("Must have mailbox selected to fetch messages")

        command = IMAPCommandBuilder.fetch(sequence_set, items)
        await self._send_command_untagged(command)

        async for response in self._read_fetch_responses():
            yield self._parse_fetch_response(response)

    async def _capability(self) -> None:
        """Get server capabilities per RFC 9051 Section 6.1.1."""
        command = IMAPCommandBuilder.capability()
        response = await self._send_command(command)

        if response.status == 'OK':
            # Parse capabilities from response
            cap_line = next((line for line in response.data if line.startswith('CAPABILITY')), None)
            if cap_line:
                self._capabilities = set(cap_line.split()[1:])

    async def _send_command(self, command: IMAPCommand) -> IMAPResponse:
        """Send tagged IMAP command per RFC 9051 using AnyIO."""
        tag = f"A{self._tag_counter:04d}"
        self._tag_counter += 1

        command_line = f"{tag} {command.to_string()}\r\n"
        # CRITICAL: Use AnyIO stream send only
        await self._stream.send(command_line.encode('utf-8'))

        # Read response until we get the tagged response
        while True:
            response = await self._read_response()
            if response.tag == tag:
                return response
            # Handle untagged responses
            await self._handle_untagged_response(response)

    async def _read_response(self) -> IMAPResponse:
        """Read IMAP response per RFC 9051 Section 7 using AnyIO."""
        line = await self._read_line()
        return IMAPResponseParser.parse(line)

    async def _read_line(self) -> str:
        """Read a CRLF-terminated line from the server using AnyIO."""
        buffer = b''
        while True:
            # CRITICAL: Use AnyIO stream receive only - NO asyncio I/O
            chunk = await self._stream.receive(1)
            if not chunk:
                raise ConnectionError("Connection closed by server")
            buffer += chunk
            if buffer.endswith(b'\r\n'):
                return buffer[:-2].decode('utf-8')

    async def _send_command_untagged(self, command: IMAPCommand) -> None:
        """Send untagged command for operations like FETCH."""
        command_line = f"{command.to_string()}\r\n"
        # CRITICAL: Use AnyIO stream send only
        await self._stream.send(command_line.encode('utf-8'))

    async def _read_fetch_responses(self) -> AsyncIterator[IMAPResponse]:
        """Read FETCH responses using AnyIO stream operations."""
        while True:
            try:
                response = await self._read_response()
                if response.tag:  # Tagged response ends the FETCH
                    break
                yield response
            except ConnectionError:
                break

    def _parse_select_response(self, response: IMAPResponse) -> Dict[str, Any]:
        """Parse SELECT response data per RFC 9051."""
        # Implementation of RFC 9051 SELECT response parsing
        return {}

    def _parse_fetch_response(self, response: IMAPResponse) -> Dict[str, Any]:
        """Parse FETCH response data per RFC 9051."""
        # Implementation of RFC 9051 FETCH response parsing
        return {}

    async def _handle_untagged_response(self, response: IMAPResponse) -> None:
        """Handle untagged IMAP responses per RFC 9051."""
        # Handle server status updates, mailbox changes, etc.
        pass

    async def _sasl_authenticate(self, method: str, credentials: Dict[str, Any]) -> bool:
        """Perform SASL authentication per RFC 4422."""
        # Implementation of SASL authentication mechanisms
        return False
```

### OAuth 2.0 Client (RFC 6749/6750) - Priority 3 - COMPLETE IMPLEMENTATION

```python
# anyrfc/auth/oauth2/client.py
# CRITICAL: ONLY ANYIO FOR ALL I/O - NO ASYNCIO IMPORTS
# NOTE: This example uses httpx which would require approval for production
import anyio
from typing import Dict, Optional, Any, List
from urllib.parse import urlencode, parse_qs, urlparse  # stdlib parsing acceptable
import secrets  # stdlib crypto acceptable
import base64  # stdlib encoding acceptable
import hashlib  # stdlib crypto acceptable
from datetime import datetime, timedelta  # stdlib time acceptable

# WARNING: httpx would require approval - shown for example only
# In production, might need to implement HTTP client using raw AnyIO
# or get approval for httpx dependency
import httpx  # REQUIRES APPROVAL FOR PRODUCTION BUILD

from ...core.types import AuthenticationClient, RFCCompliance
from .flows import AuthorizationCodeFlow, DeviceAuthorizationFlow
from .tokens import TokenManager, OAuth2Token
from .pkce import PKCEChallenge
from .compliance import OAuth2Compliance

class OAuth2Client(AuthenticationClient, RFCCompliance):
    """RFC 6749/6750 compliant OAuth 2.0 client - httpx requires approval."""

    def __init__(self,
                 client_id: str,
                 client_secret: Optional[str] = None,
                 authorization_endpoint: str = None,
                 token_endpoint: str = None,
                 *,
                 redirect_uri: Optional[str] = None,
                 scope: Optional[List[str]] = None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.authorization_endpoint = authorization_endpoint
        self.token_endpoint = token_endpoint
        self.redirect_uri = redirect_uri
        self.scope = scope or []

        # WARNING: httpx usage requires approval for production
        # Alternative: implement HTTP client using AnyIO directly
        self._http_client = httpx.AsyncClient()
        self._token_manager = TokenManager()

    def get_rfc_number(self) -> str:
        return "RFC 6749, RFC 6750"

    async def validate_compliance(self) -> Dict[str, bool]:
        """Validate OAuth 2.0 RFC compliance."""
        return await OAuth2Compliance.run_compliance_tests(self)

    async def authorization_code_flow(self,
                                    code_verifier: Optional[str] = None,
                                    state: Optional[str] = None) -> Dict[str, str]:
        """Perform Authorization Code flow per RFC 6749 Section 4.1."""

        # Generate PKCE challenge per RFC 7636 if code_verifier provided
        # Uses stdlib crypto operations - acceptable
        pkce_challenge = None
        if code_verifier:
            pkce_challenge = PKCEChallenge.from_verifier(code_verifier)

        # Step 1: Build authorization URL per RFC 6749 Section 4.1.1
        auth_params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'scope': ' '.join(self.scope) if self.scope else '',
            'state': state or secrets.token_urlsafe(32)  # stdlib crypto acceptable
        }

        if self.redirect_uri:
            auth_params['redirect_uri'] = self.redirect_uri

        if pkce_challenge:
            auth_params.update(pkce_challenge.to_auth_params())

        # stdlib urllib.parse acceptable for URL construction
        authorization_url = f"{self.authorization_endpoint}?{urlencode(auth_params)}"

        return {
            'authorization_url': authorization_url,
            'state': auth_params['state'],
            'code_verifier': code_verifier
        }

    async def exchange_code_for_token(self,
                                    code: str,
                                    code_verifier: Optional[str] = None,
                                    state: Optional[str] = None) -> OAuth2Token:
        """Exchange authorization code for token per RFC 6749 Section 4.1.3."""

        token_params = {
            'grant_type': 'authorization_code',
            'code': code,
            'client_id': self.client_id
        }

        if self.redirect_uri:
            token_params['redirect_uri'] = self.redirect_uri

        if code_verifier:
            token_params['code_verifier'] = code_verifier

        # Prepare authentication per RFC 6749 Section 2.3
        auth = None
        if self.client_secret:
            auth = (self.client_id, self.client_secret)
        else:
            token_params['client_secret'] = ''  # Public client

        # WARNING: httpx usage - requires approval for production
        # Alternative: implement using AnyIO HTTP client or get httpx approved
        response = await self._http_client.post(
            self.token_endpoint,
            data=token_params,
            auth=auth,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )

        if response.status_code != 200:
            raise ValueError(f"Token exchange failed: {response.text}")

        token_data = response.json()
        return OAuth2Token.from_response(token_data)

    # Additional OAuth 2.0 methods would follow same pattern...
    # All using stdlib for computation, httpx for HTTP (requiring approval)

    async def close(self) -> None:
        """Close HTTP client."""
        await self._http_client.aclose()


# Alternative implementation without third-party HTTP client
class OAuth2ClientPureAnyIO(AuthenticationClient, RFCCompliance):
    """RFC 6749/6750 compliant OAuth 2.0 client using ONLY AnyIO and stdlib."""

    def __init__(self,
                 client_id: str,
                 client_secret: Optional[str] = None,
                 authorization_endpoint: str = None,
                 token_endpoint: str = None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.authorization_endpoint = authorization_endpoint
        self.token_endpoint = token_endpoint

    async def _http_request(self, method: str, url: str,
                           headers: Dict[str, str],
                           body: Optional[bytes] = None) -> Dict[str, Any]:
        """HTTP request implementation using ONLY AnyIO - no third-party deps."""
        parsed = urlparse(url)

        # CRITICAL: Use ONLY AnyIO for network I/O
        if parsed.scheme == 'https':
            stream = await anyio.connect_tcp(parsed.hostname, parsed.port or 443, tls=True)
        else:
            stream = await anyio.connect_tcp(parsed.hostname, parsed.port or 80)

        # Construct HTTP request manually using stdlib
        request_lines = [
            f"{method} {parsed.path or '/'} HTTP/1.1",
            f"Host: {parsed.hostname}"
        ]

        for key, value in headers.items():
            request_lines.append(f"{key}: {value}")

        if body:
            request_lines.append(f"Content-Length: {len(body)}")

        request_lines.append("")
        if body:
            request_lines.append(body.decode('utf-8'))

        request = '\r\n'.join(request_lines) + '\r\n'

        # CRITICAL: Use AnyIO stream send/receive only
        await stream.send(request.encode('utf-8'))

        # Read HTTP response using AnyIO
        response_data = b''
        while True:
            chunk = await stream.receive(4096)
            if not chunk:
                break
            response_data += chunk
            if b'\r\n\r\n' in response_data:
                break

        await stream.aclose()

        # Parse HTTP response using stdlib
        response_text = response_data.decode('utf-8')
        # Implementation of HTTP response parsing...

        return {}  # Parsed response
```

## Testing Strategy

### RFC Compliance Testing Framework

```python
# tests/rfc_compliance/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List
import pytest

class RFCComplianceTest(ABC):
    """Base class for RFC compliance testing."""

    @abstractmethod
    def get_rfc_number(self) -> str:
        """Return RFC number being tested."""

    @abstractmethod
    async def test_protocol_states(self) -> Dict[str, bool]:
        """Test all protocol state transitions per RFC."""

    @abstractmethod
    async def test_message_format(self) -> Dict[str, bool]:
        """Test message format compliance per RFC."""

    @abstractmethod
    async def test_error_handling(self) -> Dict[str, bool]:
        """Test error condition handling per RFC."""

# tests/rfc_compliance/websocket/test_rfc6455.py
import pytest
from anyrfc.websocket import WebSocketClient
from ..base import RFCComplianceTest

class TestRFC6455Compliance(RFCComplianceTest):
    """RFC 6455 WebSocket compliance tests."""

    def get_rfc_number(self) -> str:
        return "RFC 6455"

    async def test_handshake_compliance(self):
        """Test WebSocket handshake per RFC 6455 Section 4."""
        client = WebSocketClient("ws://echo.websocket.org/")

        # Test Sec-WebSocket-Key generation (16 bytes, base64 encoded)
        assert len(client._sec_websocket_key) == 24  # 16 bytes base64 encoded

        # Test handshake headers presence
        await client.connect()
        # Validate all required headers were sent

    async def test_frame_format_compliance(self):
        """Test WebSocket frame format per RFC 6455 Section 5.2."""
        from anyrfc.websocket.frames import WSFrame, OpCode

        # Test text frame format
        frame = WSFrame(fin=True, opcode=OpCode.TEXT, payload=b"Hello", masked=True)
        serialized = frame.to_bytes()

        # Validate frame structure
        assert serialized[0] & 0x80 == 0x80  # FIN bit set
        assert serialized[0] & 0x0F == OpCode.TEXT.value  # Opcode
        assert serialized[1] & 0x80 == 0x80  # MASK bit set (client frames)

        # Test frame parsing
        parsed_frame = WSFrame.from_bytes(serialized)
        assert parsed_frame.fin == True
        assert parsed_frame.opcode == OpCode.TEXT
        assert parsed_frame.payload == b"Hello"

    async def test_close_handshake_compliance(self):
        """Test close handshake per RFC 6455 Section 7."""
        # Test proper close frame format and status codes
        pass

    async def test_ping_pong_compliance(self):
        """Test ping/pong frames per RFC 6455 Section 5.5.2 & 5.5.3."""
        # Test ping/pong control frame handling
        pass

    async def test_extension_negotiation(self):
        """Test extension negotiation per RFC 6455 Section 9."""
        # Test per-message-deflate and other extensions
        pass

# tests/rfc_compliance/imap/test_rfc9051.py
class TestRFC9051Compliance(RFCComplianceTest):
    """RFC 9051 IMAP4rev2 compliance tests."""

    def get_rfc_number(self) -> str:
        return "RFC 9051"

    async def test_command_format_compliance(self):
        """Test IMAP command format per RFC 9051 Section 6."""
        from anyrfc.email.imap.commands import IMAPCommandBuilder

        # Test SELECT command format
        select_cmd = IMAPCommandBuilder.select("INBOX")
        assert select_cmd.to_string() == 'SELECT "INBOX"'

        # Test FETCH command format
        fetch_cmd = IMAPCommandBuilder.fetch("1:10", "FLAGS BODY[HEADER]")
        assert "1:10" in fetch_cmd.to_string()

    async def test_response_parsing_compliance(self):
        """Test IMAP response parsing per RFC 9051 Section 7."""
        from anyrfc.email.imap.responses import IMAPResponseParser

        # Test tagged response parsing
        response = IMAPResponseParser.parse("A001 OK SELECT completed")
        assert response.tag == "A001"
        assert response.status == "OK"
        assert "SELECT completed" in response.message

    async def test_mailbox_operations_compliance(self):
        """Test mailbox operations per RFC 9051."""
        # Test SELECT, EXAMINE, CREATE, DELETE operations
        pass

    async def test_message_operations_compliance(self):
        """Test message operations per RFC 9051."""
        # Test FETCH, STORE, SEARCH, COPY operations
        pass

# tests/rfc_compliance/oauth2/test_rfc6749.py
class TestRFC6749Compliance(RFCComplianceTest):
    """RFC 6749 OAuth 2.0 compliance tests."""

    def get_rfc_number(self) -> str:
        return "RFC 6749"

    async def test_authorization_request_compliance(self):
        """Test authorization request per RFC 6749 Section 4.1.1."""
        from anyrfc.auth.oauth2 import OAuth2Client

        client = OAuth2Client(
            client_id="test_client",
            authorization_endpoint="https://auth.example.com/oauth/authorize",
            redirect_uri="https://app.example.com/callback"
        )

        flow_data = await client.authorization_code_flow()
        auth_url = flow_data['authorization_url']

        # Validate required parameters
        assert "response_type=code" in auth_url
        assert "client_id=test_client" in auth_url
        assert "redirect_uri=" in auth_url
        assert "state=" in auth_url

    async def test_token_request_compliance(self):
        """Test token request per RFC 6749 Section 4.1.3."""
        # Test authorization code exchange
        pass

    async def test_token_refresh_compliance(self):
        """Test token refresh per RFC 6749 Section 6."""
        # Test refresh token flow
        pass

    async def test_pkce_compliance(self):
        """Test PKCE per RFC 7636."""
        from anyrfc.auth.oauth2.pkce import PKCEChallenge

        verifier = "test_verifier_123456789"
        challenge = PKCEChallenge.from_verifier(verifier)

        assert challenge.code_challenge_method == "S256"
        assert len(challenge.code_challenge) > 0
```

### Unit Testing Framework

```python
# tests/conftest.py
import pytest
import anyio
from typing import AsyncGenerator
import asyncio

@pytest.fixture
async def anyio_backend():
    """Configure AnyIO backend for tests."""
    return "asyncio"

@pytest.fixture
async def mock_server() -> AsyncGenerator[MockServer, None]:
    """Provide mock server for protocol testing."""
    server = MockServer()
    async with anyio.create_task_group() as tg:
        tg.start_soon(server.serve)
        yield server
        server.shutdown()

@pytest.fixture
def rfc_compliance_suite():
    """Provide RFC compliance test suite."""
    return RFCComplianceTestSuite()

# Parametrized tests for multiple server implementations
@pytest.fixture(params=[
    "echo.websocket.org",
    "ws://localhost:8080",  # Local test server
])
def websocket_test_servers(request):
    """Provide multiple WebSocket servers for interop testing."""
    return request.param

@pytest.fixture(params=[
    ("imap.gmail.com", 993),
    ("imap.outlook.com", 993),
    ("localhost", 1143),  # Local test server
])
def imap_test_servers(request):
    """Provide multiple IMAP servers for interop testing."""
    return request.param
```

### Interoperability Testing

```python
# tests/interop/test_real_servers.py
import pytest
from anyrfc.websocket import WebSocketClient
from anyrfc.email.imap import IMAPClient
from anyrfc.auth.oauth2 import OAuth2Client

@pytest.mark.integration
class TestWebSocketInterop:
    """Test against real WebSocket server implementations."""

    async def test_echo_websocket_org(self):
        """Test against wss://echo.websocket.org/"""
        client = WebSocketClient("wss://echo.websocket.org/")
        await client.connect()

        # Test text message echo
        await client.send_text("Hello, World!")
        async for message in client.receive():
            assert message == "Hello, World!"
            break

        # Test binary message echo
        test_data = b"\x00\x01\x02\x03"
        await client.send_binary(test_data)
        async for message in client.receive():
            assert message == test_data
            break

        await client.disconnect()

    async def test_cloudflare_websocket(self):
        """Test against Cloudflare WebSocket endpoint."""
        # Test with different WebSocket server implementation
        pass

@pytest.mark.integration
class TestIMAPInterop:
    """Test against real IMAP server implementations."""

    @pytest.mark.parametrize("server_config", [
        {"host": "imap.gmail.com", "port": 993, "tls": True},
        {"host": "imap.outlook.com", "port": 993, "tls": True},
    ])
    async def test_capability_command(self, server_config):
        """Test CAPABILITY command against real servers."""
        client = IMAPClient(
            hostname=server_config["host"],
            port=server_config["port"],
            use_tls=server_config["tls"]
        )

        await client.connect()
        # Validate server capabilities include required RFC 9051 features
        assert "IMAP4rev1" in client._capabilities or "IMAP4rev2" in client._capabilities

    async def test_gmail_imap_compliance(self):
        """Test specific Gmail IMAP quirks and compliance."""
        # Test Gmail-specific IMAP behaviors
        pass

@pytest.mark.integration
class TestOAuth2Interop:
    """Test against real OAuth 2.0 providers."""

    async def test_google_oauth2_discovery(self):
        """Test Google OAuth 2.0 endpoint discovery."""
        # Test .well-known/openid_configuration discovery
        pass

    async def test_github_oauth2_flow(self):
        """Test GitHub OAuth 2.0 authorization flow."""
        # Test GitHub-specific OAuth flow
        pass
```

### Security Testing

```python
# tests/security/test_protocol_security.py
import pytest
from anyrfc.websocket import WebSocketClient

class TestSecurityCompliance:
    """Security-focused testing for all protocols."""

    async def test_websocket_masking_required(self):
        """Test that client frames are properly masked per RFC 6455."""
        client = WebSocketClient("ws://echo.websocket.org/")

        # Mock frame creation and verify masking
        from anyrfc.websocket.frames import WSFrame, OpCode
        frame = WSFrame(fin=True, opcode=OpCode.TEXT, payload=b"test", masked=True)

        serialized = frame.to_bytes()
        # Verify MASK bit is set (bit 7 of second byte)
        assert serialized[1] & 0x80 == 0x80

    async def test_tls_certificate_validation(self):
        """Test TLS certificate validation for all secure protocols."""
        # Test certificate validation for WSS, IMAPS, HTTPS
        pass

    async def test_oauth2_pkce_required(self):
        """Test PKCE implementation for public OAuth clients."""
        from anyrfc.auth.oauth2.pkce import PKCEChallenge

        verifier = PKCEChallenge.generate_verifier()
        challenge = PKCEChallenge.from_verifier(verifier)

        # Verify S256 challenge method
        assert challenge.code_challenge_method == "S256"
        assert len(challenge.code_challenge) == 43  # Base64url without padding

    async def test_credential_storage_security(self):
        """Test secure credential storage and handling."""
        # Test that credentials are not logged or stored insecurely
        pass
```

## Development Workflow

### Setup with uv

```bash
# Initialize project
uv init anyio-rfc-clients
cd anyio-rfc-clients

# Add dependencies
uv add anyio httpx
uv add --dev pytest pytest-asyncio mypy ruff

# Setup development environment
uv sync
```

### pyproject.toml Configuration

```toml
[project]
name = "anyio-rfc-clients"
version = "0.1.0"
description = "RFC-compliant protocol clients using AnyIO structured concurrency"
authors = [{name = "Development Team"}]
dependencies = [
    "anyio>=4.0.0",
    "httpx>=0.25.0",
    "typing-extensions>=4.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "mypy>=1.0.0",
    "ruff>=0.1.0",
    "coverage>=7.0.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.ruff]
line-length = 88
target-version = "py311"

[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
markers = [
    "integration: marks tests as integration tests",
    "interop: marks tests as interoperability tests",
]
```

### CI/CD Pipeline

```yaml
# .github/workflows/test.yml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]

    steps:
    - uses: actions/checkout@v4
    - name: Install uv
      uses: astral-sh/setup-uv@v1
    - name: Set up Python
      run: uv python install ${{ matrix.python-version }}
    - name: Install dependencies
      run: uv sync --all-extras
    - name: Run tests
      run: uv run pytest
    - name: Type checking
      run: uv run mypy src/
    - name: Linting
      run: uv run ruff check src/
```

## Risk Mitigation

### Protocol Complexity Management

- **Modular design**: Each protocol in separate package
- **Incremental implementation**: Start with basic features, add extensions
- **Protocol state machines**: Use explicit state management
- **Comprehensive testing**: Unit, integration, and interoperability tests

### Performance Considerations

- **Connection pooling**: Reuse connections where possible
- **Streaming interfaces**: Use AsyncIterator for large data
- **Memory management**: Explicit resource cleanup with context managers
- **Profiling integration**: Built-in performance monitoring hooks

### Security Best Practices

- **TLS by default**: Secure transport for all applicable protocols
- **Input validation**: Strict parsing with error handling
- **Timeout handling**: Prevent hanging connections
- **Dependency management**: Regular security updates with uv

## Success Criteria

### Phase 1 Success Metrics

- [ ] WebSocket client passes RFC 6455 compliance tests
- [ ] Successfully connects to major WebSocket servers (AWS, Cloudflare)
- [ ] Handles connection failures and reconnection gracefully
- [ ] Project structure supports easy addition of new protocols

### Phase 2 Success Metrics

- [ ] DNS-over-HTTPS client resolves queries correctly
- [ ] SMTP client sends emails through major providers
- [ ] Performance comparable to existing Python clients
- [ ] Documentation covers all implemented protocols

### Phase 3+ Success Metrics

- [ ] Full email client functionality (SMTP + IMAP)
- [ ] mDNS service discovery works on local networks
- [ ] OAuth 2.0 integration with popular providers
- [ ] CoAP client communicates with IoT devices

## Timeline & Milestones

| Week | Milestone | Deliverable |
|------|-----------|-------------|
| 1-2  | Project setup & WebSocket foundation | Working WebSocket client |
| 3-4  | WebSocket completion & testing | RFC 6455 compliant implementation |
| 5-6  | DNS-over-HTTPS implementation | DoH client with caching |
| 7-8  | SMTP client development | Email sending capability |
| 9-10 | IMAP client foundation | Email reading capability |
| 11-12| Service discovery protocols | mDNS/DNS-SD implementation |
| 13-14| OAuth 2.0 framework | Modern authentication support |
| 15-16| CoAP client for IoT | Constrained device communication |
| 17-18| XMPP messaging client | Real-time messaging capability |
| 19-20| Integration & documentation | Complete protocol suite |

This comprehensive implementation plan provides a structured approach to building complete, RFC-compliant clients using AnyIO's structured concurrency, with absolute adherence to the AnyIO-only I/O constraint while establishing a foundation for the broader protocol ecosystem.

---

## ⚠️ CRITICAL IMPLEMENTATION CONSTRAINTS ⚠️

### AnyIO-ONLY I/O POLICY - NO EXCEPTIONS

**🚫 ABSOLUTELY PROHIBITED:**

- ANY `import asyncio` or `from asyncio` statements
- ANY use of asyncio APIs: `asyncio.connect()`, `asyncio.create_task()`, `asyncio.gather()`, etc.
- ANY third-party I/O libraries without explicit approval: `requests`, `aiohttp`, `urllib3`, etc.

**✅ REQUIRED:**

- ALL I/O operations MUST use AnyIO: `anyio.connect_tcp()`, `anyio.create_task_group()`, `anyio.Event()`, etc.
- ALL network operations through AnyIO stream interfaces: `ByteStream`, `SocketStream`
- ALL concurrency through AnyIO structured concurrency: nurseries, task groups, cancellation scopes

**📋 IMPLEMENTATION CHECKLIST:**

- [ ] Zero `asyncio` imports in entire codebase
- [ ] All network I/O uses `anyio.connect_tcp()` or `anyio.connect_udp()`
- [ ] All file I/O uses `anyio.open_file()` or `anyio.Path`
- [ ] All concurrency uses `anyio.create_task_group()`
- [ ] All synchronization uses `anyio.Event()`, `anyio.Lock()`, `anyio.Semaphore()`
- [ ] All timeouts use `anyio.move_on_after()` or `anyio.fail_after()`

### DEPENDENCY APPROVAL PROCESS

**🔒 PRODUCTION BUILD REQUIREMENTS:**

- **ONLY `anyio` is pre-approved** for production builds
- **Every other third-party dependency requires explicit approval**
- **Justification document required** for each proposed dependency
- **Security review mandatory** for all approved dependencies
- **Alternative analysis required**: Why stdlib + AnyIO cannot achieve the same functionality

**📝 APPROVAL REQUEST FORMAT:**

```
Dependency: [package-name]
Version: [version-requirement]
Justification: [why this dependency is essential]
Alternatives Considered: [stdlib/AnyIO alternatives and why they're insufficient]
Security Assessment: [security analysis of dependency]
RFC Compliance Impact: [how this affects RFC compliance]
```

**⚡ ENFORCEMENT:**

- Automated checks in CI/CD pipeline
- Pre-commit hooks to detect violations
- Code review requirements for any new dependencies
- Regular dependency audits and security scans

This plan ensures maximum performance, security, and maintainability by leveraging AnyIO's structured concurrency while maintaining strict control over the dependency surface area.
