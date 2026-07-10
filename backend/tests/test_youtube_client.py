"""Tests for the YouTube Data API v3 REST wrapper (Story 2.3).

All tests monkeypatch requests.get -- no real network call, no real
YOUTUBE_API_KEY needed.
"""
import pytest

from app.content.youtube_client import (
    QuotaExceededError,
    get_video_durations,
    search_videos,
)


class _FakeResponse:
    def __init__(self, status_code: int, json_body: dict):
        self.status_code = status_code
        self._json_body = json_body

    def json(self):
        return self._json_body


def test_search_videos_parses_successful_response(monkeypatch):
    """search_videos should parse a successful search.list response into the
    expected {video_id, title, description, thumbnail_url} shape."""
    fake_body = {
        "items": [
            {
                "id": {"videoId": "abc123"},
                "snippet": {
                    "title": "Intro to Data Visualization",
                    "description": "Learn charting basics",
                    "thumbnails": {"default": {"url": "https://img.example.com/abc123.jpg"}},
                },
            },
            {
                "id": {"videoId": "def456"},
                "snippet": {
                    "title": "Advanced Charts",
                    "description": "Deep dive into chart types",
                    "thumbnails": {"default": {"url": "https://img.example.com/def456.jpg"}},
                },
            },
        ]
    }

    def fake_get(url, params=None, timeout=None):
        assert "search" in url
        assert params["q"] == "Data Visualization"
        assert params["maxResults"] == 3
        return _FakeResponse(200, fake_body)

    monkeypatch.setattr("app.content.youtube_client.requests.get", fake_get)

    results = search_videos(api_key="fake-key", query="Data Visualization", max_results=3)

    assert len(results) == 2
    assert results[0] == {
        "video_id": "abc123",
        "title": "Intro to Data Visualization",
        "description": "Learn charting basics",
        "thumbnail_url": "https://img.example.com/abc123.jpg",
    }
    assert results[1]["video_id"] == "def456"


def test_search_videos_raises_quota_exceeded_on_403_quota_body(monkeypatch):
    """A 403 response whose body names reason 'quotaExceeded' must raise
    QuotaExceededError specifically, not a generic exception."""
    fake_body = {
        "error": {
            "code": 403,
            "message": "The request cannot be completed because you have exceeded your quota.",
            "errors": [{"domain": "youtube.quota", "reason": "quotaExceeded"}],
        }
    }

    def fake_get(url, params=None, timeout=None):
        return _FakeResponse(403, fake_body)

    monkeypatch.setattr("app.content.youtube_client.requests.get", fake_get)

    with pytest.raises(QuotaExceededError):
        search_videos(api_key="fake-key", query="Python", max_results=3)


def test_search_videos_raises_generic_exception_on_other_error(monkeypatch):
    """A non-403 error, or a 403 with a different reason, must NOT raise
    QuotaExceededError -- it should raise a generic exception instead."""
    fake_body = {
        "error": {
            "code": 400,
            "message": "Invalid query parameter",
            "errors": [{"domain": "youtube.parameter", "reason": "invalidQuery"}],
        }
    }

    def fake_get(url, params=None, timeout=None):
        return _FakeResponse(400, fake_body)

    monkeypatch.setattr("app.content.youtube_client.requests.get", fake_get)

    with pytest.raises(Exception) as exc_info:
        search_videos(api_key="fake-key", query="???", max_results=3)

    assert not isinstance(exc_info.value, QuotaExceededError)
    assert "Invalid query parameter" in str(exc_info.value)


def test_get_video_durations_parses_response_into_dict(monkeypatch):
    """get_video_durations should batch-fetch durations and return a
    {video_id: iso8601_duration} mapping."""
    fake_body = {
        "items": [
            {"id": "abc123", "contentDetails": {"duration": "PT10M32S"}},
            {"id": "def456", "contentDetails": {"duration": "PT5M0S"}},
        ]
    }

    def fake_get(url, params=None, timeout=None):
        assert "videos" in url
        assert params["id"] == "abc123,def456"
        return _FakeResponse(200, fake_body)

    monkeypatch.setattr("app.content.youtube_client.requests.get", fake_get)

    durations = get_video_durations(api_key="fake-key", video_ids=["abc123", "def456"])

    assert durations == {"abc123": "PT10M32S", "def456": "PT5M0S"}


def test_get_video_durations_never_raises_quota_exceeded_on_403(monkeypatch):
    """videos.list draws from a different quota bucket than search.list
    (Scope Note 5) -- even a 403 quotaExceeded body here must NOT raise
    QuotaExceededError, only the generic exception."""
    fake_body = {
        "error": {
            "code": 403,
            "message": "quota exceeded",
            "errors": [{"domain": "youtube.quota", "reason": "quotaExceeded"}],
        }
    }

    def fake_get(url, params=None, timeout=None):
        return _FakeResponse(403, fake_body)

    monkeypatch.setattr("app.content.youtube_client.requests.get", fake_get)

    with pytest.raises(Exception) as exc_info:
        get_video_durations(api_key="fake-key", video_ids=["abc123"])

    assert not isinstance(exc_info.value, QuotaExceededError)
