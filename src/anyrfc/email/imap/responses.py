"""IMAP response parsing per RFC 9051."""
# CRITICAL: ALL I/O OPERATIONS MUST USE ANYIO - NO ASYNCIO IMPORTS ALLOWED
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import re

class IMAPResponseType(Enum):
    """IMAP response types per RFC 9051 Section 7."""
    TAGGED = "tagged"
    UNTAGGED = "untagged"
    CONTINUATION = "continuation"

class IMAPStatus(Enum):
    """IMAP response status per RFC 9051."""
    OK = "OK"
    NO = "NO"
    BAD = "BAD"
    PREAUTH = "PREAUTH"
    BYE = "BYE"

@dataclass
class IMAPResponse:
    """IMAP response representation."""
    response_type: IMAPResponseType
    tag: Optional[str]
    status: Optional[IMAPStatus]
    command: Optional[str]
    message: str
    data: List[str]
    raw_line: str

class IMAPResponseParser:
    """IMAP response parser per RFC 9051 Section 7."""
    
    # IMAP response patterns
    TAGGED_PATTERN = re.compile(r'^([A-Z0-9]+)\s+(OK|NO|BAD)\s+(.*)')
    UNTAGGED_PATTERN = re.compile(r'^\*\s+(.*)')
    CONTINUATION_PATTERN = re.compile(r'^\+\s*(.*)')
    STATUS_PATTERN = re.compile(r'^(OK|NO|BAD|PREAUTH|BYE)\s+(.*)')
    
    @classmethod
    def parse(cls, line: str) -> IMAPResponse:
        """Parse IMAP response line per RFC 9051."""
        line = line.strip()
        
        # Try tagged response first
        tagged_match = cls.TAGGED_PATTERN.match(line)
        if tagged_match:
            tag = tagged_match.group(1)
            status_str = tagged_match.group(2)
            message = tagged_match.group(3)
            
            return IMAPResponse(
                response_type=IMAPResponseType.TAGGED,
                tag=tag,
                status=IMAPStatus(status_str),
                command=None,
                message=message,
                data=[],
                raw_line=line
            )
        
        # Try untagged response
        untagged_match = cls.UNTAGGED_PATTERN.match(line)
        if untagged_match:
            content = untagged_match.group(1)
            
            # Check if it's a status response
            status_match = cls.STATUS_PATTERN.match(content)
            if status_match:
                status_str = status_match.group(1)
                message = status_match.group(2)
                
                return IMAPResponse(
                    response_type=IMAPResponseType.UNTAGGED,
                    tag=None,
                    status=IMAPStatus(status_str),
                    command=None,
                    message=message,
                    data=[],
                    raw_line=line
                )
            else:
                # Regular untagged response (data)
                return IMAPResponse(
                    response_type=IMAPResponseType.UNTAGGED,
                    tag=None,
                    status=None,
                    command=None,
                    message=content,
                    data=[content],
                    raw_line=line
                )
        
        # Try continuation response
        continuation_match = cls.CONTINUATION_PATTERN.match(line)
        if continuation_match:
            message = continuation_match.group(1)
            
            return IMAPResponse(
                response_type=IMAPResponseType.CONTINUATION,
                tag=None,
                status=None,
                command=None,
                message=message,
                data=[],
                raw_line=line
            )
        
        # If no pattern matches, treat as untagged data
        return IMAPResponse(
            response_type=IMAPResponseType.UNTAGGED,
            tag=None,
            status=None,
            command=None,
            message=line,
            data=[line],
            raw_line=line
        )
    
    @classmethod
    def parse_capability_response(cls, response_line: str) -> List[str]:
        """Parse CAPABILITY response per RFC 9051 Section 6.1.1."""
        # Response format: * CAPABILITY IMAP4rev1 STARTTLS AUTH=GSSAPI LOGINDISABLED
        if response_line.startswith("* CAPABILITY"):
            parts = response_line.split()
            return parts[2:]  # Skip "* CAPABILITY"
        return []
    
    @classmethod
    def parse_list_response(cls, response_line: str) -> Optional[Dict[str, Any]]:
        """Parse LIST response per RFC 9051 Section 6.3.9."""
        # Response format: * LIST (\\HasNoChildren) "/" "INBOX"
        if response_line.startswith("* LIST "):
            # More robust parsing
            # Find the flags parentheses
            start_paren = response_line.find('(')
            end_paren = response_line.find(')', start_paren)
            
            if start_paren == -1 or end_paren == -1:
                return None
            
            # Extract flags
            flags_str = response_line[start_paren+1:end_paren]
            flags = [f.strip() for f in flags_str.split()] if flags_str else []
            
            # Find delimiter and mailbox after the flags
            remainder = response_line[end_paren+1:].strip()
            parts = remainder.split(None, 1)  # Split into max 2 parts
            
            if len(parts) >= 2:
                delimiter = parts[0].strip('"')
                mailbox = parts[1].strip('"')
                
                return {
                    'flags': flags,
                    'delimiter': delimiter,
                    'mailbox': mailbox
                }
        return None
    
    @classmethod
    def parse_status_response(cls, response_line: str) -> Optional[Dict[str, int]]:
        """Parse STATUS response per RFC 9051 Section 6.3.10."""
        # Response format: * STATUS "INBOX" (MESSAGES 52 UIDNEXT 4827 UIDVALIDITY 1234567890)
        if response_line.startswith("* STATUS"):
            # Find the parentheses containing the status items
            paren_start = response_line.find('(')
            paren_end = response_line.rfind(')')
            
            if paren_start != -1 and paren_end != -1:
                status_items = response_line[paren_start+1:paren_end]
                parts = status_items.split()
                
                status_dict = {}
                for i in range(0, len(parts), 2):
                    if i + 1 < len(parts):
                        key = parts[i]
                        value = int(parts[i + 1])
                        status_dict[key] = value
                
                return status_dict
        return None
    
    @classmethod
    def parse_fetch_response(cls, response_line: str) -> Optional[Dict[str, Any]]:
        """Parse FETCH response per RFC 9051 Section 6.4.5."""
        # Response format: * 12 FETCH (FLAGS (\\Seen) INTERNALDATE "17-Jul-1996 02:44:25 -0700" ...)
        if " FETCH " in response_line:
            parts = response_line.split()
            if len(parts) >= 3 and parts[0] == "*":
                message_num = int(parts[1])
                
                # Find the parentheses containing the fetch items
                paren_start = response_line.find('(')
                paren_end = response_line.rfind(')')
                
                if paren_start != -1 and paren_end != -1:
                    fetch_data = response_line[paren_start+1:paren_end]
                    
                    # Simple parsing - production would need more sophisticated parsing
                    return {
                        'message_number': message_num,
                        'fetch_data': fetch_data,
                        'raw': response_line
                    }
        return None
    
    @classmethod
    def parse_search_response(cls, response_line: str) -> List[int]:
        """Parse SEARCH response per RFC 9051 Section 6.4.4."""
        # Response format: * SEARCH 2 84 882
        if response_line.startswith("* SEARCH"):
            parts = response_line.split()
            if len(parts) > 2:
                return [int(num) for num in parts[2:]]
        return []
    
    @classmethod
    def parse_mailbox_data(cls, response_line: str) -> Optional[Dict[str, Any]]:
        """Parse various mailbox data responses."""
        if response_line.startswith("* "):
            parts = response_line.split()
            if len(parts) >= 3:
                if parts[2] == "EXISTS":
                    return {'type': 'EXISTS', 'count': int(parts[1])}
                elif parts[2] == "RECENT":
                    return {'type': 'RECENT', 'count': int(parts[1])}
                elif parts[2] == "EXPUNGE":
                    return {'type': 'EXPUNGE', 'message_number': int(parts[1])}
        return None

