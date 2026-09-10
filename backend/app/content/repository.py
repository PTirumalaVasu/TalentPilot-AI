"""Repository layer for the content module. Only this module's own code may query its tables."""
import json
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.assignments.models import AdminApiKey, ContentCatalog, OrgApiCredential
from app.core.secrets import encrypt_secret

# Cosine similarity a Content match must clear to be recommended (Story 2.4,
# AD-7). Plain module constant, not a Settings field -- mirrors
# core/embedding.py's MODEL_NAME/EMBEDDING_DIM (no other module-tunable
# numeric constant is env-configurable either).
# Recalibrated from 0.7 -> 0.4 (2026-07-11): the original value was never
# checked against real embed_text() output. Measured cosine similarity for
# genuinely on-topic YouTube titles against their skill's embedding (e.g.
# "Top 5 Data Visualizations..." vs the "Data Visualization" skill) landed at
# 0.49-0.57 -- 0.7 silently rejected every real match ever ingested.
SIMILARITY_THRESHOLD = 0.4


async def get_content_by_id(
    db: AsyncSession, content_id: UUID
) -> ContentCatalog | None:
    """Get a single content item by ID.

    Args:
        db: Async database session
        content_id: UUID of the content item

    Returns:
        ContentCatalog ORM instance or None if not found
    """
    result = await db.execute(select(ContentCatalog).where(ContentCatalog.id == content_id))
    return result.scalar_one_or_none()


async def list_content_by_skill(
    db: AsyncSession, skill_id: UUID
) -> list[ContentCatalog]:
    """Get all content items for a specific skill.

    Args:
        db: Async database session
        skill_id: UUID of the skill

    Returns:
        List of ContentCatalog ORM instances (empty list if no matches)
    """
    result = await db.execute(
        select(ContentCatalog)
        .where(ContentCatalog.skill_id == skill_id)
        # Deterministic order: real "best match" ranking now lives in
        # find_best_matching_content() below (Story 2.4); this listing is
        # still used as-is by list_content_for_skill()/ingestion de-dup, so
        # keep it stable across identical requests regardless.
        .order_by(ContentCatalog.ingested_at, ContentCatalog.id)
    )
    return list(result.scalars().all())


async def create_content(db: AsyncSession, content_data: dict) -> ContentCatalog:
    """Create a new content item.

    Args:
        db: Async database session
        content_data: Dictionary with content fields (skill_id, title, description, type, url, embedding, source, content_metadata)

    Returns:
        Created ContentCatalog ORM instance with assigned ID
    """
    content = ContentCatalog(**content_data)
    db.add(content)
    await db.flush()
    await db.refresh(content)
    return content


async def find_best_matching_content(
    db: AsyncSession,
    skill_id: UUID,
    skill_embedding: list[float],
    threshold: float = SIMILARITY_THRESHOLD,
) -> ContentCatalog | None:
    """Filter-then-rank Content for a Skill (Story 2.4, AD-7).

    Pre-filters to the given skill_id, ranks by pgvector cosine distance
    (computed once and reused for the WHERE/ORDER BY clauses below), and
    returns only the single top match if it clears `threshold` similarity.
    `ingested_at` is an explicit tie-break so equally-similar candidates
    resolve to the earlier-inserted row deterministically (AC6) rather than
    by incidental row-fetch order; `ContentCatalog.id` (a random UUID, not
    time-ordered) breaks any remaining tie for rows ingested simultaneously.

    Returns:
        The best-matching ContentCatalog ORM instance, or None if no
        Content for this skill clears the threshold (including when the
        skill has zero Content rows at all).
    """
    distance = ContentCatalog.embedding.cosine_distance(skill_embedding)
    stmt = (
        select(ContentCatalog)
        .where(ContentCatalog.skill_id == skill_id, distance < (1 - threshold))
        .order_by(distance.asc(), ContentCatalog.ingested_at.asc(), ContentCatalog.id.asc())
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


# ---------------------------------------------------------------------------
# Admin/org API credential storage (AD-10, Story 6.5). encrypt_secret() is
# called only here, in the repository -- content/service.py never sees
# ciphertext, per the epic's own wording (Story 6.5 Scope Note 2).
# ---------------------------------------------------------------------------


async def upsert_admin_api_key(db: AsyncSession, *, admin_id: UUID, source: str, plaintext_key: str) -> None:
    """Create or replace a per-admin credential (Story 6.5 AC3). Postgres
    ON CONFLICT on the (admin_id, source) unique constraint (migration 005)
    -- a plain INSERT would raise IntegrityError on a second save for the
    same admin+source instead of replacing it, which the AC requires."""
    encrypted = encrypt_secret(plaintext_key)
    stmt = pg_insert(AdminApiKey).values(admin_id=admin_id, source=source, encrypted_key=encrypted)
    # onupdate=func.now() (the model's ORM-level default) never fires for a
    # Core-level execute() like this one -- set it explicitly, same reasoning
    # as skills/repository.py's Core-UPDATE precedent.
    stmt = stmt.on_conflict_do_update(
        index_elements=[AdminApiKey.admin_id, AdminApiKey.source],
        set_={"encrypted_key": encrypted, "updated_at": func.now()},
    )
    await db.execute(stmt)


async def delete_admin_api_key(db: AsyncSession, *, admin_id: UUID, source: str) -> None:
    await db.execute(delete(AdminApiKey).where(AdminApiKey.admin_id == admin_id, AdminApiKey.source == source))


async def get_admin_api_key(db: AsyncSession, *, admin_id: UUID, source: str) -> AdminApiKey | None:
    result = await db.execute(
        select(AdminApiKey).where(AdminApiKey.admin_id == admin_id, AdminApiKey.source == source)
    )
    return result.scalar_one_or_none()


async def upsert_org_api_credential(
    db: AsyncSession, *, source: str, client_id: str, client_secret: str, configured_by: UUID
) -> None:
    """Create or replace the single org-wide credential row for `source`
    (Story 6.5 AC4) -- both fields are packed into one JSON blob before
    encryption (see OrgApiCredential's docstring for why). Postgres
    ON CONFLICT on the `source` unique constraint (migration 008) replaces
    the row regardless of which Admin configured it before, per AC4's
    "regardless of which Admin configured it before me"."""
    encrypted = encrypt_secret(json.dumps({"client_id": client_id, "client_secret": client_secret}))
    stmt = pg_insert(OrgApiCredential).values(source=source, encrypted_key=encrypted, configured_by=configured_by)
    stmt = stmt.on_conflict_do_update(
        index_elements=[OrgApiCredential.source],
        set_={"encrypted_key": encrypted, "configured_by": configured_by, "updated_at": func.now()},
    )
    await db.execute(stmt)


async def delete_org_api_credential(db: AsyncSession, *, source: str) -> None:
    await db.execute(delete(OrgApiCredential).where(OrgApiCredential.source == source))


async def get_org_api_credential(db: AsyncSession, *, source: str) -> OrgApiCredential | None:
    result = await db.execute(select(OrgApiCredential).where(OrgApiCredential.source == source))
    return result.scalar_one_or_none()
