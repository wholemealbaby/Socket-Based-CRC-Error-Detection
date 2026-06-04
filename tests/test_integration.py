"""End-to-end integration tests for the CRC client–server system.

Tests use a real TCP server started in a daemon background thread so that
the full client–server data path is exercised.
"""

import socket
import threading
import time

import pytest

from lib.crc import crc_division, DIVISOR
import server


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _raw_send(host: str, port: int, payload: str) -> str:
    """Send *payload* over a raw TCP socket and return the decoded response.

    Uses ``shutdown(SHUT_WR)`` after sending so the server sees EOF even
    when the payload is empty (``sendall(b"")`` is a no-op).
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((host, port))
        if payload:
            sock.sendall(payload.encode("utf-8"))
        sock.shutdown(socket.SHUT_WR)
        response = sock.recv(1024).decode("utf-8")
    return response


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def server_fixture() -> int:
    """Start the CRC server on a random port in a daemon background thread.

    Yields:
        The port number that the server is listening on.
    """
    # 1. Find a free ephemeral port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        actual_port = s.getsockname()[1]

    # 2. Start the server in a daemon thread
    t = threading.Thread(
        target=server.run_server,
        args=("127.0.0.1", actual_port),
        daemon=True,
    )
    t.start()
    # Poll until the server port is accepting connections
    import socket as _socket
    for _ in range(50):
        try:
            with _socket.create_connection(("127.0.0.1", actual_port), timeout=0.5):
                break
        except ConnectionRefusedError:
            time.sleep(0.05)
    else:
        raise RuntimeError(f"Server on port {actual_port} failed to start within timeout")

    # 3. Yield the port to tests
    yield actual_port

    # No explicit teardown is needed: the daemon thread is automatically
    # terminated when the test process exits.  The server's KeyboardInterrupt
    # handler will fire if the process receives SIGINT.


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _find_free_port() -> int:
    """Return a temporary free TCP port on 127.0.0.1."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

class TestIntegration:
    """End-to-end client–server integration tests."""

    def test_valid_codeword(self, server_fixture: int, capsys: pytest.CaptureFixture) -> None:
        """Send a valid codeword via :func:`client.run_client` and expect success."""
        import client

        actual_port = server_fixture
        client.run_client(host="127.0.0.1", port=actual_port, data="100100")

        captured = capsys.readouterr()
        assert "Success" in captured.out, (
            f"Expected 'Success' in client output, got: {captured.out}"
        )

    def test_corrupted_codeword(self, server_fixture: int) -> None:
        """Send a codeword with one bit flipped; the server must detect the error."""
        actual_port = server_fixture

        # Build a valid codeword
        data = "100100"
        remainder = crc_division(data, DIVISOR)
        codeword = data + remainder

        # Flip bit 0
        corrupted = list(codeword)
        corrupted[0] = "1" if corrupted[0] == "0" else "0"
        corrupted = "".join(corrupted)

        response = _raw_send("127.0.0.1", actual_port, corrupted)
        assert "Failure" in response, (
            f"Expected 'Failure' in server response, got: {response}"
        )

    def test_multiple_connections(self, server_fixture: int, capsys: pytest.CaptureFixture) -> None:
        """Three sequential valid connections to the same server all succeed."""
        import client

        actual_port = server_fixture

        for i in range(3):
            client.run_client(host="127.0.0.1", port=actual_port, data="1010")
            captured = capsys.readouterr()
            assert "Success" in captured.out, (
                f"Connection {i + 1} failed: {captured.out}"
            )

    @pytest.mark.parametrize(
        "payload, description",
        [
            ("", "empty string"),
            ("hello", "non-binary (alphabetic) string"),
        ],
    )
    def test_empty_malformed_data(
        self, server_fixture: int, payload: str, description: str, capsys: pytest.CaptureFixture
    ) -> None:
        """Send edge-case payloads through the full client code path.

        Exercises the entire client code path (CRC computation → codeword
        construction → socket send → response print) instead of testing
        the server in isolation.
        """
        actual_port = server_fixture
        import client
        client.run_client(host="127.0.0.1", port=actual_port, data=payload)

        captured = capsys.readouterr()
        # The server does not raise an exception; it responds with a
        # success message because the CRC remainder of non-binary data
        # (treated as all-zeros) is itself all zeros.
        assert "Success" in captured.out, (
            f"Unexpected output for {description} (payload={payload!r}): "
            f"{captured.out}"
        )

    def test_connection_refused(self) -> None:
        """``client.run_client`` raises ``ConnectionRefusedError`` when no server is listening."""
        import client

        with pytest.raises(ConnectionRefusedError):
            client.run_client(host="127.0.0.1", port=1, data="1010")

    def test_failure_response_handling(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        """Client gracefully prints a Failure response from the server without crashing."""
        import client

        # Start a minimal mock server that always returns Failure
        mock_port = _find_free_port()

        def _mock_server() -> None:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("127.0.0.1", mock_port))
                s.listen(1)
                conn, _ = s.accept()
                with conn:
                    conn.recv(1024)  # discard codeword
                    conn.sendall(
                        b"SERVER: Failure! Error detected using CRC"
                    )

        t = threading.Thread(target=_mock_server, daemon=True)
        t.start()
        time.sleep(0.1)

        client.run_client(host="127.0.0.1", port=mock_port, data="1010")

        captured = capsys.readouterr()
        assert "Failure" in captured.out, (
            f"Expected 'Failure' in client output, got: {captured.out}"
        )

    def test_large_payload(
        self, server_fixture: int, capsys: pytest.CaptureFixture
    ) -> None:
        """Client–server handles a payload approaching the 1024-byte recv buffer."""
        import client

        # Generate enough data that the codeword is ~1000 bytes
        # Each "1010" is 4 bits; the CRC adds 3 bits → 7 bytes per pattern unit
        # 150 reps × 7 bytes = 1050 bytes (just over 1024)
        data = "1010" * 150  # 600 bits → codeword ~1050 bytes

        client.run_client(
            host="127.0.0.1", port=server_fixture, data=data
        )

        captured = capsys.readouterr()
        assert "Success" in captured.out, (
            f"Expected 'Success' for large payload, got: {captured.out}"
        )
