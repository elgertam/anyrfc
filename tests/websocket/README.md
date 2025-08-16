# WebSocket Tests (RFC 6455)

Comprehensive test suite for WebSocket protocol implementation.

## Test Structure

### 🔧 Unit Tests (`unit/`)
Fast, isolated tests for WebSocket components:
- Frame parsing and construction
- Handshake logic
- Protocol state machine
- Masking/unmasking operations

### 🌐 Integration Tests (`integration/`)
Tests against real WebSocket servers:
- `test_websocket_interop.py` - Echo servers and real services
- `test_ping_compliance.py` - Ping/pong functionality with live servers

### 📋 Compliance Tests (`compliance/`)
RFC 6455 specification compliance:
- `test_rfc6455_vectors.py` - Official RFC test vectors
- `test_autobahn.py` - Autobahn Testsuite integration
- `autobahn_runner.py` - Complete compliance test runner

## Running WebSocket Tests

### All WebSocket Tests
```bash
uv run pytest tests/websocket/ -v
```

### By Test Type
```bash
# Unit tests (fast)
uv run pytest tests/websocket/unit/ -v

# Integration tests (network required)
uv run pytest tests/websocket/integration/ -v

# RFC compliance tests
uv run pytest tests/websocket/compliance/ -v
```

### Specific Test Suites
```bash
# RFC 6455 test vectors
uv run pytest tests/websocket/compliance/test_rfc6455_vectors.py -v

# Real server interoperability
uv run pytest tests/websocket/integration/test_websocket_interop.py -v

# Autobahn Testsuite (requires server)
python tests/websocket/compliance/autobahn_runner.py
```

## Autobahn Testsuite

Industry-standard WebSocket compliance testing:

1. **Start test server**: `uv run wstest -m fuzzingserver`
2. **Run compliance tests**: `python tests/websocket/compliance/autobahn_runner.py`  
3. **View results**: `open reports/clients/index.html`

## Test Coverage

- ✅ **Frame Types**: Text, binary, ping, pong, close, continuation
- ✅ **Protocol Features**: Masking, fragmentation, extensions
- ✅ **Error Conditions**: Invalid frames, oversized payloads
- ✅ **Real Servers**: Binance, Kraken, echo servers
- ✅ **RFC Compliance**: Official test vectors and Autobahn suite