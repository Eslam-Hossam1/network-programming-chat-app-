import imaplib

# Your Gmail credentials
username = "testimap221@gmail.com"
password = "01233210!@"  # Replace with your app password or real password if 2FA is not enabled

# Use IMAP4_SSL for a secure connection
try:
    # Connect to Gmail's IMAP server using SSL
    server = imaplib.IMAP4_SSL('imap.gmail.com', 993)
    server.login(username, password)
    print("Login successful!")
except imaplib.IMAP4.error as e:
    print("Login failed:", e)
except TimeoutError as te:
    print("Connection timed out:", te)
finally:
    try:
        server.logout()
    except Exception:
        pass
