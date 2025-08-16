"""WebSocket client implementation per RFC 6455."""
# CRITICAL: ALL I/O OPERATIONS MUST USE ANYIO - NO ASYNCIO IMPORTS ALLOWED
import anyio
from anyio.abc import ByteStream
from typing import AsyncIterator, Optional, Union, Dict, List, Any
from ..core.types import ProtocolClient, ProtocolState, RFCCompliance
from ..core.streams import AnyIOStreamHelpers
from ..core.uri import URIParser, ParsedURI
from ..core.tls import TLSHelper
from .frames import WSFrame, OpCode, CloseCode, WSFrameBuilder
from .state_machine import WebSocketStateMachine, WSState, WSEvent
from .handshake import WebSocketHandshake

class WebSocketClient(ProtocolClient[Union[str, bytes]], RFCCompliance):
    """RFC 6455 compliant WebSocket client implementation using ONLY AnyIO for I/O."""
    
    def __init__(self, uri: str, *, 
                 protocols: Optional[List[str]] = None,
                 extensions: Optional[List[str]] = None,
                 origin: Optional[str] = None,
                 extra_headers: Optional[Dict[str, str]] = None,
                 strict_rfc_validation: bool = True):
        super().__init__()
        self.uri = uri
        self.parsed_uri = URIParser.parse(uri)
        self.protocols = protocols or []
        self.extensions = extensions or []
        self.origin = origin
        self.extra_headers = extra_headers or {}
        self.strict_rfc_validation = strict_rfc_validation
        
        # Validate URI scheme
        if self.parsed_uri.scheme not in {'ws', 'wss'}:
            raise ValueError(f"Invalid WebSocket scheme: {self.parsed_uri.scheme}")
        
        self._stream: Optional[ByteStream] = None
        self._ws_state_machine = WebSocketStateMachine()
        self._handshake = WebSocketHandshake()
        self._negotiated_protocol: Optional[str] = None
        self._negotiated_extensions: List[str] = []
        self._close_code: Optional[CloseCode] = None
        self._close_reason: str = ""
        
        # Message fragmentation support
        self._fragmented_message: List[WSFrame] = []
        self._fragmented_opcode: Optional[OpCode] = None
    
    def get_rfc_number(self) -> str:
        return "RFC 6455"
    
    async def validate_compliance(self) -> Dict[str, bool]:
        """Validate RFC 6455 compliance."""
        # This would be implemented by the compliance testing framework
        return {}
    
    def get_test_vectors(self) -> Dict[str, Any]:
        """Return RFC 6455 test vectors."""
        # This would be implemented by the compliance testing framework
        return {}
    
    @property
    def websocket_state(self) -> WSState:
        """Get current WebSocket protocol state."""
        return self._ws_state_machine.current_state
    
    @property
    def negotiated_protocol(self) -> Optional[str]:
        """Get negotiated subprotocol."""
        return self._negotiated_protocol
    
    @property
    def negotiated_extensions(self) -> List[str]:
        """Get negotiated extensions."""
        return self._negotiated_extensions
    
    async def connect(self) -> None:
        """Establish RFC 6455 compliant WebSocket connection using AnyIO."""
        await self._transition_state(ProtocolState.CONNECTING)
        await self._ws_state_machine.send_event(WSEvent.CONNECT)
        
        try:
            # Establish TCP connection
            hostname = self.parsed_uri.hostname
            port = self.parsed_uri.effective_port
            
            if not hostname:
                raise ValueError("Invalid WebSocket URI: missing hostname")
            
            # CRITICAL: Use ONLY AnyIO for network I/O
            if self.parsed_uri.scheme == 'wss':
                tls_context = TLSHelper.create_default_client_context()
                self._stream = await anyio.connect_tcp(hostname, port, tls=True, ssl_context=tls_context)
            else:
                self._stream = await anyio.connect_tcp(hostname, port)
            
            # Perform WebSocket handshake
            self._negotiated_protocol, self._negotiated_extensions = await self._handshake.perform_client_handshake(
                self._stream,
                self.parsed_uri,
                self.protocols,
                self.extensions,
                self.origin,
                self.extra_headers
            )
            
            # Handshake successful
            await self._ws_state_machine.send_event(WSEvent.HANDSHAKE_COMPLETE)
            await self._transition_state(ProtocolState.CONNECTED)
            
        except Exception as e:
            await self._ws_state_machine.send_event(WSEvent.HANDSHAKE_FAILED)
            await self._transition_state(ProtocolState.ERROR)
            raise
    
    async def disconnect(self) -> None:
        """Gracefully close WebSocket connection per RFC 6455 Section 7."""
        if self._ws_state_machine.can_send_control():
            await self.close(CloseCode.NORMAL_CLOSURE)
        
        await self._cleanup_connection()
        await self._ws_state_machine.send_event(WSEvent.DISCONNECT)
        await self._transition_state(ProtocolState.DISCONNECTED)
    
    async def send(self, message: Union[str, bytes]) -> None:
        """Send message following RFC encoding rules."""
        if isinstance(message, str):
            await self.send_text(message)
        else:
            await self.send_binary(message)
    
    async def send_text(self, text: str) -> None:
        """Send text message per RFC 6455."""
        if not self._ws_state_machine.can_send_data():
            raise RuntimeError(f"Cannot send data in state: {self.websocket_state}")
        
        frame = WSFrameBuilder.text_frame(text)
        await self._send_frame(frame)
    
    async def send_binary(self, data: bytes) -> None:
        """Send binary message per RFC 6455."""
        if not self._ws_state_machine.can_send_data():
            raise RuntimeError(f"Cannot send data in state: {self.websocket_state}")
        
        frame = WSFrameBuilder.binary_frame(data)
        await self._send_frame(frame)
    
    async def ping(self, payload: bytes = b'') -> None:
        """Send ping frame per RFC 6455 Section 5.5.2."""
        if not self._ws_state_machine.can_send_control():
            raise RuntimeError(f"Cannot send control frames in state: {self.websocket_state}")
        
        if len(payload) > 125:
            raise ValueError("Ping payload cannot exceed 125 bytes")
        
        frame = WSFrameBuilder.ping_frame(payload)
        await self._send_frame(frame)
    
    async def close(self, code: CloseCode = CloseCode.NORMAL_CLOSURE, reason: str = '') -> None:
        """Send close frame per RFC 6455 Section 7."""
        if not self._ws_state_machine.can_send_control():
            return  # Already closing or closed
        
        await self._ws_state_machine.send_event(WSEvent.CLOSE_INITIATED)
        
        frame = WSFrameBuilder.close_frame(code, reason)
        await self._send_frame(frame)
    
    async def receive(self) -> AsyncIterator[Union[str, bytes]]:
        """Receive messages following RFC 6455 specification."""
        while self._ws_state_machine.is_connected() or self._ws_state_machine.is_closing():
            try:
                frame = await self._receive_frame()
                
                # Handle control frames
                if frame.is_control_frame():
                    await self._handle_control_frame(frame)
                    continue
                
                # Handle data frames
                message = await self._handle_data_frame(frame)
                if message is not None:
                    yield message
                    
            except Exception as e:
                await self._ws_state_machine.send_event(WSEvent.ERROR_OCCURRED)
                await self._transition_state(ProtocolState.ERROR)
                raise
    
    async def _send_frame(self, frame: WSFrame) -> None:
        """Send WebSocket frame with RFC 6455 compliance validation using AnyIO."""
        if not frame.validate_rfc_compliance():
            raise ValueError("Frame violates RFC 6455 requirements")
        
        if not self._stream:
            raise RuntimeError("Not connected")
        
        frame_bytes = frame.to_bytes()
        await AnyIOStreamHelpers.send_all(self._stream, frame_bytes)
    
    async def _receive_frame(self) -> WSFrame:
        """Receive and parse WebSocket frame per RFC 6455 using AnyIO."""
        if not self._stream:
            raise RuntimeError("Not connected")
        
        # Read frame header (minimum 2 bytes)
        header = await AnyIOStreamHelpers.read_exact(self._stream, 2)
        
        # Parse basic frame info to determine full frame size
        first_byte = header[0]
        second_byte = header[1]
        
        masked = bool(second_byte & 0x80)
        payload_len = second_byte & 0x7F
        
        # Calculate total bytes needed
        total_header_size = 2
        
        # Extended payload length
        if payload_len == 126:
            total_header_size += 2
        elif payload_len == 127:
            total_header_size += 8
        
        # Masking key (server frames should not be masked)
        if masked:
            total_header_size += 4
        
        # Read remaining header bytes
        if total_header_size > 2:
            remaining_header = await AnyIOStreamHelpers.read_exact(self._stream, total_header_size - 2)
            header += remaining_header
        
        # Parse extended length
        if payload_len == 126:
            import struct
            payload_len = struct.unpack('!H', header[2:4])[0]
        elif payload_len == 127:
            import struct
            payload_len = struct.unpack('!Q', header[2:10])[0]
        
        # Read payload
        payload_data = b''
        if payload_len > 0:
            payload_data = await AnyIOStreamHelpers.read_exact(self._stream, payload_len)
        
        # Reconstruct full frame data for parsing
        full_frame_data = header + payload_data
        
        # Parse frame
        frame = WSFrame.from_bytes(full_frame_data)
        
        if self.strict_rfc_validation:
            if not frame.validate_rfc_compliance():
                # Server frames should not be masked, so we need custom validation
                if not self._validate_server_frame(frame):
                    raise ValueError("Received frame violates RFC 6455")
        
        return frame
    
    def _validate_server_frame(self, frame: WSFrame) -> bool:
        """Validate server frame (different rules than client frames)."""
        # Control frames must have FIN=1
        if frame.opcode.value >= 0x8 and not frame.fin:
            return False
        
        # Control frames cannot have payload > 125 bytes
        if frame.opcode.value >= 0x8 and len(frame.payload) > 125:
            return False
        
        # Server frames must NOT be masked per RFC 6455 Section 5.1
        if frame.masked:
            return False
        
        return True
    
    async def _handle_control_frame(self, frame: WSFrame) -> None:
        """Handle control frames per RFC 6455."""
        if frame.opcode == OpCode.PING:
            # Respond with pong
            pong_frame = WSFrameBuilder.pong_frame(frame.payload)
            await self._send_frame(pong_frame)
            
        elif frame.opcode == OpCode.PONG:
            # Handle pong response (could notify waiting ping)
            pass
            
        elif frame.opcode == OpCode.CLOSE:
            # Handle close frame
            self._close_code = frame.get_close_code()
            self._close_reason = frame.get_close_reason()
            
            if self._ws_state_machine.is_connected():
                # Echo close frame back
                await self._ws_state_machine.send_event(WSEvent.CLOSE_RECEIVED)
                echo_frame = WSFrameBuilder.close_frame(
                    self._close_code or CloseCode.NORMAL_CLOSURE
                )
                await self._send_frame(echo_frame)
            
            await self._ws_state_machine.send_event(WSEvent.CLOSE_COMPLETE)
            await self._cleanup_connection()
    
    async def _handle_data_frame(self, frame: WSFrame) -> Optional[Union[str, bytes]]:
        """Handle data frames with fragmentation support per RFC 6455 Section 5.4."""
        if frame.opcode == OpCode.CONTINUATION:
            # Continuation frame
            if not self._fragmented_message:
                raise ValueError("Unexpected continuation frame")
            
            self._fragmented_message.append(frame)
            
            if frame.fin:
                # End of fragmented message
                message = self._reconstruct_fragmented_message()
                self._fragmented_message = []
                self._fragmented_opcode = None
                return message
            
        elif frame.opcode in {OpCode.TEXT, OpCode.BINARY}:
            if frame.fin:
                # Complete message
                if frame.opcode == OpCode.TEXT:
                    return frame.payload.decode('utf-8')
                else:
                    return frame.payload
            else:
                # Start of fragmented message
                if self._fragmented_message:
                    raise ValueError("Fragmented message already in progress")
                
                self._fragmented_message = [frame]
                self._fragmented_opcode = frame.opcode
        
        return None
    
    def _reconstruct_fragmented_message(self) -> Union[str, bytes]:
        """Reconstruct fragmented message from frames."""
        if not self._fragmented_message:
            raise ValueError("No fragmented message to reconstruct")
        
        # Combine payloads
        combined_payload = b''.join(frame.payload for frame in self._fragmented_message)
        
        # Decode based on original opcode
        if self._fragmented_opcode == OpCode.TEXT:
            return combined_payload.decode('utf-8')
        else:
            return combined_payload
    
    async def __aenter__(self) -> 'WebSocketClient':
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.disconnect()
    
    async def _cleanup_connection(self) -> None:
        """Clean up connection resources."""
        if self._stream:
            try:
                await self._stream.aclose()
            except Exception:
                # Ignore cleanup errors (common with TLS connections)
                pass
            finally:
                self._stream = None