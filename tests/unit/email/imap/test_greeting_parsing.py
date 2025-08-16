#!/usr/bin/env python3
"""
Test IMAP greeting parsing.
"""
import pytest
from anyrfc.email.imap.responses import IMAPResponseParser

def test_greeting_parsing():
    """Test parsing of Gmail IMAP greeting."""
    
    # This is the actual greeting we received from Gmail
    greeting_line = "* OK Gimap ready for requests from 204.111.238.10 d75a77b69052e-4b10507e313mb1355161611cf"
    
    print(f"Parsing greeting: {greeting_line}")
    
    try:
        response = IMAPResponseParser.parse(greeting_line)
        
        print(f"Response type: {response.response_type}")
        print(f"Tag: {response.tag}")
        print(f"Status: {response.status}")
        print(f"Command: {response.command}")
        print(f"Message: {response.message}")
        print(f"Data: {response.data}")
        print(f"Raw line: {response.raw_line}")
        
        # Check if status is OK or PREAUTH
        print(f"\nIs status OK? {response.status.value == 'OK' if response.status else False}")
        print(f"Is status PREAUTH? {response.status.value == 'PREAUTH' if response.status else False}")
        
    except Exception as e:
        print(f"Error parsing greeting: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_greeting_parsing()