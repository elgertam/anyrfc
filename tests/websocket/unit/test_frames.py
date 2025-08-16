"""Unit tests for WebSocket frame handling."""
import pytest
from anyrfc.websocket.frames import WSFrame, OpCode, WSFrameBuilder, CloseCode


@pytest.mark.unit
class TestWSFrame:
    """Test WebSocket frame construction and parsing."""
    
    def test_text_frame_creation(self):
        """Test text frame creation."""
        frame = WSFrameBuilder.text_frame("Hello")
        
        assert frame.fin is True
        assert frame.opcode == OpCode.TEXT
        assert frame.masked is True
        assert frame.mask_key is not None
        assert len(frame.mask_key) == 4
        
        # Verify unmasked payload
        unmasked = WSFrame._apply_mask(frame.payload, frame.mask_key)
        assert unmasked == b"Hello"
    
    def test_binary_frame_creation(self):
        """Test binary frame creation."""
        data = b"\x01\x02\x03\x04"
        frame = WSFrameBuilder.binary_frame(data)
        
        assert frame.fin is True
        assert frame.opcode == OpCode.BINARY
        assert frame.masked is True
        
        # Verify unmasked payload
        unmasked = WSFrame._apply_mask(frame.payload, frame.mask_key)
        assert unmasked == data
    
    def test_ping_frame_creation(self):
        """Test ping frame creation."""
        payload = b"ping test"
        frame = WSFrameBuilder.ping_frame(payload)
        
        assert frame.fin is True
        assert frame.opcode == OpCode.PING
        assert frame.masked is True
        
        # Verify unmasked payload
        unmasked = WSFrame._apply_mask(frame.payload, frame.mask_key)
        assert unmasked == payload
    
    def test_close_frame_creation(self):
        """Test close frame creation."""
        frame = WSFrameBuilder.close_frame(CloseCode.NORMAL_CLOSURE, "Goodbye")
        
        assert frame.fin is True
        assert frame.opcode == OpCode.CLOSE
        assert frame.masked is True
        
        # Close frame should have code + reason
        assert len(frame.payload) >= 2  # At least the status code
    
    def test_frame_serialization_roundtrip(self):
        """Test frame serialization and deserialization."""
        original = WSFrameBuilder.text_frame("Test message")
        
        # Serialize to bytes
        frame_bytes = original.to_bytes()
        assert isinstance(frame_bytes, bytes)
        assert len(frame_bytes) > 0
        
        # Deserialize back
        reconstructed = WSFrame.from_bytes(frame_bytes)
        
        # Verify frame structure matches
        assert reconstructed.fin == original.fin
        assert reconstructed.opcode == original.opcode
        assert reconstructed.masked == original.masked
        assert reconstructed.payload == original.payload
        assert reconstructed.mask_key == original.mask_key
    
    def test_control_frame_size_validation(self):
        """Test control frame size limits."""
        # Valid 125-byte payload
        max_payload = b"x" * 125
        frame = WSFrameBuilder.ping_frame(max_payload)
        assert len(frame.payload) == 125
        
        # Invalid 126-byte payload
        oversized_payload = b"x" * 126
        with pytest.raises(ValueError, match="cannot exceed 125 bytes"):
            WSFrameBuilder.ping_frame(oversized_payload)
        
        # Test pong frame validation too
        with pytest.raises(ValueError, match="cannot exceed 125 bytes"):
            WSFrameBuilder.pong_frame(oversized_payload)
    
    def test_masking_operation(self):
        """Test frame masking operation."""
        # Test with known values
        payload = b"Hello"
        mask_key = b"\x37\xfa\x21\x3d"
        
        # Apply masking
        masked = WSFrame._apply_mask(payload, mask_key)
        
        # Apply masking again to unmask
        unmasked = WSFrame._apply_mask(masked, mask_key)
        
        # Should get original payload back
        assert unmasked == payload
    
    def test_reserved_bits_default(self):
        """Test reserved bits are False by default."""
        frame = WSFrameBuilder.text_frame("test")
        
        assert frame.rsv1 is False
        assert frame.rsv2 is False
        assert frame.rsv3 is False


@pytest.mark.unit 
class TestOpCode:
    """Test WebSocket opcodes."""
    
    def test_opcode_values(self):
        """Test opcode enum values match RFC 6455."""
        assert OpCode.CONTINUATION.value == 0x0
        assert OpCode.TEXT.value == 0x1
        assert OpCode.BINARY.value == 0x2
        assert OpCode.CLOSE.value == 0x8
        assert OpCode.PING.value == 0x9
        assert OpCode.PONG.value == 0xA


@pytest.mark.unit
class TestCloseCode:
    """Test WebSocket close codes."""
    
    def test_close_code_values(self):
        """Test close code enum values match RFC 6455."""
        assert CloseCode.NORMAL_CLOSURE.value == 1000
        assert CloseCode.GOING_AWAY.value == 1001
        assert CloseCode.PROTOCOL_ERROR.value == 1002


if __name__ == "__main__":
    pytest.main([__file__, "-v"])