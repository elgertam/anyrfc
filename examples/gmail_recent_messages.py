#!/usr/bin/env python3
"""
Gmail IMAP example: Retrieve the most recent 20 messages.

This example demonstrates using the AnyRFC IMAP client to connect to Gmail
and retrieve the most recent 20 messages from the INBOX.

IMPORTANT: Gmail requires app-specific passwords for IMAP access.
1. Enable 2-factor authentication on your Google account
2. Generate an app password for "Mail" in your Google Account settings
3. Use the app password (not your regular password) in GMAIL_PASSWORD

Setup:
1. Create a .env file with:
   GMAIL_USERNAME=your.email@gmail.com
   GMAIL_PASSWORD=your_app_specific_password
2. Run: uv run python examples/gmail_recent_messages.py
"""
import anyio
import os
from datetime import datetime
from typing import Dict, Any

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed. Using os.environ directly.")

from anyrfc.email.imap import IMAPClient
from anyrfc.parsing import IMAPParser


async def get_recent_gmail_messages() -> None:
    """Retrieve the most recent 20 messages from Gmail INBOX."""
    
    # Get credentials from environment
    username = os.getenv("GMAIL_USERNAME")
    password = os.getenv("GMAIL_PASSWORD")
    
    if not username or not password:
        print("Error: GMAIL_USERNAME and GMAIL_PASSWORD must be set in .env file")
        return
    
    print("Connecting to Gmail IMAP server...")
    
    # Create and connect to Gmail IMAP server
    client = IMAPClient("imap.gmail.com", 993, use_tls=True)
    
    try:
        # Add timeout for connection
        with anyio.move_on_after(30):  # 30 second timeout
            await client.connect()
            print(f"Connected to {client.hostname}:{client.port}")
        
        if client.state.value != "connected":
            print("Error: Connection timed out after 30 seconds")
            print("This may be due to:")
            print("1. Network connectivity issues")
            print("2. Gmail requiring app-specific password (see docstring)")
            print("3. IMAP access disabled in Gmail settings")
            return
        
        # Authenticate
        print("Authenticating...")
        with anyio.move_on_after(30):  # 30 second timeout
            await client.authenticate({
                "username": username,
                "password": password
            })
        
        if client.imap_state.value != "authenticated":
            print("Error: Authentication failed or timed out")
            print("Please check:")
            print("1. Your username and password are correct")
            print("2. You're using an app-specific password (not regular password)")
            print("3. IMAP is enabled in Gmail settings")
            return
        
        print("Authentication successful!")
        
        # Select INBOX
        print("Selecting INBOX...")
        with anyio.move_on_after(10):  # 10 second timeout
            mailbox_info = await client.select_mailbox("INBOX")
        
        # Get total message count from mailbox info
        total_messages = mailbox_info.get("exists", 0)
        print(f"Total messages in INBOX: {total_messages}")
        
        if total_messages == 0:
            print("No messages found in INBOX.")
            return
        
        # Calculate range for most recent 20 messages
        start_msg = max(1, total_messages - 19)  # Get last 20 messages
        end_msg = total_messages
        message_range = f"{start_msg}:{end_msg}"
        
        print(f"Fetching messages {message_range} (most recent 20)...")
        
        # Fetch message headers and basic info
        with anyio.move_on_after(30):  # 30 second timeout
            messages = await client.fetch_messages(
                message_range,
                "(ENVELOPE UID FLAGS INTERNALDATE BODYSTRUCTURE)"
            )
        
        print(f"\nRetrieved {len(messages)} messages:")
        print("=" * 80)
        
        # Create parser for processing FETCH responses
        parser = IMAPParser()
        
        # Display messages in reverse order (newest first)
        for msg in reversed(messages):
            # Use the new PEG parser instead of regex
            raw_line = msg.get("raw", "")
            
            if raw_line:
                # Parse the raw FETCH response line
                parse_result = parser.parse_fetch_response(raw_line)
                
                if parse_result.success:
                    fetch_response = parse_result.value
                    
                    print(f"Message: {fetch_response.message_number}")
                    print(f"UID: {fetch_response.uid or 'Unknown'}")
                    print(f"Flags: {fetch_response.flags or []}")
                    print(f"Internal Date: {fetch_response.internal_date or 'Unknown'}")
                    
                    
                    # Display structured envelope data
                    if fetch_response.envelope:
                        env = fetch_response.envelope
                        print(f"Subject: {env.subject or 'None'}")
                        
                        # Format From field nicely
                        if env.from_addr:
                            from_list = []
                            for addr in env.from_addr:
                                if addr.get('name') and addr.get('email'):
                                    from_list.append(f"{addr['name']} <{addr['email']}>")
                                elif addr.get('email'):
                                    from_list.append(addr['email'])
                                else:
                                    from_list.append(str(addr))
                            print(f"From: {', '.join(from_list)}")
                        else:
                            print("From: None")
                            
                        print(f"Date: {env.date or 'None'}")
                        if env.message_id:
                            print(f"Message-ID: {env.message_id}")
                    else:
                        print("Envelope: No data available")
                        
                    # Show BODYSTRUCTURE with improved formatting
                    if fetch_response.body_structure:
                        body = fetch_response.body_structure
                        if isinstance(body, dict):
                            content_type = body.get('content_type', 'unknown')
                            is_multipart = body.get('is_multipart', False)
                            size = body.get('size')
                            
                            if is_multipart:
                                parts_count = len(body.get('parts', []))
                                print(f"Body: {content_type} ({parts_count} parts)")
                            else:
                                size_str = f", {size} bytes" if size else ""
                                print(f"Body: {content_type}{size_str}")
                        else:
                            print(f"Body Structure: Available ({len(str(body))} chars)")
                    else:
                        print("Body Structure: Not available")
                        
                    print("-" * 80)
                else:
                    print(f"Parse error: {parse_result.error}")
                    print(f"Raw line: {raw_line}")
                    print("-" * 80)
            else:
                # Fallback for messages without raw data
                print(f"Message: {msg.get('message_number', 'Unknown')}")
                print(f"No raw data available for parsing")
                print("-" * 80)
        
        print(f"\nSuccessfully retrieved {len(messages)} recent messages from Gmail!")
        
    finally:
        # Ensure we disconnect properly
        try:
            await client.disconnect()
            print("Disconnected from Gmail.")
        except Exception as e:
            print(f"Warning: Error during disconnect: {e}")


async def main():
    """Main function."""
    try:
        await get_recent_gmail_messages()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    anyio.run(main)