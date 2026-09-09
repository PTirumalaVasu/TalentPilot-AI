"""Service layer for the skills module. Cross-module callers must go
through here (AD-1) -- `content/` no longer imports `Skill` or queries the
`skills` table directly (AD-11)."""
import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.skills import repository
from app.skills.models import Skill

logger = logging.getLogger(__name__)

# Same safe character budget as content/service.py's _build_embedding_text
# (Story 2.2's truncation fix) -- kept as an independent module constant
# rather than imported from content/, since skills/ must not depend on
# content/ (AD-8: dependencies point Content -> Skills, never back).
EMBEDDING_TEXT_MAX_CHARS = 1000


def _build_embedding_text(name: str, description: str | None) -> str:
    """Build the text fed to embed_text() for a Skill, truncated to a safe
    character budget. Mirrors content/'s existing embedding-on-write
    pattern exactly (AD-11 point 4) so Story 6.2 (create) and Story 6.3
    (rename) share one implementation instead of each re-deriving their
    own -- this is the "embedding-write helper" this story is scoped to
    provide; the create/rename endpoints that call it are out of scope
    here."""
    raw = f"{name}: {description or ''}"
    if len(raw) > EMBEDDING_TEXT_MAX_CHARS:
        logger.debug(
            "Truncating embedding text from %d to %d chars for name=%r",
            len(raw), EMBEDDING_TEXT_MAX_CHARS, name,
        )
    return raw[:EMBEDDING_TEXT_MAX_CHARS]


async def list_all_skills(db: AsyncSession) -> list[Skill]:
    """Read-only enumeration of every Skill (the Service API `content/`'s
    batch ingestion job now calls instead of querying `skills` directly,
    AD-11 point 1)."""
    return await repository.list_all_skills(db)


async def get_skill_embedding(db: AsyncSession, skill_id: UUID) -> list[float] | None:
    """A single Skill's embedding, for `content/`'s semantic matching
    (Story 2.4) to consume without importing `Skill` itself."""
    return await repository.get_skill_embedding(db, skill_id)
