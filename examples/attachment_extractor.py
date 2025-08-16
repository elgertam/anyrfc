#!/usr/bin/env python3
"""
Extract email attachments as BLOBs using AnyRFC IMAP client.

This example demonstrates:
1. Finding emails with attachments using BODYSTRUCTURE
2. Extracting attachment metadata (filename, size, type)
3. Downloading attachment content as binary BLOBs
4. Saving attachments to files or keeping in memory
"""

import anyio
import os
import re
import base64
from anyrfc.core.streams import AnyIOStreamHelpers

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from anyrfc.email.imap import IMAPClient


async def parse_bodystructure(bodystructure_text: str) -> list:
    """Parse IMAP BODYSTRUCTURE to find attachments."""
    attachments = []

    # Look for multipart structures with attachments
    # This is a simplified parser - production would need more robust parsing

    # Find attachment patterns in BODYSTRUCTURE
    # Look for disposition "attachment" or "inline" with filenames
    attachment_patterns = [
        r'attachment.*?filename["\s]*([^")\s]+)',
        r'inline.*?filename["\s]*([^")\s]+)',
        r'name["\s]*([^")\s]+).*?attachment',
    ]

    for pattern in attachment_patterns:
        matches = re.findall(pattern, bodystructure_text, re.IGNORECASE)
        for match in matches:
            if match and "." in match:  # Likely a filename
                attachments.append({"filename": match.strip('"'), "disposition": "attachment"})

    # Look for multipart sections that might be attachments
    # Pattern: ("TYPE" "SUBTYPE" (...) (...) (...) "ENCODING" SIZE ...)
    multipart_pattern = r'\("([^"]+)"\s+"([^"]+)"[^)]+\)\s+[^)]+\)\s+[^)]+\)\s+"([^"]+)"\s+(\d+)'
    multipart_matches = re.findall(multipart_pattern, bodystructure_text)

    for match in multipart_matches:
        media_type, media_subtype, encoding, size = match
        if media_type.lower() not in ["text", "multipart"]:
            attachments.append(
                {
                    "filename": f"attachment.{media_subtype.lower()}",
                    "media_type": media_type,
                    "media_subtype": media_subtype,
                    "encoding": encoding,
                    "size": int(size),
                    "disposition": "attachment",
                }
            )

    return attachments


async def extract_attachment_blob(client: IMAPClient, message_num: int, part_number: str) -> bytes:
    """Extract attachment content as binary BLOB."""
    try:
        # Get next tag
        tag = f"A{client._tag_counter:04d}"
        client._tag_counter += 1

        # Fetch specific body part
        fetch_cmd = f"{tag} FETCH {message_num} (BODY.PEEK[{part_number}])\r\n"

        print(f"📥 Fetching attachment part {part_number}...")
        await AnyIOStreamHelpers.send_all(client._stream, fetch_cmd)

        # Read response
        response_lines = []
        in_literal = False
        literal_size = 0
        literal_data = b""

        while True:
            line = await AnyIOStreamHelpers.read_line(client._stream)
            response_lines.append(line)

            # Check for literal size indicator
            if "{" in line and "}" in line:
                size_match = re.search(r"\{(\d+)\}", line)
                if size_match:
                    literal_size = int(size_match.group(1))
                    in_literal = True
                    continue

            # If we're in a literal, read the exact number of bytes
            if in_literal and literal_size > 0:
                # Read literal data as bytes
                literal_data = await client._stream.receive(literal_size)
                in_literal = False
                continue

            if line.startswith(tag):
                break

            if len(response_lines) > 20:
                break

        if literal_data:
            return literal_data

        # Fallback: extract from text response
        full_response = "".join(response_lines)

        # Look for base64 encoded content
        base64_match = re.search(r"[A-Za-z0-9+/]{20,}={0,2}", full_response)
        if base64_match:
            try:
                return base64.b64decode(base64_match.group(0))
            except Exception:
                pass

        return b""

    except Exception as e:
        print(f"❌ Error extracting attachment: {e}")
        return b""


