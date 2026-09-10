"""Service layer for the content module. Cross-module callers must go through here (AD-1)."""
import asyncio
import datetime
import logging
import re
from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse
from uuid import UUID

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import CurrentUser
from app.auth.service import require_hr_admin
from app.content import repository
from app.content import udemy_client
from app.content import youtube_client
from app.content.schemas import (
    ContentLookupCandidate,
    ContentLookupResponse,
    ContentLookupSourceError,
    ContentResponse,
    ManualContentCandidate,
    ManualContentCreate,
)
from app.core.config import settings
from app.core.embedding import embed_text
from app.core.errors import AppException
from app.skills import service as skills_service

logger = logging.getLogger(__name__)

EMBEDDING_TEXT_MAX_CHARS = 1000


def _build_embedding_text(title: str, description: str | None) -> str:
    """Build the text fed to embed_text(), truncated to a safe character
    budget (~256 tokens at ~4 chars/token) so a long YouTube description
    doesn't get silently truncated inside the model with no visibility
    (Story 2.2's deferred item, closed here)."""
    raw = f"{title}: {description or ''}"
    if len(raw) > EMBEDDING_TEXT_MAX_CHARS:
        logger.debug(
            "Truncating embedding text from %d to %d chars for title=%r",
            len(raw), EMBEDDING_TEXT_MAX_CHARS, title,
        )
    return raw[:EMBEDDING_TEXT_MAX_CHARS]


async def ingest_content_for_skill(
    db: AsyncSession, *, skill_id: UUID, skill_name: str, api_key: str
) -> dict:
    """Search YouTube for the given Skill, fetch durations, de-dup against
    already-ingested videos for this Skill, and store new Content rows.
    Takes skill_id/skill_name as plain values (not a live ORM Skill object)
    because a sibling Skill's rollback() earlier in the same
    run_ingestion_job loop expires every ORM object bound to the shared
    session -- accessing an expired attribute would trigger an
    out-of-greenlet async reload. Lets QuotaExceededError propagate
    uncaught -- the caller (run_ingestion_job) decides how to handle a
    quota stop across multiple Skills."""
    search_results = youtube_client.search_videos(
        api_key=api_key, query=skill_name, max_results=youtube_client.MAX_RESULTS_PER_SKILL
    )

    if not search_results:
        await db.commit()
        return {"skill_name": skill_name, "ingested": 0, "skipped_duplicate": 0}

    video_ids = [r["video_id"] for r in search_results]
    durations = youtube_client.get_video_durations(api_key=api_key, video_ids=video_ids)

    existing_rows = await repository.list_content_by_skill(db, skill_id)
    existing_video_ids = {
        row.content_metadata.get("video_id")
        for row in existing_rows
        if row.content_metadata
    }

    ingested = 0
    skipped_duplicate = 0
    for result in search_results:
        video_id = result["video_id"]
        if video_id in existing_video_ids:
            skipped_duplicate += 1
            continue

        embedding = embed_text(_build_embedding_text(result["title"], result["description"]))
        await repository.create_content(
            db,
            {
                "skill_id": skill_id,
                "title": result["title"],
                "description": result["description"],
                "type": "VIDEO",
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "embedding": embedding,
                "source": "YOUTUBE",
                "content_metadata": {
                    "video_id": video_id,
                    "duration": durations.get(video_id),
                    "thumbnail_url": result.get("thumbnail_url"),
                },
            },
        )
        ingested += 1

    await db.commit()
    return {"skill_name": skill_name, "ingested": ingested, "skipped_duplicate": skipped_duplicate}


