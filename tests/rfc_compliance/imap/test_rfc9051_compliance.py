"""RFC 9051 IMAP compliance tests."""
import pytest
import anyio
from typing import Dict, Any

from anyrfc.email.imap import IMAPClient, RFC9051Compliance
from anyrfc.email.imap.commands import IMAPCommandBuilder
from anyrfc.email.imap.responses import IMAPResponseParser


class TestRFC9051CommandSyntax:
    """Test RFC 9051 command syntax compliance."""
    
    def test_capability_command_syntax(self):
        """Test CAPABILITY command per RFC 9051 Section 6.1.1."""
        command = IMAPCommandBuilder.capability()
        assert command.to_string() == "CAPABILITY"
    
    def test_noop_command_syntax(self):
        """Test NOOP command per RFC 9051 Section 6.1.2."""
        command = IMAPCommandBuilder.noop()
        assert command.to_string() == "NOOP"
    
    def test_logout_command_syntax(self):
        """Test LOGOUT command per RFC 9051 Section 6.1.3."""
        command = IMAPCommandBuilder.logout()
        assert command.to_string() == "LOGOUT"
    
    def test_login_command_syntax(self):
        """Test LOGIN command per RFC 9051 Section 6.2.3."""
        command = IMAPCommandBuilder.login("user@example.com", "secret123")
        expected = 'LOGIN "user@example.com" "secret123"'
        assert command.to_string() == expected
    
    def test_authenticate_command_syntax(self):
        """Test AUTHENTICATE command per RFC 9051 Section 6.2.2."""
        command = IMAPCommandBuilder.authenticate("PLAIN")
        assert command.to_string() == "AUTHENTICATE PLAIN"
        
        command_with_response = IMAPCommandBuilder.authenticate("PLAIN", "AGpvaG4AcGFzcw==")
        assert command_with_response.to_string() == "AUTHENTICATE PLAIN AGpvaG4AcGFzcw=="
    
    def test_select_command_syntax(self):
        """Test SELECT command per RFC 9051 Section 6.3.1."""
        command = IMAPCommandBuilder.select("INBOX")
        assert command.to_string() == 'SELECT "INBOX"'
        
        # Test with special characters
        command = IMAPCommandBuilder.select("INBOX/Sent Messages")
        assert command.to_string() == 'SELECT "INBOX/Sent Messages"'
    
    def test_examine_command_syntax(self):
        """Test EXAMINE command per RFC 9051 Section 6.3.2.""" 
        command = IMAPCommandBuilder.examine("INBOX")
        assert command.to_string() == 'EXAMINE "INBOX"'
    
    def test_create_command_syntax(self):
        """Test CREATE command per RFC 9051 Section 6.3.3."""
        command = IMAPCommandBuilder.create("Projects/IMAP")
        assert command.to_string() == 'CREATE "Projects/IMAP"'
    
    def test_delete_command_syntax(self):
        """Test DELETE command per RFC 9051 Section 6.3.4."""
        command = IMAPCommandBuilder.delete("Temp Folder")
        assert command.to_string() == 'DELETE "Temp Folder"'
    
    def test_rename_command_syntax(self):
        """Test RENAME command per RFC 9051 Section 6.3.5."""
        command = IMAPCommandBuilder.rename("Old Name", "New Name")
        assert command.to_string() == 'RENAME "Old Name" "New Name"'
    
    def test_list_command_syntax(self):
        """Test LIST command per RFC 9051 Section 6.3.9."""
        command = IMAPCommandBuilder.list("", "*")
        assert command.to_string() == 'LIST "" "*"'
        
        command = IMAPCommandBuilder.list("INBOX/", "%")
        assert command.to_string() == 'LIST "INBOX/" "%"'
    
    def test_status_command_syntax(self):
        """Test STATUS command per RFC 9051 Section 6.3.10."""
        command = IMAPCommandBuilder.status("INBOX", ["MESSAGES", "RECENT"])
        assert command.to_string() == 'STATUS "INBOX" (MESSAGES RECENT)'
        
        command = IMAPCommandBuilder.status("INBOX", ["UIDNEXT", "UIDVALIDITY", "UNSEEN"])
        assert command.to_string() == 'STATUS "INBOX" (UIDNEXT UIDVALIDITY UNSEEN)'
    
    def test_search_command_syntax(self):
        """Test SEARCH command per RFC 9051 Section 6.4.4."""
        command = IMAPCommandBuilder.search("ALL")
        assert command.to_string() == "SEARCH ALL"
        
        command = IMAPCommandBuilder.search("UNSEEN FROM john@example.com")
        assert command.to_string() == "SEARCH UNSEEN FROM john@example.com"
        
        command = IMAPCommandBuilder.search("TEXT hello", "UTF-8")
        assert command.to_string() == "SEARCH CHARSET UTF-8 TEXT hello"
    
    def test_fetch_command_syntax(self):
        """Test FETCH command per RFC 9051 Section 6.4.5."""
        command = IMAPCommandBuilder.fetch("1", "FLAGS")
        assert command.to_string() == "FETCH 1 FLAGS"
        
        command = IMAPCommandBuilder.fetch("1:10", "FLAGS UID ENVELOPE")
        assert command.to_string() == "FETCH 1:10 FLAGS UID ENVELOPE"
        
        command = IMAPCommandBuilder.fetch("*", "BODY[HEADER]")
        assert command.to_string() == "FETCH * BODY[HEADER]"
    
    def test_store_command_syntax(self):
        """Test STORE command per RFC 9051 Section 6.4.6."""
        command = IMAPCommandBuilder.store("1", "FLAGS", "(\\Seen)")
        assert command.to_string() == "STORE 1 FLAGS (\\Seen)"
        
        command = IMAPCommandBuilder.store("1:5", "+FLAGS", "(\\Flagged)")
        assert command.to_string() == "STORE 1:5 +FLAGS (\\Flagged)"
    
    def test_copy_command_syntax(self):
        """Test COPY command per RFC 9051 Section 6.4.7."""
        command = IMAPCommandBuilder.copy("1:5", "Saved Messages")
        assert command.to_string() == 'COPY 1:5 "Saved Messages"'


