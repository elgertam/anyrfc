#!/usr/bin/env python3
"""
Minimal test of IMAP client connection.
"""

import pytest
import anyio
import os

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from anyrfc.email.imap import IMAPClient


@pytest.mark.anyio
@pytest.mark.skipif(
    not (os.getenv("GMAIL_USERNAME") and os.getenv("GMAIL_PASSWORD")), reason="Gmail credentials not available"
)
async def test_minimal_connection():
    """Test minimal IMAP connection with detailed logging."""

    username = os.getenv("GMAIL_USERNAME")
    password = os.getenv("GMAIL_PASSWORD")

    print("Creating IMAP client...")
    client = IMAPClient("imap.gmail.com", 993, use_tls=True)
    print(f"Initial state: {client.state.value}")
    print(f"Initial IMAP state: {client.imap_state.value}")

    try:
        print("\nStep 1: Starting connection...")

        # Add some debugging to see where it hangs
        print("About to call client.connect()...")

        # Let's break down the connect method step by step
        print("Transitioning to CONNECTING state...")
        await client._transition_state(client.state.__class__.CONNECTING)
        print(f"State after transition: {client.state.value}")

        print("Creating TLS context...")
        from src.anyrfc.core.tls import TLSHelper

        tls_context = TLSHelper.create_default_client_context()
        print("✓ TLS context created")

        print("Establishing TCP+TLS connection...")
        client._stream = await anyio.connect_tcp("imap.gmail.com", 993, tls=True, ssl_context=tls_context)
        print("✓ TCP+TLS connection established")

        print("Reading greeting...")
        greeting = await client._read_response()
        print(f"✓ Greeting received: {greeting.raw_line}")
        print(f"Greeting status: {greeting.status}")

        if greeting.status.value not in ["OK", "PREAUTH"]:
            print(f"✗ Invalid greeting status: {greeting.status}")
            return

        print("Transitioning to CONNECTED state...")
        await client._transition_state(client.state.__class__.CONNECTED)
        print(f"State after greeting: {client.state.value}")

        print("Getting capabilities...")
        await client._get_capabilities()
        print(f"✓ Capabilities retrieved: {len(client.capabilities)} capabilities")

        print("Connection successful! Now testing authentication...")

        result = await client.authenticate({"username": username, "password": password})

        print(f"Authentication result: {result}")
        print(f"Final state: {client.state.value}")
        print(f"Final IMAP state: {client.imap_state.value}")

    except Exception as e:
        print(f"Error during connection: {e}")
        import traceback

        traceback.print_exc()

    finally:
        try:
            await client.disconnect()
        except Exception:
            pass


if __name__ == "__main__":
    anyio.run(test_minimal_connection)