async def run_ingestion_job(
    db: AsyncSession, *, skill_ids: list[UUID] | None = None
) -> dict:
    """Runs ingestion across all Skills (or an explicit subset). Stops
    immediately on quota exhaustion -- quota is shared across the whole API
    key, not per-Skill -- and reports which Skills were processed vs.
    skipped due to quota. Non-quota per-Skill failures are caught, logged,
    and do not abort the run (AC4)."""
    api_key = settings.YOUTUBE_API_KEY
    if not api_key:
        raise ValueError(
            "YOUTUBE_API_KEY is not configured; cannot run ingestion. "
            "Set it in backend/.env before calling run_ingestion_job()."
        )

    if skill_ids is not None:
        all_skills = await skills_service.list_all_skills(db)
        skills = [s for s in all_skills if s.id in set(skill_ids)]
    else:
        skills = await skills_service.list_all_skills(db)

    # Extract plain (id, name) pairs up front: a rollback() triggered by
    # any skill's failure expires every ORM object on the shared session,
    # so a later loop iteration must never touch a live Skill attribute.
    skill_refs = [(s.id, s.name) for s in skills]

    processed: list[dict] = []
    skipped_due_to_quota: list[str] = []
    quota_exhausted = False

    for index, (skill_id, skill_name) in enumerate(skill_refs):
        try:
            result = await ingest_content_for_skill(
                db, skill_id=skill_id, skill_name=skill_name, api_key=api_key
            )
            processed.append(result)
            logger.info(
                "Ingestion succeeded for skill=%r: %d new, %d skipped duplicates",
                skill_name, result["ingested"], result["skipped_duplicate"],
            )
        except youtube_client.QuotaExceededError:
            await db.rollback()
            quota_exhausted = True
            tomorrow = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1)).date()
            logger.warning(
                "YouTube search.list quota exhausted while processing skill=%r. "
                "Remaining skills will be skipped. Retry on or after %s.",
                skill_name, tomorrow,
            )
            skipped_due_to_quota.extend(name for _, name in skill_refs[index:])
            break
        except Exception:
            await db.rollback()
            logger.exception("Ingestion failed for skill=%r; continuing to next skill", skill_name)

    return {
        "processed": processed,
        "skipped_due_to_quota": skipped_due_to_quota,
        "quota_exhausted": quota_exhausted,
    }


async def manual_seed_content(db: AsyncSession, *, data: ManualContentCreate) -> ContentResponse:
    """Insert a Content row directly, with zero calls to YouTube's API
    (AC5). Computes an embedding from the provided title+description exactly
    as the YouTube ingestion path does."""
    embedding = embed_text(_build_embedding_text(data.title, data.description))

    content_orm = await repository.create_content(
        db,
        {
            "skill_id": data.skill_id,
            "title": data.title,
            "description": data.description,
            "type": data.type,
            "url": data.url,
            "embedding": embedding,
            "source": data.source,
            "content_metadata": None,
        },
    )
    await db.commit()
    return ContentResponse.model_validate(content_orm)


async def get_content(db: AsyncSession, content_id: UUID) -> ContentResponse | None:
    """Get a single content item by ID.

    Args:
        db: Async database session
        content_id: UUID of the content item

    Returns:
        ContentResponse (Pydantic) or None if not found
    """
    content_orm = await repository.get_content_by_id(db, content_id)
    if content_orm is None:
        return None

    return ContentResponse.model_validate(content_orm)


async def list_content_for_skill(
    db: AsyncSession, skill_id: UUID
) -> list[ContentResponse]:
    """Get all content items for a specific skill.

    Args:
        db: Async database session
        skill_id: UUID of the skill

    Returns:
        List of ContentResponse (Pydantic), empty list if no matches
    """
    content_orms = await repository.list_content_by_skill(db, skill_id)
    return [ContentResponse.model_validate(orm) for orm in content_orms]


