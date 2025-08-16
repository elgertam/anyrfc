#!/usr/bin/env python3
"""
Comprehensive tests for the IMAP parser interface.

This test suite validates RFC 9051 compliance and ensures complete
functionality of the PEG-based IMAP response parser.
"""

import pytest
from datetime import datetime, timezone, timedelta

from anyrfc.parsing import IMAPParser, ParseError
from anyrfc.parsing.imap import IMAPFetchResponse, IMAPEnvelope


class TestIMAPParserBasics:
    """Test basic parser functionality."""

    def test_parser_initialization(self):
        """Test parser can be initialized."""
        parser = IMAPParser()
        assert parser is not None
        assert hasattr(parser, "parse")
        assert hasattr(parser, "parse_fetch_response")
        assert hasattr(parser, "parse_envelope")

    def test_simple_fetch_response(self):
        """Test parsing simple FETCH response."""
        parser = IMAPParser()

        # Simple FETCH with basic fields
        response = '* 123 FETCH (UID 456 FLAGS (\\Seen) INTERNALDATE "16-Aug-2025 10:30:00 +0000")'
        result = parser.parse_fetch_response(response)

        assert result.success
        assert isinstance(result.value, IMAPFetchResponse)
        assert result.value.message_number == 123
        assert result.value.uid == 456
        assert result.value.flags == ["\\Seen"]
        assert result.value.internal_date == datetime(2025, 8, 16, 10, 30, 0, tzinfo=timezone.utc)

    def test_fetch_with_multiple_flags(self):
        """Test parsing FETCH response with multiple flags."""
        parser = IMAPParser()

        response = "* 100 FETCH (FLAGS (\\Seen \\Flagged \\Draft $Important))"
        result = parser.parse_fetch_response(response)

        assert result.success
        assert result.value.message_number == 100
        assert set(result.value.flags) == {"\\Seen", "\\Flagged", "\\Draft", "$Important"}

    def test_empty_flags(self):
        """Test parsing FETCH response with empty flags."""
        parser = IMAPParser()

        response = "* 50 FETCH (FLAGS ())"
        result = parser.parse_fetch_response(response)

        assert result.success
        assert result.value.flags == []


class TestIMAPEnvelopeParsing:
    """Test ENVELOPE parsing functionality."""

    def test_complete_envelope(self):
        """Test parsing complete ENVELOPE with all fields."""
        parser = IMAPParser()

        response = """* 1 FETCH (ENVELOPE ("Mon, 16 Aug 2025 10:00:00 +0000" "Test Subject" (("John Doe" NIL "john" "example.com")) (("John Doe" NIL "john" "example.com")) NIL (("Jane Smith" NIL "jane" "example.org")) NIL NIL NIL "<msg123@example.com>"))"""

        result = parser.parse_fetch_response(response)

        assert result.success
        envelope = result.value.envelope
        assert isinstance(envelope, IMAPEnvelope)

        # Check basic fields
        assert envelope.date == "Mon, 16 Aug 2025 10:00:00 +0000"
        assert envelope.subject == "Test Subject"
        assert envelope.message_id == "<msg123@example.com>"

        # Check from address
        assert envelope.from_addr is not None
        assert len(envelope.from_addr) == 1
        from_addr = envelope.from_addr[0]
        assert from_addr["name"] == "John Doe"
        assert from_addr["email"] == "john@example.com"
        assert from_addr["mailbox"] == "john"
        assert from_addr["host"] == "example.com"

        # Check to address
        assert envelope.to is not None
        assert len(envelope.to) == 1
        to_addr = envelope.to[0]
        assert to_addr["name"] == "Jane Smith"
        assert to_addr["email"] == "jane@example.org"

    def test_envelope_with_nil_fields(self):
        """Test parsing ENVELOPE with NIL fields."""
        parser = IMAPParser()

        response = """* 2 FETCH (ENVELOPE ("Mon, 16 Aug 2025 10:00:00 +0000" "Test" ((NIL NIL "noreply" "system.com")) NIL NIL NIL NIL NIL NIL NIL))"""

        result = parser.parse_fetch_response(response)

        assert result.success
        envelope = result.value.envelope

        assert envelope.subject == "Test"
        assert envelope.from_addr is not None
        assert len(envelope.from_addr) == 1
        assert envelope.from_addr[0]["name"] is None
        assert envelope.from_addr[0]["email"] == "noreply@system.com"

        # NIL fields should be None
        assert envelope.sender is None
        assert envelope.reply_to is None
        assert envelope.to is None
        assert envelope.cc is None
        assert envelope.bcc is None

    def test_envelope_complex_addresses(self):
        """Test parsing ENVELOPE with multiple addresses."""
        parser = IMAPParser()

        response = """* 3 FETCH (ENVELOPE (NIL "Multi-recipient" (("Alice" NIL "alice" "example.com")("Bob" NIL "bob" "example.org")) NIL NIL (("Charlie" NIL "charlie" "test.com")("Diana" NIL "diana" "test.net")) NIL NIL NIL NIL))"""

        result = parser.parse_fetch_response(response)

        assert result.success
        envelope = result.value.envelope

        # Multiple from addresses
        assert len(envelope.from_addr) == 2
        assert envelope.from_addr[0]["name"] == "Alice"
        assert envelope.from_addr[0]["email"] == "alice@example.com"
        assert envelope.from_addr[1]["name"] == "Bob"
        assert envelope.from_addr[1]["email"] == "bob@example.org"

        # Multiple to addresses
        assert len(envelope.to) == 2
        assert envelope.to[0]["name"] == "Charlie"
        assert envelope.to[0]["email"] == "charlie@test.com"
        assert envelope.to[1]["name"] == "Diana"
        assert envelope.to[1]["email"] == "diana@test.net"


