# Plan: Improve Test Coverage of Client–Server Interaction

## Current Gaps

After reviewing [`tests/test_integration.py`](../tests/test_integration.py), [`client.py`](../client.py), and [`server.py`](../server.py), the following gaps were identified:

| # | Gap | Severity |
|---|-----|----------|
| 1 | [`server_fixture`](../tests/test_integration.py:40) uses `time.sleep(0.1)` — flaky on slow systems | Medium |
| 2 | [`test_corrupted_codeword`](../tests/test_integration.py:88) bypasses `client.py` via `_raw_send` | High |
| 3 | [`test_empty_malformed_data`](../tests/test_integration.py:127) bypasses `client.py` via `_raw_send` | High |
| 4 | No test for client behavior when server is down (connection refused) | High |
| 5 | No test for client handling of a `"Failure"` server response | Medium |
| 6 | No test exercising payloads near or exceeding the 1024-byte `recv` buffer | Low |

---

## Proposed Changes

### Refinement 1: Robust server fixture — polling retry

**File:** [`tests/test_integration.py`](../tests/test_integration.py)

**What:** Replace the fixed `time.sleep(0.1)` at line 59 with a polling loop that retries connecting to the server port until it's ready.

**Why:** Eliminates test flakiness on loaded or slow systems.

**How:**
```python
# Before (line 59):
time.sleep(0.1)

# After:
# Poll until the server port is accepting connections
import socket
for _ in range(50):  # up to ~2.5 s
    try:
        with socket.create_connection(("127.0.0.1", actual_port), timeout=0.5):
            break  # server is ready
    except ConnectionRefusedError:
        time.sleep(0.05)
else:
    raise RuntimeError(f"Server on port {actual_port} failed to start")
```

---

### Refinement 2: Refactor `test_empty_malformed_data` to use `client.run_client()`

**File:** [`tests/test_integration.py`](../tests/test_integration.py)

**What:** Replace `_raw_send` with `client.run_client()` and use `capsys` to verify output, similar to the other tests.

**Why:** Exercises the full client–server code path (CRC computation, codeword construction, socket I/O, response printing).

**Details:**
- `data=""` → client computes `crc_division("", DIVISOR)` → `"000"`, sends codeword `"000"`, server accepts it
- `data="hello"` → client computes `crc_division("hello", DIVISOR)` → `"000"` (no `"1"` bits), sends `"hello000"`, server accepts it
- Assert on `captured.out` instead of raw socket response

---

### New Test 1: Connection-refused test

**File:** [`tests/test_integration.py`](../tests/test_integration.py) (or a separate file)

**What:** Call `client.run_client()` against a port with no server listening and verify the expected error.

**Why:** The client's socket `connect()` at [`client.py:41`](../client.py:41) will raise `ConnectionRefusedError`. Currently untested.

**How:**
```python
def test_connection_refused(self) -> None:
    """client.run_client raises ConnectionRefusedError when no server is listening."""
    import client
    with pytest.raises(ConnectionRefusedError):
        client.run_client(host="127.0.0.1", port=1, data="1010")
```

---

### New Test 2: Client handles "Failure" server response gracefully

**File:** [`tests/test_integration.py`](../tests/test_integration.py)

**What:** Start a minimal mock server that always returns a `"Failure"` message, point `client.run_client()` at it, verify the client prints the failure message without crashing.

**Why:** The client's [`recv` + `print` block](../client.py:44-45) is never tested with a failure response. A `"Failure"` response could theoretically contain unexpected formatting or cause an exception.

**How:**
```python
def test_failure_response_handling(self) -> None:
    """Client gracefully prints a Failure response from the server."""
    import client

    # Start a minimal mock server that always returns Failure
    def _mock_server(host: str, port: int) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((host, port))
            s.listen(1)
            conn, _ = s.accept()
            with conn:
                conn.recv(1024)  # discard codeword
                conn.sendall(b"SERVER: Failure! Error detected using CRC")

    mock_port = _find_free_port()
    t = threading.Thread(
        target=_mock_server,
        args=("127.0.0.1", mock_port),
        daemon=True,
    )
    t.start()
    time.sleep(0.1)

    client.run_client(host="127.0.0.1", port=mock_port, data="1010")
    captured = capsys.readouterr()
    assert "Failure" in captured.out
```

Consider using the existing `server_fixture` pattern and the `_find_free_port` helper to factor out boilerplate.

---

### New Test 3: Large-payload test

**File:** [`tests/test_integration.py`](../tests/test_integration.py)

**What:** Send data large enough that the resulting codeword exceeds or approaches the 1024-byte `recv` buffer used by both client and server.

**Why:** Both [`server.py:37`](../server.py:37) and [`client.py:44`](../client.py:44) use `recv(1024)`. A single `recv(1024)` call may not receive the full payload in one shot if the data is large. This test documents whether the implementation handles this correctly or silently truncates.

**How:**
```python
def test_large_payload(self, server_fixture: int, capsys) -> None:
    """Client–server handles a payload near the 1024-byte recv buffer boundary."""
    import client
    # Generate 1000 bits of data
    data = "1010" * 250  # 1000 bits
    client.run_client(host="127.0.0.1", port=server_fixture, data=data)
    captured = capsys.readouterr()
    assert "Success" in captured.out
```

---

## Summary of Files Changed

| File | Change |
|------|--------|
| [`tests/test_integration.py`](../tests/test_integration.py) | Refinement 1, 2 + New tests 1, 2, 3 |

No changes to [`client.py`](../client.py), [`server.py`](../server.py), or [`lib/`](../lib/) are required — the tests cover existing code paths.

---

## Execution Order

```mermaid
flowchart LR
    A[Refinement 1: polling fixture] --> B[Refinement 2: refactor test_empty_malformed_data]
    B --> C[New test 1: connection-refused]
    C --> D[New test 2: failure-response handling]
    D --> E[New test 3: large payload]
    E --> F[Run full suite: pytest -v]
```

Each step is independent enough that they can be parallelised, but order 1→2 ensures the fixture is reliable before adding new tests.