async def reembed_content_for_skill(db: AsyncSession, skill_id: UUID) -> int:
    """Recompute embeddings for a Skill's already-ingested Content afresh
    and flush the update, using the current embed_text()/_build_embedding_text()
    logic. Self-heals rows whose stored embedding drifted from what the
    current code would produce (e.g. ingested before the Story 2.2 text-
    truncation fix). No YouTube calls -- never touches ingestion, so it
    stays clear of AD-7's live-request ban.

    Uses flush(), not commit() -- this runs inside match_content_for_skill,
    a request-path read called through get_db, whose commit-on-success
    convention (core/db.py) owns the transaction boundary.

    Returns:
        Number of Content rows re-embedded (0 if the Skill has none).
    """
    content_rows = await repository.list_content_by_skill(db, skill_id)
    for row in content_rows:
        row.embedding = embed_text(_build_embedding_text(row.title, row.description))
    await db.flush()
    return len(content_rows)


async def match_content_for_skill(db: AsyncSession, skill_id: UUID) -> ContentResponse | None:
    """Recommend the single best-matching Content for a Skill (Story 2.4).

    Public entrypoint for the filter-then-rank matching logic -- the
    intended caller is a future assignment-creation flow (Story 3.4/3.5),
    which today always passes content_id=None (see
    app.assignments.service.create_assignment_service). A None result here
    means "no recommendation yet", not an error -- callers should treat it
    that way, not surface it to HR as a failure.

    If no Content clears the threshold on the first pass, re-embeds the
    Skill's existing Content afresh (reembed_content_for_skill) and retries
    once -- this recovers matches lost to stale/drifted embeddings without
    ever calling YouTube (AD-7 forbids live-request ingestion; this is a
    local recompute over rows that already exist). A Skill with zero
    ingested Content still returns None -- there is nothing to re-embed,
    and getting real Content requires running the batch ingestion CLI.

    Returns:
        ContentResponse for the best match, or None if the Skill doesn't
        exist or no Content clears the similarity threshold even after
        the re-embed retry.
    """
    skill_embedding = await skills_service.get_skill_embedding(db, skill_id)
    if skill_embedding is None:
        return None

    content_orm = await repository.find_best_matching_content(db, skill_id, skill_embedding)
    if content_orm is None:
        reembedded_count = await reembed_content_for_skill(db, skill_id)
        if reembedded_count > 0:
            content_orm = await repository.find_best_matching_content(db, skill_id, skill_embedding)

    if content_orm is None:
        return None

    return ContentResponse.model_validate(content_orm)


# ---------------------------------------------------------------------------
# Admin/org API credential management (AD-10, Story 6.5). Every function
# below calls require_hr_admin(current_user) first (AD-6) -- this is the
# service-layer gate this codebase uses everywhere else (skills/service.py),
# not a router-level Depends. None of these ever import app.assignments --
# resolving the Udemy "configured by" display name happens at the router
# layer instead (Scope Note 5), the same composition shape auth/router.py's
# get_me_route already uses.
# ---------------------------------------------------------------------------


@dataclass
class ApiKeysStatusRaw:
    """Internal status shape -- content/admin_api_keys_router.py composes
    this into the public ApiKeysStatusResponse, resolving
    udemy_configured_by_id to a display name itself."""

    youtube_configured: bool
    udemy_configured: bool
    udemy_configured_by_id: UUID | None
    udemy_configured_at: datetime.datetime | None


async def set_youtube_key(db: AsyncSession, *, current_user: CurrentUser, key: str) -> None:
    """Save/replace the caller's own YouTube key (Story 6.5 AC3)."""
    require_hr_admin(current_user)
    await repository.upsert_admin_api_key(
        db, admin_id=UUID(current_user.user_id), source="YOUTUBE", plaintext_key=key
    )


async def remove_youtube_key(db: AsyncSession, *, current_user: CurrentUser) -> None:
    """Remove the caller's own YouTube key (Story 6.5 AC5)."""
    require_hr_admin(current_user)
    await repository.delete_admin_api_key(db, admin_id=UUID(current_user.user_id), source="YOUTUBE")


