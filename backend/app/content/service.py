"""Service layer for the content module. Cross-module callers must go through here (AD-1)."""
import datetime
import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.content import repository
from app.content import youtube_client
from app.content.schemas import ContentResponse, ManualContentCreate
from app.core.config import settings
from app.core.embedding import embed_text

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
        all_skills = await repository.list_all_skills(db)
        skills = [s for s in all_skills if s.id in set(skill_ids)]
    else:
        skills = await repository.list_all_skills(db)

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
