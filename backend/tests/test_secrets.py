"""Tests for core/secrets.py's Fernet encrypt/decrypt (AD-10, Story 6.5)."""
import pytest

from app.core.secrets import decrypt_secret, encrypt_secret


def test_encrypt_then_decrypt_round_trips_to_the_original_plaintext():
    plaintext = "a-real-looking-youtube-api-key-AIzaSyExample"
    ciphertext = encrypt_secret(plaintext)

    assert ciphertext != plaintext
    assert decrypt_secret(ciphertext) == plaintext


def test_encrypting_the_same_plaintext_twice_produces_different_ciphertext():
    plaintext = "same-plaintext"
    first = encrypt_secret(plaintext)
    second = encrypt_secret(plaintext)

    # Fernet embeds a random IV + timestamp per encryption -- two encryptions
    # of the same plaintext must not be byte-identical (this is what makes
    # ciphertext non-comparable/non-indexable, an intentional property here).
    assert first != second
    assert decrypt_secret(first) == plaintext
    assert decrypt_secret(second) == plaintext


def test_decrypting_garbage_raises_cleanly():
    with pytest.raises(Exception):
        decrypt_secret("not-valid-fernet-ciphertext")


def test_round_trips_a_json_blob_for_the_udemy_two_field_packing_pattern():
    import json

    payload = json.dumps({"client_id": "abc123", "client_secret": "shh-secret"})
    ciphertext = encrypt_secret(payload)
    decrypted = decrypt_secret(ciphertext)

    assert json.loads(decrypted) == {"client_id": "abc123", "client_secret": "shh-secret"}
