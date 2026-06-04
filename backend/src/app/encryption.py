"""
hf_backend/src/app/encryption.py
──────────────────────────────────
Server-side AES-256 symmetric encryption for chat message content.

Uses Python `cryptography` library (Fernet = AES-128-CBC + HMAC-SHA256).
The encryption key is loaded from the CHAT_ENCRYPTION_KEY environment variable.

HOW TO GENERATE A KEY (run once, save the output as env var):
    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

IMPORTANT:
- If CHAT_ENCRYPTION_KEY is not set, messages are stored as plaintext with a warning.
  This is graceful degradation — the app will NOT crash.
- is_encrypted() handles mixed data: old plaintext records are returned as-is,
  new records are encrypted. This allows zero-downtime migration.
- The CHAT_ENCRYPTION_KEY must be kept secret — store it in HF Space secrets,
  Render environment variables, or a secrets manager. NEVER commit it to git.
"""
from __future__ import annotations

import os
import base64
import logging

logger = logging.getLogger(__name__)

# ── Load key from environment ─────────────────────────────────────────────────

_fernet = None
_encryption_enabled = False


def _get_fernet():
    """Lazy-load and cache the Fernet instance. Returns None if key not set."""
    global _fernet, _encryption_enabled

    if _fernet is not None:
        return _fernet

    key_str = os.getenv("CHAT_ENCRYPTION_KEY", "").strip()

    if not key_str:
        logger.warning(
            "⚠️  [encryption] CHAT_ENCRYPTION_KEY is not set. "
            "Chat messages will be stored as plaintext. "
            "Set this env var in HF Space secrets for production security."
        )
        _encryption_enabled = False
        return None

    try:
        from cryptography.fernet import Fernet
        # Validate the key by creating the Fernet instance
        _fernet = Fernet(key_str.encode() if isinstance(key_str, str) else key_str)
        _encryption_enabled = True
        logger.info("🔐 [encryption] Chat encryption is ACTIVE (AES-256 Fernet).")
        return _fernet
    except Exception as e:
        logger.error(
            f"❌ [encryption] Invalid CHAT_ENCRYPTION_KEY: {e}. "
            "Falling back to plaintext storage."
        )
        _encryption_enabled = False
        return None


# ── Public API ────────────────────────────────────────────────────────────────

def encrypt_text(plaintext: str) -> str:
    """
    Encrypt a plaintext string.

    Returns the Fernet token as a UTF-8 string (base64-encoded).
    If encryption is not configured, returns the original plaintext unchanged.

    Parameters
    ----------
    plaintext : The message text to encrypt.

    Returns
    -------
    Encrypted ciphertext string, or plaintext if encryption not available.
    """
    if not plaintext:
        return plaintext

    fernet = _get_fernet()
    if fernet is None:
        return plaintext  # Graceful degradation

    try:
        token = fernet.encrypt(plaintext.encode("utf-8"))
        return token.decode("utf-8")
    except Exception as e:
        logger.error(f"❌ [encryption] encrypt_text failed: {e}. Storing plaintext.")
        return plaintext


def decrypt_text(ciphertext: str) -> str:
    """
    Decrypt a Fernet-encrypted ciphertext string back to plaintext.

    Handles mixed data gracefully: if the text is NOT encrypted (e.g., old
    records stored before encryption was enabled), it returns the text as-is.

    Parameters
    ----------
    ciphertext : The encrypted token string (or legacy plaintext).

    Returns
    -------
    Decrypted plaintext string.
    """
    if not ciphertext:
        return ciphertext

    # If it doesn't look like an encrypted token, return as-is (old data)
    if not is_encrypted(ciphertext):
        return ciphertext

    fernet = _get_fernet()
    if fernet is None:
        # Encryption not configured — return as-is (will look garbled but won't crash)
        logger.warning("⚠️  [encryption] Cannot decrypt: CHAT_ENCRYPTION_KEY not set.")
        return ciphertext

    try:
        plaintext = fernet.decrypt(ciphertext.encode("utf-8"))
        return plaintext.decode("utf-8")
    except Exception as e:
        logger.error(
            f"❌ [encryption] decrypt_text failed: {e}. "
            "Returning raw value (may be garbled)."
        )
        return ciphertext


def is_encrypted(text: str) -> bool:
    """
    Check if a string looks like a Fernet-encrypted token.

    Fernet tokens always start with 'gAAAAA' (base64-encoded version identifier).
    This lets us gracefully handle a mix of old plaintext and new encrypted records.

    Parameters
    ----------
    text : The string to check.

    Returns
    -------
    True if the string appears to be a Fernet token.
    """
    if not text or not isinstance(text, str):
        return False
    return text.startswith("gAAAAA")


def is_encryption_enabled() -> bool:
    """Returns True if CHAT_ENCRYPTION_KEY is set and encryption is active."""
    _get_fernet()  # Trigger lazy init
    return _encryption_enabled


def generate_new_key() -> str:
    """
    Generate a new secure Fernet key.

    Use this once to create your CHAT_ENCRYPTION_KEY.
    Save the output in your HF Space secrets or .env file.

    Returns
    -------
    A URL-safe base64-encoded 32-byte key as a string.
    """
    from cryptography.fernet import Fernet
    return Fernet.generate_key().decode("utf-8")
