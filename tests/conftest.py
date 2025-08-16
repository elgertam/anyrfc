"""Pytest configuration for AnyIO RFC clients."""
import pytest
import anyio
from typing import AsyncGenerator

@pytest.fixture
def anyio_backend():
    """Configure AnyIO backend for tests."""
    return "asyncio"

@pytest.fixture
async def websocket_test_uri():
    """Provide WebSocket test URI."""
    return "wss://echo.websocket.org/"

# Parametrized tests for multiple server implementations
@pytest.fixture(params=[
    "wss://echo.websocket.org/",
    "ws://echo.websocket.org/",
])
def websocket_test_servers(request):
    """Provide multiple WebSocket servers for interop testing."""
    return request.param

@pytest.fixture
def mock_websocket_server():
    """Provide mock WebSocket server for testing."""
    # This would be implemented with a proper mock server
    return None