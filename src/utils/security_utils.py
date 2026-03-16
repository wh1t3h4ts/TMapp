def is_strong_password(password: str) -> bool:
    """Check if the provided password meets strength requirements."""
    if len(password) < 12:
        return False
    if not any(char.isdigit() for char in password):
        return False
    if not any(char.islower() for char in password):
        return False
    if not any(char.isupper() for char in password):
        return False
    if not any(char in "!@#$%^&*()-_=+[]{}|;:,.<>?/" for char in password):
        return False
    return True

def secure_delete(file_path: str) -> None:
    """Securely delete a file by overwriting its contents."""
    import os
    import random

    if os.path.isfile(file_path):
        with open(file_path, 'r+b') as f:
            length = os.path.getsize(file_path)
            f.write(os.urandom(length))
        os.remove(file_path)

def generate_secure_random_bytes(length: int) -> bytes:
    """Generate secure random bytes."""
    import os
    return os.urandom(length)