class IMAPResponseCode:
    """IMAP response code utilities per RFC 9051."""
    
    @staticmethod
    def extract_response_code(message: str) -> Optional[Tuple[str, Optional[str]]]:
        """Extract response code from message."""
        # Response codes are in square brackets: [ALERT] message
        if message.startswith('['):
            end_bracket = message.find(']')
            if end_bracket != -1:
                code = message[1:end_bracket]
                remaining = message[end_bracket+1:].strip()
                return code, remaining if remaining else None
        return None, message
    
    @staticmethod
    def is_capability_response_code(code: str) -> bool:
        """Check if response code indicates capability."""
        return code.startswith('CAPABILITY ')
    
    @staticmethod
    def is_permanentflags_response_code(code: str) -> bool:
        """Check if response code indicates permanent flags."""
        return code.startswith('PERMANENTFLAGS ')
    
    @staticmethod
    def is_uidnext_response_code(code: str) -> bool:
        """Check if response code indicates UIDNEXT."""
        return code.startswith('UIDNEXT ')
    
    @staticmethod
    def is_uidvalidity_response_code(code: str) -> bool:
        """Check if response code indicates UIDVALIDITY."""
        return code.startswith('UIDVALIDITY ')

class IMAPDataParser:
    """IMAP data structure parsing utilities."""
    
    @staticmethod
    def parse_parenthesized_list(data: str) -> List[str]:
        """Parse IMAP parenthesized list."""
        # Simple implementation - production needs more robust parsing
        if data.startswith('(') and data.endswith(')'):
            content = data[1:-1]
            # Split by spaces, handling quoted strings
            parts = []
            current = ""
            in_quotes = False
            
            for char in content:
                if char == '"' and (not current or current[-1] != '\\'):
                    in_quotes = not in_quotes
                    current += char
                elif char == ' ' and not in_quotes:
                    if current:
                        parts.append(current)
                        current = ""
                else:
                    current += char
            
            if current:
                parts.append(current)
            
            return parts
        return [data]
    
    @staticmethod
    def parse_quoted_string(data: str) -> str:
        """Parse IMAP quoted string."""
        if data.startswith('"') and data.endswith('"'):
            # Remove quotes and unescape
            content = data[1:-1]
            return content.replace('\\"', '"').replace('\\\\', '\\')
        return data
    
    @staticmethod
    def parse_atom(data: str) -> str:
        """Parse IMAP atom."""
        # Atoms are unquoted strings without special characters
        return data