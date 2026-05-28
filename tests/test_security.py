import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.core.security import encrypt_secret, decrypt_secret

test_secret = "my_super_secret_key_123"
encrypted = encrypt_secret(test_secret)
decrypted = decrypt_secret(encrypted)

print(f"Original: {test_secret}")
print(f"Encrypted: {encrypted}")
print(f"Decrypted: {decrypted}")

if test_secret == decrypted:
    print("Encryption/Decryption test PASSED")
else:
    print("Encryption/Decryption test FAILED")
