"""Unit tests for app.employees.service's password hashing helper (Story 7.1)
and password generation (Story 7.2).

No DB required -- pure functions, mirroring test_skills_service.py's
sync-test-for-pure-helper precedent (_build_embedding_text).
"""
from app.employees.service import _PASSWORD_ALPHABET, generate_password, hash_password, verify_password


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
    # Regression guard for the exact bug found during this story's
    # authoring: the old seeded placeholder hash has valid bcrypt shape but
    # does not validate against "demo123". Pinned here so it can never
    # silently come back.
    placeholder = "$2b$12$Ej1cKPsyxQqFWK/8PHT0d.c0yoIbR1Z2r.uV5XvDWMmr.B8xN3RBG"
    assert verify_password("demo123", placeholder) is False


def test_generate_password_is_12_characters():
    assert len(generate_password()) == 12


def test_generate_password_uses_only_the_documented_alphabet():
    password = generate_password()
    assert all(char in _PASSWORD_ALPHABET for char in password)


def test_generate_password_excludes_visually_ambiguous_characters():
    for char in "IOl01":
        assert char not in _PASSWORD_ALPHABET


def test_generate_password_produces_different_values_across_calls():
    # Statistical, not exhaustive -- 20 calls keeps the false-failure rate
    # negligible without asserting anything about the RNG's internals.
    passwords = {generate_password() for _ in range(20)}
    assert len(passwords) == 20
