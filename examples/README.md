# AnyRFC Examples

This directory contains example scripts demonstrating the capabilities of the AnyRFC library.

## Setup

1. Install dependencies:

   ```bash
   uv sync --group examples
   ```

2. Create a `.env` file in the project root with your credentials:

   ```env
   # For IMAP examples
   IMAP_HOSTNAME=imap.gmail.com
   IMAP_PORT=993
   IMAP_USERNAME=your.email@example.com
   IMAP_PASSWORD=your_app_specific_password
   
   # For Gmail-specific examples (legacy)
   GMAIL_USERNAME=your.email@gmail.com
   GMAIL_PASSWORD=your_app_specific_password
   ```

## WebSocket Examples

### `simple_websocket.py`

Basic WebSocket client demonstrating connection, message sending, and receiving.

```bash
uv run python examples/simple_websocket.py
```

### `websocket_realtime.py`

Advanced WebSocket example with real-time bidirectional communication.

```bash
uv run python examples/websocket_realtime.py
```

## IMAP Email Examples

### `imap_demo.py`

Comprehensive IMAP client demonstration showing:

- Connection and authentication
- Mailbox operations
- Message fetching and parsing
- IMAP extensions usage

```bash
uv run python examples/imap_demo.py
```

### `mark_email_as_read.py`

Find and mark emails as read by subject.

```bash
# Use default subject
uv run python examples/mark_email_as_read.py

# Specify custom subject
uv run python examples/mark_email_as_read.py "Your Email Subject"
```

### `create_draft_email.py`

Create draft emails in your drafts folder using IMAP APPEND.

```bash
# Use default content
uv run python examples/create_draft_email.py

# Specify custom content
uv run python examples/create_draft_email.py "to@example.com" "Subject" "Email body"
```

### `email_monitoring.py`

Real-time email monitoring with live alerts for new messages.

```bash
# Monitor for 5 minutes (default)
uv run python examples/email_monitoring.py

# Monitor for custom duration
uv run python examples/email_monitoring.py 10
```

### `attachment_extractor.py`

Extract email attachments as binary BLOBs.

```bash
uv run python examples/attachment_extractor.py
```

## Requirements

- **Core**: `anyio>=4.0.0`, `httpx>=0.25.0`, `typing-extensions>=4.0.0`
- **Examples**: `python-dotenv>=1.1.1`, `pypdf2>=3.0.1` (for PDF attachment processing)

## Gmail Setup

For Gmail IMAP access:

1. Enable 2-factor authentication on your Google account
2. Generate an app-specific password:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate password for "Mail"
3. Use the app password (not your regular password) in the `.env` file

## Notes

- All examples use AnyIO for structured concurrency
- IMAP examples are tested with Gmail but should work with any RFC-compliant IMAP server
- WebSocket examples work with standard WebSocket servers
- Examples include proper error handling and connection management
- All examples respect IMAP server rate limits and best practices

## Extending Examples

These examples serve as starting points for building more complex applications:

- **Email automation**: Process attachments, auto-respond, filter messages
- **Real-time dashboards**: Monitor multiple email accounts, display metrics
- **Integration systems**: Connect email events to external APIs/databases
- **Protocol testing**: Use examples as basis for compliance testing
- **Multi-protocol apps**: Combine WebSocket and IMAP for real-time email interfaces
