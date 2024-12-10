import os
import socket
import ssl
import threading
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer

# Server details
HOST = '127.0.0.1'
TEXT_PORT = 1234
FTP_PORT = 2121
FTP_DIRECTORY = 'ftp_files'

# SSL/TLS configuration
context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain(certfile='server.crt', keyfile='server.key')

# Ensure the FTP_DIRECTORY exists
os.makedirs(FTP_DIRECTORY, exist_ok=True)

# Store connected clients
clients = {}
client_lock = threading.Lock()


# FTP server setup
def start_ftp_server():
    """Sets up and starts an FTP server."""
    authorizer = DummyAuthorizer()
    authorizer.add_user("user", "12345", FTP_DIRECTORY, perm="elradfmw")
    handler = FTPHandler
    handler.authorizer = authorizer
    ftp_server = FTPServer((HOST, FTP_PORT), handler)
    print(f"FTP server listening on {FTP_PORT}")
    ftp_server.serve_forever()


# Text server for multicast and direct messages
def handle_client(client_socket, addr):
    """Handles communication with the client, including text and email fetching."""
    username = client_socket.recv(1024).decode('utf-8')
    with client_lock:
        clients[username] = client_socket
    print(f"{username} connected from {addr}")

    try:
        while True:
            data = client_socket.recv(2048)
            if not data:
                break
            message = data.decode('utf-8')
            with client_lock:
                for client in clients.values():
                    if client != username:
                        client.send(f"[{username}] {message}".encode())

    finally:
        client_socket.close()
        with client_lock:
            del clients[username]
        print(f"{username} disconnected from {addr}")


def start_text_server():
    """Starts the SSL-wrapped text server."""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, TEXT_PORT))
    server_socket.listen(5)
    ssl_server = context.wrap_socket(server_socket, server_side=True)
    print(f"Text server listening on {TEXT_PORT}")

    while True:
        client_socket, addr = ssl_server.accept()
        threading.Thread(target=handle_client, args=(client_socket, addr), daemon=True).start()


if __name__ == "__main__":
    threading.Thread(target=start_ftp_server, daemon=True).start()
    start_text_server()
