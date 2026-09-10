"""Service layer for the content module. Cross-module callers must go through here (AD-1)."""
import datetime
import logging
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import CurrentUser
from app.auth.service import require_hr_admin
from app.content import repository
from app.content import youtube_client
from app.content.schemas import ContentResponse, ManualContentCreate
from app.core.config import settings
from app.core.embedding import embed_text
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
