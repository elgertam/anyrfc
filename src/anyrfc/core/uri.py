"""RFC 3986 URI parsing utilities."""
# Standard library imports for compute operations are acceptable
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
from typing import Dict, Optional, Any, Tuple
from dataclasses import dataclass

@dataclass
class ParsedURI:
    """Parsed URI components per RFC 3986."""
    scheme: str
    hostname: Optional[str]
    port: Optional[int]
    path: str
    query: Dict[str, Any]
    fragment: Optional[str]
    username: Optional[str]
    password: Optional[str]
    
    @property
    def is_secure(self) -> bool:
        """Check if URI uses secure scheme."""
        secure_schemes = {'https', 'wss', 'imaps', 'smtps', 'ftps'}
        return self.scheme.lower() in secure_schemes
    
    @property
    def default_port(self) -> int:
        """Get default port for scheme."""
        default_ports = {
            'http': 80,
            'https': 443,
            'ws': 80,
            'wss': 443,
            'ftp': 21,
            'ftps': 990,
            'smtp': 25,
            'smtps': 465,
            'imap': 143,
            'imaps': 993,
            'ssh': 22,
        }
        return default_ports.get(self.scheme.lower(), 80)
    
    @property
    def effective_port(self) -> int:
        """Get effective port (explicit or default)."""
        return self.port if self.port is not None else self.default_port
    
    def to_string(self) -> str:
        """Convert back to URI string."""
        # Reconstruct netloc
        netloc = ""
        if self.username:
            netloc += self.username
            if self.password:
                netloc += f":{self.password}"
            netloc += "@"
        
        if self.hostname:
            netloc += self.hostname
            if self.port is not None:
                netloc += f":{self.port}"
        
        # Reconstruct query
        query = ""
        if self.query:
            query = urlencode(self.query)
        
        return urlunparse((
            self.scheme,
            netloc,
            self.path,
            "",  # params (not used)
            query,
            self.fragment or ""
        ))

class URIParser:
    """RFC 3986 compliant URI parser."""
    
    @staticmethod
    def parse(uri: str) -> ParsedURI:
        """Parse URI string into components."""
        parsed = urlparse(uri)
        
        return ParsedURI(
            scheme=parsed.scheme,
            hostname=parsed.hostname,
            port=parsed.port,
            path=parsed.path or "/",
            query=parse_qs(parsed.query) if parsed.query else {},
            fragment=parsed.fragment,
            username=parsed.username,
            password=parsed.password
        )
    
    @staticmethod
    def is_absolute(uri: str) -> bool:
        """Check if URI is absolute (has scheme)."""
        return bool(urlparse(uri).scheme)
    
    @staticmethod
    def resolve_reference(base_uri: str, reference: str) -> str:
        """Resolve URI reference against base URI."""
        from urllib.parse import urljoin
        return urljoin(base_uri, reference)
    
    @staticmethod
    def validate_scheme(scheme: str, valid_schemes: set[str]) -> bool:
        """Validate URI scheme against allowed schemes."""
        return scheme.lower() in {s.lower() for s in valid_schemes}