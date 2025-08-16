# Autobahn Testsuite Integration

The [Autobahn Testsuite](https://github.com/crossbario/autobahn-testsuite) is the industry standard for WebSocket RFC 6455 compliance testing. It contains **500+ test cases** and is used by major libraries including:

- **Netty** (Java)
- **Undertow** (Java) 
- **Qt WebSockets** (C++)
- **Boost Beast** (C++)
- **And many others**

## Quick Start

### 1. Start Autobahn Test Server

```bash
# Start the fuzzing server (in one terminal)
uv run wstest -m fuzzingserver
```

### 2. Run AnyRFC Compliance Tests

```bash
# Run the full test suite (in another terminal)
python tests/compliance/autobahn_runner.py
```

### 3. View Results

```bash
# Open the generated report
open reports/clients/index.html
```

## Test Categories

The Autobahn Testsuite covers:

### **Basic Protocol Compliance**
- Frame format validation
- Opcode handling  
- Payload length encoding
- Masking requirements

### **Message Fragmentation**
- Text message fragmentation
- Binary message fragmentation
- Control frame intermixing
- Continuation frame validation

### **Control Frames**
- Ping/Pong handling
- Close frame processing
- Invalid control frames

### **Error Conditions**
- Invalid UTF-8 in text frames
- Reserved bits usage
- Protocol violations
- Connection state errors

### **Performance & Limits**
- Large message handling
- High frame rates
- Memory usage patterns

## Configuration

The test runner supports both:

- **Strict Mode**: Full RFC 6455 compliance (default)
- **Relaxed Mode**: Real-world server compatibility

```python
# Run in strict RFC compliance mode
await client.run_all_tests(strict_validation=True)

# Run in relaxed mode for real-world compatibility  
await client.run_all_tests(strict_validation=False)
```

## Expected Results

A well-implemented WebSocket client should achieve:

- **95%+ pass rate** in strict mode
- **98%+ pass rate** in relaxed mode

Any failures indicate potential RFC compliance issues that should be investigated.

## Integration with CI/CD

Add to your CI pipeline:

```yaml
- name: Run Autobahn Testsuite
  run: |
    uv run wstest -m fuzzingserver &
    sleep 5
    python tests/compliance/autobahn_runner.py
    pkill wstest
```

## Manual Test Examples

```bash
# Test specific case
uv run wstest -m fuzzingclient -s tests/compliance/autobahn_config.json

# Generate detailed reports
uv run wstest -m fuzzingserver --webport 8080
```

This integration ensures AnyRFC maintains the same compliance standards as major production WebSocket libraries.