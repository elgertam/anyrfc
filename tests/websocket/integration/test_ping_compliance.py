"""Test ping functionality with RFC 6455 compliance."""
import pytest
import anyio
from anyrfc import WebSocketClient


@pytest.mark.integration
async def test_ping_with_valid_payload():
    """Test ping with valid payload size."""
    uri = "wss://echo.websocket.org/"
    
    async with WebSocketClient(uri) as ws:
        # Valid ping payload (≤ 125 bytes)
        await ws.ping(b"test ping")
        
        # Maximum size ping payload
        max_payload = b"x" * 125
        await ws.ping(max_payload)


@pytest.mark.integration  
async def test_ping_oversized_payload_rejected():
    """Test that oversized ping payload is rejected."""
    uri = "wss://echo.websocket.org/"
    
    async with WebSocketClient(uri) as ws:
        # Should raise error for oversized payload
        oversized_payload = b"x" * 126
        with pytest.raises(ValueError, match="cannot exceed 125 bytes"):
            await ws.ping(oversized_payload)


if __name__ == "__main__":
    anyio.run(test_ping_with_valid_payload())