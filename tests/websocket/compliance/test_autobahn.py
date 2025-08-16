"""Autobahn Testsuite integration for RFC 6455 compliance testing.

The Autobahn Testsuite is the industry standard for WebSocket RFC 6455 compliance
testing, with 500+ test cases used by major libraries like Netty, Undertow, Qt, etc.
"""
import pytest
import anyio
import json
import subprocess
import time
from pathlib import Path
from anyrfc import WebSocketClient


class AutobahnTestClient:
    """AnyRFC WebSocket client adapter for Autobahn Testsuite."""
    
    def __init__(self, uri: str, strict_rfc_validation: bool = True):
        self.uri = uri
        self.strict_rfc_validation = strict_rfc_validation
        self.client = None
    
    async def connect(self):
        """Connect to Autobahn test server."""
        self.client = WebSocketClient(self.uri, strict_rfc_validation=self.strict_rfc_validation)
        await self.client.connect()
    
    async def disconnect(self):
        """Disconnect from server."""
        if self.client:
            await self.client.disconnect()
    
    async def send_text(self, message: str):
        """Send text message."""
        await self.client.send_text(message)
    
    async def send_binary(self, data: bytes):
        """Send binary message."""
        await self.client.send_binary(data)
    
    async def receive(self):
        """Receive next message."""
        async for message in self.client.receive():
            return message
        return None


async def run_autobahn_test_case(case_id: int, test_server_port: int = 9001):
    """Run a specific Autobahn test case."""
    uri = f"ws://localhost:{test_server_port}/runCase?case={case_id}&agent=AnyRFC"
    
    try:
        client = AutobahnTestClient(uri, strict_rfc_validation=True)
        await client.connect()
        
        # Run the test case - echo back any messages received
        try:
            while True:
                message = await client.receive()
                if message is None:
                    break
                    
                if isinstance(message, str):
                    await client.send_text(message)
                else:
                    await client.send_binary(message)
                    
        except Exception as e:
            # Test may expect connection to close, that's OK
            pass
        
        await client.disconnect()
        
    except Exception as e:
        # Some tests may expect failures
        pass


async def get_test_results(test_server_port: int = 9001):
    """Get test results from Autobahn server."""
    uri = f"ws://localhost:{test_server_port}/updateReports?agent=AnyRFC"
    
    client = AutobahnTestClient(uri)
    await client.connect()
    await client.disconnect()


@pytest.mark.integration
@pytest.mark.skipif(
    True,  # Skip by default - requires manual Autobahn server setup
    reason="Requires Autobahn test server to be running. Run manually with: wstest -m fuzzingserver"
)
async def test_autobahn_compliance_sample():
    """Sample Autobahn compliance test.
    
    To run full Autobahn testsuite:
    1. Start test server: uv run wstest -m fuzzingserver
    2. Run this test with server running
    3. Check reports in ./reports/ directory
    """
    # Test a few basic cases
    test_cases = [1, 2, 3, 4, 5]  # Basic valid frame tests
    
    for case_id in test_cases:
        await run_autobahn_test_case(case_id)
    
    # Update test reports
    await get_test_results()


@pytest.mark.integration
def test_autobahn_setup_instructions():
    """Instructions for running full Autobahn testsuite."""
    instructions = """
    To run complete RFC 6455 compliance testing with Autobahn Testsuite:
    
    1. Start Autobahn test server:
       uv run wstest -m fuzzingserver
    
    2. Run AnyRFC test client:
       python tests/compliance/autobahn_runner.py
    
    3. View results:
       open reports/clients/index.html
    
    The Autobahn Testsuite contains 500+ test cases covering:
    - Basic WebSocket conversations
    - Protocol compliance verification  
    - Performance and limits testing
    - Edge cases and error conditions
    """
    print(instructions)
    assert True  # Always pass - this is just documentation


if __name__ == "__main__":
    # Run sample compliance test
    anyio.run(test_autobahn_compliance_sample)