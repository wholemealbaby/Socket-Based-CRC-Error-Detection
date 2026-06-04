# Prompt: Build a CRC Error Detection System from Scratch (with Tests)

```
You are a software engineer building a CRC-based error detection system over TCP.
I need you to implement the full system from scratch — including the CRC algorithm,
a TCP client, a TCP server, and a comprehensive test suite — based ONLY on the
specifications below. Do not reference or copy any existing code; build everything
from these requirements.

---

## Specification

### 1. CRC Algorithm (library module)

The project must include a reusable CRC library module with the following:

#### 1.1 Constants
- A divisor (polynomial key) of `1101` (binary). This is a 3-bit CRC polynomial.

#### 1.2 `xor(dividend: str, divisor: str) -> str`
- Accept two binary strings of equal length.
- Perform a bitwise XOR operation.
- Return the result as a binary string.
- Example: `xor("1100", "1010")` → `"0110"`.

#### 1.3 `crc_division(data: str, key: str) -> str`
- Accept a binary string `data` and a binary string `key` (the polynomial divisor).
- Implement binary polynomial division (modulo-2 division, i.e., XOR-based):
  1. Append `len(key) - 1` zeros to the data (this is the dividend).
  2. Walk through the dividend bit by bit from left to right.
  3. Whenever the current bit is `1`, XOR the next `len(key)` bits with the key.
  4. After processing all original data bits, the last `len(key) - 1` bits of the
     working value are the CRC remainder.
- Return the remainder as a binary string of length `len(key) - 1`.
- Example: `crc_division("100100", "1101")` → `"001"`.

#### 1.4 Codeword property
- A **codeword** is formed as `data + remainder`.
- If you pass a valid codeword back through `crc_division()` with the same key,
  the remainder MUST be all zeros (i.e., `"00"` for a 3-bit CRC).
  This is the fundamental invariant of CRC error detection.

### 2. Network Configuration (separate module)

- Define a default server port constant: `55772`.
- This module should be importable by both client and server.

### 3. TCP Server

The server must:
- Create a TCP socket bound to `127.0.0.1` on the default port.
- Listen for incoming connections (backlog of 5).
- Accept a connection, then:
  - Receive up to 1024 bytes from the client, decoded as a UTF-8 string.
  - Treat the received string as a binary codeword (data + CRC).
  - Run `crc_division()` on the codeword using the divisor `1101`.
  - If the remainder is all zeros → send back the message
    `"SERVER: Success! No error detected using CRC"`
  - If the remainder is non-zero → send back the message
    `"SERVER: Failure! Error detected using CRC"`
  - Close the client connection.
- Continue accepting new connections until interrupted (Ctrl+C).
- Handle `KeyboardInterrupt` gracefully by shutting down the server socket.
- Print status messages to stdout (connection info, errors detected, etc.).

### 4. TCP Client

The client must:
- Prompt the user to enter a binary string (e.g., `"100100"`).
- Compute the CRC remainder of that data using `crc_division()` and the divisor `1101`.
- Form the codeword as `data + remainder`.
- Print the codeword to stdout.
- Create a TCP socket and connect to `127.0.0.1` on the default port.
- Send the codeword as a UTF-8 encoded string.
- Receive the server's response (up to 1024 bytes) and print it.
- Close the connection.

### 5. Testing

Write tests using **pytest**. Do NOT depend on any external test utilities beyond
pytest and the Python standard library. Tests go in a `tests/` directory.

#### 5.1 Unit Tests (no network required)

Test `xor()`:
- Standard case: `xor("1100", "1010")` → `"0110"`
- All bits set: `xor("111", "111")` → `"000"`
- No bits set: `xor("000", "111")` → `"111"`
- Single bit: `xor("1", "1")` → `"0"`
- Mismatched length (if not validated, document the behaviour)

Test `crc_division()`:
- Known case: `crc_division("100100", "1101")` → `"001"`
- Verify the remainder length is always `len(key) - 1`
- **Codeword validity property**: For any random data string, compute
  `remainder = crc_division(data, key)`, then verify
  `crc_division(data + remainder, key)` produces all zeros.
- Edge cases: empty string, single-bit data, data shorter than key.

#### 5.2 End-to-End Tests (network required; run against a real server)

Use pytest fixtures to manage the server lifecycle:
- Start the server in a background thread listening on `127.0.0.1`.
- Use **a random available port** (port 0) — do NOT hardcode port 55772.
- Gracefully shut down the server after each test (fixture teardown).

Tests:
- **Valid codeword**: Send a correctly computed codeword. Assert the response
  contains `"Success! No error detected using CRC"`.
- **Corrupted codeword**: Send a valid codeword, then flip one bit, and send it.
  Assert the response contains `"Failure! Error detected using CRC"`.
- **Multiple connections**: Send valid codewords across 3 sequential connections
  to the same server instance. All 3 should succeed.
- **Empty/malformed data**: Send an empty string or a non-binary string.
  Document and test the server's behaviour.

### 6. Project Structure

```
<project-root>/
├── lib/
│   ├── __init__.py
│   ├── crc.py          # CRC algorithm (xor, crc_division, DIVISOR)
│   └── network.py      # SERVER_PORT constant
├── client.py            # TCP client
├── server.py            # TCP server
├── tests/
│   ├── __init__.py
│   ├── test_crc.py      # Unit tests for CRC functions
│   └── test_integration.py  # End-to-end client-server tests
├── requirements.txt     # pytest only
└── README.md            # Explain the system, the CRC algorithm, how to run
```

### 7. Constraints

- Python 3.10+.
- Single `pytest` command runs all tests.
- The server must use `threading` for the test fixture (not `subprocess`).
- The E2E tests must NOT hardcode port 55772 — bind to port 0 and retrieve
  the actual port from the socket.
- All binary strings are plain Python `str` objects containing only `'0'` and `'1'`.
- Include clear docstrings and type hints on all public functions.
```
