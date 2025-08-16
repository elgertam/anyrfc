"""
IMAP-specific parser implementation using PEG grammar.

This module implements RFC 9051 compliant IMAP response parsing using
a vendored PEG parser with proper grammar definitions.
"""

from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime
import re

from .base import RFCParser, ParseError, ParseResult, ParserConfig
from .._vendor.arpeggio import ParserPython, SemanticError, NoMatch
from . import imap_grammar


# IMAP Data Structures
@dataclass
class IMAPEnvelope:
    """IMAP ENVELOPE structure."""
    date: Optional[str] = None
    subject: Optional[str] = None
    from_addr: Optional[List[Dict[str, str]]] = None
    sender: Optional[List[Dict[str, str]]] = None
    reply_to: Optional[List[Dict[str, str]]] = None
    to: Optional[List[Dict[str, str]]] = None
    cc: Optional[List[Dict[str, str]]] = None
    bcc: Optional[List[Dict[str, str]]] = None
    in_reply_to: Optional[str] = None
    message_id: Optional[str] = None


@dataclass
class IMAPFetchResponse:
    """IMAP FETCH response structure."""
    message_number: int
    uid: Optional[int] = None
    flags: Optional[List[str]] = None
    internal_date: Optional[datetime] = None
    envelope: Optional[IMAPEnvelope] = None
    body_structure: Optional[Dict] = None
    body: Optional[str] = None


# Grammar is now defined in imap_grammar.py


class IMAPParser(RFCParser):
    """IMAP parser using PEG grammar."""
    
    def __init__(self, config: Optional[ParserConfig] = None):
        """Initialize IMAP parser."""
        self.config = config or ParserConfig()
        
        # Create Arpeggio parser with skipws=False for precise IMAP parsing
        self._parser = ParserPython(
            imap_grammar.response,
            debug=self.config.debug,
            memoization=self.config.memoization,
            reduce_tree=self.config.reduce_tree,
            ignore_case=self.config.ignore_case,
            skipws=False  # IMAP requires precise whitespace handling
        )
        
        # Specific parsers for different rules
        self._fetch_parser = ParserPython(imap_grammar.fetch_response, skipws=False)
        self._envelope_parser = ParserPython(imap_grammar.envelope, skipws=False)
    
    def parse(self, text: str, rule: Optional[str] = None) -> ParseResult:
        """Parse IMAP response text."""
        try:
            if rule:
                return self.parse_partial(text, rule)
            
            parse_tree = self._parser.parse(text.strip())
            result = self._transform_tree(parse_tree)
            return ParseResult.success_result(result)
            
        except (NoMatch, SemanticError) as e:
            error = ParseError(
                message=str(e),
                position=getattr(e, 'position', None),
                line=getattr(e, 'line', None),
                column=getattr(e, 'col', None)
            )
            return ParseResult.error_result(error)
        except Exception as e:
            error = ParseError(f"Unexpected parsing error: {e}")
            return ParseResult.error_result(error)
    
    def parse_partial(self, text: str, rule: str) -> ParseResult:
        """Parse text starting from specific rule."""
        try:
            if rule == "fetch_response":
                parse_tree = self._fetch_parser.parse(text.strip())
                result = self._transform_fetch_response(parse_tree)
            elif rule == "envelope":
                parse_tree = self._envelope_parser.parse(text.strip())
                result = self._transform_envelope(parse_tree)
            else:
                raise ParseError(f"Unknown rule: {rule}")
            
            return ParseResult.success_result(result)
            
        except (NoMatch, SemanticError) as e:
            error = ParseError(
                message=str(e),
                position=getattr(e, 'position', None),
                line=getattr(e, 'line', None),
                column=getattr(e, 'col', None)
            )
            return ParseResult.error_result(error)
        except Exception as e:
            error = ParseError(f"Unexpected parsing error: {e}")
            return ParseResult.error_result(error)
    
    def parse_fetch_response(self, text: str) -> ParseResult:
        """Parse FETCH response specifically."""
        return self.parse_partial(text, "fetch_response")
    
    def parse_envelope(self, text: str) -> ParseResult:
        """Parse ENVELOPE data specifically.""" 
        return self.parse_partial(text, "envelope")
    
    def _transform_tree(self, tree) -> Any:
        """Transform parse tree to Python objects."""
        # This is a simplified transformation
        # In a full implementation, you'd use Arpeggio's visitor pattern
        return str(tree)
    
    def _transform_fetch_response(self, tree) -> IMAPFetchResponse:
        """Transform FETCH response parse tree."""
        # Simplified transformation - in reality would be more complex
        text = str(tree)
        
        # Extract message number
        match = re.search(r'^\* (\d+) FETCH', text)
        message_number = int(match.group(1)) if match else 0
        
        result = IMAPFetchResponse(message_number=message_number)
        
        # Extract UID
        uid_match = re.search(r'UID (\d+)', text)
        if uid_match:
            result.uid = int(uid_match.group(1))
        
        # Extract flags
        flags_match = re.search(r'FLAGS \\(([^)]+)\\)', text)
        if flags_match:
            result.flags = flags_match.group(1).split()
        
        # Extract internal date
        date_match = re.search(r'INTERNALDATE "([^"]+)"', text)
        if date_match:
            try:
                # Parse IMAP date format
                date_str = date_match.group(1)
                result.internal_date = datetime.strptime(date_str, "%d-%b-%Y %H:%M:%S %z")
            except ValueError:
                pass  # Keep as None if parsing fails
        
        return result
    
    def _transform_envelope(self, tree) -> IMAPEnvelope:
        """Transform ENVELOPE parse tree."""
        # Simplified transformation
        return IMAPEnvelope()


# Convenience functions for common IMAP parsing tasks
def parse_fetch_response(text: str) -> ParseResult:
    """Parse a FETCH response line."""
    parser = IMAPParser()
    return parser.parse_fetch_response(text)


def parse_envelope(text: str) -> ParseResult:
    """Parse ENVELOPE data."""
    parser = IMAPParser()
    return parser.parse_envelope(text)