import os
import re
import hmac
import hashlib
from typing import List, Dict
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend


FIXED_SALT = b"hackathon-demo-salt"
PBKDF2_ITERATIONS = 100_000


def derive_key(password: str) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=FIXED_SALT,
        iterations=PBKDF2_ITERATIONS,
        backend=default_backend()
    )
    return kdf.derive(password.encode())


def encrypt_document(key: bytes, plaintext: str) -> bytes:
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)
    return nonce + ciphertext


def decrypt_document(key: bytes, encrypted_blob: bytes) -> str:
    nonce = encrypted_blob[:12]
    ciphertext = encrypted_blob[12:]
    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    return plaintext.decode()


def extract_trigrams(text: str) -> List[str]:
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', '', text)

    trigrams = set()
    words = text.split()

    for word in words:
        if len(word) < 3:
            word = word.ljust(3, "_")

        for i in range(len(word) - 2):
            trigrams.add(word[i:i+3])

    return list(trigrams)


def generate_trapdoor(key: bytes, trigram: str) -> str:
    h = hmac.new(key, trigram.encode(), hashlib.sha256)
    return h.hexdigest()