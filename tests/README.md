# AnyRFC Test Suite

Comprehensive test suite for AnyRFC protocol implementations, organized by test type and protocol.

## Test Organization

### Current Structure

```dir
tests/
├── conftest.py                    # Pytest configuration and shared fixtures
├── unit/                          # Unit tests for individual components
│   ├── core/                      # Core functionality tests
│   ├── email/                     # Email protocol tests (IMAP, SMTP)
│   │   └── imap/                  # IMAP-specific tests
│   └── parsing/                   # Parser framework tests
├── integration/                   # Integration tests with real services
├── rfc_compliance/               # RFC compliance validation tests
│   └── imap/                     # IMAP RFC 9051 compliance tests
└── websocket/                    # WebSocket protocol tests
    ├── unit/                     # WebSocket unit tests
    ├── integration/              # WebSocket integration tests
    └── compliance/               # WebSocket RFC 6455 compliance tests
```

### Design Principles

- **Test Type First**: Unit, integration, and compliance tests are organized by type
- **Protocol Specific**: WebSocket maintains its own structure due to comprehensive testing
- **Consistent Structure**: All protocols follow the same organizational pattern

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
uv run pytest tests/unit/email/

# Core framework tests
uv run pytest tests/unit/core/

# Parser framework tests
uv run pytest tests/unit/parsing/
```

### By Test Type

```bash
# Unit tests (fast)
uv run pytest tests/unit/

# Integration tests (require network)
uv run pytest tests/integration/

# RFC compliance tests
uv run pytest tests/rfc_compliance/

# WebSocket-specific tests
uv run pytest tests/websocket/
```

### Specific Protocols

```bash
# RFC 6455 WebSocket compliance
uv run pytest tests/websocket/compliance/

# WebSocket real-world interoperability
uv run pytest tests/websocket/integration/

# IMAP RFC 9051 compliance
uv run pytest tests/rfc_compliance/imap/

# IMAP unit tests
uv run pytest tests/unit/email/imap/
```

## Test Markers

- `unit` - Fast unit tests
- `integration` - Integration tests requiring network access
- `interop` - Interoperability tests with real servers
- `compliance` - RFC compliance validation tests

## Dependencies

Test dependencies are managed in `pyproject.toml` under `[dependency-groups]`:

### `dev` group

- `pytest` - Test framework
- `mypy` - Type checking
- `ruff` - Linting and formatting
- `coverage` - Test coverage analysis
- `autobahntestsuite` - WebSocket compliance testing
- `commitizen` - Conventional commits
- `twine` - Package publishing

### `examples` group

- `python-dotenv` - Environment variable management for examples

### `notebook` group

- `jupyter` - Interactive notebooks
- `pandas` - Data analysis
- `matplotlib` - Plotting

### Installation

```bash
# Development and testing
uv sync --group dev

# Example running
uv sync --group examples

# Data analysis
uv sync --group notebook

# Multiple groups
uv sync --group dev --group examples
```

## Coverage Goals

- **Unit Tests**: >95% code coverage
- **Integration Tests**: All major protocols and servers
- **Compliance Tests**: 100% RFC test vector coverage
