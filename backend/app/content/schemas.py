"""Pydantic request/response schemas for the content module."""
from datetime import datetime
from typing import Any, Literal
from urllib.parse import urlparse
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _reject_blank(value: str) -> str:
    # Mirrors skills/schemas.py::_reject_blank -- Field(min_length=1) alone
    # would accept a whitespace-only value, which the ACs' "non-empty"
    # requirement means to exclude (Story 6.5, UX spec's Form Validation
    # section: "required non-empty string/both required non-empty").
    stripped = value.strip()
    if not stripped:
        raise ValueError("must not be blank")
    return stripped


class ContentResponse(BaseModel):
    """Default public API response for content (excludes embedding for performance)."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    skill_id: UUID
    title: str
    description: str | None
    type: Literal["VIDEO", "DOCUMENT", "WEBSITE"]
    url: str
    source: Literal["YOUTUBE", "UDEMY", "MANUAL"]
    ingested_at: datetime
    # validation_alias (not alias): accept the ORM's content_metadata attribute
    # name on input, but serialize as "metadata" -- the intended public field
    # name per this schema's own docstring/Story 2.1 Dev Notes. A plain
    # `alias=` uses the same name for both validation AND serialization, which
    # would leak the DB-internal name over HTTP via FastAPI's response_model
    # (by_alias=True by default) -- invisible until this field's first real
    # HTTP response (Story 2.5), since content/router.py had zero routes before.
    metadata: dict[str, Any] | None = Field(default=None, validation_alias="content_metadata")


class SkillWithContentResponse(BaseModel):
    """GET /api/admin/skills response item (Story 6.10 AC1). Extends the
    plain Skill shape with its currently-approved Content -- the most
    recent origin="ADMIN_LOOKUP" content_catalog row, or None if it has
    none yet (Scope Note 2: BATCH-ingested rows are never "approved" in
    this epic's sense). Lives here, not skills/schemas.py, because it
    embeds ContentResponse and AD-8 requires the Content->Skills dependency
    arrow, never the reverse -- skills/router.py imports this the same way
    it already imports ContentLookupResponse for its other sub-routes."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    ever_assigned: bool
    approved_content: ContentResponse | None


class ContentWithEmbedding(ContentResponse):
    """Content response WITH 384-dim embedding (debug/admin only, not default)."""

    embedding: list[float]


class EmbeddingInput(BaseModel):
    """Input schema for embedding computation (internal use, Story 2.2)."""

    text: str


class EmbeddingOutput(BaseModel):
    """Output schema for embedding computation (internal use, Story 2.2)."""

    embedding: list[float]
    text: str  # Echo back for verification


class ManualContentCreate(BaseModel):
    """Input schema for manual content seeding via the CLI (Story 2.3, AC5).
    Bypasses youtube_client entirely -- no YouTube API call is ever made
    for this path. `source` is pinned to "MANUAL" (not caller-configurable):
    manual_seed_content always writes content_metadata=None, so a row
    claiming source="YOUTUBE" here would have no video_id and be invisible
    to ingest_content_for_skill's de-dup check, risking a future duplicate
    insert of the same video by a real ingestion run."""

    skill_id: UUID
    title: str
    url: str
    type: Literal["VIDEO", "DOCUMENT", "WEBSITE"]
    description: str | None = None
    source: Literal["MANUAL"] = "MANUAL"


# Upper bound on submitted credential values (code review, 2026-09-10) --
# real API keys/secrets are always well under this; guards against an
# arbitrarily large payload being accepted and encrypted/stored with no
# application-level limit. Same lesson Story 6.2's review already applied to
# CreateSkillRequest.name (max_length=255 there), sized generously here since
# a real-world API credential is unpredictable in exact format/length.
CREDENTIAL_MAX_LENGTH = 4096


class SetYoutubeKeyRequest(BaseModel):
    """PUT /api/admin/api-keys/youtube body (Story 6.5, FR-16). No format
    validation beyond non-blank -- a real invalid/revoked key surfaces its
    error at first search (Story 6.6), per the UX spec's own Form Validation
    section, not here."""

    model_config = ConfigDict(extra="forbid")

    key: str = Field(min_length=1, max_length=CREDENTIAL_MAX_LENGTH)

    @field_validator("key")
    @classmethod
    def key_must_not_be_blank(cls, value: str) -> str:
        return _reject_blank(value)


class SetUdemyCredentialRequest(BaseModel):
    """PUT /api/admin/api-keys/udemy body (Story 6.5, FR-16). Both fields
    required non-blank; no further format validation (same rationale as
    SetYoutubeKeyRequest)."""

    model_config = ConfigDict(extra="forbid")

    client_id: str = Field(min_length=1, max_length=CREDENTIAL_MAX_LENGTH)
    client_secret: str = Field(min_length=1, max_length=CREDENTIAL_MAX_LENGTH)

    @field_validator("client_id", "client_secret")
    @classmethod
    def fields_must_not_be_blank(cls, value: str) -> str:
        return _reject_blank(value)


class YoutubeKeyStatus(BaseModel):
    configured: bool


class UdemyCredentialStatus(BaseModel):
    configured: bool
    configured_by: str | None = None
    configured_at: str | None = None


class ApiKeysStatusResponse(BaseModel):
    """GET /api/admin/api-keys response (Story 6.5, FR-16). Never carries the
    encrypted or decrypted key/secret value, in any field, under any
    condition -- only configured-or-not + attribution metadata."""

    youtube: YoutubeKeyStatus
    udemy: UdemyCredentialStatus


# ---------------------------------------------------------------------------
# Live content lookup (Story 6.6, FR-17). No content_catalog row is ever
# written from this path -- search-only, writing happens in Story 6.8's
# (not yet built) approve action.
# ---------------------------------------------------------------------------

# Query length bound -- no epic-specified limit; sized generously (same
# reasoning as CREDENTIAL_MAX_LENGTH above) since a real search phrase is
# always well under this.
CONTENT_LOOKUP_QUERY_MAX_LENGTH = 500


class ContentLookupRequest(BaseModel):
    """POST /api/admin/skills/{id}/content-lookup body (Story 6.6 AC1)."""

    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1, max_length=CONTENT_LOOKUP_QUERY_MAX_LENGTH)

    @field_validator("query")
    @classmethod
    def query_must_not_be_blank(cls, value: str) -> str:
        return _reject_blank(value)


