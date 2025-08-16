#!/usr/bin/env python3
"""
Test Gmail connection using Python's standard library imaplib.
This verifies credentials and connection work before testing with AnyRFC.
"""
import imaplib
import os
import email
from email.header import decode_header

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed. Using os.environ directly.")


def test_gmail_stdlib():
    """Test Gmail connection using standard library imaplib."""
    
    username = os.getenv("GMAIL_USERNAME")
    password = os.getenv("GMAIL_PASSWORD")
    
    if not username or not password:
        print("Error: GMAIL_USERNAME and GMAIL_PASSWORD must be set in .env file")
        return
    
    print("Testing Gmail IMAP with Python standard library...")
    
    try:
        # Connect to Gmail IMAP server
        print("Connecting to imap.gmail.com:993...")
        mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
        print("✓ Connected successfully!")
        
        # Authenticate
        print("Authenticating...")
        mail.login(username, password)
        print("✓ Authentication successful!")
        
        # Select INBOX
        print("Selecting INBOX...")
        status, message_count = mail.select("INBOX")
        total_messages = int(message_count[0])
        print(f"✓ INBOX selected. Total messages: {total_messages}")
        
        if total_messages == 0:
            print("No messages found in INBOX.")
            mail.logout()
            return
        
        # Get the most recent 20 messages
        start_msg = max(1, total_messages - 19)
        end_msg = total_messages
        
        print(f"Fetching messages {start_msg}:{end_msg} (most recent 20)...")
        
        # Search for messages in range
        status, message_ids = mail.search(None, f"{start_msg}:{end_msg}")
        message_list = message_ids[0].split()
        
        print(f"\nRetrieved {len(message_list)} messages:")
        print("=" * 80)
        
        # Fetch and display message headers (newest first)
        for msg_id in reversed(message_list[-20:]):  # Last 20, newest first
            try:
                print(f"Message ID: {msg_id.decode()}")
                
                # Fetch just the headers for easier parsing
                status, header_data = mail.fetch(msg_id, "(BODY[HEADER.FIELDS (FROM SUBJECT DATE)])")
                if status == "OK" and header_data and header_data[0] and len(header_data[0]) > 1:
                    header_str = header_data[0][1].decode('utf-8', errors='ignore')
                    
                    # Parse headers
                    from_addr = ""
                    subject = ""
                    date = ""
                    
                    for line in header_str.split('\n'):
                        line = line.strip()
                        if line.lower().startswith('from:'):
                            from_addr = line[5:].strip()
                        elif line.lower().startswith('subject:'):
                            subject = line[8:].strip()
                        elif line.lower().startswith('date:'):
                            date = line[5:].strip()
                    
                    print(f"From: {from_addr}")
                    print(f"Subject: {subject}")
                    print(f"Date: {date}")
                else:
                    print("Could not fetch headers for this message")
                
                print("-" * 80)
                
            except Exception as e:
                print(f"Error processing message {msg_id}: {e}")
                print("-" * 80)
        
        print(f"\n✓ Successfully retrieved recent messages using stdlib imaplib!")
        
        # Logout
        mail.logout()
        print("✓ Logged out successfully")
        
    except imaplib.IMAP4.error as e:
        print(f"✗ IMAP error: {e}")
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_gmail_stdlib()