"""
Base parsing interfaces and types for AnyRFC.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional
from dataclasses import dataclass
from enum import Enum


class ParseError(Exception):
    """Exception raised when parsing fails."""
    
    def __init__(self, message: str, position: Optional[int] = None, 
                 line: Optional[int] = None, column: Optional[int] = None):
        self.message = message
        self.position = position
        self.line = line
        self.column = column
        super().__init__(self.message)
    
    def __str__(self):
        if self.line is not None and self.column is not None:
            return f"{self.message} at line {self.line}, column {self.column}"
        elif self.position is not None:
            return f"{self.message} at position {self.position}"
        return self.message


@dataclass
class ParseResult:
    """Result of a parsing operation."""
    success: bool
    value: Any = None
    error: Optional[ParseError] = None
    
    @classmethod
    def success_result(cls, value: Any) -> 'ParseResult':
        """Create a successful parse result."""
        return cls(success=True, value=value)
    
    @classmethod
    def error_result(cls, error: ParseError) -> 'ParseResult':
        """Create a failed parse result."""
        return cls(success=False, error=error)


class RFCParser(ABC):
    """Abstract base class for RFC protocol parsers."""
    
    @abstractmethod
    def parse(self, text: str, rule: Optional[str] = None) -> ParseResult:
        """
        Parse text according to the grammar.
        
        Args:
            text: The text to parse
            rule: Optional specific rule to start parsing from
            
        Returns:
            ParseResult containing the parsed value or error
        """
        pass
    
    @abstractmethod
    def parse_partial(self, text: str, rule: str) -> ParseResult:
        """
        Parse text starting from a specific grammar rule.
        
        Args:
            text: The text to parse
            rule: The grammar rule to start from
            
        Returns:
            ParseResult containing the parsed value or error
        """
        pass
    
    def parse_or_raise(self, text: str, rule: Optional[str] = None) -> Any:
        """
        Parse text and raise exception on failure.
        
        Args:
            text: The text to parse
            rule: Optional specific rule to start parsing from
            
        Returns:
            The parsed value
            
        Raises:
            ParseError: If parsing fails
        """
        result = self.parse(text, rule)
        if not result.success:
            raise result.error
        return result.value
    
    def validate_syntax(self, text: str, rule: Optional[str] = None) -> bool:
        """
        Validate if text conforms to grammar without returning parsed value.
        
        Args:
            text: The text to validate
            rule: Optional specific rule to validate against
            
        Returns:
            True if text is valid, False otherwise
        """
        result = self.parse(text, rule)
        return result.success


class ParserBackend(Enum):
    """Available parser backend implementations."""
    ARPEGGIO = "arpeggio"
    # Future backends can be added here:
    # PARSIMONIOUS = "parsimonious"
    # CUSTOM_OHQM = "custom_ohm"


@dataclass
class ParserConfig:
    """Configuration for parser instances."""
    backend: ParserBackend = ParserBackend.ARPEGGIO
    debug: bool = False
    memoization: bool = True
    reduce_tree: bool = True
    ignore_case: bool = False