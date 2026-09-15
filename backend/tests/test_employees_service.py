"""Unit tests for app.employees.service's password generation (Story 7.2).

Password hash/verify helper tests moved to test_security.py (auth-wiring
story) -- they now live in app.core.security, shared crypto infra used by
both employees/service.py and auth/service.py, not employees-owned logic.

No DB required -- pure functions, mirroring test_skills_service.py's
sync-test-for-pure-helper precedent (_build_embedding_text).
"""
from app.employees.service import _PASSWORD_ALPHABET, generate_password


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
