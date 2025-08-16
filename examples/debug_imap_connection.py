#!/usr/bin/env python3
"""
Debug AnyRFC IMAP connection issues.
"""
import anyio
import os
import ssl
from typing import Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from src.anyrfc.core.streams import AnyIOStreamHelpers
from src.anyrfc.core.tls import TLSHelper


async def test_raw_tcp_connection():
    """Test raw TCP connection to Gmail IMAP."""
    print("=== Testing Raw TCP Connection ===")
    
    try:
        print("Connecting to imap.gmail.com:993 without TLS...")
        stream = await anyio.connect_tcp("imap.gmail.com", 993)
        print("✓ Raw TCP connection successful")
        
        # Try to read first few bytes (should fail since Gmail requires TLS)
        try:
            with anyio.move_on_after(5):
                data = await stream.receive(100)
                print(f"Received data: {data}")
        except Exception as e:
            print(f"Expected failure reading without TLS: {e}")
        
        await stream.aclose()
        print("✓ Raw TCP connection closed")
        
    except Exception as e:
        print(f"✗ Raw TCP connection failed: {e}")


async def test_tls_connection():
    """Test TLS connection to Gmail IMAP."""
    print("\n=== Testing TLS Connection ===")
    
    try:
        print("Creating TLS context...")
        tls_context = TLSHelper.create_default_client_context()
        print("✓ TLS context created")
        
        print("Connecting to imap.gmail.com:993 with TLS...")
        stream = await anyio.connect_tcp("imap.gmail.com", 993, tls=True, ssl_context=tls_context)
        print("✓ TLS connection successful")
        
        # Try to read Gmail's greeting
        print("Reading IMAP greeting...")
        with anyio.move_on_after(10):  # 10 second timeout
            try:
                # Read greeting using our stream helper
                greeting = await AnyIOStreamHelpers.read_line(stream)
                print(f"✓ Greeting received: {greeting}")
            except Exception as e:
                print(f"✗ Error reading greeting: {e}")
                # Try reading raw bytes instead
                print("Trying to read raw bytes...")
                data = await stream.receive(1024)
                print(f"Raw data: {data}")
        
        await stream.aclose()
        print("✓ TLS connection closed")
        
    except Exception as e:
        print(f"✗ TLS connection failed: {e}")
        import traceback
        traceback.print_exc()


async def test_anyio_stream_helpers():
    """Test AnyIO stream helpers with a simple server."""
    print("\n=== Testing AnyIO Stream Helpers ===")
    
    try:
        print("Testing read_line with HTTP server...")
        
        # Connect to a simple HTTP server to test our read_line function
        stream = await anyio.connect_tcp("httpbin.org", 80)
        
        # Send HTTP request
        request = "GET / HTTP/1.1\r\nHost: httpbin.org\r\nConnection: close\r\n\r\n"
        await AnyIOStreamHelpers.send_all(stream, request)
        
        # Try to read response line
        with anyio.move_on_after(5):
            response_line = await AnyIOStreamHelpers.read_line(stream)
            print(f"✓ HTTP response line: {response_line}")
        
        await stream.aclose()
        
    except Exception as e:
        print(f"✗ Stream helpers test failed: {e}")
        import traceback
        traceback.print_exc()


async def test_improved_stream_reading():
    """Test improved stream reading method."""
    print("\n=== Testing Improved Stream Reading ===")
    
    try:
        tls_context = TLSHelper.create_default_client_context()
        stream = await anyio.connect_tcp("imap.gmail.com", 993, tls=True, ssl_context=tls_context)
        
        # Alternative reading method - read larger chunks
        print("Reading with larger buffer...")
        with anyio.move_on_after(10):
            buffer = b''
            while b'\r\n' not in buffer:
                chunk = await stream.receive(4096)  # Read larger chunks
                if not chunk:
                    break
                buffer += chunk
                print(f"Buffer so far ({len(buffer)} bytes): {buffer[:100]}...")
                
                if b'\r\n' in buffer:
                    line_end = buffer.find(b'\r\n')
                    line = buffer[:line_end].decode('utf-8')
                    print(f"✓ Complete line received: {line}")
                    break
        
        await stream.aclose()
        
    except Exception as e:
        print(f"✗ Improved reading failed: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Run all diagnostic tests."""
    print("AnyRFC IMAP Connection Diagnostics")
    print("=" * 50)
    
    await test_raw_tcp_connection()
    await test_tls_connection()
    await test_anyio_stream_helpers()
    await test_improved_stream_reading()
    
    print("\n" + "=" * 50)
    print("Diagnostics complete")


if __name__ == "__main__":
    anyio.run(main)