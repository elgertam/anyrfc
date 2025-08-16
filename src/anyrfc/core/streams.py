# CRITICAL: ALL I/O OPERATIONS MUST USE ANYIO - NO ASYNCIO IMPORTS ALLOWED
import anyio
from anyio.abc import ByteStream
from typing import Optional, Union
import ssl


class AnyIOStreamHelpers:
    """Helper utilities for AnyIO stream operations."""
    
    @staticmethod
    async def connect_tcp_secure(hostname: str, port: int, *, 
                                tls: bool = False, 
                                tls_context: Optional[ssl.SSLContext] = None) -> ByteStream:
        """Connect to TCP server with optional TLS using AnyIO only."""
        if tls:
            return await anyio.connect_tcp(hostname, port, tls=True, ssl_context=tls_context)
        else:
            return await anyio.connect_tcp(hostname, port)
    
    @staticmethod
    async def read_until(stream: ByteStream, delimiter: bytes, max_size: int = 8192) -> bytes:
        """Read from stream until delimiter is found using AnyIO."""
        buffer = b''
        while len(buffer) < max_size:
            chunk = await stream.receive(1)
            if not chunk:
                break
            buffer += chunk
            if buffer.endswith(delimiter):
                return buffer[:-len(delimiter)]
        raise ValueError(f"Delimiter not found within {max_size} bytes")
    
    @staticmethod
    async def read_line(stream: ByteStream, max_size: int = 8192) -> str:
        """Read a CRLF-terminated line from stream using AnyIO."""
        line_bytes = await AnyIOStreamHelpers.read_until(stream, b'\r\n', max_size)
        return line_bytes.decode('utf-8')
    
    @staticmethod
    async def read_exact(stream: ByteStream, size: int) -> bytes:
        """Read exactly 'size' bytes from stream using AnyIO."""
        buffer = b''
        while len(buffer) < size:
            chunk = await stream.receive(size - len(buffer))
            if not chunk:
                raise ConnectionError("Unexpected end of stream")
            buffer += chunk
        return buffer
    
    @staticmethod
    async def send_all(stream: ByteStream, data: Union[str, bytes]) -> None:
        """Send all data to stream using AnyIO."""
        if isinstance(data, str):
            data = data.encode('utf-8')
        await stream.send(data)