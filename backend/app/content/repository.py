"""Repository layer for the content module. Only this module's own code may query its tables."""
import json
from uuid import UUID

from sqlalchemy import delete, func, or_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.assignments.models import AdminApiKey, ContentCatalog, OrgApiCredential
from app.core.secrets import decrypt_secret, encrypt_secret

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


async def delete_content(db: AsyncSession, content_id: UUID) -> None:
    """Hard delete a content_catalog row (Story 6.9 AC1). Core-level
    delete(), not db.delete(<ORM object>), so the ORM's unit-of-work never
    loads the row's `skill`/`assignments` relationships -- mirrors
    skills/repository.py::delete_skill's identical reasoning. A nonexistent
    content_id matches zero rows and is a silent no-op, same as
    delete_admin_api_key/delete_org_api_credential below.
    """
    await db.execute(delete(ContentCatalog).where(ContentCatalog.id == content_id))


async def list_admin_lookup_content_for_skills(
    db: AsyncSession, skill_ids: list[UUID]
) -> list[ContentCatalog]:
    """All origin="ADMIN_LOOKUP" content_catalog rows for the given Skill
    ids, ordered so the LAST row per skill_id is the most recently ingested
    (Story 6.10 AC1) -- one bulk query instead of N+1 per-Skill lookups.
    Callers pick the most recent row per skill_id themselves (e.g. by
    overwriting a dict keyed on skill_id while iterating in this order).
    Excludes BATCH-origin rows entirely -- those are never "approved" in
    this epic's sense (Story 6.9's reject_content's identical origin filter).

    Args:
        db: Async database session
        skill_ids: Skill ids to fetch admin-sourced content for

    Returns:
        List of ContentCatalog ORM instances, ordered by (skill_id,
        ingested_at, id); empty list if skill_ids is empty or none match.
    """
    if not skill_ids:
        return []
    result = await db.execute(
        select(ContentCatalog)
        .where(ContentCatalog.skill_id.in_(skill_ids), ContentCatalog.origin == "ADMIN_LOOKUP")
        .order_by(ContentCatalog.skill_id, ContentCatalog.ingested_at, ContentCatalog.id)
    )
    return list(result.scalars().all())


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


# ---------------------------------------------------------------------------
# Decrypt-and-return credential functions (Story 6.6). The first callers in
# this codebase to call decrypt_secret() in a live code path (Story 6.5 Dev
# Notes' explicit forward note) -- content/service.py never sees ciphertext,
# same repository-only decrypt boundary Story 6.5 established.
# ---------------------------------------------------------------------------


async def get_decrypted_admin_youtube_key(db: AsyncSession, *, admin_id: UUID) -> str | None:
    """The caller's own YouTube key, decrypted (AD-7 branch 2: per-admin
    credential). None if not configured -- this IS the "no_credential"
    signal, same as Story 6.5's get_api_keys_status (no separate
    `configured` column)."""
    row = await get_admin_api_key(db, admin_id=admin_id, source="YOUTUBE")
    if row is None:
        return None
    return decrypt_secret(row.encrypted_key)


async def get_decrypted_org_udemy_credential(db: AsyncSession) -> dict | None:
    """The single org-wide Udemy credential, decrypted and unpacked (AD-7
    branch 3: org-wide credential). Story 6.5 packed {client_id,
    client_secret} into one encrypted JSON blob (OrgApiCredential's
    docstring) -- this is the first caller that needs to unpack it. None
    if not configured."""
    row = await get_org_api_credential(db, source="UDEMY")
    if row is None:
        return None
    return json.loads(decrypt_secret(row.encrypted_key))


async def admin_actor_exists_for_employee(db: AsyncSession, employee_id: UUID) -> bool:
    """Whether this employee has ever configured an AdminApiKey or attached
    Content -- Story 7.5 (FR-27) code review, 2026-09-12: broadens the
    Delete/Archive confirm dialog's has_assignment_history prediction to
    cover this content-module admin-actor history too (AD-1: content/ owns
    both tables, so employees/ reaches them through here)."""
    stmt = select(AdminApiKey.id).where(AdminApiKey.admin_id == employee_id).limit(1)
    if (await db.execute(stmt)).scalar_one_or_none() is not None:
        return True
    stmt = select(ContentCatalog.id).where(ContentCatalog.attached_by == employee_id).limit(1)
    return (await db.execute(stmt)).scalar_one_or_none() is not None


async def distinct_employee_ids_with_admin_actor_history(db: AsyncSession) -> set[UUID]:
    """Bulk version of admin_actor_exists_for_employee, for the roster's
    one-query-not-N+1 has_assignment_history computation (Story 7.5 code
    review)."""
    stmt = select(AdminApiKey.admin_id).union(select(ContentCatalog.attached_by))
    result = await db.execute(stmt)
    return {row for row in result.scalars().all() if row is not None}
