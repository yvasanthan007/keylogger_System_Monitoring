import os
from cryptography.fernet import Fernet

def encrypt_logs():
    try:
        os.makedirs("data/encrypted", exist_ok=True)
        key = Fernet.generate_key()
        with open("data/encrypted/key.bin", "wb") as kf:
            kf.write(key)
        cipher = Fernet(key)
        with open("data/logs/keystrokes.txt", "rb") as f:
            data = f.read()
        encrypted = cipher.encrypt(data)
        with open("data/encrypted/logs.enc", "wb") as f:
            f.write(encrypted)
        return "Logs encrypted (key saved)"
    except Exception as e:
        return f"Error: {e}"