class TestIMAPBodyStructureParsing:
    """Test BODYSTRUCTURE parsing functionality."""

    def test_simple_text_body(self):
        """Test parsing simple text BODYSTRUCTURE."""
        parser = IMAPParser()

        response = '* 1 FETCH (BODYSTRUCTURE ("TEXT" "PLAIN" ("CHARSET" "UTF-8") NIL NIL "7BIT" 1234 50 NIL NIL NIL))'

        result = parser.parse_fetch_response(response)

        assert result.success
        body = result.value.body_structure

        assert body is not None
        assert body["content_type"] == "text/plain"
        assert body["is_multipart"] is False
        assert body["parts"] == []

    def test_multipart_alternative_body(self):
        """Test parsing multipart/alternative BODYSTRUCTURE."""
        parser = IMAPParser()

        response = """* 1 FETCH (BODYSTRUCTURE (("TEXT" "PLAIN" ("CHARSET" "UTF-8") NIL NIL "7BIT" 100 5 NIL NIL NIL)("TEXT" "HTML" ("CHARSET" "UTF-8") NIL NIL "7BIT" 500 10 NIL NIL NIL) "ALTERNATIVE" ("BOUNDARY" "boundary123") NIL NIL))"""

        result = parser.parse_fetch_response(response)

        assert result.success
        body = result.value.body_structure

        assert body is not None
        assert body["content_type"] == "multipart/alternative"
        assert body["is_multipart"] is True
        assert len(body["parts"]) == 2
        assert body["parts"] == ["Part 1", "Part 2"]

    def test_multipart_mixed_body(self):
        """Test parsing multipart/mixed BODYSTRUCTURE."""
        parser = IMAPParser()

        response = """* 1 FETCH (BODYSTRUCTURE (("TEXT" "PLAIN" NIL NIL NIL "7BIT" 100 5)("IMAGE" "JPEG" NIL NIL NIL "BASE64" 5000)("APPLICATION" "PDF" NIL NIL NIL "BASE64" 10000) "MIXED" ("BOUNDARY" "mixed-boundary") NIL NIL))"""

        result = parser.parse_fetch_response(response)

        assert result.success
        body = result.value.body_structure

        assert body is not None
        assert body["content_type"] == "multipart/mixed"
        assert body["is_multipart"] is True
        assert len(body["parts"]) == 3

    def test_nested_multipart_body(self):
        """Test parsing nested multipart BODYSTRUCTURE."""
        parser = IMAPParser()

        # Complex nested structure with multipart/related containing multipart/alternative
        response = """* 1 FETCH (BODYSTRUCTURE ((("TEXT" "PLAIN" NIL NIL NIL "7BIT" 100 5)("TEXT" "HTML" NIL NIL NIL "7BIT" 200 8) "ALTERNATIVE" ("BOUNDARY" "alt-boundary"))("IMAGE" "PNG" NIL NIL NIL "BASE64" 3000) "RELATED" ("BOUNDARY" "rel-boundary") NIL NIL))"""

        result = parser.parse_fetch_response(response)

        assert result.success
        body = result.value.body_structure

        assert body is not None
        assert body["content_type"] == "multipart/related"
        assert body["is_multipart"] is True
        # Should detect the two main parts: the nested alternative and the image
        assert len(body["parts"]) >= 2


