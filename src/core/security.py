import uuid
import hashlib
import base64
from cryptography.fernet import Fernet

class DecryptionError(Exception):
    """Custom exception raised when cryptographic decryption fails."""
    pass

def _get_machine_key():
    """Generates a consistent machine-specific key for encryption."""
    # Use hardware UUID as the base for the key
    machine_id = str(uuid.getnode())
    # Create a 32-byte key from the machine ID
    key_hash = hashlib.sha256(machine_id.encode()).digest()
    return base64.urlsafe_b64encode(key_hash)

def encrypt_secret(plaintext: str) -> str:
    """Encrypts a string using the machine-specific key."""
    if not plaintext:
        return ""
    try:
        f = Fernet(_get_machine_key())
        return f.encrypt(plaintext.encode()).decode()
    except Exception:
        return ""

def decrypt_secret(ciphertext: str) -> str:
    """Decrypts a string using the machine-specific key."""
    if not ciphertext:
        return ""
    try:
        f = Fernet(_get_machine_key())
        return f.decrypt(ciphertext.encode()).decode()
    except Exception as e:
        # If decryption fails (e.g. data was not encrypted or key changed), 
        # raise DecryptionError to be caught by the credentials loader
        raise DecryptionError("Decryption failed. The secret may have been encrypted on a different machine or the key has changed.") from e