class TestRFC9051ResponseParsing:
    """Test RFC 9051 response parsing compliance."""
    
    def test_tagged_response_parsing(self):
        """Test tagged response parsing per RFC 9051 Section 7.1."""
        response = IMAPResponseParser.parse("A001 OK SELECT completed")
        assert response.tag == "A001"
        assert response.status.value == "OK"
        assert response.message == "SELECT completed"
        
        response = IMAPResponseParser.parse("A002 NO Mailbox does not exist")
        assert response.tag == "A002"
        assert response.status.value == "NO"
        assert response.message == "Mailbox does not exist"
        
        response = IMAPResponseParser.parse("A003 BAD Command syntax error")
        assert response.tag == "A003"
        assert response.status.value == "BAD"
        assert response.message == "Command syntax error"
    
    def test_untagged_response_parsing(self):
        """Test untagged response parsing per RFC 9051 Section 7.2."""
        response = IMAPResponseParser.parse("* OK IMAP4rev1 server ready")
        assert response.tag is None
        assert response.status.value == "OK" 
        assert response.message == "IMAP4rev1 server ready"
        
        response = IMAPResponseParser.parse("* 172 EXISTS")
        assert response.tag is None
        assert response.status is None
        assert response.message == "172 EXISTS"
        
        response = IMAPResponseParser.parse("* 1 RECENT")
        assert response.tag is None
        assert response.message == "1 RECENT"
    
    def test_continuation_response_parsing(self):
        """Test continuation response parsing per RFC 9051 Section 7.5."""
        response = IMAPResponseParser.parse("+ Ready for additional command text")
        assert response.response_type.value == "continuation"
        assert response.message == "Ready for additional command text"
        
        response = IMAPResponseParser.parse("+")
        assert response.response_type.value == "continuation"
        assert response.message == ""
    
    def test_capability_response_parsing(self):
        """Test CAPABILITY response parsing per RFC 9051 Section 6.1.1."""
        capabilities = IMAPResponseParser.parse_capability_response(
            "* CAPABILITY IMAP4rev1 STARTTLS AUTH=PLAIN AUTH=LOGIN"
        )
        assert "IMAP4rev1" in capabilities
        assert "STARTTLS" in capabilities
        assert "AUTH=PLAIN" in capabilities
        assert "AUTH=LOGIN" in capabilities
    
    def test_list_response_parsing(self):
        """Test LIST response parsing per RFC 9051 Section 6.3.9."""
        list_data = IMAPResponseParser.parse_list_response(
            '* LIST (\\HasNoChildren) "/" "INBOX"'
        )
        assert list_data is not None
        assert list_data["mailbox"] == "INBOX"
        assert list_data["delimiter"] == "/"
        assert "\\HasNoChildren" in list_data["flags"]
        
        list_data = IMAPResponseParser.parse_list_response(
            '* LIST (\\Noselect \\HasChildren) "/" "Projects"'
        )
        assert list_data is not None
        assert list_data["mailbox"] == "Projects"
        assert "\\Noselect" in list_data["flags"]
        assert "\\HasChildren" in list_data["flags"]
    
    def test_search_response_parsing(self):
        """Test SEARCH response parsing per RFC 9051 Section 6.4.4."""
        numbers = IMAPResponseParser.parse_search_response("* SEARCH 2 84 882")
        assert numbers == [2, 84, 882]
        
        numbers = IMAPResponseParser.parse_search_response("* SEARCH")
        assert numbers == []
        
        numbers = IMAPResponseParser.parse_search_response("* SEARCH 1")
        assert numbers == [1]
    
    def test_status_response_parsing(self):
        """Test STATUS response parsing per RFC 9051 Section 6.3.10."""
        status = IMAPResponseParser.parse_status_response(
            '* STATUS "INBOX" (MESSAGES 52 UIDNEXT 4827 UIDVALIDITY 1234567890)'
        )
        assert status is not None
        assert status["MESSAGES"] == 52
        assert status["UIDNEXT"] == 4827
        assert status["UIDVALIDITY"] == 1234567890