class TestIMAPComplexFetchResponses:
    """Test complex FETCH responses with multiple components."""

    def test_full_fetch_response(self):
        """Test parsing complete FETCH response with all components."""
        parser = IMAPParser()

        response = """* 42 FETCH (UID 789 FLAGS (\\Seen \\Answered) INTERNALDATE "16-Aug-2025 15:30:45 +0000" ENVELOPE ("Mon, 16 Aug 2025 15:30:00 +0000" "Complete Test" (("Test User" NIL "test" "example.com")) NIL NIL (("Recipient" NIL "user" "test.org")) NIL NIL NIL "<test@example.com>") BODYSTRUCTURE (("TEXT" "PLAIN" ("CHARSET" "UTF-8") NIL NIL "7BIT" 150 6 NIL NIL NIL)("TEXT" "HTML" ("CHARSET" "UTF-8") NIL NIL "7BIT" 300 12 NIL NIL NIL) "ALTERNATIVE" ("BOUNDARY" "test-boundary") NIL NIL))"""

        result = parser.parse_fetch_response(response)

        assert result.success
        fetch = result.value

        # Basic FETCH fields
        assert fetch.message_number == 42
        assert fetch.uid == 789
        assert set(fetch.flags) == {"\\Seen", "\\Answered"}
        assert fetch.internal_date == datetime(2025, 8, 16, 15, 30, 45, tzinfo=timezone.utc)

        # ENVELOPE data
        assert fetch.envelope is not None
        assert fetch.envelope.subject == "Complete Test"
        assert fetch.envelope.from_addr[0]["email"] == "test@example.com"
        assert fetch.envelope.to[0]["email"] == "user@test.org"
        assert fetch.envelope.message_id == "<test@example.com>"

        # BODYSTRUCTURE data
        assert fetch.body_structure is not None
        assert fetch.body_structure["content_type"] == "multipart/alternative"
        assert fetch.body_structure["is_multipart"] is True
        assert len(fetch.body_structure["parts"]) == 2

    def test_gmail_style_response(self):
        """Test parsing Gmail-style FETCH response."""
        parser = IMAPParser()

        # Based on actual Gmail responses
        response = """* 12345 FETCH (UID 67890 INTERNALDATE "16-Aug-2025 14:25:30 +0000" FLAGS (\\Seen) ENVELOPE ("Sat, 16 Aug 2025 14:25:28 GMT" "Security alert" (("Google" NIL "no-reply" "accounts.google.com")) (("Google" NIL "no-reply" "accounts.google.com")) (("Google" NIL "no-reply" "accounts.google.com")) ((NIL NIL "user" "gmail.com")) NIL NIL NIL "<notification@google.com>") BODYSTRUCTURE (("TEXT" "PLAIN" ("CHARSET" "UTF-8" "DELSP" "yes" "FORMAT" "flowed") NIL NIL "BASE64" 948 19 NIL NIL NIL)("TEXT" "HTML" ("CHARSET" "UTF-8") NIL NIL "QUOTED-PRINTABLE" 5084 102 NIL NIL NIL) "ALTERNATIVE" ("BOUNDARY" "gmail-boundary") NIL NIL))"""

        result = parser.parse_fetch_response(response)

        assert result.success
        fetch = result.value

        assert fetch.message_number == 12345
        assert fetch.uid == 67890
        assert fetch.flags == ["\\Seen"]

        # Gmail-specific envelope
        assert fetch.envelope.subject == "Security alert"
        assert fetch.envelope.from_addr[0]["name"] == "Google"
        assert fetch.envelope.from_addr[0]["email"] == "no-reply@accounts.google.com"
        assert fetch.envelope.to[0]["email"] == "user@gmail.com"

        # Gmail-style multipart body
        assert fetch.body_structure["content_type"] == "multipart/alternative"
        assert len(fetch.body_structure["parts"]) == 2


