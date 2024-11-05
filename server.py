import socket
import threading

# Server details
HOST = '127.0.0.1'
PORT = 1234

# Store connected clients
clients = {}
client_lock = threading.Lock()


def handle_client(client_socket, username):
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if message:  # Check if the message is not empty
                print(f"{username}: {message}")
                # Handle multicast messages
                if message.startswith('@'):
                    parts = message.split(' ', 1)
                    if len(parts) > 1:
                        target_users = parts[0][1:].split(',')  # Handle multiple clients
                        message_content = parts[1]
                        with client_lock:
                            for target_user in target_users:
                                target_user = target_user.strip()
                                if target_user in clients:
                                    clients[target_user].send(
                                        f"{username} (to {target_user}): {message_content}".encode())
                    else:
                        print("No message content provided for multicast.")
                else:
                    # Broadcast to all clients
                    with client_lock:
                        for client in clients.values():
                            client.send(f"{username}: {message}".encode())
            else:
                print(f"Empty message received from {username}.")
                break  # Exit if empty message
        except Exception as e:
            print(f"Error: {e}")
            break

    client_socket.close()
    with client_lock:
        del clients[username]
    print(f"{username} disconnected.")


def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    print("Server listening on port", PORT)

    while True:
        client_socket, address = server_socket.accept()
        username = client_socket.recv(1024).decode('utf-8')

        with client_lock:
            clients[username] = client_socket

        print(f"{username} connected from {address}")

        threading.Thread(target=handle_client, args=(client_socket, username)).start()


if __name__ == '__main__':
    start_server()
