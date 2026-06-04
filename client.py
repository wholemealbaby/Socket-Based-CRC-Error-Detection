"""
CRC Error Detection — TCP Client

Takes a binary string from the user (or via an argument), computes the
CRC remainder, forms a codeword, sends it to the CRC server, and prints
the server's response.
"""

from lib.crc import crc_division, DIVISOR
from lib.network import SERVER_PORT

import socket


def run_client(
    host: str = "127.0.0.1",
    port: int = SERVER_PORT,
    data: str | None = None,
) -> None:
    """Run the TCP CRC client.

    If *data* is ``None`` the user is prompted for a binary string.
    The client computes the CRC remainder, forms the codeword
    (``data + remainder``), sends it to the server, and prints the reply.

    Args:
        host:  Server host address (default ``"127.0.0.1"``).
        port:  Server port number (default :data:`SERVER_PORT <lib.network.SERVER_PORT>`).
        data:  Binary string to send.  When ``None`` (the default) the user
               is prompted interactively.
    """
    if data is None:
        data = input("Enter a binary string (example: 100100): ")

    crc = crc_division(data, DIVISOR)
    codeword = data + crc
    print(f"Send to server (data + CRC): {codeword}")

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))
    client_socket.sendall(codeword.encode("utf-8"))

    response = client_socket.recv(1024).decode("utf-8")
    print(response)

    client_socket.close()


if __name__ == "__main__":
    run_client()
