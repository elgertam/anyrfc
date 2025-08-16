"""RFC 6455 test vectors and compliance tests.

This module contains specific test vectors from RFC 6455 and other compliance tests
that can run without external dependencies like the Autobahn server.
"""
import pytest
import anyio
from anyrfc.websocket.frames import WSFrame, OpCode, WSFrameBuilder, CloseCode
from anyrfc.websocket.handshake import WebSocketHandshake


class TestRFC6455Vectors:
    """Test vectors directly from RFC 6455 specification."""
    
    def test_sec_websocket_accept_calculation(self):
        """Test Sec-WebSocket-Accept calculation from RFC 6455 Section 4.2.2."""
        handshake = WebSocketHandshake()
        
        # Test vector from RFC 6455
        key = "dGhlIHNhbXBsZSBub25jZQ=="
        expected_accept = "s3pPLMBiTxaQ9kYGzzhZRbK+xOo="
        
        actual_accept = handshake.calculate_accept_key(key)
        assert actual_accept == expected_accept
    
    def test_frame_masking_rfc_example(self):
        """Test frame masking example from RFC 6455 Section 5.3."""
        # RFC 6455 example: "Hello" with mask [0x37, 0xfa, 0x21, 0x3d]
        payload = b"Hello"
        mask = bytes([0x37, 0xfa, 0x21, 0x3d])
        
        # Apply masking as per RFC
        masked_payload = bytearray()
        for i, byte in enumerate(payload):
            masked_payload.append(byte ^ mask[i % 4])
        
        expected_masked = bytes([0x7f, 0x9f, 0x4d, 0x51, 0x58])
        assert bytes(masked_payload) == expected_masked
    
    def test_text_frame_construction(self):
        """Test text frame construction per RFC 6455."""
        frame = WSFrameBuilder.text_frame("Hello")
        
        assert frame.fin is True
        assert frame.opcode == OpCode.TEXT
        assert frame.masked is True  # Client frames must be masked
        
        # Unmask the payload to check original data
        unmasked = WSFrame._apply_mask(frame.payload, frame.mask_key)
        assert unmasked == b"Hello"
    
    def test_binary_frame_construction(self):
        """Test binary frame construction per RFC 6455."""
        data = b"\x01\x02\x03\x04"
        frame = WSFrameBuilder.binary_frame(data)
        
        assert frame.fin is True
        assert frame.opcode == OpCode.BINARY
        assert frame.masked is True
        
        # Unmask the payload to check original data
        unmasked = WSFrame._apply_mask(frame.payload, frame.mask_key)
        assert unmasked == data
    
    def test_ping_frame_construction(self):
        """Test ping frame construction per RFC 6455."""
        payload = b"test ping"
        frame = WSFrameBuilder.ping_frame(payload)
        
        assert frame.fin is True
        assert frame.opcode == OpCode.PING
        assert frame.masked is True
        
        # Unmask the payload to check original data
        unmasked = WSFrame._apply_mask(frame.payload, frame.mask_key)
        assert unmasked == payload
        assert len(frame.payload) <= 125  # Control frames limited to 125 bytes
    
    def test_close_frame_construction(self):
        """Test close frame construction per RFC 6455."""
        from anyrfc.websocket.frames import CloseCode
        
        frame = WSFrameBuilder.close_frame(CloseCode.NORMAL_CLOSURE, "Goodbye")
        
        assert frame.fin is True
        assert frame.opcode == OpCode.CLOSE
        assert frame.masked is True
        
        # Close frame should contain code + reason
        assert len(frame.payload) >= 2  # At least the status code
    
    def test_frame_serialization_deserialization(self):
        """Test frame can be serialized and deserialized correctly."""
        original_frame = WSFrameBuilder.text_frame("Test message")
        
        # Serialize to bytes
        frame_bytes = original_frame.to_bytes()
        
        # Deserialize back
        reconstructed_frame = WSFrame.from_bytes(frame_bytes)
        
        assert reconstructed_frame.fin == original_frame.fin
        assert reconstructed_frame.opcode == original_frame.opcode
        assert reconstructed_frame.payload == original_frame.payload
    
    def test_invalid_frame_detection(self):
        """Test detection of invalid frames per RFC 6455."""
        # Test invalid opcode
        with pytest.raises(ValueError):
            WSFrame(
                fin=True,
                rsv1=False,
                rsv2=False, 
                rsv3=False,
                opcode=OpCode(15),  # Invalid opcode
                masked=True,
                payload=b"test",
                masking_key=b"\x00\x00\x00\x00"
            )
    
    def test_control_frame_size_limit(self):
        """Test control frames are limited to 125 bytes per RFC 6455."""
        # Should work with 125 bytes
        payload_125 = b"x" * 125
        frame = WSFrameBuilder.ping_frame(payload_125)
        assert len(frame.payload) == 125
        
        # Should raise error with 126 bytes (RFC 6455 Section 5.5)
        payload_126 = b"x" * 126
        with pytest.raises(ValueError, match="cannot exceed 125 bytes"):
            WSFrameBuilder.ping_frame(payload_126)
            
        # Test pong frame limit too
        with pytest.raises(ValueError, match="cannot exceed 125 bytes"):
            WSFrameBuilder.pong_frame(payload_126)
            
        # Test close frame limit (code + reason must be ≤ 125 bytes)
        long_reason = "x" * 124  # 124 + 2 bytes for code = 126 bytes
        with pytest.raises(ValueError, match="cannot exceed 125 bytes"):
            WSFrameBuilder.close_frame(CloseCode.NORMAL_CLOSURE, long_reason)


