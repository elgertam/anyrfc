#!/usr/bin/env python3
"""
Test simple parser to debug grammar issues.
"""

import pytest
from anyrfc._vendor.arpeggio import ParserPython, Optional as ArpeggioOptional, \
    ZeroOrMore, OneOrMore, EOF, SemanticError, NoMatch
from anyrfc._vendor.arpeggio import RegExMatch as _

# Very simple IMAP grammar to start
def sp(): return ' '  # Use literal space
def number(): return _("\\d+")
def word(): return _("\\w+")
def simple_fetch(): return '*', sp, number, sp, 'FETCH'

def test_simple():
    """Test very simple parsing."""
    
    parser = ParserPython(simple_fetch, debug=False, skipws=False)  # Disable auto whitespace skipping
    
    test_text = "* 1 FETCH"
    print(f"Testing: '{test_text}'")
    print(f"Characters: {[c for c in test_text]}")
    print(f"Text length: {len(test_text)}")
    
    try:
        result = parser.parse(test_text)
        print("✓ Success!")
        print(f"Result type: {type(result)}")
        print(f"Result: {result}")
        print(f"Result._repr_: {repr(result)}")
    except Exception as e:
        print(f"✗ Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple()