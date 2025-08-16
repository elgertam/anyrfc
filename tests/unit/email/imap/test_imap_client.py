"""Unit tests for IMAP client."""
import pytest
import anyio
from unittest.mock import Mock, AsyncMock
from typing import Dict, Any

from anyrfc.email.imap import (
    IMAPClient, IMAPState, IMAPCommandBuilder, 
    MailboxManager, MessageManager, ExtensionManager
)
from anyrfc.email.imap.responses import IMAPStatus, IMAPResponse, IMAPResponseType
from anyrfc.core.types import ProtocolState


class MockStream:
    """Mock AnyIO stream for testing."""
    
    def __init__(self):
        self.sent_data = []
        self.responses = []
        self.response_index = 0
    
    async def send(self, data: bytes) -> None:
        self.sent_data.append(data)
    
    async def receive(self, max_bytes: int) -> bytes:
        if self.response_index < len(self.responses):
            response = self.responses[self.response_index]
            self.response_index += 1
            return response
        return b''
    
    async def aclose(self) -> None:
        pass
    
    def add_response(self, response: str) -> None:
        """Add response to be returned by receive."""
        self.responses.append(response.encode('utf-8') + b'\r\n')


@pytest.fixture
def mock_stream():
    """Provide mock stream for testing."""
    return MockStream()


@pytest.fixture
def imap_client():
    """Provide IMAP client for testing."""
    return IMAPClient("imap.example.com", 993, use_tls=True)


class TestIMAPClient:
    """Test IMAP client functionality."""
    
    def test_client_initialization(self, imap_client):
        """Test client initialization."""
        assert imap_client.hostname == "imap.example.com"
        assert imap_client.port == 993
        assert imap_client.use_tls is True
        assert imap_client.state == ProtocolState.DISCONNECTED
        assert imap_client.imap_state == IMAPState.NOT_AUTHENTICATED
        assert isinstance(imap_client.mailbox, MailboxManager)
        assert isinstance(imap_client.messages, MessageManager)
        assert isinstance(imap_client.extensions, ExtensionManager)
    
    def test_rfc_compliance_info(self, imap_client):
        """Test RFC compliance information."""
        assert imap_client.get_rfc_number() == "RFC 9051"
        test_vectors = imap_client.get_test_vectors()
        assert "commands" in test_vectors
        assert "responses" in test_vectors
    
    def test_capability_check(self, imap_client):
        """Test capability checking."""
        imap_client._capabilities = {"IMAP4rev1", "STARTTLS", "IDLE"}
        
        assert imap_client.has_capability("IMAP4rev1")
        assert imap_client.has_capability("IDLE")
        assert not imap_client.has_capability("NONEXISTENT")
        
        capabilities = imap_client.capabilities
        assert "IMAP4rev1" in capabilities
        assert "IDLE" in capabilities
    
    @pytest.mark.anyio
    async def test_state_transitions(self, imap_client):
        """Test protocol state transitions."""
        assert imap_client.state == ProtocolState.DISCONNECTED
        
        await imap_client._transition_state(ProtocolState.CONNECTING)
        assert imap_client.state == ProtocolState.CONNECTING
        
        await imap_client._transition_state(ProtocolState.CONNECTED)
        assert imap_client.state == ProtocolState.CONNECTED


class TestIMAPCommands:
    """Test IMAP command building."""
    
    def test_capability_command(self):
        """Test CAPABILITY command building."""
        command = IMAPCommandBuilder.capability()
        assert command.to_string() == "CAPABILITY"
    
    def test_login_command(self):
        """Test LOGIN command building."""
        command = IMAPCommandBuilder.login("testuser", "testpass")
        assert command.to_string() == 'LOGIN "testuser" "testpass"'
    
    def test_select_command(self):
        """Test SELECT command building."""
        command = IMAPCommandBuilder.select("INBOX")
        assert command.to_string() == 'SELECT "INBOX"'
    
    def test_list_command(self):
        """Test LIST command building."""
        command = IMAPCommandBuilder.list("", "*")
        assert command.to_string() == 'LIST "" "*"'
    
    def test_fetch_command(self):
        """Test FETCH command building."""
        command = IMAPCommandBuilder.fetch("1:10", "FLAGS UID")
        assert command.to_string() == "FETCH 1:10 FLAGS UID"
    
    def test_search_command(self):
        """Test SEARCH command building."""
        command = IMAPCommandBuilder.search("UNSEEN")
        assert command.to_string() == "SEARCH UNSEEN"
    
    def test_store_command(self):
        """Test STORE command building."""
        command = IMAPCommandBuilder.store("1", "FLAGS", "(\\Seen)")
        assert command.to_string() == "STORE 1 FLAGS (\\Seen)"


