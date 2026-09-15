import time

import jwt
import pytest

from app.core.security import create_access_token, decode_access_token, hash_password, verify_password


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


def test_hash_password_produces_a_bcrypt_hash():
    hashed = hash_password("demo123")
    assert hashed.startswith("$2b$")
    assert hashed != "demo123"


def test_verify_password_accepts_the_correct_password():
    hashed = hash_password("demo123")
    assert verify_password("demo123", hashed) is True


def test_verify_password_rejects_an_incorrect_password():
    hashed = hash_password("demo123")
    assert verify_password("wrong-password", hashed) is False


def test_hash_password_is_salted_not_deterministic():
    # Two hashes of the same password must differ (random salt per call) --
    # this is what makes the previous, hardcoded-identical-across-5-rows
    # placeholder value a red flag in retrospect, not just an invalid one.
    first = hash_password("demo123")
    second = hash_password("demo123")
    assert first != second
    assert verify_password("demo123", first) is True
    assert verify_password("demo123", second) is True


def test_verify_password_rejects_the_known_bad_placeholder_hash():
    # Regression guard for the exact bug found during Story 7.1's authoring:
    # the old seeded placeholder hash has valid bcrypt shape but does not
    # validate against "demo123". Pinned here so it can never silently come
    # back.
    placeholder = "$2b$12$Ej1cKPsyxQqFWK/8PHT0d.c0yoIbR1Z2r.uV5XvDWMmr.B8xN3RBG"
    assert verify_password("demo123", placeholder) is False
