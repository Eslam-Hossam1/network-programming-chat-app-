import os
import socket
import ssl
import threading
import time
import tkinter as tk
from ftplib import FTP
from tkinter import scrolledtext, filedialog, messagebox
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import imaplib
import email
from email.header import decode_header

from PIL import Image, ImageTk

HOST = '127.0.0.1'
TEXT_PORT = 1234
FTP_PORT = 2121
FTP_USER = 'user'
FTP_PASS = '12345'

# SSL/TLS configuration for the text server
context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
context.load_verify_locations('server.crt')
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE

# Create a socket and wrap it with SSL
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ssl_client = context.wrap_socket(client_socket, server_hostname=HOST)

# UI settings for styling
DARK_BLUE = '#2C3E50'
LIGHT_GRAY = '#BDC3C7'
BLUE = '#3498DB'
WHITE = "white"
FONT = ("Helvetica", 17)
BUTTON_FONT = ("Helvetica", 15, "bold")
SMALL_FONT = ("Helvetica", 13)

IMAP_SERVER = "imap.gmail.com"
EMAIL_ADDRESS = "testimap221@gmail.com"
PASSWORD = "ciby wchd gkwg hovv"


def add_message(message):
    """Adds a message to the chat display area."""
    message_box.config(state=tk.NORMAL)
    message_box.insert(tk.END, message + '\n')
    message_box.config(state=tk.DISABLED)


def add_email_message(message):
    """Adds a message to the email display area."""
    email_box.config(state=tk.NORMAL,width=40)
    email_box.insert(tk.END, message + '\n')
    email_box.config(state=tk.DISABLED,width=40)


def connect():
    """Connects to the text server and sends the username."""
    try:
        ssl_client.connect((HOST, TEXT_PORT))
        username = username_textbox.get()
        if username:
            ssl_client.sendall(username.encode())
            add_message(f"[SERVER] Connected as {username}.")
            threading.Thread(target=listen_for_messages_from_server, daemon=True).start()
            threading.Thread(target=fetch_emails_periodically, daemon=True).start()
            username_textbox.config(state=tk.DISABLED)
            username_button.config(state=tk.DISABLED)
        else:
            messagebox.showerror("Username Error", "Username cannot be empty.")
    except Exception as e:
        messagebox.showerror("Connection Error", f"Could not connect to server. Error: {e}")


def send_message():
    """Sends a text message entered by the user."""
    message = message_textbox.get()
    if message:
        ssl_client.sendall(message.encode())
        message_textbox.delete(0, tk.END)


def upload_file():
    """Uploads a file to the FTP server."""
    file_path = filedialog.askopenfilename(title="Select a file to upload")
    if file_path:
        try:
            with FTP() as ftp:
                ftp.connect(HOST, FTP_PORT)
                ftp.login(FTP_USER, FTP_PASS)
                file_name = os.path.basename(file_path)
                with open(file_path, 'rb') as file:
                    ftp.storbinary(f"STOR {file_name}", file)
            add_message(f"[FILE] {file_name} uploaded successfully!")
        except Exception as e:
            messagebox.showerror("File Upload Error", f"Failed to upload file: {e}")


def listen_for_messages_from_server():
    """Listens for messages from the server."""
    while True:
        try:
            data = ssl_client.recv(2048)
            if data:
                # Decode the received data using UTF-8
                message = data.decode('utf-8')
                root.after(0, add_message, message)
        except UnicodeDecodeError as ude:
            root.after(0, add_message, f"[ERROR] Failed to decode message: {ude}")
        except Exception as e:
            root.after(0, add_message, f"[SERVER] Connection lost: {e}")
            break


processed_email_ids = set()


def display_image(filepath):
    """Displays an image attachment in the email box."""
    try:
        img = Image.open(filepath)
        img.thumbnail((200, 200))  # Resize image for display
        img_tk = ImageTk.PhotoImage(img)

        # Add image to email display
        img_label = tk.Label(email_box, image=img_tk, bg=LIGHT_GRAY)
        img_label.image = img_tk  # Keep a reference to avoid garbage collection
        email_box.window_create(tk.END, window=img_label)
        email_box.insert(tk.END, "\n")  # Add spacing after the image
    except Exception as e:
        add_email_message(f"[EMAIL] Failed to display image: {e}")


