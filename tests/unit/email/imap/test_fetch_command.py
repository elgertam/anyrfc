#!/usr/bin/env python3
"""
Test FETCH command building.
"""
import pytest
from anyrfc.email.imap.commands import IMAPCommandBuilder

def test_fetch_command():
    """Test FETCH command construction."""
    
    sequence_set = "72176:72195"
    items = "ENVELOPE UID FLAGS INTERNALDATE BODYSTRUCTURE"
    
    command = IMAPCommandBuilder.fetch(sequence_set, items)
    
    print(f"Command type: {command.command_type}")
    print(f"Arguments: {command.arguments}")
    print(f"Full command: {command.to_string()}")
    
    # According to RFC 9051, FETCH items should be in parentheses
    # Let's test with proper format
    items_proper = "(ENVELOPE UID FLAGS INTERNALDATE BODYSTRUCTURE)"
    command_proper = IMAPCommandBuilder.fetch(sequence_set, items_proper)
    
    print(f"\nWith parentheses:")
    print(f"Full command: {command_proper.to_string()}")

if __name__ == "__main__":
    test_fetch_command()