class ContentLookupCandidate(BaseModel):
    """One search result, from either source. Shaped identically to Story
    6.7's manual-entry candidate (source="MANUAL" there, no thumbnail_url)
    so both flow through the same downstream review/approve treatment
    (Story 6.8)."""

    title: str
    source: Literal["YOUTUBE", "UDEMY"]
    url: str
    thumbnail_url: str | None = None
    duration_hours: float | None = None


class ContentLookupSourceError(BaseModel):
    """One source's distinct failure (Story 6.6 AC's error union) -- the
    other source's results, if any, are unaffected (NFR-RES1)."""

    source: Literal["YOUTUBE", "UDEMY"]
    error: Literal["no_credential", "invalid_credential", "rate_limited", "source_error"]


class ContentLookupResponse(BaseModel):
    """GET.../content-lookup response. Flat, not nested per-source
    (Story 6.6 Scope Note 7 -- the epics AC describes per-source results/
    errors but doesn't pin an exact envelope): successful sources
    contribute tagged candidates to `results`, failed/unconfigured sources
    contribute one entry each to `errors`. A caller groups by
    `result.source` client-side if it needs per-source sections."""

    results: list[ContentLookupCandidate]
    errors: list[ContentLookupSourceError]


# ---------------------------------------------------------------------------
# Manual content entry (Story 6.7, FR-17a). No content_catalog row is ever
# written from this path -- same search-only invariant as Story 6.6's
# content-lookup, writing happens in Story 6.8's (not yet built) approve
# action.
# ---------------------------------------------------------------------------

# Generous URL length bound (same reasoning as CREDENTIAL_MAX_LENGTH/
# CONTENT_LOOKUP_QUERY_MAX_LENGTH above) -- a real URL is always well under
# this; guards against an arbitrarily large payload.
MANUAL_URL_MAX_LENGTH = 2048


def _validate_url(value: str) -> str:
    # Client-side-equivalent format check only (FR-17a's own consequence:
    # "HR Admin is responsible for the link being correct") -- no
    # reachability/content check. Requires an http(s) scheme and a
    # non-empty host, rejecting everything else (bare strings, other
    # schemes, scheme-only strings with no host).
    stripped = value.strip()
    parsed = urlparse(stripped)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError("must be a well-formed http(s) URL")
    return stripped


class ManualContentEntryRequest(BaseModel):
    """POST /api/admin/skills/{id}/content-manual body (Story 6.7 AC1)."""

    model_config = ConfigDict(extra="forbid")

    url: str = Field(min_length=1, max_length=MANUAL_URL_MAX_LENGTH)
    title: str = Field(min_length=1, max_length=255)
    # gt=0 rejects negative and zero values (code review, 2026-09-10) -- a
    # direct API call could otherwise submit a non-positive duration_hours,
    # which the frontend's numeric-only parser can never produce but the
    # schema didn't guard against; would echo straight back and render as a
    # nonsensical negative/zero days-to-complete estimate. Also rejects NaN,
    # since `NaN > 0` is always False.
    duration_hours: float | None = Field(default=None, gt=0)

    @field_validator("url")
    @classmethod
    def url_must_be_well_formed(cls, value: str) -> str:
        return _validate_url(value)

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, value: str) -> str:
        return _reject_blank(value)


class ManualContentCandidate(BaseModel):
    """Response shape for a manually-entered candidate (Story 6.7 AC1).
    Deliberately NOT a reuse of ContentLookupCandidate -- that schema's
    docstring already flags this fork: same downstream review/approve
    treatment, but no thumbnail_url field at all here (not just None),
    since a manual entry never has one."""

    title: str
    source: Literal["MANUAL"] = "MANUAL"
    url: str
    duration_hours: float | None = None


# ---------------------------------------------------------------------------
# Attach content (Story 6.8, FR-18/FR-19). Writes a content_catalog row --
# unlike Story 6.6/6.7's search-only candidates, this is the actual approve
# action any candidate (searched or manual) eventually needs.
# ---------------------------------------------------------------------------


class AttachContentRequest(BaseModel):
    """POST /api/admin/content/attach body (Story 6.8 AC2). No `description`
    field: neither ContentLookupCandidate (Story 6.6) nor ManualContentCandidate
    (Story 6.7) -- the only two candidate shapes that can reach this endpoint
    today -- carries one, so there is nothing for a caller to actually supply.
    No `type` field either: always hardcoded to "VIDEO" in the service layer,
    never client-supplied (epics AC's own wording)."""

    model_config = ConfigDict(extra="forbid")

    skill_id: UUID
    title: str = Field(min_length=1, max_length=255)
    source: Literal["YOUTUBE", "UDEMY", "MANUAL"]
    url: str = Field(min_length=1, max_length=MANUAL_URL_MAX_LENGTH)
    duration_hours: float | None = Field(default=None, gt=0)

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, value: str) -> str:
        return _reject_blank(value)

    @field_validator("url")
    @classmethod
    def url_must_be_well_formed(cls, value: str) -> str:
        return _validate_url(value)