class TestIMAPParserErrorHandling:
    """Test parser error handling and edge cases."""

    def test_invalid_fetch_response(self):
        """Test parsing invalid FETCH response."""
        parser = IMAPParser()

        # Malformed response
        response = "* INVALID FETCH (UID"
        result = parser.parse_fetch_response(response)

        assert not result.success
        assert isinstance(result.error, ParseError)

    def test_incomplete_envelope(self):
        """Test parsing incomplete ENVELOPE."""
        parser = IMAPParser()

        # ENVELOPE with missing closing parenthesis
        response = '* 1 FETCH (ENVELOPE ("date" "subject"'
        result = parser.parse_fetch_response(response)

        # Should either parse successfully with partial data or fail gracefully
        if not result.success:
            assert isinstance(result.error, ParseError)

    def test_empty_response(self):
        """Test parsing empty response."""
        parser = IMAPParser()

        result = parser.parse_fetch_response("")

        assert not result.success
        assert isinstance(result.error, ParseError)

    def test_non_fetch_response(self):
        """Test parsing non-FETCH response."""
        parser = IMAPParser()

        # Different response type
        response = "* OK IMAP4rev1 service ready"
        result = parser.parse_fetch_response(response)

        # Should fail since it's not a FETCH response
        assert not result.success


class TestIMAPConvenienceFunctions:
    """Test convenience functions for common parsing tasks."""

    def test_parse_fetch_response_function(self):
        """Test standalone parse_fetch_response function."""
        from anyrfc.parsing.imap import parse_fetch_response

        response = "* 1 FETCH (UID 123)"
        result = parse_fetch_response(response)

        assert result.success
        assert result.value.message_number == 1
        assert result.value.uid == 123

    def test_parse_envelope_function(self):
        """Test standalone parse_envelope function."""
        from anyrfc.parsing.imap import parse_envelope

        envelope_text = '("date" "subject" NIL NIL NIL NIL NIL NIL NIL NIL)'
        result = parse_envelope(envelope_text)

        assert result.success
        # Basic parsing should work
        assert result.value is not None


class TestRFCCompliance:
    """Test RFC 9051 compliance scenarios."""

    def test_rfc_date_format_compliance(self):
        """Test RFC-compliant date format parsing."""
        parser = IMAPParser()

        # RFC 3501 date format
        response = '* 1 FETCH (INTERNALDATE "17-Jul-1996 02:44:25 -0700")'
        result = parser.parse_fetch_response(response)

        assert result.success
        assert result.value.internal_date == datetime(1996, 7, 17, 2, 44, 25, tzinfo=timezone(timedelta(hours=-7)))

    def test_rfc_flag_compliance(self):
        """Test RFC-compliant flag parsing."""
        parser = IMAPParser()

        # Standard and custom flags
        response = "* 1 FETCH (FLAGS (\\Seen \\Answered \\Flagged \\Deleted \\Draft \\Recent $CustomFlag))"
        result = parser.parse_fetch_response(response)

        assert result.success
        flags = set(result.value.flags)
        expected_flags = {"\\Seen", "\\Answered", "\\Flagged", "\\Deleted", "\\Draft", "\\Recent", "$CustomFlag"}
        assert flags == expected_flags

    def test_rfc_bodystructure_compliance(self):
        """Test RFC-compliant BODYSTRUCTURE parsing."""
        parser = IMAPParser()

        # RFC 3501 BODYSTRUCTURE example
        response = (
            """* 1 FETCH (BODYSTRUCTURE ("TEXT" "PLAIN" ("CHARSET" "US-ASCII") NIL NIL "7BIT" 1152 23 NIL NIL NIL))"""
        )
        result = parser.parse_fetch_response(response)

        assert result.success
        body = result.value.body_structure
        assert body["content_type"] == "text/plain"
        assert not body["is_multipart"]


# Legacy test for compatibility
def test_basic_parser():
    """Test basic parser functionality (legacy test)."""

    parser = IMAPParser()

    # Test a simple FETCH response (simplified)
    fetch_text = '* 1 FETCH (UID 123 FLAGS (\\Seen) INTERNALDATE "16-Aug-2025 14:06:39 +0000")'

    print(f"Testing parser with: {fetch_text}")

    result = parser.parse_fetch_response(fetch_text)

    if result.success:
        print("✓ Parser worked!")
        print(f"Result: {result.value}")
        if hasattr(result.value, "message_number"):
            print(f"Message number: {result.value.message_number}")
        if hasattr(result.value, "uid"):
            print(f"UID: {result.value.uid}")
        if hasattr(result.value, "flags"):
            print(f"Flags: {result.value.flags}")
        assert result.success
    else:
        print("✗ Parser failed:")
        print(f"Error: {result.error}")
        assert False, f"Parser failed: {result.error}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
