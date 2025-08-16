#!/usr/bin/env python3
"""
Basic test of the new IMAP parser.
"""

import pytest
from anyrfc.parsing import IMAPParser, ParseError

def test_basic_parser():
    """Test basic parser functionality."""
    
    parser = IMAPParser()
    
    # Test a simple FETCH response (simplified)
    fetch_text = '* 1 FETCH (UID 123 FLAGS (\\Seen) INTERNALDATE "16-Aug-2025 14:06:39 +0000")'
    
    print(f"Testing parser with: {fetch_text}")
    
    result = parser.parse_fetch_response(fetch_text)
    
    if result.success:
        print("✓ Parser worked!")
        print(f"Result: {result.value}")
        if hasattr(result.value, 'message_number'):
            print(f"Message number: {result.value.message_number}")
        if hasattr(result.value, 'uid'):
            print(f"UID: {result.value.uid}")
        if hasattr(result.value, 'flags'):
            print(f"Flags: {result.value.flags}")
    else:
        print("✗ Parser failed:")
        print(f"Error: {result.error}")

if __name__ == "__main__":
    test_basic_parser()