async def set_udemy_credential(db: AsyncSession, *, current_user: CurrentUser, client_id: str, client_secret: str) -> None:
    """Save/replace the single org-wide Udemy credential (Story 6.5 AC4) --
    deliberately not scoped to the caller's own identity beyond attribution
    (AD-10: org-wide, not personal)."""
    require_hr_admin(current_user)
    await repository.upsert_org_api_credential(
        db,
        source="UDEMY",
        client_id=client_id,
        client_secret=client_secret,
        configured_by=UUID(current_user.user_id),
    )


async def remove_udemy_credential(db: AsyncSession, *, current_user: CurrentUser) -> None:
    """Remove the org-wide Udemy credential (Story 6.5 AC5) -- any HR Admin
    may remove it, not just whoever configured it (same org-wide scoping as
    set_udemy_credential)."""
    require_hr_admin(current_user)
    await repository.delete_org_api_credential(db, source="UDEMY")


async def get_api_keys_status(db: AsyncSession, *, current_user: CurrentUser) -> ApiKeysStatusRaw:
    """Read-only status for both credential types (Story 6.5 AC6) -- never
    returns the encrypted or decrypted value, only configured-or-not plus
    Udemy's raw attribution id/timestamp (the router resolves the id to a
    display name)."""
    require_hr_admin(current_user)
    admin_id = UUID(current_user.user_id)

    youtube_row = await repository.get_admin_api_key(db, admin_id=admin_id, source="YOUTUBE")
    udemy_row = await repository.get_org_api_credential(db, source="UDEMY")

    return ApiKeysStatusRaw(
        youtube_configured=youtube_row is not None,
        udemy_configured=udemy_row is not None,
        udemy_configured_by_id=udemy_row.configured_by if udemy_row else None,
        udemy_configured_at=udemy_row.updated_at if udemy_row else None,
    )


# ---------------------------------------------------------------------------
# Live content lookup (Story 6.6, FR-17, AD-7 branches 2 & 3). Search-only --
# no content_catalog row is ever written here (Story 6.8's approve action
# owns that). Both sources are always attempted (Scope Note 8); one
# source's failure never blocks the other (NFR-RES1).
# ---------------------------------------------------------------------------

# Live interactive search, distinct from ingestion's MAX_RESULTS_PER_SKILL=3
# (youtube_client's own constant, sized for curated auto-ingestion) -- an
# Admin reviewing search results benefits from seeing more candidates.
CONTENT_LOOKUP_MAX_RESULTS = 5

_ISO8601_DURATION_RE = re.compile(r"^PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?$")


def _parse_iso8601_duration_hours(duration: str | None) -> float | None:
    """YouTube's videos.list returns an ISO-8601 duration (e.g. 'PT10M32S').
    Story 6.6 is the first caller that needs it as a float hours value --
    ingest_content_for_skill above just stores the raw string. Returns None
    on a missing/unparseable value, never a guessed one."""
    if not duration:
        return None
    match = _ISO8601_DURATION_RE.match(duration)
    if not match:
        return None
    hours, minutes, seconds = (int(g) if g else 0 for g in match.groups())
    return hours + minutes / 60 + seconds / 3600


def _not_found_skill() -> AppException:
    # Mirrors skills/service.py's own _not_found() -- not imported directly
    # since that's a private helper of a different module; small,
    # intentional duplication rather than a cross-module import for a
    # two-line error constructor (matches this codebase's general
    # preference for explicit per-module error helpers).
    return AppException(status.HTTP_404_NOT_FOUND, error_code="SKILL_NOT_FOUND", message="Skill not found")


def _not_found_content() -> AppException:
    # Distinct resource/message from _not_found_skill() above -- Story 6.9's
    # reject endpoint 404s on content_id, not skill_id.
    return AppException(status.HTTP_404_NOT_FOUND, error_code="CONTENT_NOT_FOUND", message="Content not found")


