"""WebSocket frame handling per RFC 6455."""
# CRITICAL: ALL I/O OPERATIONS MUST USE ANYIO - NO ASYNCIO IMPORTS ALLOWED
from enum import Enum
from typing import Union, Optional
import struct
import secrets  # stdlib crypto acceptable
from ..core.types import MessageFrame

class OpCode(Enum):
    """WebSocket opcodes per RFC 6455 Section 5.2."""
    CONTINUATION = 0x0
    TEXT = 0x1
    BINARY = 0x2
    # 0x3-0x7 reserved for further non-control frames
    CLOSE = 0x8
    PING = 0x9
    PONG = 0xA
    # 0xB-0xF reserved for further control frames

class CloseCode(Enum):
    """WebSocket close codes per RFC 6455 Section 7.4."""
    NORMAL_CLOSURE = 1000
    GOING_AWAY = 1001
    PROTOCOL_ERROR = 1002
    UNSUPPORTED_DATA = 1003
    NO_STATUS_RCVD = 1005
    ABNORMAL_CLOSURE = 1006
    INVALID_FRAME_PAYLOAD_DATA = 1007
    POLICY_VIOLATION = 1008
    MESSAGE_TOO_BIG = 1009
    MANDATORY_EXTENSION = 1010
    INTERNAL_ERROR = 1011
    SERVICE_RESTART = 1012
    TRY_AGAIN_LATER = 1013
    BAD_GATEWAY = 1014
    TLS_HANDSHAKE = 1015

class WSFrame(MessageFrame):
    """WebSocket frame per RFC 6455 Section 5.2."""
    
    def __init__(self, 
                 fin: bool,
                 rsv1: bool = False,
                 rsv2: bool = False, 
                 rsv3: bool = False,
                 opcode: OpCode = OpCode.TEXT,
                 masked: bool = True,
                 payload: bytes = b'',
                 mask_key: Optional[bytes] = None):
        self.fin = fin
        self.rsv1 = rsv1
        self.rsv2 = rsv2
        self.rsv3 = rsv3
        self.opcode = opcode
        self.masked = masked
        self.payload = payload
        self.mask_key = mask_key or (secrets.token_bytes(4) if masked else b'')
        
        # Apply masking if this is a client frame
        if self.masked and payload:
            self.payload = self._apply_mask(payload, self.mask_key)
    
    def to_bytes(self) -> bytes:
        """Serialize frame to bytes per RFC 6455 Section 5.2."""
        # First byte: FIN(1) + RSV(3) + Opcode(4)
        first_byte = 0
        if self.fin:
            first_byte |= 0x80
        if self.rsv1:
            first_byte |= 0x40
        if self.rsv2:
            first_byte |= 0x20
        if self.rsv3:
            first_byte |= 0x10
        first_byte |= self.opcode.value
        
        # Second byte: MASK(1) + Payload length(7)
        payload_len = len(self.payload)
        
        if payload_len < 126:
            second_byte = payload_len
        elif payload_len < 65536:
            second_byte = 126
        else:
            second_byte = 127
            
        if self.masked:
            second_byte |= 0x80
        
        # Build frame
        frame_data = bytes([first_byte, second_byte])
        
        # Extended payload length
        if payload_len >= 126:
            if payload_len < 65536:
                frame_data += struct.pack('!H', payload_len)
            else:
                frame_data += struct.pack('!Q', payload_len)
        
        # Masking key
        if self.masked:
            frame_data += self.mask_key
        
        # Payload
        frame_data += self.payload
        
        return frame_data
    
    @classmethod
    def from_bytes(cls, data: bytes) -> 'WSFrame':
        """Deserialize frame from bytes per RFC 6455 Section 5.2."""
        if len(data) < 2:
            raise ValueError("Frame too short")
        
        # Parse first byte
        first_byte = data[0]
        fin = bool(first_byte & 0x80)
        rsv1 = bool(first_byte & 0x40)
        rsv2 = bool(first_byte & 0x20)
        rsv3 = bool(first_byte & 0x10)
        opcode = OpCode(first_byte & 0x0F)
        
        # Parse second byte
        second_byte = data[1]
        masked = bool(second_byte & 0x80)
        payload_len = second_byte & 0x7F
        
        offset = 2
        
        # Extended payload length
        if payload_len == 126:
            if len(data) < offset + 2:
                raise ValueError("Frame too short for extended length")
            payload_len = struct.unpack('!H', data[offset:offset+2])[0]
            offset += 2
        elif payload_len == 127:
            if len(data) < offset + 8:
                raise ValueError("Frame too short for extended length")
            payload_len = struct.unpack('!Q', data[offset:offset+8])[0]
            offset += 8
        
        # Masking key
        mask_key = b''
        if masked:
            if len(data) < offset + 4:
                raise ValueError("Frame too short for mask key")
            mask_key = data[offset:offset+4]
            offset += 4
        
        # Payload
        if len(data) < offset + payload_len:
            raise ValueError("Frame too short for payload")
        payload = data[offset:offset+payload_len]
        
        # Unmask payload if masked
        if masked and payload:
            payload = cls._apply_mask(payload, mask_key)
        
        return cls(
            fin=fin,
            rsv1=rsv1,
            rsv2=rsv2,
            rsv3=rsv3,
            opcode=opcode,
            masked=masked,
            payload=payload,
            mask_key=mask_key
        )
    
    def validate_rfc_compliance(self) -> bool:
        """Validate frame against RFC 6455 requirements."""
        # Control frames must have FIN=1
        if self.opcode.value >= 0x8 and not self.fin:
            return False
        
        # Control frames cannot have payload > 125 bytes
        if self.opcode.value >= 0x8 and len(self.payload) > 125:
            return False
        
        # Reserved bits must be 0 unless extensions define them
        if self.rsv1 or self.rsv2 or self.rsv3:
            # For now, reject reserved bits (no extensions implemented)
            return False
        
        # Client frames must be masked per RFC 6455 Section 5.3
        # Note: This implementation assumes client-side usage
        if not self.masked:
            return False
        
        return True
    
    @staticmethod
    def _apply_mask(payload: bytes, mask_key: bytes) -> bytes:
        """Apply WebSocket masking per RFC 6455 Section 5.3."""
        if not mask_key or len(mask_key) != 4:
            return payload
        
        masked = bytearray()
        for i, byte in enumerate(payload):
            masked.append(byte ^ mask_key[i % 4])
        return bytes(masked)
    
    def is_control_frame(self) -> bool:
        """Check if this is a control frame."""
        return self.opcode.value >= 0x8
    
    def get_close_code(self) -> Optional[CloseCode]:
        """Get close code if this is a close frame."""
        if self.opcode != OpCode.CLOSE or len(self.payload) < 2:
            return None
        
        code = struct.unpack('!H', self.payload[:2])[0]
        try:
            return CloseCode(code)
        except ValueError:
            return None
    
    def get_close_reason(self) -> str:
        """Get close reason if this is a close frame."""
        if self.opcode != OpCode.CLOSE or len(self.payload) < 2:
            return ""
        
        if len(self.payload) > 2:
            return self.payload[2:].decode('utf-8', errors='replace')
        return ""

