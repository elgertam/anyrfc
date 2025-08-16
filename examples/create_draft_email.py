#!/usr/bin/env python3
"""
Create draft email example using AnyRFC IMAP client.

This example demonstrates how to:
1. Connect to Gmail via IMAP
2. Compose a properly formatted email message
3. Save the email as a draft in the Drafts folder using IMAP APPEND

IMPORTANT: Gmail requires app-specific passwords for IMAP access.
1. Enable 2-factor authentication on your Google account
2. Generate an app password for "Mail" in your Google Account settings
3. Use the app password (not your regular password) in GMAIL_PASSWORD

Setup:
1. Create a .env file with:
   GMAIL_USERNAME=your.email@gmail.com
   GMAIL_PASSWORD=your_app_specific_password
2. Run: uv sync --group examples
3. Run: uv run python examples/create_draft_email.py
"""

import anyio
import os
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate, make_msgid

# Load environment variables
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed. Using os.environ directly.")

from anyrfc.email.imap import IMAPClient


async def create_draft_email(to_email: str, subject: str, body: str, from_name: str = "AnyRFC Demo") -> bool:
    """
    Create and save a draft email in Gmail's Drafts folder.

    Args:
        to_email: Recipient email address
        subject: Email subject line
        body: Email body content
        from_name: Sender display name

    Returns:
        bool: True if draft was created successfully, False otherwise
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

        # Compose the email message
        print("Composing email message...")

        # Create a multipart message
        msg = MIMEMultipart()

        # Set headers
        msg["From"] = f"{from_name} <{username}>"
        msg["To"] = to_email
        msg["Subject"] = subject
        msg["Date"] = formatdate(localtime=True)
        msg["Message-ID"] = make_msgid()

        # Add X-Draft header to indicate this is a draft
        msg["X-Draft"] = "true"

        # Create body
        body_part = MIMEText(body, "plain", "utf-8")
        msg.attach(body_part)

        # Convert message to string
        email_content = msg.as_string()

        print("Email composed:")
        print(f"From: {msg['From']}")
        print(f"To: {msg['To']}")
        print(f"Subject: {msg['Subject']}")
        print(f"Body length: {len(body)} characters")
        print()

        # Check if Drafts folder exists and select it
        print("Accessing Drafts folder...")

        # List mailboxes to find the Drafts folder
        with anyio.move_on_after(10):
            mailboxes = await client.list_mailboxes()

        # Find the Drafts folder (it might be named differently)
        drafts_folder = None
        for mailbox in mailboxes:
            mailbox_name = mailbox.get("name", "").lower()
            if "drafts" in mailbox_name or mailbox_name == "[gmail]/drafts":
                drafts_folder = mailbox.get("name")
                break

        # If we can't find Drafts, try common variations
        if not drafts_folder:
            common_drafts_names = ["Drafts", "[Gmail]/Drafts", "INBOX.Drafts", "Draft"]
            for name in common_drafts_names:
                try:
                    # Try to select this folder to see if it exists
                    await client.select_mailbox(name)
                    drafts_folder = name
                    print(f"Found Drafts folder: {name}")
                    break
                except Exception:
                    continue

        if not drafts_folder:
            print("Warning: Could not find Drafts folder, using INBOX instead")
            drafts_folder = "INBOX"
        else:
            print(f"Using Drafts folder: {drafts_folder}")

        # Append the email to the Drafts folder
        print(f"Saving draft to {drafts_folder}...")

        success = False
        with anyio.move_on_after(30):
            # Use the MessageManager to append the email
            # Mark it as a draft with \Draft flag (if supported)
            success = await client.messages.append_message(
                mailbox=drafts_folder,
                message=email_content,
                flags=["\\Draft"],  # Mark as draft
                internal_date=datetime.now(),
            )

        if success:
            print("✅ Draft email created successfully!")

            # Verify by checking the Drafts folder
            print("Verifying draft was created...")

            with anyio.move_on_after(10):
                mailbox_info = await client.select_mailbox(drafts_folder)

            total_messages = mailbox_info.get("exists", 0)
            print(f"📧 {drafts_folder} now contains {total_messages} messages")

            return True
        else:
            print("❌ Failed to create draft email")
            return False

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

    print("=" * 80)
    print("AnyRFC IMAP Draft Email Creation Example")
    print("=" * 80)
    print()

    import sys

    # Get email details from command line or use defaults
    if len(sys.argv) >= 4:
        to_email = sys.argv[1]
        subject = sys.argv[2]
        body = sys.argv[3]
    else:
        to_email = "test@example.com"
        subject = "Test Draft from AnyRFC"
        body = """Hello!

This is a test draft email created using the AnyRFC library.

AnyRFC is a complete, RFC-compliant protocol client library that supports:
- IMAP email operations (like creating this draft!)
- WebSocket connections
- SMTP email sending
- And much more!

This draft was created using the IMAP APPEND command and should appear
in your email Drafts folder.

Best regards,
AnyRFC Demo

---
Generated on {timestamp}
""".format(timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        if len(sys.argv) == 1:
            print('Usage: python create_draft_email.py "to@example.com" "Subject" "Body"')
            print("Using default values for demo...")

    print("Creating draft email:")
    print(f"To: {to_email}")
    print(f"Subject: {subject}")
    print()

    success = await create_draft_email(to_email=to_email, subject=subject, body=body, from_name="AnyRFC Demo")

    print()
    print("=" * 80)
    if success:
        print("🎉 SUCCESS: Draft email created in Gmail!")
        print("👀 Check your Gmail Drafts folder to see the new draft!")
    else:
        print("❌ FAILED: Could not create draft email")
    print("=" * 80)


if __name__ == "__main__":
    anyio.run(main)
