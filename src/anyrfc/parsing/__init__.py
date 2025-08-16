"""
AnyRFC Parsing Framework

This module provides a unified parsing interface for RFC protocols.
It abstracts away the underlying parser implementation to allow for
easy swapping of parsing backends.
"""

from .base import RFCParser, ParseError, ParseResult
from .imap import IMAPParser

__all__ = ["RFCParser", "ParseError", "ParseResult", "IMAPParser"]