class WSFrameBuilder:
    """Helper for building WebSocket frames."""
    
    @staticmethod
    def text_frame(text: str, fin: bool = True) -> WSFrame:
        """Create text frame."""
        return WSFrame(
            fin=fin,
            opcode=OpCode.TEXT,
            payload=text.encode('utf-8'),
            masked=True
        )
    
    @staticmethod
    def binary_frame(data: bytes, fin: bool = True) -> WSFrame:
        """Create binary frame."""
        return WSFrame(
            fin=fin,
            opcode=OpCode.BINARY,
            payload=data,
            masked=True
        )
    
    @staticmethod
    def ping_frame(payload: bytes = b'') -> WSFrame:
        """Create ping frame."""
        if len(payload) > 125:
            raise ValueError("Control frame payload cannot exceed 125 bytes")
        return WSFrame(
            fin=True,
            opcode=OpCode.PING,
            payload=payload,
            masked=True
        )
    
    @staticmethod
    def pong_frame(payload: bytes = b'') -> WSFrame:
        """Create pong frame."""
        if len(payload) > 125:
            raise ValueError("Control frame payload cannot exceed 125 bytes")
        return WSFrame(
            fin=True,
            opcode=OpCode.PONG,
            payload=payload,
            masked=True
        )
    
    @staticmethod
    def close_frame(code: CloseCode = CloseCode.NORMAL_CLOSURE, reason: str = '') -> WSFrame:
        """Create close frame."""
        payload = struct.pack('!H', code.value)
        if reason:
            payload += reason.encode('utf-8')
        
        if len(payload) > 125:
            raise ValueError("Control frame payload cannot exceed 125 bytes")
        
        return WSFrame(
            fin=True,
            opcode=OpCode.CLOSE,
            payload=payload,
            masked=True
        )