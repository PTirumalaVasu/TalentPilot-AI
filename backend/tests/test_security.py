import time

import jwt
import pytest

from app.core.security import create_access_token, decode_access_token


def test_create_and_decode_round_trip():
    token = create_access_token(user_id="casey", role="EMPLOYEE")
    payload = decode_access_token(token)
    assert payload["user_id"] == "casey"
    assert payload["role"] == "EMPLOYEE"
    assert "exp" in payload


def test_decode_expired_token_raises():
    token = create_access_token(user_id="casey", role="EMPLOYEE", expires_in_hours=-1)
    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(token)


def test_decode_tampered_signature_raises():
    token = create_access_token(user_id="casey", role="EMPLOYEE")
    header, payload, signature = token.split(".")
    flipped = "".join(
        ("A" if c != "A" else "B") if i % 2 == 0 else c for i, c in enumerate(signature)
    )
    tampered = f"{header}.{payload}.{flipped}"
    with pytest.raises(jwt.InvalidSignatureError):
        decode_access_token(tampered)


def test_token_uses_hs256_only():
    token = create_access_token(user_id="rita", role="HR_ADMIN")
    header = jwt.get_unverified_header(token)
    assert header["alg"] == "HS256"
