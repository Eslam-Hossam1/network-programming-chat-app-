import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox

# Server details
HOST = '127.0.0.1'
PORT = 1234

# Colors and Fonts
DARK_BLUE = '#2C3E50'
LIGHT_GRAY = '#BDC3C7'
BLUE = '#3498DB'
WHITE = "white"
FONT = ("Helvetica", 17)
BUTTON_FONT = ("Helvetica", 15, "bold")
SMALL_FONT = ("Helvetica", 13)

# Socket setup
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def add_message(message):
    message_box.config(state=tk.NORMAL)
    message_box.insert(tk.END, message + '\n')
    message_box.config(state=tk.DISABLED)

def connect():
    try:
        client.connect((HOST, PORT))
        add_message("[SERVER] Connected to the server successfully.")
    except Exception as e:
        messagebox.showerror("Connection Error", f"Could not connect to server {HOST} {PORT}. Error: {e}")
        return

    username = username_textbox.get()
    if username:
        client.sendall(username.encode())
        threading.Thread(target=listen_for_messages_from_server).start()
        username_textbox.config(state=tk.DISABLED)
        username_button.config(state=tk.DISABLED)
    else:
        messagebox.showerror("Invalid Username", "Username cannot be empty")

def send_message():
    message = message_textbox.get()
    if message:
        client.sendall(message.encode())  # Send message as is (including @username for multicast)
        message_textbox.delete(0, tk.END)
    else:
        messagebox.showerror("Empty Message", "Message cannot be empty")

def listen_for_messages_from_server():
    while True:
        try:
            message = client.recv(2048).decode('utf-8')
            if message:
                add_message(message)
            else:
                messagebox.showerror("Error", "Received empty message from server.")
                break
        except Exception as e:
            add_message("[SERVER] Connection lost.")
            break

# GUI setup
root = tk.Tk()
root.geometry("600x650")
root.title("Messenger Client")
root.configure(bg=DARK_BLUE)
root.resizable(False, False)

# Layout configurations
root.grid_rowconfigure(0, weight=1)
root.grid_rowconfigure(1, weight=4)
root.grid_rowconfigure(2, weight=1)

# Top frame
top_frame = tk.Frame(root, bg=DARK_BLUE)
top_frame.grid(row=0, column=0, sticky=tk.EW, padx=20, pady=10)

username_label = tk.Label(top_frame, text="Username:", font=FONT, bg=DARK_BLUE, fg=WHITE)
username_label.pack(side=tk.LEFT, padx=(0, 10))

username_textbox = tk.Entry(top_frame, font=FONT, bg=LIGHT_GRAY, fg=DARK_BLUE, width=18, insertbackground=DARK_BLUE)
username_textbox.pack(side=tk.LEFT)

username_button = tk.Button(top_frame, text="Join Chat", font=BUTTON_FONT, bg=BLUE, fg=WHITE, command=connect)
username_button.pack(side=tk.LEFT, padx=10)

# Middle frame
middle_frame = tk.Frame(root, bg=LIGHT_GRAY)
middle_frame.grid(row=1, column=0, sticky=tk.NSEW, padx=20, pady=10)

message_box = scrolledtext.ScrolledText(middle_frame, font=SMALL_FONT, bg=LIGHT_GRAY, fg=DARK_BLUE, wrap=tk.WORD)
message_box.config(state=tk.DISABLED)
message_box.pack(fill=tk.BOTH, expand=True)

# Bottom frame
bottom_frame = tk.Frame(root, bg=DARK_BLUE)
bottom_frame.grid(row=2, column=0, sticky=tk.EW, padx=20, pady=10)

message_textbox = tk.Entry(bottom_frame, font=FONT, bg=LIGHT_GRAY, fg=DARK_BLUE, width=40, insertbackground=DARK_BLUE)
message_textbox.pack(side=tk.LEFT, padx=(0, 10))

message_button = tk.Button(bottom_frame, text="Send", font=BUTTON_FONT, bg=BLUE, fg=WHITE, command=send_message)
message_button.pack(side=tk.LEFT)

# Main function
def main():
    root.mainloop()

if __name__ == '__main__':
    main()