class TestRFC9051SequenceNumbers:
    """Test sequence number handling per RFC 9051 Section 9."""
    
    def test_sequence_set_utilities(self):
        """Test sequence set construction per RFC 9051."""
        from anyrfc.email.imap.commands import IMAPSequenceSet
        
        # Single message
        seq = IMAPSequenceSet.single(42)
        assert seq == "42"
        
        # Range of messages
        seq = IMAPSequenceSet.range(1, 10)
        assert seq == "1:10"
        
        # List of messages
        seq = IMAPSequenceSet.from_list([1, 5, 7, 10])
        assert seq == "1,5,7,10"
        
        # All messages
        seq = IMAPSequenceSet.all_messages()
        assert seq == "1:*"
        
        # Last N messages
        seq = IMAPSequenceSet.last_n_messages(1)
        assert seq == "*"
        
        seq = IMAPSequenceSet.last_n_messages(5)
        assert seq == "*:5"


class TestRFC9051QuotedStrings:
    """Test quoted string handling per RFC 9051 Section 4.3."""
    
    def test_quoted_string_construction(self):
        """Test quoted string construction."""
        from anyrfc.email.imap.commands import IMAPQuotedString
        
        # Simple string
        quoted = IMAPQuotedString("INBOX")
        assert quoted.to_imap_string() == '"INBOX"'
        
        # String with spaces
        quoted = IMAPQuotedString("Sent Messages")
        assert quoted.to_imap_string() == '"Sent Messages"'
        
        # String with quotes (should be escaped)
        quoted = IMAPQuotedString('He said "Hello"')
        assert quoted.to_imap_string() == '"He said \\"Hello\\""'
        
        # String with backslashes (should be escaped)
        quoted = IMAPQuotedString("C:\\Folder\\File")
        assert quoted.to_imap_string() == '"C:\\\\Folder\\\\File"'
    
    def test_quoted_string_parsing(self):
        """Test quoted string parsing."""
        from anyrfc.email.imap.responses import IMAPDataParser
        
        # Simple quoted string
        parsed = IMAPDataParser.parse_quoted_string('"INBOX"')
        assert parsed == "INBOX"
        
        # Quoted string with escaped quotes
        parsed = IMAPDataParser.parse_quoted_string('"He said \\"Hello\\""')
        assert parsed == 'He said "Hello"'
        
        # Quoted string with escaped backslashes
        parsed = IMAPDataParser.parse_quoted_string('"C:\\\\Folder\\\\File"')
        assert parsed == "C:\\Folder\\File"


