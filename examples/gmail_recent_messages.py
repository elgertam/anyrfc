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
import re
from datetime import datetime
from typing import Dict, Any

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed. Using os.environ directly.")

from anyrfc.email.imap import IMAPClient


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
        
        # Display messages in reverse order (newest first)
        for msg in reversed(messages):
            # Parse the fetch_data string for basic info
            fetch_data = msg.get("fetch_data", "")
            message_num = msg.get("message_number", "Unknown")
            
            # Extract UID
            uid = "Unknown"
            uid_match = re.search(r'UID (\d+)', fetch_data)
            if uid_match:
                uid = uid_match.group(1)
            
            # Extract flags
            flags_str = ""
            flags_match = re.search(r'FLAGS \(([^)]+)\)', fetch_data)
            if flags_match:
                flags_str = flags_match.group(1)
            
            # Extract internal date
            date_str = "Unknown"
            date_match = re.search(r'INTERNALDATE "([^"]+)"', fetch_data)
            if date_match:
                date_str = date_match.group(1)
            
            # Extract subject from envelope
            subject = "No Subject"
            # ENVELOPE format: ("date" "subject" (from) (sender) (reply-to) (to) ...)
            envelope_match = re.search(r'ENVELOPE \("([^"]*)" "([^"]*)"', fetch_data)
            if envelope_match:
                subject = envelope_match.group(2) or "No Subject"
            
            # Extract from address from envelope (simplified)
            from_addr = "Unknown"
            # Look for the from field in envelope: (("name" NIL "mailbox" "host"))
            from_match = re.search(r'ENVELOPE \("[^"]*" "[^"]*" \(\(("[^"]*"|NIL) NIL "([^"]*)" "([^"]*)"\)\)', fetch_data)
            if from_match and len(from_match.groups()) >= 3:
                name = from_match.group(1)
                mailbox = from_match.group(2) 
                host = from_match.group(3)
                if name and name != "NIL":
                    name = name.strip('"')
                    from_addr = f"{name} <{mailbox}@{host}>"
                else:
                    from_addr = f"{mailbox}@{host}"
            
            # Format flags
            flag_symbols = []
            if "\\Seen" in flags_str:
                flag_symbols.append("📖")  # Read
            else:
                flag_symbols.append("📧")  # Unread
            
            if "\\Flagged" in flags_str:
                flag_symbols.append("⭐")  # Flagged
            
            if "\\Answered" in flags_str:
                flag_symbols.append("↩️")  # Replied
            
            flags_display = " ".join(flag_symbols) if flag_symbols else "📧"
            
            print(f"Message: {message_num}")
            print(f"UID: {uid}")
            print(f"From: {from_addr}")
            print(f"Subject: {subject}")
            print(f"Date: {date_str}")
            print(f"Flags: {flags_display}")
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