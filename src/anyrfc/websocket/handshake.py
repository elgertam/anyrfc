"""WebSocket handshake implementation per RFC 6455 Section 4."""
# CRITICAL: ALL I/O OPERATIONS MUST USE ANYIO - NO ASYNCIO IMPORTS ALLOWED
import anyio
from anyio.abc import ByteStream
from typing import Dict, List, Optional, Tuple
import base64
import hashlib
import secrets
from ..core.streams import AnyIOStreamHelpers
from ..core.uri import ParsedURI

class WebSocketHandshake:
    """WebSocket handshake per RFC 6455 Section 4."""
    
    # WebSocket GUID per RFC 6455
    WEBSOCKET_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
    
    def __init__(self):
        self.sec_websocket_key: Optional[str] = None
        self.sec_websocket_accept: Optional[str] = None
        self.protocols: List[str] = []
        self.extensions: List[str] = []
        self.origin: Optional[str] = None
    
    def generate_key(self) -> str:
        """Generate Sec-WebSocket-Key per RFC 6455 Section 4.1."""
        # Must be 16 random bytes, base64 encoded
        self.sec_websocket_key = base64.b64encode(secrets.token_bytes(16)).decode('ascii')
        return self.sec_websocket_key
    
    def calculate_accept_key(self, websocket_key: str) -> str:
        """Calculate Sec-WebSocket-Accept per RFC 6455 Section 4.2.2."""
        # Concatenate key with GUID and hash with SHA-1
        combined = websocket_key + self.WEBSOCKET_GUID
        sha1_hash = hashlib.sha1(combined.encode('utf-8')).digest()
        return base64.b64encode(sha1_hash).decode('ascii')
    
    async def send_client_handshake(self, 
                                  stream: ByteStream, 
                                  parsed_uri: ParsedURI,
                                  protocols: Optional[List[str]] = None,
                                  extensions: Optional[List[str]] = None,
                                  origin: Optional[str] = None,
                                  extra_headers: Optional[Dict[str, str]] = None) -> None:
        """Send client handshake request per RFC 6455 Section 4.2.1."""
        
        # Generate WebSocket key
        if not self.sec_websocket_key:
            self.generate_key()
        
        # Store parameters
        self.protocols = protocols or []
        self.extensions = extensions or []
        self.origin = origin
        
        # Build request line
        path = parsed_uri.path or "/"
        if parsed_uri.query:
            # Convert query dict back to string
            from urllib.parse import urlencode
            query_items = []
            for key, values in parsed_uri.query.items():
                if isinstance(values, list):
                    for value in values:
                        query_items.append((key, value))
                else:
                    query_items.append((key, values))
            if query_items:
                path += "?" + urlencode(query_items)
        
        request_lines = [f"GET {path} HTTP/1.1"]
        
        # Required headers per RFC 6455
        port = parsed_uri.effective_port
        default_port = (80 if parsed_uri.scheme == 'ws' else 443)
        host = parsed_uri.hostname
        if port != default_port:
            host += f":{port}"
        
        headers = {
            "Host": host,
            "Upgrade": "websocket",
            "Connection": "Upgrade",
            "Sec-WebSocket-Key": self.sec_websocket_key,
            "Sec-WebSocket-Version": "13"
        }
        
        # Optional headers
        if self.origin:
            headers["Origin"] = self.origin
        
        if self.protocols:
            headers["Sec-WebSocket-Protocol"] = ", ".join(self.protocols)
        
        if self.extensions:
            headers["Sec-WebSocket-Extensions"] = ", ".join(self.extensions)
        
        # Add extra headers
        if extra_headers:
            headers.update(extra_headers)
        
        # Build header lines
        for key, value in headers.items():
            request_lines.append(f"{key}: {value}")
        
        # Send request
        request = "\r\n".join(request_lines) + "\r\n\r\n"
        await AnyIOStreamHelpers.send_all(stream, request)
    
    async def receive_server_response(self, stream: ByteStream) -> Dict[str, str]:
        """Receive and parse server handshake response per RFC 6455 Section 4.2.2."""
        
        # Read HTTP response headers
        response_lines = []
        while True:
            line = await AnyIOStreamHelpers.read_line(stream)
            if not line:
                break
            response_lines.append(line)
        
        if not response_lines:
            raise ValueError("Empty response from server")
        
        # Parse status line
        status_line = response_lines[0]
        if not status_line.startswith("HTTP/1.1 101"):
            raise ValueError(f"Invalid response status: {status_line}")
        
        # Parse headers
        headers = {}
        for line in response_lines[1:]:
            if ":" in line:
                key, value = line.split(":", 1)
                headers[key.strip().lower()] = value.strip()
        
        return headers
    
    def validate_server_response(self, headers: Dict[str, str]) -> None:
        """Validate server response per RFC 6455 Section 4.2.2."""
        
        # Check required headers
        required_headers = {
            "upgrade": "websocket",
            "connection": "upgrade"
        }
        
        for header, expected_value in required_headers.items():
            if header not in headers:
                raise ValueError(f"Missing required header: {header}")
            
            # Connection header can contain multiple values
            if header == "connection":
                connection_values = [v.strip().lower() for v in headers[header].split(",")]
                if expected_value not in connection_values:
                    raise ValueError(f"Invalid {header} header: {headers[header]}")
            else:
                if headers[header].lower() != expected_value:
                    raise ValueError(f"Invalid {header} header: {headers[header]}")
        
        # Validate Sec-WebSocket-Accept
        if "sec-websocket-accept" not in headers:
            raise ValueError("Missing Sec-WebSocket-Accept header")
        
        expected_accept = self.calculate_accept_key(self.sec_websocket_key)
        if headers["sec-websocket-accept"] != expected_accept:
            raise ValueError("Invalid Sec-WebSocket-Accept header")
        
        self.sec_websocket_accept = headers["sec-websocket-accept"]
    
    def get_negotiated_protocol(self, headers: Dict[str, str]) -> Optional[str]:
        """Get negotiated subprotocol from response."""
        if "sec-websocket-protocol" not in headers:
            return None
        
        negotiated = headers["sec-websocket-protocol"]
        
        # Verify it's one we requested
        if self.protocols and negotiated in self.protocols:
            return negotiated
        
        return None
    
    def get_negotiated_extensions(self, headers: Dict[str, str]) -> List[str]:
        """Get negotiated extensions from response."""
        if "sec-websocket-extensions" not in headers:
            return []
        
        # Parse extension list (simplified parsing)
        extensions_header = headers["sec-websocket-extensions"]
        extensions = [ext.strip() for ext in extensions_header.split(",")]
        
        return extensions
    
    async def perform_client_handshake(self, 
                                     stream: ByteStream,
                                     parsed_uri: ParsedURI,
                                     protocols: Optional[List[str]] = None,
                                     extensions: Optional[List[str]] = None,
                                     origin: Optional[str] = None,
                                     extra_headers: Optional[Dict[str, str]] = None) -> Tuple[Optional[str], List[str]]:
        """Perform complete client handshake and return negotiated protocol and extensions."""
        
        # Send handshake request
        await self.send_client_handshake(
            stream, parsed_uri, protocols, extensions, origin, extra_headers
        )
        
        # Receive and validate response
        response_headers = await self.receive_server_response(stream)
        self.validate_server_response(response_headers)
        
        # Get negotiated parameters
        negotiated_protocol = self.get_negotiated_protocol(response_headers)
        negotiated_extensions = self.get_negotiated_extensions(response_headers)
        
        return negotiated_protocol, negotiated_extensions