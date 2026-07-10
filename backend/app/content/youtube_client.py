"""Thin REST wrapper around YouTube Data API v3's search.list/videos.list
endpoints. Called only from content/service.py's ingestion job and this
module's own tests -- never from a router or main.py (AD-7, AC6)."""
import requests

YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"
MAX_RESULTS_PER_SKILL = 3
REQUEST_TIMEOUT_SECONDS = 10


class QuotaExceededError(Exception):
    """Raised when search.list's dedicated ~100 calls/day quota bucket is
    exhausted (HTTP 403, error.errors[].reason == 'quotaExceeded'). videos.list
    draws from a separate, much larger quota bucket and never raises this."""


def _is_quota_exceeded(body: dict) -> bool:
    errors = body.get("error", {}).get("errors", [])
    return any(err.get("reason") == "quotaExceeded" for err in errors)


def search_videos(
    api_key: str, query: str, max_results: int = MAX_RESULTS_PER_SKILL
) -> list[dict]:
    """Search YouTube for videos matching `query`. Returns a list of
    {video_id, title, description, thumbnail_url} dicts.

    Raises QuotaExceededError on a 403 quotaExceeded response; raises a
    generic Exception (with the API's message) on any other non-2xx.
    """
    response = requests.get(
        YOUTUBE_SEARCH_URL,
        params={
            "part": "snippet",
            "type": "video",
            "q": query,
            "maxResults": max_results,
            "key": api_key,
        },
        timeout=REQUEST_TIMEOUT_SECONDS,
    )

    if response.status_code != 200:
        try:
            body = response.json()
        except ValueError:
            body = {}
        if response.status_code == 403 and _is_quota_exceeded(body):
            raise QuotaExceededError(
                f"YouTube search.list quota exceeded: {body.get('error', {}).get('message', '')}"
            )
        raise Exception(
            f"YouTube search.list failed ({response.status_code}): "
            f"{body.get('error', {}).get('message', 'unknown error')}"
        )

    body = response.json()
    results = []
    for item in body.get("items", []):
        video_id = (item.get("id") or {}).get("videoId")
        if not video_id:
            continue
        snippet = item.get("snippet", {})
        thumbnails = snippet.get("thumbnails", {})
        results.append(
            {
                "video_id": video_id,
                "title": snippet.get("title"),
                "description": snippet.get("description"),
                "thumbnail_url": thumbnails.get("default", {}).get("url"),
            }
        )
    return results


def get_video_durations(api_key: str, video_ids: list[str]) -> dict[str, str]:
    """Batch-fetch ISO-8601 durations for the given video IDs in one call.

    Raises a generic Exception on any non-2xx response -- never
    QuotaExceededError, since videos.list draws from a different, much
    larger quota bucket than search.list (Scope Note 5).
    """
    response = requests.get(
        YOUTUBE_VIDEOS_URL,
        params={
            "part": "contentDetails",
            "id": ",".join(video_ids),
            "key": api_key,
        },
        timeout=REQUEST_TIMEOUT_SECONDS,
    )

    if response.status_code != 200:
        try:
            body = response.json()
        except ValueError:
            body = {}
        raise Exception(
            f"YouTube videos.list failed ({response.status_code}): "
            f"{body.get('error', {}).get('message', 'unknown error')}"
        )

    body = response.json()
    return {
        item["id"]: item.get("contentDetails", {}).get("duration")
        for item in body.get("items", [])
    }
