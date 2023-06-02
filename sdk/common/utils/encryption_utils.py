from cryptography.fernet import Fernet


def generate_key() -> str:
    return Fernet.generate_key().decode()


def encrypt(message: str, secret: str) -> str:
    message_bytes = bytes(message, "utf-8")
    return Fernet(secret).encrypt(message_bytes).decode("utf-8")


def decrypt(message: str, secret: str) -> str:
    message_bytes = bytes(message, "utf-8")
    return Fernet(secret).decrypt(message_bytes).decode("utf-8")