class TestWebSocketHandshake:
    """Test WebSocket handshake compliance."""
    
    def test_key_generation(self):
        """Test Sec-WebSocket-Key generation."""
        handshake = WebSocketHandshake()
        key = handshake.generate_key()
        
        # Should be base64 encoded 16 bytes
        import base64
        decoded = base64.b64decode(key)
        assert len(decoded) == 16
        
        # Should be different each time
        key2 = handshake.generate_key()
        assert key != key2
    
    def test_websocket_guid_constant(self):
        """Test WebSocket GUID constant from RFC 6455."""
        expected_guid = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
        assert WebSocketHandshake.WEBSOCKET_GUID == expected_guid


@pytest.mark.unit
class TestFrameValidation:
    """Test frame validation rules from RFC 6455."""
    
    def test_client_frame_masking_required(self):
        """Client frames MUST be masked per RFC 6455 Section 5.3."""
        frame = WSFrameBuilder.text_frame("test")
        assert frame.masked is True
        assert frame.mask_key is not None
        assert len(frame.mask_key) == 4
    
    def test_reserved_bits_must_be_zero(self):
        """Reserved bits must be 0 unless extension negotiated per RFC 6455."""
        frame = WSFrameBuilder.text_frame("test")
        assert frame.rsv1 is False
        assert frame.rsv2 is False  
        assert frame.rsv3 is False
    
    def test_continuation_frame_rules(self):
        """Test continuation frame rules per RFC 6455 Section 5.4."""
        # First frame should not be continuation
        first_frame = WSFrame(
            fin=False,  # Not final
            rsv1=False,
            rsv2=False,
            rsv3=False,
            opcode=OpCode.TEXT,  # Start with text
            masked=True,
            payload=b"Hello ",
            mask_key=b"\x00\x00\x00\x00"
        )
        
        # Continuation frame
        cont_frame = WSFrame(
            fin=True,  # Final
            rsv1=False,
            rsv2=False,
            rsv3=False,
            opcode=OpCode.CONTINUATION,  # Continuation
            masked=True,
            payload=b"World!",
            mask_key=b"\x00\x00\x00\x00"
        )
        
        assert first_frame.opcode == OpCode.TEXT
        assert cont_frame.opcode == OpCode.CONTINUATION


if __name__ == "__main__":
    pytest.main([__file__, "-v"])