async def _get_source_credential(db: AsyncSession, *, admin_id: UUID, source: str) -> str | dict | None:
    """CREDENTIAL_SCOPE = {YOUTUBE: PER_ADMIN, UDEMY: ORG_WIDE} (AD-10) --
    the one place that decides which repository function to call per
    source. Never decrypts itself; both repository functions already
    return plaintext/None (Story 6.5's decrypt-only-in-repository
    boundary, Scope Note 3)."""
    if source == "YOUTUBE":
        return await repository.get_decrypted_admin_youtube_key(db, admin_id=admin_id)
    if source == "UDEMY":
        return await repository.get_decrypted_org_udemy_credential(db)
    raise ValueError(f"unknown content source: {source}")


def _search_youtube(api_key: str, query: str) -> list[ContentLookupCandidate]:
    search_results = youtube_client.search_videos(
        api_key=api_key, query=query, max_results=CONTENT_LOOKUP_MAX_RESULTS
    )
    if not search_results:
        return []

    video_ids = [r["video_id"] for r in search_results]
    try:
        durations = youtube_client.get_video_durations(api_key=api_key, video_ids=video_ids)
    except Exception:
        # A duration-lookup failure (e.g. a transient network hiccup) after
        # a successful search must not discard the already-fetched search
        # results (code review, 2026-09-10) -- degrade to no duration for
        # this batch rather than failing the whole branch.
        logger.exception("YouTube duration lookup failed; returning results without durations")
        durations = {}

    return [
        ContentLookupCandidate(
            title=result["title"],
            source="YOUTUBE",
            url=f"https://www.youtube.com/watch?v={result['video_id']}",
            thumbnail_url=result.get("thumbnail_url"),
            duration_hours=_parse_iso8601_duration_hours(durations.get(result["video_id"])),
        )
        for result in search_results
    ]


def _search_udemy(credential: dict, query: str) -> list[ContentLookupCandidate]:
    search_results = udemy_client.search_courses(
        client_id=credential["client_id"],
        client_secret=credential["client_secret"],
        query=query,
        max_results=CONTENT_LOOKUP_MAX_RESULTS,
    )
    subdomain = settings.UDEMY_ORGANIZATION_SUBDOMAIN

    candidates = []
    for result in search_results:
        if not result.get("url"):
            # A course with no url can't produce a usable link (code
            # review, 2026-09-10) -- skip it rather than emitting a
            # garbage "https://{subdomain}.udemy.comNone" string with no
            # error surfaced.
            logger.warning(
                "Skipping Udemy course result with missing url: course_id=%s", result.get("course_id")
            )
            continue
        candidates.append(
            ContentLookupCandidate(
                title=result["title"],
                source="UDEMY",
                url=f"https://{subdomain}.udemy.com{result['url']}",
                thumbnail_url=result.get("thumbnail_url"),
                duration_hours=udemy_client.parse_content_info_to_hours(result.get("content_info")),
            )
        )
    return candidates