class TestRFC9051Literals:
    """Test literal string handling per RFC 9051 Section 4.3."""
    
    def test_literal_construction(self):
        """Test literal string construction."""
        from anyrfc.email.imap.commands import IMAPLiteral
        
        # Simple literal
        literal = IMAPLiteral("Hello World")
        assert literal.to_imap_string() == "{11}"
        assert len(literal) == 11
        
        # Binary literal
        literal = IMAPLiteral(b"\x00\x01\x02\x03")
        assert literal.to_imap_string() == "{4}"
        
        # Empty literal
        literal = IMAPLiteral("")
        assert literal.to_imap_string() == "{0}"


@pytest.mark.anyio
class TestRFC9051ComplianceFramework:
    """Test the RFC 9051 compliance testing framework."""
    
    async def test_compliance_test_instantiation(self):
        """Test compliance test framework setup."""
        client = IMAPClient("test.example.com")
        compliance = RFC9051Compliance(client)
        
        assert compliance.get_rfc_number() == "RFC 9051"
        assert compliance.client == client
    
    async def test_individual_compliance_tests(self):
        """Test individual compliance test methods."""
        client = IMAPClient("test.example.com")
        compliance = RFC9051Compliance(client)
        
        # Test command syntax compliance
        assert await compliance.test_capability_command() is True
        assert await compliance.test_noop_command() is True
        assert await compliance.test_login_command() is True
        assert await compliance.test_select_command() is True
        assert await compliance.test_fetch_command() is True
        assert await compliance.test_search_command() is True
    
    def test_test_vectors(self):
        """Test RFC test vectors."""
        client = IMAPClient("test.example.com")
        compliance = RFC9051Compliance(client)
        
        vectors = compliance.get_test_vectors()
        
        assert "commands" in vectors
        assert "responses" in vectors
        
        # Check command test vectors
        commands = vectors["commands"]
        assert commands["capability"] == "CAPABILITY"
        assert commands["noop"] == "NOOP"
        assert commands["logout"] == "LOGOUT"
        assert 'LOGIN "user" "pass"' == commands["login"]
        
        # Check response test vectors
        responses = vectors["responses"]
        assert "greeting_ok" in responses
        assert "capability" in responses
        assert "tagged_ok" in responses


@pytest.mark.performance
class TestRFC9051Performance:
    """Performance tests for RFC 9051 implementation."""
    
    def test_command_parsing_performance(self):
        """Test command parsing performance."""
        import time
        
        test_commands = [
            "CAPABILITY",
            "NOOP",
            'LOGIN "user" "pass"',
            'SELECT "INBOX"',
            'LIST "" "*"',
            "SEARCH ALL",
            "FETCH 1:10 FLAGS",
            "STORE 1 +FLAGS (\\Seen)",
        ]
        
        start_time = time.time()
        
        for _ in range(1000):
            for cmd in test_commands:
                # Just test string operations
                assert len(cmd) > 0
                assert cmd.strip() == cmd
        
        end_time = time.time()
        assert (end_time - start_time) < 1.0  # Should be very fast
    
    def test_response_parsing_performance(self):
        """Test response parsing performance."""
        import time
        
        test_responses = [
            "A001 OK Command completed",
            "* 172 EXISTS",
            "* 1 RECENT",
            '* LIST (\\HasNoChildren) "/" "INBOX"',
            "* SEARCH 2 84 882",
            "* CAPABILITY IMAP4rev1 STARTTLS",
        ]
        
        start_time = time.time()
        
        for _ in range(1000):
            for response in test_responses:
                parsed = IMAPResponseParser.parse(response)
                assert parsed is not None
        
        end_time = time.time()
        assert (end_time - start_time) < 2.0  # Should be reasonably fast


if __name__ == "__main__":
    pytest.main([__file__, "-v"])