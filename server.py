"""
CRC Error Detection — TCP Server

Accepts binary codewords (data + CRC remainder) over TCP and verifies
them using binary polynomial (CRC) division.
"""

from lib.crc import crc_division, DIVISOR
from lib.network import SERVER_PORT

import socket


def run_server(host: str = "127.0.0.1", port: int = SERVER_PORT) -> None:
    """Start the TCP CRC server.

    The server binds to *host*:*port*, listens for incoming connections,
    receives a binary codeword, runs CRC division on it, and sends back a
    success / failure message.

    Args:
        host:  Host address to bind to (default ``"127.0.0.1"``).
        port:  Port number to listen on (default :data:`SERVER_PORT <lib.network.SERVER_PORT>`).
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server_socket.bind((host, port))
        server_socket.listen(5)
        print(f"Server is listening on port {port}...")

        while True:
            client_socket, client_address = server_socket.accept()
            print(f"Connection established with {client_address}")

            data = client_socket.recv(1024).decode("utf-8")
            print(f"Received codeword: {data}")

            remainder = crc_division(data, DIVISOR)
            if remainder == "0" * len(remainder):
                response = "SERVER: Success! No error detected using CRC"
                print("Status: No error detected")
            else:
                response = "SERVER: Failure! Error detected using CRC"
                print("Status: Error detected")

            client_socket.sendall(response.encode("utf-8"))
            client_socket.close()

    except KeyboardInterrupt:
        print("\nServer shutting down...")
    finally:
        server_socket.close()


if __name__ == "__main__":
    run_server()