async def search_content_for_skill(
    db: AsyncSession, *, current_user: CurrentUser, skill_id: UUID, query: str
) -> ContentLookupResponse:
    """Live, on-demand search across YouTube (per-admin key) and Udemy
    (org-wide credential) for a Skill (Story 6.6 AC1-AC7). HR_ADMIN-only.
    Both sources are always attempted; a missing credential, an invalid/
    revoked one, a rate limit, or any other source failure each produce a
    distinct per-source error entry rather than blocking the whole
    request or the other source's results (NFR-RES1)."""
    require_hr_admin(current_user)
    admin_id = UUID(current_user.user_id)

    skill = await skills_service.get_skill_by_id(db, skill_id)
    if skill is None:
        raise _not_found_skill()

    results: list[ContentLookupCandidate] = []
    errors: list[ContentLookupSourceError] = []

    # Each source's credential fetch AND search now run inside the same
    # try/except (code review, 2026-09-10) -- a decrypt_secret()/json.loads()
    # failure fetching a credential is a source_error like any other search
    # failure, not an unhandled exception that 500s the whole request and
    # discards the other source's (possibly already-computed) results.
    # Blocking, synchronous network I/O (_search_youtube/_search_udemy) runs
    # via asyncio.to_thread so a slow external API never stalls the event
    # loop for other concurrent requests.
    try:
        youtube_key = await _get_source_credential(db, admin_id=admin_id, source="YOUTUBE")
        if youtube_key is None:
            errors.append(ContentLookupSourceError(source="YOUTUBE", error="no_credential"))
        else:
            results.extend(await asyncio.to_thread(_search_youtube, youtube_key, query))
    except youtube_client.QuotaExceededError:
        errors.append(ContentLookupSourceError(source="YOUTUBE", error="rate_limited"))
    except youtube_client.InvalidCredentialError:
        errors.append(ContentLookupSourceError(source="YOUTUBE", error="invalid_credential"))
    except Exception:
        logger.exception("YouTube content lookup failed for skill_id=%s", skill_id)
        errors.append(ContentLookupSourceError(source="YOUTUBE", error="source_error"))

    try:
        udemy_credential = await _get_source_credential(db, admin_id=admin_id, source="UDEMY")
        if udemy_credential is None:
            errors.append(ContentLookupSourceError(source="UDEMY", error="no_credential"))
        else:
            results.extend(await asyncio.to_thread(_search_udemy, udemy_credential, query))
    except udemy_client.RateLimitExceededError:
        errors.append(ContentLookupSourceError(source="UDEMY", error="rate_limited"))
    except udemy_client.InvalidCredentialError:
        errors.append(ContentLookupSourceError(source="UDEMY", error="invalid_credential"))
    except Exception:
        logger.exception("Udemy content lookup failed for skill_id=%s", skill_id)
        errors.append(ContentLookupSourceError(source="UDEMY", error="source_error"))

    return ContentLookupResponse(results=results, errors=errors)


# ---------------------------------------------------------------------------
# Manual content entry (Story 6.7, FR-17a). No content_catalog row is ever
# written by this path (same search-only invariant as search_content_for_skill
# above) -- writing happens only on Story 6.8's (not yet built) approve
# action. No youtube_client/udemy_client call is ever made either: unlike
# search_content_for_skill, this function's body never references them at
# all, mirroring manual_seed_content's existing guarantee (Story 2.3).
# ---------------------------------------------------------------------------


async def submit_manual_content(
    db: AsyncSession,
    *,
    current_user: CurrentUser,
    skill_id: UUID,
    url: str,
    title: str,
    duration_hours: float | None,
) -> ManualContentCandidate:
    """Validates a manually-pasted content link against a Skill and echoes
    it back as a review candidate (Story 6.7 AC1) -- no source API call, no
    content_catalog write. HR_ADMIN-only."""
    require_hr_admin(current_user)

    skill = await skills_service.get_skill_by_id(db, skill_id)
    if skill is None:
        raise _not_found_skill()

    return ManualContentCandidate(title=title, source="MANUAL", url=url, duration_hours=duration_hours)


# ---------------------------------------------------------------------------
# Attach content (Story 6.8, FR-18/FR-19). Unlike search_content_for_skill/
# submit_manual_content above, this is the actual write/approve action any
# reviewed candidate (searched or manual) needs -- writes content_catalog
# with origin="ADMIN_LOOKUP" and attached_by set, distinguishing it from the
# batch job's rows (origin="BATCH", attached_by=None).
# ---------------------------------------------------------------------------


_YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "youtu.be"}


def _extract_youtube_video_id(url: str) -> str | None:
    """Best-effort extraction of a YouTube video id from a `watch?v=` or
    `youtu.be/` URL (review patch, 2026-09-10) -- without this,
    ingest_content_for_skill's de-dup check (content_metadata.get("video_id"))
    can't recognize an admin-attached video and would re-ingest it as a
    duplicate row on the next batch run. Hostname-checked, not substring-
    matched (same lesson as ContentPreviewModal.tsx's Story 6.7 review
    patch) -- a URL that merely contains "youtube.com" in a query param
    must not be misidentified. Returns None (not a guess) for anything
    unrecognized, matching FR-17a's "no data beats a guessed one" principle."""
    parsed = urlparse(url)
    if parsed.hostname not in _YOUTUBE_HOSTS:
        return None
    if parsed.hostname == "youtu.be":
        video_id = parsed.path.lstrip("/")
        return video_id or None
    return parse_qs(parsed.query).get("v", [None])[0]


