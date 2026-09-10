"""Thin REST wrapper around the Udemy for Business Courses API (api-2.0).
Mirrors youtube_client.py's shape: a search function + a dedicated
rate-limit exception. Called only from content/service.py's live
content-lookup path (Story 6.6, AD-7 branch 3) -- there is no Udemy
ingestion path, unlike YouTube's batch job.

[ASSUMPTION] The exact endpoint/auth/rate-limit shape below is built from
Udemy for Business's publicly documented Courses API v2.0 reference (no
live Udemy for Business sandbox credential was available in this
environment to verify against) -- confirm against a real account before
this ever runs against production Udemy data (Story 6.6 Scope Note 5):
  - GET https://{subdomain}.udemy.com/api-2.0/organizations/{account_id}/courses/list/
  - HTTP Basic Auth (client_id, client_secret)
  - 429 = rate limited (trusted directly, no local counter, per AD-7)
  - 401/403 = invalid/revoked credential
"""
import re

import requests

from app.core.config import settings

UDEMY_API_URL_TEMPLATE = "https://{subdomain}.udemy.com/api-2.0/organizations/{account_id}/courses/list/"
MAX_RESULTS_PER_SKILL = 5
REQUEST_TIMEOUT_SECONDS = 10

_CONTENT_INFO_HOURS_RE = re.compile(r"([\d.]+)\s+total hours?", re.IGNORECASE)


class RateLimitExceededError(Exception):
    """Raised on a 429 response -- Udemy's own rate-limit signal, trusted
    directly rather than a local call counter or concurrency semaphore
    (AD-7: "premature to build now" at this pilot's scale)."""


class InvalidCredentialError(Exception):
    """Raised on a 401/403 response -- an invalid or revoked
    client_id/client_secret (HTTP Basic Auth rejection)."""


def parse_content_info_to_hours(content_info: str | None) -> float | None:
    """Best-effort parse of Udemy's free-text content_info_short field
    (e.g. "10.5 total hours") into a float. Returns None on a missing
    field or a format that doesn't match -- never a guessed value."""
    if not content_info:
        return None
    match = _CONTENT_INFO_HOURS_RE.search(content_info)
    if not match:
        return None
    return float(match.group(1))


def search_courses(
    client_id: str, client_secret: str, query: str, max_results: int = MAX_RESULTS_PER_SKILL
) -> list[dict]:
    """Search Udemy for Business's licensed course catalog for `query`.
    Returns a list of {course_id, title, url, thumbnail_url, content_info}
    dicts -- `url` is still relative (caller builds the absolute link,
    matching where the organization subdomain is known) and `content_info`
    is Udemy's free-text duration string, not yet parsed to hours (callers
    use parse_content_info_to_hours for that).

    Raises RateLimitExceededError on a 429; InvalidCredentialError on a
    401/403; a generic Exception on any other non-2xx, including when
    UDEMY_ORGANIZATION_SUBDOMAIN/UDEMY_ACCOUNT_ID aren't configured (a
    real, distinct-from-"no key" deployment gap -- see module docstring).
    """
    if not settings.UDEMY_ORGANIZATION_SUBDOMAIN or not settings.UDEMY_ACCOUNT_ID:
        raise Exception(
            "Udemy organization subdomain/account id is not configured "
            "(set UDEMY_ORGANIZATION_SUBDOMAIN and UDEMY_ACCOUNT_ID)"
        )

    url = UDEMY_API_URL_TEMPLATE.format(
        subdomain=settings.UDEMY_ORGANIZATION_SUBDOMAIN, account_id=settings.UDEMY_ACCOUNT_ID
    )
    response = requests.get(
        url,
        params={"search": query, "page_size": max_results},
        auth=(client_id, client_secret),
        timeout=REQUEST_TIMEOUT_SECONDS,
    )

    if response.status_code == 429:
        raise RateLimitExceededError("Udemy courses.list rate limit exceeded")
    if response.status_code in (401, 403):
        raise InvalidCredentialError(
            f"Udemy courses.list rejected the client_id/client_secret ({response.status_code})"
        )
    if response.status_code != 200:
        try:
            body = response.json()
        except ValueError:
            body = {}
        raise Exception(f"Udemy courses.list failed ({response.status_code}): {body}")

    body = response.json()
    return [
        {
            "course_id": item.get("id"),
            "title": item.get("title"),
            "url": item.get("url"),
            "thumbnail_url": item.get("image_480x270"),
            "content_info": item.get("content_info_short"),
        }
        for item in body.get("results", [])
    ]