def add_email_component(sender, subject, body, attachments):
    """Adds a UI component for an email to the email box."""
    email_frame = tk.Frame(email_box, bg=LIGHT_GRAY, pady=5, padx=5, relief=tk.RIDGE, bd=2,width=40)

    # Sender
    sender_label = tk.Label(email_frame, text=f"From: {sender}", font=SMALL_FONT, bg=LIGHT_GRAY, fg=DARK_BLUE,
                            anchor="w",width=40)
    sender_label.pack(fill=tk.X, pady=2)

    # Subject
    subject_label = tk.Label(email_frame, text=f"Subject: {subject}", font=SMALL_FONT, bg=LIGHT_GRAY, fg=DARK_BLUE,
                             anchor="w",width=40)
    subject_label.pack(fill=tk.X, pady=2)

    # Body (enable selection)
    body_text = tk.Text(email_frame, font=SMALL_FONT, bg=LIGHT_GRAY, fg=DARK_BLUE, wrap=tk.WORD, height=5, padx=5,
                        pady=5,width=40)
    body_text.insert(tk.END, body)
    body_text.config(state=tk.DISABLED,width=40)  # Prevent editing
    body_text.pack(fill=tk.X, pady=2)

    # Attachments
    for attachment in attachments:
        def create_command(path, button):
            return lambda: [
                display_image(path) if path.lower().endswith(
                    ('.png', '.jpg', '.jpeg', '.gif')) else messagebox.showinfo("Attachment",
                                                                                f"Attachment saved at {path}"),
                button.config(state=tk.DISABLED)
            ]

        attachment_button = tk.Button(
           
            email_frame,
            text=f"Open Attachment: {os.path.basename(attachment)}",
            font=SMALL_FONT,
            bg=BLUE,
            fg=WHITE,
             width=40,
        )
        attachment_button.config(command=create_command(attachment, attachment_button),width=40)
        attachment_button.pack(fill=tk.X, pady=2)

    email_frame.pack(fill=tk.X, padx=5, pady=5, anchor="w")
    email_box.window_create(tk.END, window=email_frame)
    email_box.insert(tk.END, "\n")  # Add spacing between emails


def fetch_emails():
    """Fetches the latest emails from the inbox and displays attachments."""
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL_ADDRESS, PASSWORD)
        mail.select("inbox")

        status, messages = mail.search(None, "ALL")
        email_ids = messages[0].split()[-5:]  # Fetch the last 5 emails

        for e_id in email_ids:
            if e_id in processed_email_ids:
                continue  # Skip already processed emails

            status, msg_data = mail.fetch(e_id, '(RFC822)')
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])

                    # Decode the subject
                    raw_subject = msg["subject"]
                    decoded_subject = decode_header(raw_subject)[0][0] if raw_subject else ""
                    if isinstance(decoded_subject, bytes):
                        decoded_subject = decoded_subject.decode('utf-8')

                    # Skip if the subject is empty or malformed
                    if not decoded_subject.strip():
                        continue

                    sender = msg["from"]

                    # Extract the email body
                    body = ""
                    attachments = []
                    if msg.is_multipart():
                        for part in msg.walk():
                            content_type = part.get_content_type()
                            if content_type == "text/plain" and part.get("Content-Disposition") is None:
                                body = part.get_payload(decode=True).decode('utf-8').strip()
                            elif part.get("Content-Disposition") is not None:
                                # Handle attachments
                                filename = part.get_filename()
                                if filename:
                                    filepath = os.path.join("attachments", filename)
                                    os.makedirs("attachments", exist_ok=True)
                                    with open(filepath, "wb") as f:
                                        f.write(part.get_payload(decode=True))
                                    attachments.append(filepath)
                    else:
                        body = msg.get_payload(decode=True).decode('utf-8').strip()

                    # Add email details to the email box using the new UI component
                    add_email_component(sender, decoded_subject, body, attachments)

                    processed_email_ids.add(e_id)  # Mark email as processed
        mail.logout()
    except Exception as e:
        add_email_message(f"[EMAIL] Failed to fetch emails: {e}")


def fetch_emails_periodically():
    """Fetch emails periodically in the background."""
    while True:
        fetch_emails()
        time.sleep(60)


def open_email_window():
    """Opens a new window for composing and sending an email."""
    email_window = tk.Toplevel(root)
    email_window.title("Invite")
    email_window.geometry("400x300")
    email_window.configure(bg=DARK_BLUE)

    to_label = tk.Label(email_window, text="To:", font=FONT, bg=DARK_BLUE, fg=WHITE)
    to_label.pack(anchor="w", padx=10, pady=(10, 0))
    to_entry = tk.Entry(email_window, font=SMALL_FONT, bg=LIGHT_GRAY, fg=DARK_BLUE)
    to_entry.pack(fill="x", padx=10, pady=5)

    subject_label = tk.Label(email_window, text="Subject:", font=FONT, bg=DARK_BLUE, fg=WHITE)
    subject_label.pack(anchor="w", padx=10, pady=(10, 0))
    subject_entry = tk.Entry(email_window, font=SMALL_FONT, bg=LIGHT_GRAY, fg=DARK_BLUE)
    subject_entry.pack(fill="x", padx=10, pady=5)

    body_label = tk.Label(email_window, text="Body:", font=FONT, bg=DARK_BLUE, fg=WHITE)
    body_label.pack(anchor="w", padx=10, pady=(10, 0))
    body_text = tk.Text(email_window, font=SMALL_FONT, bg=LIGHT_GRAY, fg=DARK_BLUE, height=8)
    body_text.pack(fill="both", padx=10, pady=5)

    send_button = tk.Button(
        email_window,
        text="Invite",
        font=BUTTON_FONT,
        bg=BLUE,
        fg=WHITE,
        command=lambda: send_email(to_entry.get(), subject_entry.get(), body_text.get("1.0", tk.END), email_window)
    )
    send_button.pack(pady=10)