def _build_attach_content_metadata(
    *, source: str, url: str, duration_hours: float | None
) -> dict | None:
    """content_metadata for an attach_content write (review patch,
    2026-09-10). Two independent concerns, both additive so neither
    displaces the other:
    - `duration_hours` (epics AC's literal field name) alongside `duration`
      in whole seconds -- the key/unit ProgressRepository.parse_duration_seconds/
      get_video_duration (AD-3's single derivation authority for dashboard
      Status/percent) actually reads. Without `duration`, every Assignment
      on this Content would be stuck "In Progress" at 0% forever.
    - `video_id` for a recognized YOUTUBE url, so the batch ingestion job's
      de-dup check doesn't re-ingest the same video.
    Returns None (not `{}`) when there's nothing to record, matching every
    other content_metadata writer in this module."""
    metadata: dict = {}
    if duration_hours is not None:
        metadata["duration_hours"] = duration_hours
        metadata["duration"] = round(duration_hours * 3600)
    if source == "YOUTUBE":
        video_id = _extract_youtube_video_id(url)
        if video_id:
            metadata["video_id"] = video_id
    return metadata or None


async def attach_content(
    db: AsyncSession,
    *,
    current_user: CurrentUser,
    skill_id: UUID,
    title: str,
    source: str,
    url: str,
    duration_hours: float | None,
) -> ContentResponse:
    """Approves a reviewed candidate as Content for a Skill (Story 6.8
    AC2-AC6). HR_ADMIN-only. `type` is always hardcoded "VIDEO" -- content
    type inference from source is out of scope (epics AC's own wording).
    No `description` is embedded: neither candidate shape that can reach
    this endpoint (ContentLookupCandidate, ManualContentCandidate) carries
    one."""
    require_hr_admin(current_user)

    skill = await skills_service.get_skill_by_id(db, skill_id)
    if skill is None:
        raise _not_found_skill()

    embedding = embed_text(_build_embedding_text(title, None))
    content_orm = await repository.create_content(
        db,
        {
            "skill_id": skill_id,
            "title": title,
            "description": None,
            "type": "VIDEO",
            "url": url,
            "embedding": embedding,
            "source": source,
            "content_metadata": _build_attach_content_metadata(
                source=source, url=url, duration_hours=duration_hours
            ),
            "attached_by": UUID(current_user.user_id),
            "origin": "ADMIN_LOOKUP",
        },
    )
    await db.commit()
    return ContentResponse.model_validate(content_orm)


# ---------------------------------------------------------------------------
# Reject content (Story 6.9, FR-23). Hard-deletes an admin-attached
# content_catalog row outright, independent of approving a replacement.
# Not gated by the Skill's ever_assigned flag at all (AD-11 point 5) -- this
# function never looks at the Skill row or its lock.
# ---------------------------------------------------------------------------


async def reject_content(db: AsyncSession, *, current_user: CurrentUser, content_id: UUID) -> None:
    """Hard-deletes a Content row previously approved via attach_content
    (Story 6.9 AC1-AC5). HR_ADMIN-only. 404s uniformly whether content_id
    doesn't exist or exists but wasn't admin-sourced (origin != "ADMIN_LOOKUP")
    -- there is no skill_id in this endpoint's signature to additionally
    scope by (Scope Note 2)."""
    require_hr_admin(current_user)

    content = await repository.get_content_by_id(db, content_id)
    if content is None or content.origin != "ADMIN_LOOKUP":
        raise _not_found_content()

    await repository.delete_content(db, content_id)
    await db.commit()
