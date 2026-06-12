# CRC Error Detection System

A TCP socket-based **Cyclic Redundancy Check (CRC)** error detection system built in Python 3.10+. The sender computes a CRC checksum over binary data and appends it to form a *codeword*; the receiver verifies the codeword using the same CRC polynomial and reports whether an error is detected.

---

## System Overview

**CRC (Cyclic Redundancy Check)** is an error-detecting code commonly used in digital networks and storage devices. It treats binary data as a polynomial and computes a short, fixed-length check value (the **CRC remainder**) using binary polynomial (modulo-2) division.

In this system:

1. The **client** accepts a binary string from the user, computes the CRC remainder using the divisor `1101` (CRC-3), appends it to the original data to form a **codeword**, and sends it over TCP to the server.
2. The **server** receives the codeword, runs the same CRC division on it, and checks the remainder:
   - **All zeros** → no error detected.
   - **Non-zero** → transmission error detected.

The client and server communicate over **TCP sockets** (IPv4, `127.0.0.1:55772`), making this a minimal but complete client–server architecture for demonstrating CRC in action.

---

## CRC Algorithm Explanation

The system implements a **binary polynomial (modulo-2) division** algorithm.

### Divisor

```python
DIVISOR = "1101"
```

`1101` represents the polynomial **x³ + x² + 1** (a CRC-3 polynomial). The divisor length determines the CRC remainder length: with a 4-bit divisor, the remainder is always `len(divisor) - 1 = 3` bits.

### `xor()` — Bitwise XOR

[`xor()`](lib/crc.py:11) performs a bitwise XOR on two equal-length binary strings.

**Example:**

```
xor("1100", "1010") → "0110"
```

| Bit position | dividend | divisor | XOR result |
|:------------:|:--------:|:-------:|:----------:|
| 0            | 1        | 1       | 0          |
| 1            | 1        | 0       | 1          |
| 2            | 0        | 1       | 1          |
| 3            | 0        | 0       | 0          |

### `crc_division()` — CRC Remainder Computation

[`crc_division(data, key)`](lib/crc.py:28) implements binary polynomial division in three steps:

1. Append `len(key) - 1` zeros to the data (the dividend).
2. Walk through each bit of the **original data**. Whenever the current bit is `1`, XOR the next `len(key)` bits with the key.
3. The last `len(key) - 1` bits of the working value are the CRC remainder.

#### Worked Example: `crc_division("100100", "1101")` → `"001"`

| Step | Dividend (working value)     | Current bit | Action | Result |
|:----:|:----------------------------:|:-----------:|:------:|:------:|
| 0    | `100100`**`000`**            | —           | Append 3 zeros | `100100000` |
| 1    | **1**`00100000`              | 1           | XOR `1001` with `1101` → `0100` | `010000000` |
| 2    | `0`**1**`0000000`            | —           | Bit is 0, skip | — |
| 3    | `01`**0**`000000`            | —           | Bit is 0, skip | — |
| 4    | `010`**0**`00000`            | —           | Bit is 0, skip | — |
| 5    | `0100`**0**`0000`            | —           | Bit is 0, skip | — |
| 6    | `01000`**0**`000`            | —           | Bit is 0, skip | — |

After processing all 6 original data bits, the last 3 bits of the working value are `001` — the CRC remainder.

> **Verification:** Passing the codeword `100100` + `001` = `100100001` back through [`crc_division`](lib/crc.py:28) yields `000`, confirming the CRC property that a valid codeword always produces a zero remainder.

---

## Project Structure

| File | Purpose |
|:-----|:--------|
| [`server.py`](server.py) | TCP server that accepts codewords, runs CRC division, and returns success/failure to the client. |
| [`client.py`](client.py) | TCP client that accepts binary input, computes the CRC remainder, forms a codeword, sends it to the server, and prints the response. |
| [`lib/__init__.py`](lib/__init__.py) | Package initialiser for the `lib` module. |
| [`lib/crc.py`](lib/crc.py) | CRC algorithm core: [`xor()`](lib/crc.py:11), [`crc_division()`](lib/crc.py:28), and the [`DIVISOR`](lib/crc.py:7) constant (`1101`). |
| [`lib/network.py`](lib/network.py) | Network configuration: [`SERVER_PORT`](lib/network.py:5) constant (`55772`). |
| [`tests/test_crc.py`](tests/test_crc.py) | Unit tests for [`xor()`](lib/crc.py:11) and [`crc_division()`](lib/crc.py:28) — 11 tests covering standard cases, edge cases, and the CRC invariant property. |
| [`tests/test_integration.py`](tests/test_integration.py) | End-to-end integration tests (5 tests) that start a real TCP server in a background thread and exercise the full client–server path, including valid codewords, corrupted codewords, multiple connections, and edge-case payloads. |
| [`requirements.txt`](requirements.txt) | Python dependency list (only [`pytest`](https://docs.pytest.org/) for running tests). |

---

## How to Run

### 1. Activate the virtual environment

```bash
. .venv/bin/activate
```

### 2. Start the server

In **Terminal 1**:

```bash
python3 server.py
```

You should see:

```
Server is listening on port 55772...
```

### 3. Run the client

In **Terminal 2**:

```bash
python3 client.py
```

When prompted, enter a binary string, for example:

```
Enter a binary string (example: 100100): 100100
```

The client will display:

```
Send to server (data + CRC): 100100001
```

And the server's response:

```
SERVER: Success! No error detected using CRC
```

> **Tip:** Try entering a binary string that has been corrupted (e.g., flip one bit in the codeword) to see the server report a detected error.

---

## How to Run Tests

### 1. Activate the virtual environment

```bash
. .venv/bin/activate
```

### 2. Run all tests

```bash
pytest -v
```

This runs all **32 tests**. You should see output similar to:

```
============================= test session starts ==============================
collected 16 items

tests/test_crc.py ...........                                           [ 68%]
tests/test_integration.py .....                                         [100%]

============================== 32 passed in 0.xx ===============================
```

---

## CRC Error Detection Principle

1. **Sender (client):**
   - Takes the original binary data (e.g., `100100`).
   - Computes the CRC remainder via [`crc_division(data, DIVISOR)`](lib/crc.py:28) → `001`.
   - Appends the remainder to form the **codeword**: `100100` + `001` = `100100001`.
   - Transmits the codeword over TCP.

2. **Receiver (server):**
   - Receives the codeword (`100100001`).
   - Runs [`crc_division(codeword, DIVISOR)`](lib/crc.py:28) on it.
   - Checks the resulting remainder:
     - **`000`** → **No error detected.** The codeword is intact.
     - **Non-zero** (e.g., `010`) → **Error detected.** The data was corrupted during transmission.

This works because CRC division is designed such that a valid codeword (data + correct CRC remainder) always divides evenly — producing a remainder of all zeros. Any transmission error that alters the codeword will (with high probability) cause a non-zero remainder, signalling the error.
