# AnyRFC

> **Complete, RFC-compliant protocol clients built with AnyIO structured concurrency**

[![PyPI version](https://badge.fury.io/py/anyrfc.svg)](https://badge.fury.io/py/anyrfc)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

AnyRFC provides **production-ready, RFC-compliant protocol clients** that prioritize correctness, security, and modern
async patterns. Built exclusively with [AnyIO](https://anyio.readthedocs.io/) for structured concurrency.

## Why AnyRFC?

🎯 **RFC Compliance First** - Every implementation passes comprehensive RFC test suites  
⚡ **Modern Async** - Structured concurrency with AnyIO (no asyncio dependency hell)  
🔒 **Security by Default** - TLS everywhere, proper certificate validation, secure authentication  
🧪 **Battle-Tested** - Real-world interoperability testing against major servers  
📝 **Type Safe** - Full mypy compliance with strict typing  
🚀 **Production Ready** - Complete implementations, not toys or demos  

## Quick Start

```bash
pip install anyrfc
```

```python
import anyio
from anyrfc import WebSocketClient

async def main():
    async with WebSocketClient("wss://echo.websocket.org/") as ws:
        await ws.send_text("Hello, AnyRFC!")
        async for message in ws.receive():
            print(f"Received: {message}")
            break  # Just get the first message

anyio.run(main)
```

## What's Included

### 🌐 WebSocket Client (RFC 6455) - **Production Ready**

Complete WebSocket implementation with all RFC 6455 features:

```python
from anyrfc import WebSocketClient, CloseCode

async with WebSocketClient("wss://api.example.com/ws") as ws:
    # Send different message types
    await ws.send_text("Hello!")
    await ws.send_binary(b"\\x00\\x01\\x02\\x03")

    # Handle incoming messages
    async for message in ws.receive():
        if isinstance(message, str):
            print(f"Text: {message}")
        else:
            print(f"Binary: {message.hex()}")

        if should_close:
            await ws.close(CloseCode.NORMAL_CLOSURE)
            break
```

**Features:**

- ✅ All frame types (text, binary, ping, pong, close)
- ✅ Message fragmentation and reassembly
- ✅ Proper client-side frame masking
- ✅ Extension support framework
- ✅ Graceful connection handling
- ✅ Real-server compatibility

### 📧 Email Clients (IMAP & SMTP) - **Production Ready**

Battle-tested email clients with full RFC compliance and real-world Gmail compatibility:

```python
from anyrfc import IMAPClient, SMTPClient

# IMAP - Complete email operations
async with IMAPClient("imap.gmail.com", use_tls=True) as imap:
    await imap.authenticate({"username": "user", "password": "app_password"})
    await imap.select_mailbox("INBOX")

    # Search and read emails
    messages = await imap.search_messages("UNSEEN")
    for msg_id in messages[:5]:
        email = await imap.fetch_messages(str(msg_id), "BODY[]")
        
        # Mark as read
        await imap.store_message_flags(str(msg_id), [b"\\Seen"], "FLAGS")

    # Create drafts with proper literal continuation
    await imap.append_message("Drafts", email_content, [b"\\Draft"])

    # Extract attachments as binary BLOBs
    bodystructure = await imap.fetch_messages(str(msg_id), "BODYSTRUCTURE")
    # Parse structure and fetch binary parts...

# SMTP - Send emails with authentication
async with SMTPClient("smtp.gmail.com", use_starttls=True) as smtp:
    await smtp.authenticate({"username": "user", "password": "app_password"})
    await smtp.send_message(
        from_addr="sender@example.com",
        to_addrs=["recipient@example.com"],
        message="""Subject: Hello from AnyRFC!

This email was sent using AnyRFC's production-ready SMTP client!
"""
    )
```

**IMAP Features (RFC 9051 Compliant):**

- ✅ **Complete email operations**: Read, flag, search, delete
- ✅ **Draft creation**: APPEND with proper literal continuation
- ✅ **Real-time monitoring**: Live email detection with polling
- ✅ **Attachment extraction**: Binary BLOB downloads (PDFs, images, etc.)
- ✅ **Gmail compatibility**: Tested with live Gmail IMAP servers
- ✅ **Extension support**: IDLE, SORT, THREAD, CONDSTORE, QRESYNC
- ✅ **Production proven**: Handles 178KB+ attachments and complex operations

## Architecture Highlights

### AnyIO Structured Concurrency

Every I/O operation uses AnyIO's structured concurrency primitives:

```python
async def websocket_with_timeout():
    async with anyio.create_task_group() as tg:
        # Connection with automatic cleanup
        tg.start_soon(websocket_handler)

        # Heartbeat with cancellation scope
        with anyio.move_on_after(30):
            tg.start_soon(heartbeat_sender)
```

### RFC Compliance Testing

```python
from anyrfc.websocket import WebSocketClient

client = WebSocketClient("wss://example.com")
compliance_report = await client.validate_compliance()

# Returns detailed RFC 6455 test results
assert compliance_report["handshake_validation"] == True
assert compliance_report["frame_parsing"] == True
assert compliance_report["close_sequence"] == True
```

### Type Safety

```python
from anyrfc import WebSocketClient
from anyrfc.websocket import WSFrame, OpCode

# Fully typed interfaces
client: WebSocketClient = WebSocketClient("wss://api.example.com")
frame: WSFrame = WSFrame(fin=True, opcode=OpCode.TEXT, payload=b"test")

# MyPy validates everything
reveal_type(client.websocket_state)  # WSState
reveal_type(await client.receive())  # Union[str, bytes]
```

## Installation & Setup

### Basic Installation

```bash
pip install anyrfc
```

### Development Setup

```bash
git clone https://github.com/elgertam/anyrfc.git
cd anyrfc

# Install with uv (recommended)
uv sync --all-extras

# Or with pip
pip install -e ".[dev]"
```

### Requirements

- **Python**: 3.11+
- **Core**: `anyio>=4.0.0`
- **HTTP**: `httpx>=0.25.0` (approved dependency)
- **Types**: `typing-extensions>=4.0.0`

## Real-World Examples

### WebSocket Trading Client

```python
from anyrfc import WebSocketClient
import json

async def crypto_prices():
    # Binance public data stream (no authentication required)
    uri = "wss://data-stream.binance.vision/ws/btcusdt@ticker"

    # Use relaxed validation for real-world servers
    async with WebSocketClient(uri, strict_rfc_validation=False) as ws:
        async for message in ws.receive():
            data = json.loads(message)
            if 'c' in data:  # Current price
                price = float(data['c'])
                change = float(data['P'])  # 24hr change %
                print(f"💰 BTC-USDT: ${price:,.2f} ({change:+.2f}%)")
```

### Email Monitoring Service

```python
from anyrfc import IMAPClient
import anyio
import re

async def email_monitor():
    """Real-time email monitoring with secret code extraction."""
    async with IMAPClient("imap.gmail.com", use_tls=True) as imap:
        await imap.authenticate({"username": "user", "password": "app_password"})
        await imap.select_mailbox("INBOX")

        while True:
            # Check for new emails every 5 seconds (production-tested)
            unread = await imap.search_messages("UNSEEN")
            if unread:
                print(f"📧 {len(unread)} new emails!")
                
                for msg_id in unread:
                    # Fetch email content
                    email_data = await imap.fetch_messages(str(msg_id), "BODY[]")
                    email_text = email_data[str(msg_id)][b"BODY[]"].decode()
                    
                    # Extract verification codes (6 digits)
                    codes = re.findall(r'\b\d{6}\b', email_text)
                    if codes:
                        print(f"🔐 Verification code found: {codes[0]}")
                    
                    # Mark as read
                    await imap.store_message_flags(str(msg_id), [b"\\Seen"], "FLAGS")

            await anyio.sleep(5)  # 5-second polling proven effective
```

## Testing & Quality

### Comprehensive Test Suite

```bash
# Run all tests
uv run pytest

# RFC compliance tests
uv run pytest tests/rfc_compliance/ -v

# Real-server interoperability
uv run pytest tests/interop/ -v

# Type checking
uv run mypy src/

# Linting
uv run ruff check src/
```

### Real-Server Testing

AnyRFC is extensively tested against production servers:

- ✅ **WebSocket**: echo.websocket.org, Binance WebSocket API, major services
- ✅ **IMAP**: Live Gmail operations (read, flag, drafts, attachments)
- ✅ **SMTP**: Gmail, SendGrid, major SMTP services
- ✅ **Production verified**: Real-time email monitoring, 178KB+ file transfers
- ✅ **Compliance tested**: Autobahn WebSocket suite, RFC test vectors

## Protocol Roadmap

### ✅ Phase 1: WebSocket Foundation (Complete)

- [x] WebSocket Client (RFC 6455) - **Production Ready**
- [x] Autobahn test suite compliance
- [x] Real-world server compatibility

### ✅ Phase 2: Email Infrastructure (Complete)

- [x] **IMAP Client (RFC 9051) - Production Ready**
  - [x] Complete email operations (read, flag, search, delete)
  - [x] Draft creation with literal continuation
  - [x] Attachment extraction (binary BLOBs)
  - [x] Real-time email monitoring
  - [x] Gmail production testing
  - [x] Extensions: IDLE, SORT, THREAD, CONDSTORE, QRESYNC
- [x] SMTP Client Foundation (RFC 5321)
- [x] SASL authentication framework (RFC 4422)

### 🚧 Phase 3: OAuth & Modern Auth (In Progress)

- [ ] OAuth 2.0 client (RFC 6749/6750)
- [ ] JWT handling (RFC 7519)
- [ ] PKCE support (RFC 7636)
- [ ] Device authorization flow (RFC 8628)
- [ ] MIME message composition (RFC 2045-2049)
- [ ] Advanced SMTP features (DKIM, SPF validation)

### 🔮 Phase 4: Advanced Protocols

- [ ] SSH client suite (RFC 4251-4254)
- [ ] SFTP file transfer
- [ ] DNS-over-HTTPS (RFC 8484)
- [ ] CoAP for IoT (RFC 7252)

## Performance

AnyRFC is built for production workloads:

```python
# Concurrent WebSocket connections
async def stress_test():
    async with anyio.create_task_group() as tg:
        for i in range(100):
            tg.start_soon(websocket_worker, f"wss://api{i}.example.com")

# Memory-efficient message streaming
async def large_mailbox():
    async with IMAPClient("imap.example.com") as imap:
        # Stream large mailboxes without loading everything into memory
        async for message in imap.fetch_messages("1:*", "BODY[]"):
            await process_message(message)  # Process one at a time
```

## Contributing

We welcome contributions! AnyRFC follows strict quality standards:

1. **RFC Compliance**: All features must be RFC-compliant
2. **AnyIO Only**: No asyncio imports allowed
3. **Type Safety**: Full mypy compliance required
4. **Real-World Testing**: Test against actual servers
5. **Security First**: Secure by default

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## Security

- 🔒 **TLS Everywhere**: Secure connections by default
- 🛡️ **Input Validation**: Strict RFC-compliant parsing
- 🔐 **Credential Safety**: Never logs or stores credentials insecurely
- 📋 **Security Audits**: Regular dependency and code security reviews

Report security issues to: [andrew@elgert.org](mailto:andrew@elgert.org)

## License

MIT License - see [LICENSE](LICENSE) for details.

## Why "AnyRFC"?

**Any** + **RFC** = Protocol clients that work with **any** server implementing the **RFC** standard. Built on
**AnyIO** for structured concurrency.

---

**Built by [Andrew M. Elgert](https://github.com/elgertam) • [Documentation](https://github.com/elgertam/anyrfc#readme) • [Issues](https://github.com/elgertam/anyrfc/issues) • [PyPI](https://pypi.org/project/anyrfc/)**