class TestIMAPExtensions:
    """Test IMAP extensions."""
    
    def test_extension_manager(self, imap_client):
        """Test extension manager."""
        assert imap_client.extensions.get_extension("IDLE") is not None
        assert imap_client.extensions.get_extension("SORT") is not None
        assert imap_client.extensions.get_extension("NONEXISTENT") is None
    
    def test_idle_extension(self, imap_client):
        """Test IDLE extension."""
        idle_ext = imap_client.extensions.get_extension("IDLE")
        assert idle_ext.get_capability_name() == "IDLE"
        assert idle_ext.get_rfc_number() == "RFC 2177"
    
    def test_sort_extension(self, imap_client):
        """Test SORT extension."""
        sort_ext = imap_client.extensions.get_extension("SORT")
        assert sort_ext.get_capability_name() == "SORT"
        assert sort_ext.get_rfc_number() == "RFC 5256"


class TestMailboxManager:
    """Test mailbox management."""
    
    def test_mailbox_manager_init(self, imap_client):
        """Test mailbox manager initialization."""
        assert imap_client.mailbox._mailbox_cache == {}
        assert imap_client.mailbox._hierarchy_delimiter is None
    
    def test_mailbox_hierarchy_utils(self, imap_client):
        """Test mailbox hierarchy utilities."""
        imap_client.mailbox._hierarchy_delimiter = "/"
        
        parent = imap_client.mailbox.get_parent_mailbox("INBOX/Sent")
        assert parent == "INBOX"
        
        parent = imap_client.mailbox.get_parent_mailbox("INBOX")
        assert parent is None


class TestMessageManager:
    """Test message management."""
    
    def test_message_manager_init(self, imap_client):
        """Test message manager initialization."""
        assert imap_client.messages.client == imap_client
    
    def test_message_flag_operations(self, imap_client):
        """Test message flag utilities."""
        from anyrfc.email.imap.messages import MessageInfo, MessageFlag
        
        info = MessageInfo(message_number=1, flags={MessageFlag.SEEN.value, MessageFlag.FLAGGED.value})
        
        assert info.is_seen
        assert info.is_flagged
        assert not info.is_answered
        assert not info.is_deleted


@pytest.mark.anyio
class TestIMAPCompliance:
    """Test RFC 9051 compliance."""
    
    async def test_compliance_tests(self, imap_client):
        """Test compliance test framework."""
        from anyrfc.email.imap.compliance import RFC9051Compliance
        
        compliance = RFC9051Compliance(imap_client)
        
        # Test individual compliance checks
        assert await compliance.test_capability_command() is True
        assert await compliance.test_noop_command() is True
        assert await compliance.test_login_command() is True
        assert await compliance.test_select_command() is True
        
        # Test compliance summary
        summary = compliance.get_compliance_summary()
        assert "total_tests" in summary
        assert "passed_tests" in summary
        assert "failed_tests" in summary
        assert "compliance_percentage" in summary


@pytest.mark.integration
class TestIMAPIntegration:
    """Integration tests for IMAP client."""
    
    @pytest.mark.anyio
    async def test_mock_connection_flow(self, imap_client, mock_stream):
        """Test connection flow with mock stream."""
        # Mock the connection
        imap_client._stream = mock_stream
        
        # Add mock greeting response
        mock_stream.add_response("* OK IMAP4rev1 server ready")
        mock_stream.add_response("* CAPABILITY IMAP4rev1 STARTTLS AUTH=PLAIN")
        mock_stream.add_response("A0001 OK CAPABILITY completed")
        
        # This would normally test the full flow, but we'll keep it simple
        # since we need to mock the entire protocol
        assert imap_client._stream is not None
    
    @pytest.mark.anyio
    async def test_command_response_cycle(self, imap_client, mock_stream):
        """Test command/response cycle."""
        imap_client._stream = mock_stream
        
        # Mock NOOP command response
        mock_stream.add_response("A0001 OK NOOP completed")
        
        # This would test sending a command and receiving response
        # but needs more comprehensive mocking for the protocol
        assert True  # Placeholder


# Performance tests
@pytest.mark.performance
class TestIMAPPerformance:
    """Performance tests for IMAP implementation."""
    
    def test_command_building_performance(self):
        """Test command building performance."""
        import time
        
        start_time = time.time()
        
        # Build many commands
        for i in range(1000):
            IMAPCommandBuilder.fetch(f"1:{i}", "FLAGS UID")
            IMAPCommandBuilder.search(f"SUBJECT test{i}")
            IMAPCommandBuilder.select(f"Mailbox{i}")
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should be very fast (under 1 second for 3000 commands)
        assert duration < 1.0
    
    def test_response_parsing_performance(self):
        """Test response parsing performance."""
        from anyrfc.email.imap.responses import IMAPResponseParser
        import time
        
        # Sample responses
        responses = [
            "A001 OK SELECT completed",
            "* 172 EXISTS",
            "* 1 RECENT", 
            '* LIST (\\HasNoChildren) "/" "INBOX"',
            "* SEARCH 2 84 882",
            '* 12 FETCH (FLAGS (\\Seen) UID 4827)',
        ]
        
        start_time = time.time()
        
        # Parse many responses
        for _ in range(1000):
            for response in responses:
                IMAPResponseParser.parse(response)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should be fast (under 2 seconds for 6000 parses)
        assert duration < 2.0


if __name__ == "__main__":
    pytest.main([__file__])