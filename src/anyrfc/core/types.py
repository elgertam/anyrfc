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

class ProtocolClient(RFCCompliance, Generic[T], ABC):
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