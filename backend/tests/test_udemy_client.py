"""Tests for the Udemy for Business Courses API REST wrapper (Story 6.6).

Mirrors test_youtube_client.py's _FakeResponse/monkeypatch style exactly --
no real network call, no real Udemy for Business credential needed.

[ASSUMPTION] udemy_client.py's exact request/response shape is built from
Udemy's publicly documented Courses API v2.0 reference, not verified
against a live Udemy for Business sandbox (none was available in this
environment) -- see Story 6.6's Scope Note 5.
"""
import pytest

from app.content.udemy_client import (
    InvalidCredentialError,
    RateLimitExceededError,
    parse_content_info_to_hours,
    search_courses,
)


class _FakeResponse:
    def __init__(self, status_code: int, json_body: dict):
        self.status_code = status_code
        self._json_body = json_body

    def json(self):
        return self._json_body


def test_search_courses_parses_successful_response(monkeypatch):
    fake_body = {
        "results": [
            {
                "id": 111,
                "title": "Intro to Data Visualization",
                "url": "/course/intro-data-viz/",
                "image_480x270": "https://img.udemy.com/course/480x270/111.jpg",
                "content_info_short": "10.5 total hours",
            },
            {
                "id": 222,
                "title": "Advanced Charts",
                "url": "/course/advanced-charts/",
                "image_480x270": "https://img.udemy.com/course/480x270/222.jpg",
                "content_info_short": "3 total hours",
            },
        ]
    }

    def fake_get(url, params=None, auth=None, timeout=None):
        assert "courses/list" in url
        assert params["search"] == "Data Visualization"
        assert auth == ("fake-client-id", "fake-client-secret")
        return _FakeResponse(200, fake_body)

    monkeypatch.setattr("app.content.udemy_client.requests.get", fake_get)
    monkeypatch.setattr("app.content.udemy_client.settings.UDEMY_ORGANIZATION_SUBDOMAIN", "sails")
    monkeypatch.setattr("app.content.udemy_client.settings.UDEMY_ACCOUNT_ID", "12345")

    results = search_courses(
        client_id="fake-client-id", client_secret="fake-client-secret", query="Data Visualization"
    )

    assert len(results) == 2
    assert results[0] == {
        "course_id": 111,
        "title": "Intro to Data Visualization",
        "url": "/course/intro-data-viz/",
        "thumbnail_url": "https://img.udemy.com/course/480x270/111.jpg",
        "content_info": "10.5 total hours",
    }
    assert results[1]["course_id"] == 222


def test_search_courses_raises_rate_limit_exceeded_on_429(monkeypatch):
    def fake_get(url, params=None, auth=None, timeout=None):
        return _FakeResponse(429, {})

    monkeypatch.setattr("app.content.udemy_client.requests.get", fake_get)
    monkeypatch.setattr("app.content.udemy_client.settings.UDEMY_ORGANIZATION_SUBDOMAIN", "sails")
    monkeypatch.setattr("app.content.udemy_client.settings.UDEMY_ACCOUNT_ID", "12345")

    with pytest.raises(RateLimitExceededError):
        search_courses(client_id="id", client_secret="secret", query="Python")


@pytest.mark.parametrize("status_code", [401, 403])
def test_search_courses_raises_invalid_credential_on_401_or_403(monkeypatch, status_code):
    def fake_get(url, params=None, auth=None, timeout=None):
        return _FakeResponse(status_code, {})

    monkeypatch.setattr("app.content.udemy_client.requests.get", fake_get)
    monkeypatch.setattr("app.content.udemy_client.settings.UDEMY_ORGANIZATION_SUBDOMAIN", "sails")
    monkeypatch.setattr("app.content.udemy_client.settings.UDEMY_ACCOUNT_ID", "12345")

    with pytest.raises(InvalidCredentialError):
        search_courses(client_id="bad-id", client_secret="bad-secret", query="Python")


def test_search_courses_raises_generic_exception_on_other_error(monkeypatch):
    def fake_get(url, params=None, auth=None, timeout=None):
        return _FakeResponse(500, {"error": "internal"})

    monkeypatch.setattr("app.content.udemy_client.requests.get", fake_get)
    monkeypatch.setattr("app.content.udemy_client.settings.UDEMY_ORGANIZATION_SUBDOMAIN", "sails")
    monkeypatch.setattr("app.content.udemy_client.settings.UDEMY_ACCOUNT_ID", "12345")

    with pytest.raises(Exception) as exc_info:
        search_courses(client_id="id", client_secret="secret", query="Python")

    assert not isinstance(exc_info.value, InvalidCredentialError)
    assert not isinstance(exc_info.value, RateLimitExceededError)


def test_search_courses_raises_generic_exception_when_subdomain_or_account_id_unset(monkeypatch):
    """Scope Note 5: the org-wide credential can be configured (Story 6.5)
    while the organization subdomain/account id settings are still unset --
    a real, distinct-from-'no key' deployment gap, classified as
    source_error by content/service.py, not silently treated as
    not-configured."""
    monkeypatch.setattr("app.content.udemy_client.settings.UDEMY_ORGANIZATION_SUBDOMAIN", None)
    monkeypatch.setattr("app.content.udemy_client.settings.UDEMY_ACCOUNT_ID", None)

    with pytest.raises(Exception) as exc_info:
        search_courses(client_id="id", client_secret="secret", query="Python")

    assert not isinstance(exc_info.value, InvalidCredentialError)
    assert not isinstance(exc_info.value, RateLimitExceededError)


def test_parse_content_info_to_hours_matches_decimal_hours():
    assert parse_content_info_to_hours("10.5 total hours") == 10.5


def test_parse_content_info_to_hours_matches_singular_hour():
    assert parse_content_info_to_hours("1 total hour") == 1.0


def test_parse_content_info_to_hours_returns_none_on_no_match():
    assert parse_content_info_to_hours("3 lectures") is None


def test_parse_content_info_to_hours_returns_none_on_none_input():
    assert parse_content_info_to_hours(None) is None
