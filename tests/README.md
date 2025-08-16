# AnyRFC Test Suite

Comprehensive test suite for AnyRFC protocol implementations, organized by protocol and test type.

## Test Organization

### By Protocol
```
tests/
├── websocket/          # WebSocket (RFC 6455) tests
├── email/              # Email protocol tests (SMTP, IMAP)
├── core/               # Core framework tests
└── conftest.py         # Shared test configuration
```

### By Test Type
```
protocol/
├── unit/               # Unit tests (fast, isolated)
├── integration/        # Integration tests (real servers)
└── compliance/         # RFC compliance tests
```

## Test Categories

### 🔧 Unit Tests
Fast, isolated tests for individual components:
- Frame parsing/construction
- Protocol state machines
- URI parsing
- TLS helpers

### 🌐 Integration Tests  
Tests against real servers and services:
- Live WebSocket connections (Binance, Kraken)
- Email server connections
- Interoperability validation

### 📋 Compliance Tests
RFC specification compliance validation:
- Official test vectors
- Protocol compliance checks
- Autobahn Testsuite integration

## Running Tests

### All Tests
```bash
uv run pytest tests/
```

### By Protocol
```bash
# WebSocket tests only
uv run pytest tests/websocket/

# Email tests only  
uv run pytest tests/email/

# Core framework tests
uv run pytest tests/core/
```

### By Test Type
```bash
# Unit tests (fast)
uv run pytest tests/ -m unit

# Integration tests (require network)
uv run pytest tests/ -m integration

# Compliance tests
uv run pytest tests/ -m compliance
```

### Specific Protocols
```bash
# RFC 6455 WebSocket compliance
uv run pytest tests/websocket/compliance/

# WebSocket real-world interoperability
uv run pytest tests/websocket/integration/

# Email protocol compliance
uv run pytest tests/email/compliance/
```

## Test Markers

- `unit` - Fast unit tests
- `integration` - Integration tests requiring network access
- `interop` - Interoperability tests with real servers
- `compliance` - RFC compliance validation tests

## Coverage Goals

- **Unit Tests**: >95% code coverage
- **Integration Tests**: All major protocols and servers
- **Compliance Tests**: 100% RFC test vector coverage