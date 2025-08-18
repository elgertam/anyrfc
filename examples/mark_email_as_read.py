#!/usr/bin/env python3
"""
Mark specific email as read example using AnyRFC IMAP client.

This example demonstrates how to:
1. Connect to Gmail via IMAP
2. Search for an email with a specific subject
3. Mark that email as read using the STORE command

IMPORTANT: Gmail requires app-specific passwords for IMAP access.
1. Enable 2-factor authentication on your Google account
2. Generate an app password for "Mail" in your Google Account settings
3. Use the app password (not your regular password) in GMAIL_PASSWORD

Setup:
1. Create a .env file with:
   GMAIL_USERNAME=your.email@gmail.com
   GMAIL_PASSWORD=your_app_specific_password
2. Run: uv sync --group examples
3. Run: uv run python examples/mark_email_as_read.py
"""

import anyio
import os
import sys

# Load environment variables
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed. Using os.environ directly.")

from anyrfc.email.imap import (
    IMAPClient,
    MessageFlag,
    FetchItem,
    StoreAction,
    build_search_criteria,
    build_flag_list,
    build_fetch_items,
)
from anyrfc.email.imap.commands import IMAPCommandBuilder
from anyrfc.parsing import IMAPParser


async def find_and_mark_email_as_read(subject: str) -> bool:
    """
    Find an email with the specified subject and mark it as read.

    Args:
        subject: The email subject to search for

    Returns:
        bool: True if email was found and marked as read, False otherwise
    """

    # Get credentials from environment
    username = os.getenv("GMAIL_USERNAME")
    password = os.getenv("GMAIL_PASSWORD")

    if not username or not password:
        print("Error: GMAIL_USERNAME and GMAIL_PASSWORD must be set in .env file")
        return False

    print(f"Connecting to Gmail IMAP server as {username}...")

    # Create and connect to Gmail IMAP server
    client = IMAPClient("imap.gmail.com", 993, use_tls=True)

    try:
        # Connect with timeout
        with anyio.move_on_after(30):
            await client.connect()
            print(f"Connected to {client.hostname}:{client.port}")

        if client.state.value != "connected":
            print("Error: Connection timed out")
            return False

        # Authenticate
        print("Authenticating...")
        with anyio.move_on_after(30):
            await client.authenticate({"username": username, "password": password})

        if client.imap_state.value != "authenticated":
            print("Error: Authentication failed")
            return False

        print("Authentication successful!")

        # Select INBOX
        print("Selecting INBOX...")
        with anyio.move_on_after(10):
            mailbox_info = await client.select_mailbox("INBOX")

        total_messages = mailbox_info.get("exists", 0)
        print(f"Total messages in INBOX: {total_messages}")

        if total_messages == 0:
            print("No messages found in INBOX.")
            return False

        # Search for emails with the specific subject
        print(f"Searching for emails with subject: '{subject}'...")

        # Use the new enum-based search API for better ergonomics
        search_command = build_search_criteria(subject=subject)

        # Send the search command
        with anyio.move_on_after(30):
            search_results = await client.search_messages(search_command)

        if not search_results:
            print(f"No emails found with subject: '{subject}'")
            return False

        print(f"Found {len(search_results)} email(s) with matching subject")

        # Get the first matching email
        message_uid = search_results[0]
        print(f"Processing email UID: {message_uid}")

        # Fetch the email to verify it's the right one
        print("Fetching email details to verify...")
        fetch_items = build_fetch_items(FetchItem.ENVELOPE, FetchItem.FLAGS)
        with anyio.move_on_after(30):
            messages = await client.fetch_messages(str(message_uid), fetch_items)

        if not messages:
            print("Error: Could not fetch email details")
            return False

        # Parse the fetched message to display details
        parser = IMAPParser()
        message = messages[0]
        raw_line = message.get("raw", "")

        if raw_line:
            parse_result = parser.parse_fetch_response(raw_line)
            if parse_result.success:
                fetch_response = parse_result.value

                # Display email details
                print("\nEmail found:")
                print(f"UID: {fetch_response.uid}")
                print(f"Current flags: {fetch_response.flags or []}")

                if fetch_response.envelope and fetch_response.envelope.subject:
                    print(f"Subject: {fetch_response.envelope.subject}")

                    # Verify this is the email we're looking for
                    if subject.lower() in fetch_response.envelope.subject.lower():
                        print("✓ Subject matches our search criteria")
                    else:
                        print("⚠ Subject doesn't exactly match, but proceeding...")

                if fetch_response.envelope and fetch_response.envelope.from_addr:
                    from_list = []
                    for addr in fetch_response.envelope.from_addr:
                        if addr.get("name") and addr.get("email"):
                            from_list.append(f"{addr['name']} <{addr['email']}>")
                        elif addr.get("email"):
                            from_list.append(addr["email"])
                    print(f"From: {', '.join(from_list)}")

                # Check if email is already marked as read
                current_flags = fetch_response.flags or []
                if MessageFlag.SEEN.value in current_flags:
                    print("📧 Email is already marked as read")
                    return True
                else:
                    print("📬 Email is currently unread")

        # Mark the email as read by adding the \Seen flag
        print(f"\nMarking email UID {message_uid} as read...")

        with anyio.move_on_after(30):
            # Use STORE command with enum-based flag handling
            flag_list = build_flag_list(MessageFlag.SEEN)
            store_command = IMAPCommandBuilder.store(str(message_uid), StoreAction.REPLACE.value, flag_list)
            await client._send_command(store_command)

        print("✓ Email marked as read successfully!")

        # Verify the change by fetching the email again
        print("Verifying the change...")
        verify_fetch_items = build_fetch_items(FetchItem.FLAGS)
        with anyio.move_on_after(30):
            verify_messages = await client.fetch_messages(str(message_uid), verify_fetch_items)

        if verify_messages:
            verify_message = verify_messages[0]
            verify_raw = verify_message.get("raw", "")
            if verify_raw:
                verify_result = parser.parse_fetch_response(verify_raw)
                if verify_result.success:
                    verify_flags = verify_result.value.flags or []
                    if MessageFlag.SEEN.value in verify_flags:
                        print("✅ Verification successful: Email is now marked as read!")
                        return True
                    else:
                        print("❌ Verification failed: Email is still not marked as read")
                        return False

        print("⚠ Could not verify the change, but command was sent")
        return True

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
        return False

    finally:
        # Ensure we disconnect properly
        try:
            await client.disconnect()
            print("Disconnected from Gmail.")
        except Exception as e:
            print(f"Warning: Error during disconnect: {e}")


async def main():
    """Main function."""

    # Get subject from command line or use default
    if len(sys.argv) > 1:
        target_subject = sys.argv[1]
    else:
        target_subject = "Test Email"
        print('Usage: python mark_email_as_read.py "Email Subject"')
        print(f"Using default subject: '{target_subject}'")

    print("=" * 80)
    print("AnyRFC IMAP Email Marking Example")
    print("=" * 80)
    print(f"Target subject: {target_subject}")
    print()

    success = await find_and_mark_email_as_read(target_subject)

    print()
    print("=" * 80)
    if success:
        print("🎉 SUCCESS: Email found and marked as read!")
    else:
        print("❌ FAILED: Could not find or mark email as read")
    print("=" * 80)


if __name__ == "__main__":
    anyio.run(main)
