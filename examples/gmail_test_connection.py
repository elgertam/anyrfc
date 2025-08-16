#!/usr/bin/env python3
"""
Simple Gmail IMAP connection test.
"""
import anyio
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed. Using os.environ directly.")

from anyrfc.email.imap import IMAPClient


async def test_gmail_connection():
    """Test basic Gmail IMAP connection."""
    
    username = os.getenv("GMAIL_USERNAME")
    password = os.getenv("GMAIL_PASSWORD")
    
    if not username or not password:
        print("Error: GMAIL_USERNAME and GMAIL_PASSWORD must be set in .env file")
        return
    
    print("Testing Gmail IMAP connection...")
    
    client = IMAPClient("imap.gmail.com", 993, use_tls=True)
    
    try:
        print("Connecting...")
        await client.connect()
        print("✓ Connected successfully!")
        
        print("Authenticating...")
        await client.authenticate({
            "username": username,
            "password": password
        })
        print("✓ Authentication successful!")
        
        print("Connection test completed successfully!")
        
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            await client.disconnect()
            print("✓ Disconnected")
        except:
            pass


if __name__ == "__main__":
    anyio.run(test_gmail_connection)