def send_email(to_address, subject, body, email_window):
    """Sends an email using Gmail's SMTP server."""
    try:
        message = MIMEMultipart()
        message["From"] = EMAIL_ADDRESS
        message["To"] = to_address
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_ADDRESS, PASSWORD)
            server.sendmail(EMAIL_ADDRESS, to_address, message.as_string())

        messagebox.showinfo("Email Sent", f"Email successfully sent to {to_address}!")
        email_window.destroy()
    except Exception as e:
        messagebox.showerror("Email Error", f"Failed to send email: {e}")


# GUI setup
root = tk.Tk()
root.geometry("800x650")  # Adjusted width for the red box
root.title("Messenger Client")
root.configure(bg=DARK_BLUE)

# Layout configurations
root.grid_rowconfigure(0, weight=1)
root.grid_rowconfigure(1, weight=4)
root.grid_rowconfigure(2, weight=1)

# Top frame for Username input
top_frame = tk.Frame(root, bg=DARK_BLUE)
top_frame.grid(row=0, column=0, columnspan=2, sticky=tk.EW, padx=20, pady=10)

username_label = tk.Label(top_frame, text="Username:", font=FONT, bg=DARK_BLUE, fg=WHITE)
username_label.pack(side=tk.LEFT, padx=(0, 10))

username_textbox = tk.Entry(top_frame, font=FONT, bg=LIGHT_GRAY, fg=DARK_BLUE, width=18, insertbackground=DARK_BLUE)
username_textbox.pack(side=tk.LEFT)

username_button = tk.Button(top_frame, text="Join Chat", font=BUTTON_FONT, bg=BLUE, fg=WHITE, command=connect)
username_button.pack(side=tk.LEFT, padx=10)

# Middle frame for Chat messages
middle_frame = tk.Frame(root, bg=LIGHT_GRAY)
middle_frame.grid(row=1, column=0, sticky=tk.NSEW, padx=20, pady=10)

message_box = scrolledtext.ScrolledText(middle_frame, font=SMALL_FONT, bg=LIGHT_GRAY, fg=DARK_BLUE, wrap=tk.WORD)
message_box.config(state=tk.DISABLED)
message_box.pack(fill=tk.BOTH, expand=True)

# Right frame for email messages
right_frame = tk.Frame(root, bg=DARK_BLUE)
right_frame.grid(row=1, column=1, sticky=tk.NSEW, padx=10, pady=10)

email_box = scrolledtext.ScrolledText(right_frame, font=SMALL_FONT, bg=LIGHT_GRAY, fg=DARK_BLUE, wrap=tk.WORD)
email_box.config(state=tk.DISABLED,width=40)
email_box.pack(fill=tk.BOTH, expand=True)

# Bottom frame for Message input and Send buttons
bottom_frame = tk.Frame(root, bg=DARK_BLUE)
bottom_frame.grid(row=2, column=0, columnspan=2, sticky=tk.EW, padx=20, pady=10)

message_textbox = tk.Entry(bottom_frame, font=FONT, bg=LIGHT_GRAY, fg=DARK_BLUE, width=40, insertbackground=DARK_BLUE)
message_textbox.pack(side=tk.LEFT, padx=(0, 10))

message_button = tk.Button(bottom_frame, text="Send", font=BUTTON_FONT, bg=BLUE, fg=WHITE, command=send_message)
message_button.pack(side=tk.LEFT)

file_button = tk.Button(bottom_frame, text="Upload File", font=BUTTON_FONT, bg=BLUE, fg=WHITE, command=upload_file)
file_button.pack(side=tk.LEFT, padx=10)

email_button = tk.Button(bottom_frame, text="Invite", font=BUTTON_FONT, bg=BLUE, fg=WHITE, command=open_email_window)
email_button.pack(side=tk.LEFT, padx=10)

# Run the Tkinter main loop
root.mainloop()