async def find_emails_with_attachments(client: IMAPClient, limit: int = 10) -> list:
    """Find recent emails that have attachments."""
    try:
        # Search for recent emails
        from datetime import datetime, timedelta

        yesterday = (datetime.now() - timedelta(days=7)).strftime("%d-%b-%Y")

        # Search for emails from the last week
        message_uids = await client.search_messages(f'SINCE "{yesterday}"')

        print(f"📧 Found {len(message_uids)} messages from last week")

        emails_with_attachments = []

        # Check the most recent messages
        recent_uids = message_uids[-limit:] if len(message_uids) > limit else message_uids

        for uid in recent_uids:
            try:
                # Convert UID to message number (simplified)
                msg_num = uid  # In this case, using UID as message number

                # Get BODYSTRUCTURE to check for attachments
                tag = f"A{client._tag_counter:04d}"
                client._tag_counter += 1

                fetch_cmd = f"{tag} FETCH {msg_num} (ENVELOPE BODYSTRUCTURE)\r\n"
                await AnyIOStreamHelpers.send_all(client._stream, fetch_cmd)

                # Read response
                response_lines = []
                while True:
                    line = await AnyIOStreamHelpers.read_line(client._stream)
                    response_lines.append(line)
                    if line.startswith(tag):
                        break
                    if len(response_lines) > 50:
                        break

                full_response = "".join(response_lines)

                # Parse attachments from BODYSTRUCTURE
                attachments = await parse_bodystructure(full_response)

                if attachments:
                    # Extract subject
                    subject = "Unknown Subject"
                    subject_match = re.search(r'ENVELOPE \([^)]*"([^"]*)"', full_response)
                    if subject_match:
                        subject = subject_match.group(1)

                    emails_with_attachments.append(
                        {
                            "message_num": msg_num,
                            "uid": uid,
                            "subject": subject,
                            "attachments": attachments,
                            "bodystructure_response": full_response,
                        }
                    )

                    print(f"📎 Found email with {len(attachments)} attachment(s): '{subject}'")

            except Exception as e:
                print(f"❌ Error checking message {uid}: {e}")
                continue

        return emails_with_attachments

    except Exception as e:
        print(f"❌ Error finding emails with attachments: {e}")
        return []


async def demo_attachment_extraction():
    """Demonstrate attachment extraction capabilities."""

    username = os.getenv("GMAIL_USERNAME")
    password = os.getenv("GMAIL_PASSWORD")

    if not username or not password:
        print("❌ Error: Credentials not found")
        return

    print("📎 AnyRFC Attachment Extraction Demo")
    print("=" * 50)

    client = IMAPClient("imap.gmail.com", 993, use_tls=True)

    try:
        # Connect and authenticate
        print("🔗 Connecting to Gmail...")
        await client.connect()
        await client.authenticate({"username": username, "password": password})
        await client.select_mailbox("INBOX")
        print("✅ Connected and authenticated")

        # Find emails with attachments
        print("\n🔍 Searching for emails with attachments...")
        emails_with_attachments = await find_emails_with_attachments(client, limit=5)

        if not emails_with_attachments:
            print("📭 No emails with attachments found in recent messages")
            print("💡 Send an email with an attachment to your configured email account to test this feature")
            return

        print(f"\n📎 Found {len(emails_with_attachments)} email(s) with attachments:")

        for i, email in enumerate(emails_with_attachments, 1):
            print(f"\n📧 Email {i}:")
            print(f"   Subject: {email['subject']}")
            print(f"   Message: #{email['message_num']}")
            print(f"   Attachments: {len(email['attachments'])}")

            for j, attachment in enumerate(email["attachments"], 1):
                print(f"   📎 Attachment {j}:")
                print(f"      Filename: {attachment.get('filename', 'unknown')}")
                print(
                    f"      Type: {attachment.get('media_type', 'unknown')}/{attachment.get('media_subtype', 'unknown')}"
                )
                print(f"      Size: {attachment.get('size', 'unknown')} bytes")

                # Try to extract the first attachment as a demo
                if j == 1:  # Only extract first attachment
                    print("      🔄 Attempting to extract BLOB...")

                    # Try different part numbers (simplified approach)
                    for part_num in ["2", "1.2", "2.1"]:
                        try:
                            blob_data = await extract_attachment_blob(client, email["message_num"], part_num)
                            if blob_data and len(blob_data) > 0:
                                print(f"      ✅ Extracted {len(blob_data)} bytes as BLOB")
                                print(f"      📊 First 50 bytes: {blob_data[:50]}")

                                # Save to file as demo
                                filename = attachment.get("filename", f"attachment_{email['message_num']}_{j}")
                                safe_filename = re.sub(r"[^a-zA-Z0-9._-]", "_", filename)

                                try:
                                    with open(f"/tmp/{safe_filename}", "wb") as f:
                                        f.write(blob_data)
                                    print(f"      💾 Saved to /tmp/{safe_filename}")
                                except Exception as e:
                                    print(f"      ⚠️ Could not save file: {e}")

                                break
                        except Exception as e:
                            print(f"      ❌ Failed to extract part {part_num}: {e}")
                    else:
                        print("      ❌ Could not extract attachment BLOB")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
    finally:
        await client.disconnect()
        print("\n✅ Disconnected from Gmail")


if __name__ == "__main__":
    print("📎 AnyRFC Email Attachment Extraction")
    print("=" * 60)
    print()
    print("This demo searches for emails with attachments and extracts them as BLOBs.")
    print("It demonstrates:")
    print("• Finding emails with attachments using BODYSTRUCTURE")
    print("• Parsing attachment metadata (filename, size, type)")
    print("• Extracting attachment content as binary data")
    print("• Saving attachments to files")
    print()

    anyio.run(demo_attachment_extraction)
