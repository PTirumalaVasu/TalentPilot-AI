"""Generic Fernet-based secret encryption (AD-10, Story 6.5). Domain-free --
called only from content/repository.py, never from a router (per the epic's
own wording), so this module knows nothing about API keys, admins, or Skills.
"""
import base64
import hashlib

from cryptography.fernet import Fernet

from app.core.config import settings


def _fernet() -> Fernet:
    # ADMIN_KEY_ENCRYPTION_SECRET is an arbitrary-length string (like
    # JWT_SECRET), not a ready-made Fernet key -- a valid Fernet key must be
    # exactly 32 url-safe base64-encoded bytes. Deriving one via SHA-256 lets
    # the operator supply any string without hand-generating a real Fernet
    # key, the same ergonomic as JWT_SECRET.
    key_bytes = hashlib.sha256(settings.ADMIN_KEY_ENCRYPTION_SECRET.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(key_bytes))


def encrypt_secret(plaintext: str) -> str:
    return _fernet().encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt_secret(ciphertext: str) -> str:
    return _fernet().decrypt(ciphertext.encode("utf-8")).decode("utf-8")
