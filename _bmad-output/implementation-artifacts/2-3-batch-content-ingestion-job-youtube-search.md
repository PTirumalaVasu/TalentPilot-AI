---
baseline_commit: abebe3b
---

# Story 2.3: Batch Content Ingestion Job (YouTube Search)

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **developer**,
I want to build a scheduled batch job that discovers and ingests video content from YouTube,
so that the `content_catalog` is populated without exhausting YouTube's daily API quota.

## Scope Notes (read before starting)

1. **`content/` owns this job, per the architecture's module table** (`content/` owns `content_catalog` + embeddings + "ingestion job"). Job logic lives in `content/service.py` (new functions), a new `content/youtube_client.py` (HTTP wrapper), and a new `content/cli.py` (manual trigger entrypoint) — not in `core/`. This differs from Story 2.2's `embedding.py`, which is a generic dependency-free utility with zero domain awareness; this job is entirely `content_catalog`-domain-specific.

2. **Skill enumeration is a deliberate, narrow exception to AD-1, not a violation — document it as such.** AD-1's "Binds" list names `assignments`, `content_catalog`, `skill_progress`, `assignment_overrides` — it does **not** name `skills`. No module has an established owning repository for the `skills` table today (Epic 3's "Skill Master Data & Seed" story is still `backlog`; only `core/seeds.py`, a bootstrap script exempt from feature-module rules, touches `Skill` directly). This story adds `content/repository.py::list_all_skills()` — a **read-only** query against `Skill` (imported from `app.assignments.models`, same cross-file-but-same-table-ownership pattern `content/repository.py` already uses for `ContentCatalog`) — because the ingestion job must enumerate skills to search for. **Binding forward guidance:** when a future story establishes a real owning module/Service API for `skills`, migrate this read call to go through that Service API instead of a direct query.

3. **De-dup by YouTube video ID is done in Python, not a raw JSON SQL query.** `content_catalog.content_metadata` is a plain `JSON` column (not `JSONB` — see `assignments/models.py:67`), and this is a batch job with at most a handful of existing rows per Skill, not a hot request path. Reuse the existing `list_content_by_skill()` repository method, then filter in Python by checking `content_metadata.get("video_id")` against the newly-fetched video IDs — no new SQL-level JSON query, no new repository method needed for this specific check.

4. **Resolves Story 2.2's deferred truncation item, in scope for this story.** Story 2.2's code review explicitly deferred "no truncation for text exceeding `all-MiniLM-L6-v2`'s ~256 token limit" as **binding guidance for Story 2.3/2.4**, since real YouTube titles+descriptions are far more likely to exceed it than short skill names. This story must truncate the `f"{title}: {description}"` string fed to `embed_text()` to a safe character budget (**1000 characters** — a conservative proxy for ~256 tokens at ~4 chars/token, generous enough that title + a meaningful description slice both survive) before embedding. Log at `debug` level when truncation actually occurs (don't silently drop it, don't over-engineer a real tokenizer-aware truncation — a character-count slice is sufficient for this story).

5. **Quota-exhaustion detection uses the real YouTube API's own signal — no local call counter.** Per the research already in this codebase (`_bmad-output/planning-artifacts/research/technical-rag-and-vector-database-approach-for-matching-hr-assigned-skills-to-tutorials-research-2026-07-08.md:104`), `search.list` draws from a **separate ~100 calls/day bucket** (a June 2026 policy change) independent of the general 10,000-unit pool that `videos.list` draws from. YouTube signals bucket exhaustion via an HTTP `403` response whose JSON body contains `error.errors[].reason == "quotaExceeded"`. Detect exactly that shape in `youtube_client.py::search_videos()` and raise a dedicated `QuotaExceededError` — do **not** build a local per-run or persisted call counter; the API's own 403 is authoritative and survives process restarts (a local counter would not). `videos.list` (fetching duration/details) is not quota-limited at this app's scale (max 5 skills × 1 call/day, negligible against the 10,000-unit pool) — a `videos.list` failure is a per-skill failure, not a whole-job stop.

6. **Manual seeding is a CLI script, not an HTTP admin endpoint.** The epic AC offers "CLI command or admin endpoint" as alternatives. An admin endpoint would need a new authenticated/role-gated route (more surface, more review scope, and no existing admin-role concept beyond `HR_ADMIN`, which is a coaching/assignment role, not a content-curation role) for a workflow that in practice runs interactively from a terminal during content curation. `content/cli.py` (argparse, `python -m app.content.cli ...`) matches this codebase's existing "no `scripts/` directory yet, ad hoc invocation" pattern and adds zero new HTTP surface. **AD-7 still requires no live per-request YouTube search from any route** — the CLI script never touches `content/router.py`, and manual seeding specifically never calls YouTube at all (AC's own requirement).

7. **In-process/OS-level scheduling (the actual "once per day via cron/APScheduler") is explicitly out of this story's scope.** The epic AC's own phrasing ("e.g., once per day via cron/APScheduler") is illustrative, not prescriptive. This project has no production deployment target (`project-context.md`: "deployment is out of scope — local working copy only") and no existing scheduler dependency. This story delivers the **job logic** (`run_ingestion_job()`) and a **manual trigger** (`content/cli.py ingest`) that a host-level cron entry or a developer's terminal can invoke; wiring an actual recurring trigger (cron entry, APScheduler-in-process) is deferred — log this explicitly in Dev Agent Record, do not silently skip it. **Do not** wire `run_ingestion_job()` into `main.py`'s `lifespan` — that would run it on every app restart, not daily, and would violate AD-7's batch-only intent.

8. **No new third-party dependency required.** `requests==2.34.2` is already pinned in `requirements.txt` (added directly in Story 2.2's review). Use it for both YouTube Data API v3 calls (`search.list`, `videos.list`) via plain REST — do not add `google-api-python-client`, which pulls in a much heavier dependency tree for functionality `requests` already covers for two simple GET endpoints.

## Acceptance Criteria

### AC1 — Skill enumeration and per-skill YouTube search

**Given** the `skills` table has rows (seeded by Story 1.7/3.3)
**When** `run_ingestion_job()` runs with no explicit skill list
**Then** it queries all Skills via `content/repository.py::list_all_skills()`
**And** for each Skill, calls `youtube_client.search_videos(skill.name, max_results=3)` (top 3 results per Skill, per epic AC)
**And** `run_ingestion_job()` also accepts an optional explicit `skill_ids: list[UUID]` parameter to target specific Skills (used by the CLI's `ingest --skill-id` option and by tests, without requiring all 5 seeded Skills to be processed)

### AC2 — Video metadata fetch and embedding computation

**Given** `search_videos()` returns candidate video IDs + snippet data (title, description, thumbnail URL) for a Skill
**When** the job processes each result
**Then** it calls `youtube_client.get_video_durations(video_ids)` (one batched `videos.list` call per Skill, not one call per video) to fetch each video's ISO-8601 duration
**And** for each video not already ingested (AC3), computes a `sentence-transformers` embedding from `embed_text(f"{title}: {description}"[:1000])` (truncated per Scope Note 4)

### AC3 — Storage with de-duplication

**Given** a video's metadata and embedding are ready
**When** the job checks whether this video is already in the catalog
**Then** it compares the video's YouTube ID against `content_metadata.get("video_id")` for this Skill's existing Content rows (fetched via `list_content_by_skill`, per Scope Note 3 — no new SQL query)
**And** if already present, skips it (no duplicate insert, no re-fetch of an unchanged embedding)
**And** if new, calls `content/repository.py::create_content()` with `source="YOUTUBE"`, `type="VIDEO"`, and `content_metadata={"video_id": ..., "duration": <ISO-8601 string>, "thumbnail_url": ...}`

### AC4 — Per-skill logging and graceful quota-exhaustion stop

**Given** the job processes multiple Skills in one run
**When** a Skill's search/fetch/insert succeeds
**Then** it logs success with the Skill name and count of newly-ingested videos
**When** a Skill's `videos.list` call or DB insert fails for a non-quota reason
**Then** it logs the failure with the Skill name and reason, and continues to the next Skill (one Skill's failure does not abort the run)
**When** `search_videos()` raises `QuotaExceededError` for any Skill
**Then** the job stops processing all remaining Skills immediately (quota is shared across the whole API key, not per-Skill), logs a single graceful message including the next calendar date the job should be retried (quota resets at midnight Pacific Time — log the date only, not an exact-time conversion), and returns a job summary distinguishing "processed" from "skipped due to quota" Skills

### AC5 — Manual seeding bypasses YouTube entirely

**Given** an operator wants to insert Content directly (e.g., a manually-curated video/document/website)
**When** they run `python -m app.content.cli seed --skill-id <uuid> --title ... --url ... --type VIDEO --source MANUAL [--description ...]`
**Then** a new Content row is created via `content/service.py::manual_seed_content()` — computing an embedding from the provided title+description exactly as the YouTube path does, but with **zero** calls to `youtube_client`/YouTube's API
**And** input is validated via a new `ManualContentCreate` Pydantic schema (required: `skill_id`, `title`, `url`, `type`; optional: `description`, `source` defaulting to `"MANUAL"`)

### AC6 — Batch-only invariant (AD-7): never triggered by a live request

**Given** AD-7's rule that `content_catalog` is populated only by a scheduled batch job, never live per-request search
**When** reviewing all call sites of `youtube_client.search_videos`/`run_ingestion_job`
**Then** they are called only from `content/cli.py` and this story's own tests — never from any `router.py` file, and never from `main.py`'s `lifespan`
**And** a permanent regression test greps every `backend/app/*/router.py` and `backend/app/main.py` for `run_ingestion_job`/`search_videos` and fails if either appears (same pattern as Story 2.2's `test_no_router_file_calls_embed_text_directly`)

### AC7 — YouTube API key configuration fails clearly, not at app boot

**Given** `YOUTUBE_API_KEY` is a new, optional (`str | None = None`) setting in `core/config.py`'s `Settings`
**When** the FastAPI app starts with no `YOUTUBE_API_KEY` set
**Then** the app boots normally (this key is irrelevant to serving HTTP requests — only the ingestion CLI needs it)
**When** `python -m app.content.cli ingest` runs with `settings.YOUTUBE_API_KEY` unset
**Then** it exits with a clear, actionable error message (not an unhandled exception from inside an HTTP call) before making any network call

## Tasks / Subtasks

- [x] Task 1: `content/youtube_client.py` — YouTube Data API v3 wrapper (AC: #1, #2, #4, #7)
  - [x] Define `QuotaExceededError(Exception)`
  - [x] Define constants: `YOUTUBE_SEARCH_URL`, `YOUTUBE_VIDEOS_URL` (`https://www.googleapis.com/youtube/v3/{search,videos}`), `MAX_RESULTS_PER_SKILL = 3`
  - [x] `search_videos(api_key: str, query: str, max_results: int = MAX_RESULTS_PER_SKILL) -> list[dict]` — GETs `search.list` (`part=snippet`, `type=video`, `q=query`, `maxResults=max_results`, `key=api_key`); returns a list of `{video_id, title, description, thumbnail_url}`. On HTTP 403 with `error.errors[].reason == "quotaExceeded"` in the response body, raise `QuotaExceededError`. On any other non-2xx, raise a generic exception with the response body's message.
  - [x] `get_video_durations(api_key: str, video_ids: list[str]) -> dict[str, str]` — GETs `videos.list` (`part=contentDetails`, `id=<comma-joined ids>`, `key=api_key`) in one batched call; returns `{video_id: iso8601_duration_string}`. Raises a generic exception on non-2xx (never `QuotaExceededError` — different quota bucket, per Scope Note 5).
  - [x] Use `requests.get(...)` directly (already a pinned dependency); no new library.

- [x] Task 2: `content/repository.py` additions (AC: #1, #3)
  - [x] `list_all_skills(session: AsyncSession) -> list[Skill]` — plain `select(Skill)`, imported from `app.assignments.models` (Scope Note 2's documented exception)
  - [x] No change needed to `list_content_by_skill`/`create_content` — both already support this story's needs as-is

- [x] Task 3: `content/schemas.py` addition (AC: #5)
  - [x] `ManualContentCreate(BaseModel)`: `skill_id: UUID`, `title: str`, `url: str`, `type: Literal["VIDEO", "DOCUMENT", "WEBSITE"]`, `description: str | None = None`, `source: Literal["YOUTUBE", "MANUAL"] = "MANUAL"`

- [x] Task 4: `content/service.py` — ingestion + manual-seed orchestration (AC: #1, #2, #3, #4, #5)
  - [x] `_build_embedding_text(title: str, description: str | None) -> str` — `f"{title}: {description or ''}"[:1000]` (Scope Note 4), `logger.debug` when the pre-truncation string exceeded 1000 chars
  - [x] `async def ingest_content_for_skill(session, *, skill, api_key: str) -> dict` — calls `search_videos`, then `get_video_durations`, de-dups against `list_content_by_skill(session, skill.id)` per Scope Note 3, computes embeddings via `embed_text(_build_embedding_text(...))`, calls `create_content()` for each new video, `session.commit()` per skill (small batch, simple failure isolation — one skill's DB error doesn't roll back a sibling skill's already-committed inserts), returns `{"skill_name": ..., "ingested": N, "skipped_duplicate": M}`. Lets `QuotaExceededError` propagate uncaught (Task 5 catches it at the job level).
  - [x] `async def run_ingestion_job(session, *, skill_ids: list[UUID] | None = None) -> dict` — resolves the target Skill list (`list_all_skills()` or the explicit `skill_ids`), reads `settings.YOUTUBE_API_KEY` once, iterates Skills calling `ingest_content_for_skill`; on `QuotaExceededError` for any Skill, stops the loop immediately, logs the graceful quota message with tomorrow's date, and returns a summary `{"processed": [...], "skipped_due_to_quota": [...], "quota_exhausted": bool}`. Catches non-quota exceptions per-Skill, logs failure, continues.
  - [x] `async def manual_seed_content(session, *, data: ManualContentCreate) -> ContentResponse` — computes embedding via the same `_build_embedding_text` + `embed_text`, calls `create_content()`, `session.commit()`, returns `ContentResponse.model_validate(...)`. Never imports or calls anything from `youtube_client.py`.

- [x] Task 5: `content/cli.py` — manual trigger entrypoint (AC: #5, #6, #7)
  - [x] `argparse` with two subcommands: `ingest [--skill-id UUID ...]` and `seed --skill-id UUID --title ... --url ... --type ... [--description ...] [--source ...]`
  - [x] `ingest`: checks `settings.YOUTUBE_API_KEY` is set before doing anything else — if missing, prints a clear actionable message and `sys.exit(1)` (AC7) rather than letting the first HTTP call fail with an opaque error; otherwise opens a session via `app.core.db.async_session_factory` and calls `run_ingestion_job`
  - [x] `seed`: builds a `ManualContentCreate`, opens a session, calls `manual_seed_content`
  - [x] `if __name__ == "__main__":` entrypoint so `python -m app.content.cli <subcommand>` works

- [x] Task 6: AD-7 regression guard (AC: #6)
  - [x] New test asserting no `backend/app/*/router.py` or `backend/app/main.py` file contains the strings `run_ingestion_job` or `search_videos` (mirrors Story 2.2's `test_no_router_file_calls_embed_text_directly` pattern)

- [x] Task 7: `core/config.py` + `.env.example` (AC: #7)
  - [x] Add `YOUTUBE_API_KEY: str | None = None` to `Settings` — optional, does not break existing `load_settings()` fail-fast behavior for apps with no YouTube key configured
  - [x] Add a commented `YOUTUBE_API_KEY=` line + one-line explanation to `backend/.env.example`

- [x] Task 8: Tests (AC: #1–#7)
  - [x] `backend/tests/test_youtube_client.py`: `search_videos` parses a mocked successful `search.list` JSON response into the expected dict shape; `search_videos` raises `QuotaExceededError` on a mocked 403 `quotaExceeded` body; `search_videos` raises a generic exception on other non-2xx; `get_video_durations` parses a mocked `videos.list` response into `{video_id: duration}`; `get_video_durations` never raises `QuotaExceededError` even on a mocked 403 (Scope Note 5) — all via `monkeypatch`-ing `requests.get`, no real network call
  - [x] `backend/tests/test_content_ingestion.py` (live-DB, reusing `conftest.py`'s `db_session` fixture, consistent with the existing content test files): `list_all_skills` returns seeded Skills; `ingest_content_for_skill` with a mocked `youtube_client` inserts new Content rows with correct `source`/`type`/`content_metadata`; a second call with the same mocked search results skips the already-ingested video (de-dup, AC3); `run_ingestion_job` stops all remaining Skills and returns `quota_exhausted=True` when the mocked client raises `QuotaExceededError` partway through a multi-Skill run; a non-quota exception from one Skill's `get_video_durations` is caught, logged, and the job continues to the next Skill; `_build_embedding_text` truncates a long title+description to 1000 chars before it reaches `embed_text` (assert on the string passed to a monkeypatched `embed_text`, not on the real model's output)
  - [x] `backend/tests/test_content_cli.py`: `seed` subcommand invokes `manual_seed_content` with correctly-parsed args and never imports/calls `youtube_client`; `ingest` subcommand exits with a non-zero code and a clear message when `YOUTUBE_API_KEY` is unset, without attempting any HTTP call
  - [x] AD-7 regression test from Task 6 (`backend/tests/test_content_ad7_regression_guard.py`, separate file — kept isolated from `test_embedding.py` rather than added there, since it guards a different module's invariant)

### Review Findings

- [x] [Review][Patch] `ManualContentCreate.source` allowed `"YOUTUBE"` for a manually-seeded row with no `video_id` in its `content_metadata` — User decision: pin `source` to always `"MANUAL"` (drop the field's configurability entirely), matching the schema's own docstring intent ("bypasses youtube_client entirely"). Detail: `manual_seed_content` unconditionally sets `content_metadata=None`, so a manually-seeded row that had been marked `source="YOUTUBE"` was invisible to `ingest_content_for_skill`'s de-dup check (`if row.content_metadata`), letting a real ingestion run later insert a genuine duplicate for the same video. Fixed: `source: Literal["MANUAL"] = "MANUAL"`; removed `--source` from the CLI's `seed` subcommand. [backend/app/content/schemas.py:44-54, cli.py]
- [x] [Review][Patch] Missing `db.rollback()` in `run_ingestion_job`'s generic `except Exception` and `QuotaExceededError` branches — if a mid-skill failure happens after `create_content`'s flush has already dirtied the session (e.g. `embed_text` raises on the 2nd result, or a flush hits a constraint violation), the shared `db` session is left aborted; every subsequent skill's DB calls then fail too, cascading one skill's failure into the whole run and violating AC4's isolation guarantee. Confirmed by 2 of 3 review layers independently, verified by reading the code. Fixed: `await db.rollback()` added to both except branches. **Follow-on fix required**: `db.rollback()` expires every ORM object on the shared session, so `ingest_content_for_skill` was changed to take plain `skill_id`/`skill_name` values instead of a live `Skill` object (a later loop iteration touching an expired attribute outside an awaited context raised `MissingGreenlet`) — caught by re-running this story's own tests after applying the patch, not by the original review. [backend/app/content/service.py]
- [x] [Review][Patch] `skipped_due_to_quota` double-counts skills when quota exhausts before the last skill — the `except QuotaExceededError` branch did `skipped_due_to_quota.extend(skills[index:])` (covering the current skill + all remaining), but the loop then continued to each remaining index, where the top-of-loop `if quota_exhausted:` guard appended the same skill names again. Fixed: `break` immediately after the `extend`. [backend/app/content/service.py]
- [x] [Review][Patch] `response.json()` called before checking `status_code` in both `search_videos` and `get_video_durations` — a non-2xx response with a non-JSON body (e.g. HTML error page from a proxy/502/503) would raise an unhandled `JSONDecodeError` instead of the intended descriptive exception/`QuotaExceededError`. Fixed: status_code checked first; `.json()` wrapped in try/except with an empty-dict fallback on decode failure. [backend/app/content/youtube_client.py]
- [x] [Review][Patch] `search_videos`'s `item.get("id", {}).get("videoId")` didn't guard against `id` being present but `None`/missing `videoId` — either shape raised `AttributeError` or yielded a `None` `video_id` that broke `get_video_durations`'s `",".join(video_ids)` (`TypeError`) and produced a stored `url` of `.../watch?v=None`. Fixed: `(item.get("id") or {}).get("videoId")`, and result items with no valid `videoId` are skipped rather than propagated. [backend/app/content/youtube_client.py]
- [x] [Review][Patch] `run_ingestion_job` never validated `api_key` before starting — the `YOUTUBE_API_KEY` unset check existed only in `cli.py`; any other caller got a doomed per-skill HTTP call for every skill instead of AC7's intended fast, clear failure. Fixed: `run_ingestion_job` now raises `ValueError` immediately if `api_key` is falsy, before querying Skills or making any HTTP call; `cli.py`'s own check remains as an earlier, friendlier failure path. [backend/app/content/service.py]
- [x] [Review][Patch] `max_results=3` hardcoded in `service.py`'s call to `search_videos` instead of referencing `youtube_client.MAX_RESULTS_PER_SKILL` — fixed: now references the constant. [backend/app/content/service.py]
- [x] [Review][Patch] AD-7 regression guard test only checked for the literal substrings `run_ingestion_job`/`search_videos` in router/main files — an aliased import call would have defeated it. Fixed: also greps for `from app.content.service import` / `from app.content import youtube_client` (and the `app.content.service`/`app.content.youtube_client` module paths) in router/main files. [backend/tests/test_content_ad7_regression_guard.py]
- [x] [Review][Defer] Race condition / TOCTOU in de-duplication — no unique DB constraint ties `skill_id` + `content_metadata->>'video_id'`, so two concurrent ingestion runs (or a within-batch duplicate `video_id` from YouTube's own response) could both pass the Python-side dedup check before either commits, producing duplicate rows. Pre-existing risk given this story's Python-side-only dedup design (Scope Note 3); a real DB constraint would need a schema migration, out of this story's scope. — deferred, real but not blocking for a 5-skill/3-video low-volume batch job with no concurrent-run mechanism yet.
- [x] [Review][Defer] Truncation visibility logged at `logger.debug`, disabled by default in most logging configs — Story 2.2's deferred item claimed "closed" by this story's truncation logic, but the log line an operator would need to notice truncation is effectively invisible at default log levels. — deferred, cosmetic/observability gap, not a correctness bug; revisit if truncation frequency ever becomes an operational concern.
- [x] [Review][Defer] No retry/backoff for transient YouTube API failures — a network blip or transient 5xx is treated identically to a permanent failure, abandoning that skill for the run. — deferred, reasonable for an MVP unattended batch job with no SLA; revisit if real-world quota/network flakiness proves costly.
- [x] [Review][Defer] `ManualContentCreate.skill_id` has no existence check against the `Skill` table before insert — a typo'd/nonexistent `skill_id` either creates an orphaned row or raises an uncaught `IntegrityError` from the CLI with a raw stack trace. — deferred, no FK-violation handling exists anywhere else in this codebase's content/assignments write paths yet (same category as Story 3.1's already-logged deferred item); revisit together.
- [x] [Review][Defer] `skill_ids` filter in `run_ingestion_job`/CLI `--skill-id` silently drops unmatched/typo'd UUIDs with no warning — job "succeeds" having processed fewer skills than requested, with no operator-visible signal. — deferred, low-severity UX gap for an operator-facing CLI tool; revisit if this becomes a recurring real-world footgun.
- [x] [Review][Defer] Quota-retry date computed from UTC "now" + 1 day, not Pacific Time — can be off by a calendar day during the UTC/Pacific day-boundary window. Scope Note 5 explicitly tolerates skipping exact-time conversion, so this is a plausible deviation from intent, not a hard AC violation. — deferred, cosmetic logging precision; revisit only if the exact retry date ever matters operationally.
- [x] [Review][Defer] `list_all_skills`'s documented AD-1 exception has no tracking mechanism (issue/ticket) tying it to the Epic 3 Skill Master Data story that's supposed to obsolete it — just an inline code comment. — deferred, process/hygiene item; the comment itself already documents the exception per the story's own Scope Note 2, no code change needed now.

## Dev Notes

### Why `content/`, not `core/` — contrast with Story 2.2

Story 2.2's `embedding.py` is a generic, domain-free text→vector utility, correctly placed in `core/` per AD-8 (every module depends on `core/`, `core/` depends on nothing feature-specific). This story's ingestion job is the opposite: it is entirely about one table (`content_catalog`) that `content/` exclusively owns (AD-1), plus a third-party integration (YouTube) with no relevance outside `content/`. It belongs in `content/`, and it depends on `core/embedding.py`'s `embed_text()` — never the reverse.

### The Skill-ownership gap is real, not a designed feature

`skills` isn't in AD-1's "Binds" list, and no story has built a `skills`-owning repository yet (Epic 3's Skill Master Data story is still `backlog` per `sprint-status.yaml`). This story's `list_all_skills()` is a narrow, read-only, explicitly-flagged exception — not a precedent to copy elsewhere without the same flag. If Epic 3's Skill story lands before this one is implemented, re-check whether it introduced a Service API this story should call instead of querying `Skill` directly.

### Quota handling: trust the API's own signal

Do not build a local counter, a Redis-backed rate limiter, or any persisted state to "track" the ~100/day search quota. YouTube's own 403/`quotaExceeded` response is the ground truth and is the only thing that can't drift out of sync with Google's actual enforcement (a local counter reset at the wrong hour, or reset on process restart when it shouldn't be, would either falsely block valid calls or let the job burn quota it doesn't have). Detecting the real signal is simpler and more correct than reimplementing rate-limiting client-side.

### Duration storage: raw ISO 8601, not parsed minutes

`videos.list`'s `contentDetails.duration` returns ISO 8601 (`"PT10M32S"`). Store that raw string in `content_metadata["duration"]`. Converting it to a human-readable "`X` minutes" display (per Story 2.5's UX spec) is that story's frontend/display concern, not this one's — parsing/formatting logic belongs where it's rendered, not baked into the stored value.

### Truncation resolves a real deferred item, don't skip it

Story 2.2's code review explicitly named this story as the point where `embed_text`'s missing truncation guard would stop being theoretical. A YouTube video description can run to several thousand characters; feeding that whole string to `embed_text` doesn't crash (the model silently truncates internally at ~256 tokens) but wastes compute encoding text that's discarded anyway, and makes the actually-embedded slice non-obvious to a future reader. A simple `[:1000]` character slice before calling `embed_text` is proportionate — do not build a tokenizer-aware truncator for this.

### Manual seed path must never import `youtube_client`

`manual_seed_content()` exists specifically so an operator can add Content with zero YouTube API usage (AC5's own wording: "without triggering a YouTube search"). If `content/service.py` imports `youtube_client` at module level (for the ingestion functions), that's fine — but `manual_seed_content()` itself must not call anything from it. The AD-7 regression test (Task 6) only checks router/main.py files; it's still worth a direct assertion in `test_content_cli.py` that the `seed` path works with `youtube_client` entirely unmocked/unpatched (proving it was never touched), not just that it "returns the right shape."

### Scheduling is explicitly deferred — say so, don't quietly drop it

The epic AC's "e.g., once per day via cron/APScheduler" is satisfied at the *logic* layer (`run_ingestion_job` is idempotent-ish per run via de-dup, and safe to invoke repeatedly) and at the *manual trigger* layer (`content/cli.py`), but not at the *automatic recurrence* layer — no cron entry, no APScheduler process exists after this story. This is a deliberate scope cut given the project's local-only, no-production-deployment status (see `project-context.md`'s "Two spine-era changes" note) — record it plainly in Completion Notes so it isn't mistaken for an oversight, and so whoever eventually adds real scheduling knows `run_ingestion_job()` is already built and just needs a trigger.

## Project Structure Notes

Changes land in:
- `backend/app/content/youtube_client.py` (NEW): `QuotaExceededError`, `search_videos`, `get_video_durations`
- `backend/app/content/service.py` (MODIFIED): `_build_embedding_text`, `ingest_content_for_skill`, `run_ingestion_job`, `manual_seed_content`
- `backend/app/content/repository.py` (MODIFIED): `list_all_skills`
- `backend/app/content/schemas.py` (MODIFIED): `ManualContentCreate`
- `backend/app/content/cli.py` (NEW): argparse entrypoint, `ingest`/`seed` subcommands
- `backend/app/core/config.py` (MODIFIED): `YOUTUBE_API_KEY: str | None = None`
- `backend/.env.example` (MODIFIED): documented `YOUTUBE_API_KEY=` placeholder
- `backend/tests/test_youtube_client.py`, `test_content_ingestion.py`, `test_content_cli.py` (NEW)

No changes to:
- `backend/app/content/router.py` (stays gated, no new routes — AC6/AD-7)
- `backend/app/main.py` (no lifespan wiring — Scope Note 7)
- `backend/app/assignments/models.py` (`Skill`/`ContentCatalog` schemas already complete from Story 1.7)
- `backend/app/core/embedding.py` (used as-is via `embed_text` import, not modified)
- Any frontend/`frontend/` code (no UI surface — Story 2.5 is where Content Discovery UI happens)

## Library/Framework Requirements

- **`requests==2.34.2`** (already pinned, Story 2.2) — used directly for YouTube Data API v3 REST calls. No new dependency.
- **No APScheduler, no `google-api-python-client`.** See Scope Notes 7 and 8 for why.

## Testing Requirements

- Test framework: `pytest` + `pytest-asyncio` (existing, `pytest.ini`'s `asyncio_mode = auto`)
- `test_youtube_client.py`: pure unit tests, `monkeypatch` on `requests.get` — no live network call, no real `YOUTUBE_API_KEY` needed
- `test_content_ingestion.py`: live-DB tests via the existing `conftest.py` `db_session` fixture (same pattern as `test_content_repository.py`/`test_content_service.py`) — **be aware this fixture calls `Base.metadata.drop_all()` on teardown against the real dev DB** (documented, unresolved landmine from Story 3.3's review, `deferred-work.md`); this story does not fix it, just inherits the same already-accepted risk/exclusion pattern every other content-module test file uses. YouTube calls in these tests are always mocked (`youtube_client.search_videos`/`get_video_durations` monkeypatched at the service layer) — never real HTTP.
- `test_content_cli.py`: unit tests around argument parsing + dispatch, with `manual_seed_content`/`run_ingestion_job` mocked at the module level (testing CLI wiring, not re-testing service logic already covered above)
- Follow the established exclusion pattern if running the full suite: live-DB test files (`test_database_schema.py`, `test_skill_progress.py`, and now potentially `test_content_ingestion.py` if it uses `db_session`) may need `--deselect` when run together in one session per the still-open cross-file shared-engine bug (`deferred-work.md`) — verify in isolation if the full-suite run shows unrelated `InterfaceError`/event-loop errors.

Test coverage expectations:
- All 3 YouTube API response shapes (success, quota-exceeded 403, other error) for both `search_videos` and `get_video_durations`
- De-dup correctness (second ingestion run of the same Skill inserts zero new rows)
- Quota-exhaustion mid-run stops remaining Skills and reports which ones were skipped
- Per-skill non-quota failure isolation (one Skill's failure doesn't abort the run)
- Truncation applied before `embed_text` is called
- Manual seed path never touches `youtube_client`
- AD-7 regression guard (no router/`main.py` references)

## Previous Story Intelligence

From Story 2.2 (`2-2-embedding-model-integration-sentence-transformers.md`, status `done`):
- `embed_text(text: str) -> list[float]` is importable from `app.core.embedding`, lazy-loads on first call, deterministic, ~fast when warm — this story's only interaction with it is calling it with a truncated string; no changes needed there
- **Explicit deferred item this story must close**: "no truncation/length handling for text exceeding the model's max sequence length (~256 tokens)... binding guidance for Story 2.3/2.4" — addressed via Scope Note 4/`_build_embedding_text`
- Established pattern: a permanent grep-based regression test (`test_no_router_file_calls_embed_text_directly`) is how this codebase proves a "never called from a route" invariant — reuse the identical technique for AC6 (Task 6)
- Established pattern: `logging.getLogger(__name__)`, not `print()`

From Story 2.1 (`2-1-content-catalog-data-model-and-schema.md`, status `done`):
- `content/repository.py`'s existing `list_content_by_skill`/`create_content`/`get_content_by_id` are reused as-is by this story; no signature changes needed
- `content_metadata` maps to the DB column named `metadata` via `Column(JSON, name="metadata")` in the ORM — Pydantic-side alias handling (`ContentResponse`) is unaffected by this story since ingestion writes ORM directly via `create_content(dict)`, not through `ContentResponse`
- Established pattern: embedding field excluded from default API responses — irrelevant here since this story adds no routes

From Story 3.1 (`3-1-assignments-data-model-and-hr-admin-scope.md`, status `done`):
- Established the "each live-DB test file gets its own private `create_async_engine`" workaround for the cross-file shared-engine bug — **not needed here** if `test_content_ingestion.py` reuses `conftest.py`'s shared `db_session` fixture the same way `test_content_repository.py`/`test_content_service.py` already do (consistent with those, not with the assignments-module tests' different workaround)
- `_parse_user_id`/`require_hr_admin` patterns are irrelevant to this story — the ingestion job and CLI have no `CurrentUser`/auth context at all (it's an offline batch process, not a request handler)

From Story 3.3 (`3-3-employee-master-data-and-seed.md`, status `done`) / `deferred-work.md`:
- **The `conftest.py` `drop_all()`-on-teardown landmine is still open and unfixed** — this story's own live-DB tests inherit the same risk every other content-module test file already accepts; not this story's job to fix (out of file-change scope), but worth re-confirming via `git stash`/isolation runs if the full suite behaves unexpectedly, per the established diagnostic pattern.

## Architecture Compliance

**AD-1 — Single-owner data modules:**
- `content_catalog` remains sole-owned by `content/repository.py` — this story adds no new callers outside `content/`
- `skills` read access is the documented, narrow exception (Scope Note 2) — not a precedent, flagged for future correction once a real owner exists
- ✅ Compliant with the documented exception

**AD-7 — Content ingestion is batch-only; matching is filter-then-rank with a threshold [ADOPTED]:**
- This story implements exactly the ingestion half of AD-7: `content_catalog` populated only via `run_ingestion_job`/CLI, never live per-request search (AC6, Task 6's regression guard)
- The filter-then-rank matching half is Story 2.4's job, not this one's — this story does not implement any matching logic
- ✅ This story is what makes AD-7's "batch-only" half concretely enforceable, closing the forward reference Story 2.2's Dev Notes left open

**AD-8 — Module dependency direction:**
- `content/` depends on `core/embedding.py` (`embed_text`) and `core/config.py` (`settings.YOUTUBE_API_KEY`) — both allowed, `core/` never depends back on `content/`
- No other feature module depends on this story's new `content/youtube_client.py`/`cli.py` — correctly leaf-level within `content/`
- ✅ Compliant

**Stack compliance ("Content ingestion quota" NFR, `prd.md` §"Content ingestion quota"):**
- "The video-source API's daily search quota caps content-catalog ingestion to a scheduled batch job — see FR-3/FR-4 feature-specific NFR. This is a hard external constraint, not a design choice." — implemented via AC4's quota-exhaustion handling
- ✅ This story implements that already-locked constraint; it does not re-decide it

## References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 2.3] — full AC text
- [Source: _bmad-output/planning-artifacts/architecture/architecture-TalentPilot-AI-2026-07-09/ARCHITECTURE-SPINE.md#AD-1] — single-owner data modules, `skills` not in the Binds list
- [Source: _bmad-output/planning-artifacts/architecture/architecture-TalentPilot-AI-2026-07-09/ARCHITECTURE-SPINE.md#AD-7] — batch-only ingestion rule
- [Source: _bmad-output/planning-artifacts/architecture/architecture-TalentPilot-AI-2026-07-09/ARCHITECTURE-SPINE.md#Module set] — `content/` owns `content_catalog` (+ embeddings), ingestion job
- [Source: _bmad-output/planning-artifacts/research/technical-rag-and-vector-database-approach-for-matching-hr-assigned-skills-to-tutorials-research-2026-07-08.md:104] — `search.list`'s dedicated ~100 calls/day bucket, June 2026 policy change
- [Source: _bmad-output/planning-artifacts/prds/prd-TalentPilot-AI-2026-07-09/prd.md#NFR "Content ingestion quota"] — hard external constraint framing
- [Source: backend/app/content/repository.py, service.py, schemas.py] — existing content-module code this story extends
- [Source: backend/app/assignments/models.py:41-53] — `Skill` ORM model (name, description, embedding columns), `ContentCatalog` model (content_metadata as plain JSON, not JSONB)
- [Source: backend/app/core/embedding.py] — `embed_text` signature/behavior this story calls into
- [Source: backend/app/core/config.py] — `Settings`/`load_settings` pattern this story extends with `YOUTUBE_API_KEY`
- [Source: backend/tests/test_embedding.py — test_no_router_file_calls_embed_text_directly] — regression-guard pattern reused for AC6
- [Source: _bmad-output/implementation-artifacts/deferred-work.md#"Deferred from: code review of 2-2-embedding-model-integration-sentence-transformers"] — the truncation item this story closes
- [Source: _bmad-output/implementation-artifacts/deferred-work.md#"Deferred from: dev-story of 3-3-employee-master-data-and-seed"] — the still-open `conftest.py drop_all()` landmine this story's live-DB tests inherit but do not fix

## Git Intelligence

- Current branch: `Story2.3` (already created for this story, tracks `origin/Story2.3`, currently identical to `main` — no divergent commits yet, confirmed via `git diff main...Story2.3` returning empty)
- Recent commits on `main`: `abebe3b` (Story 2.2, #40), `0e1cab3` (Merge from Main), `b2671f7` (Story 4-2 watch position capture, #41) — Epic 4 (progress capture) has progressed in parallel with Epic 2 stalling between 2.2 and 2.3, same pattern noted in Story 2.2's own Git Intelligence about Epic 2 vs. other epics
- Established workflow: implement on the existing story branch, commit, push, merge via PR, then next story starts from updated `main`
- No `2-3-*` story file existed before this one; `sprint-status.yaml` had `2-3-batch-content-ingestion-job-youtube-search: backlog` despite `2-2-...` being `done`

Expected workflow for this story:
1. Implement on the existing `Story2.3` branch
2. TDD: write failing tests first per task (`test_youtube_client.py` → `youtube_client.py`; `test_content_ingestion.py` → `repository.py`/`service.py` additions; `test_content_cli.py` → `cli.py`)
3. Run tests: `pytest backend/tests/test_youtube_client.py backend/tests/test_content_ingestion.py backend/tests/test_content_cli.py -v`
4. Run full regression, excluding known cross-file live-DB conflicts per the established pattern
5. Mark story status: `backlog` → `ready-for-dev` → `in-progress` → `review` → `done`
6. Merge via PR when code review passes

## Dev Agent Record

### Agent Model Used

Claude Sonnet 5 (Amelia persona, `bmad-dev-story`)

### Debug Log References

- Ran full backend suite mid-implementation and hit the pre-existing, already-documented `conftest.py`/`db_session` `drop_all()` landmine (`deferred-work.md`, "Deferred from: dev-story of 3-3-employee-master-data-and-seed") — the dev DB's tables were fully wiped down to just `alembic_version` by an earlier content-module test run in this same session. Root-caused via a direct `information_schema.tables` query (`['alembic_version']` only), confirming it wasn't caused by this story's own new code. Recovered per the established procedure: `DROP SCHEMA public CASCADE; CREATE SCHEMA public;`, `alembic upgrade head`, re-run `run_seeds()`.
- After recovery, re-ran the full suite excluding the two already-known cross-file live-DB conflict files (`test_database_schema.py`, `test_skill_progress.py`) plus, this time, the `db_session`-based content-module files (`test_content_repository.py`, `test_content_service.py`, `test_content_ingestion.py`) — since those wipe the shared DB on teardown and would otherwise re-trigger the same landmine for whatever runs after them alphabetically (`test_db.py`, `test_seed_employee_identity_alignment.py`). 143/143 passed.
- Verified `test_content_repository.py` + `test_content_service.py` + `test_content_ingestion.py` together in isolation (18/18 passing) — confirms this story's new tests integrate cleanly with the existing content-module test files under the same `db_session` fixture.
- Independently re-verified `test_database_schema.py` (16/16) and `test_skill_progress.py` (7/7) still pass 100% in isolation, confirming the already-known cross-file conflict is unrelated to this story's changes.
- Restored the dev DB to a clean migrated+seeded state as the final action, so the environment is left ready for the next session/story.

### Code Review Follow-up (2026-07-10)

3 parallel adversarial layers (Blind Hunter, Edge Case Hunter, Acceptance Auditor) ran against the diff vs. `baseline_commit`. Blind Hunter and Acceptance Auditor independently converged on the same critical bug (missing `db.rollback()`); Edge Case Hunter found a related double-count bug in the same code path. 1 decision resolved (source pinned to `MANUAL`), 8 patches applied, 7 deferred, 4 dismissed as noise.

1. **`ManualContentCreate.source` pinned to `"MANUAL"`** — was `Literal["YOUTUBE", "MANUAL"]`, now `Literal["MANUAL"] = "MANUAL"`; removed the CLI's now-meaningless `--source` flag.
2. **`db.rollback()` added to both `run_ingestion_job` except branches** — closes the cascading-failure gap where one skill's mid-batch DB error would poison the shared session for every subsequent skill.
3. **Follow-on fix discovered while verifying patch 2, not by the review itself**: `db.rollback()` expires every ORM object bound to the shared session, so the next loop iteration's `skill.name`/`skill.id` access on an already-expired `Skill` raised `sqlalchemy.exc.MissingGreenlet` (an out-of-greenlet async attribute reload). Fixed by changing `ingest_content_for_skill`'s signature to take plain `skill_id: UUID`/`skill_name: str` instead of a live `Skill` object, and pre-extracting `(id, name)` tuples in `run_ingestion_job` before the loop starts. Two of this story's own tests needed a matching fix (capture `skill.name` into a local variable before the `run_ingestion_job` call, for the same expired-attribute reason).
4. **`skipped_due_to_quota` double-count fixed** — `break` now follows the `extend` in the quota-exceeded branch instead of relying on the loop's `continue` to skip re-processing already-recorded skills.
5. **`response.json()` reordered after the `status_code` check** in both `search_videos`/`get_video_durations`, with a try/except fallback for a non-JSON error body.
6. **`search_videos` guards against `None`/missing `videoId`** — skips the malformed result item instead of propagating `None` into `video_ids`/the stored URL.
7. **`run_ingestion_job` validates `api_key` itself** (raises `ValueError` before querying Skills or making any HTTP call) — the CLI's own check remains as a friendlier, earlier gate for that specific entrypoint.
8. **`max_results=3` replaced with `youtube_client.MAX_RESULTS_PER_SKILL`** — removes the drift risk between the constant and the call site.
9. **AD-7 regression guard hardened** — now also greps for `from app.content.service import` / `from app.content import youtube_client` module-path references, not just the literal function-name substrings, closing the aliased-import bypass Blind Hunter identified.

**Deferred** (`deferred-work.md`, 7 items): TOCTOU race in Python-side de-dup (no DB unique constraint); truncation logged at `debug` level (limited real-world visibility); no retry/backoff for transient YouTube failures; `ManualContentCreate.skill_id` has no existence check; `--skill-id`/`skill_ids` silently drops unmatched UUIDs; quota-retry date computed from UTC not Pacific (Scope Note 5 tolerates this); `list_all_skills`'s AD-1 exception has no issue-tracking reference.

**Test Results (post-review):**
```
test_youtube_client.py: 5/5 passed
test_content_ingestion.py: 8/8 passed (2 tests updated to capture skill.name
  before the run_ingestion_job call, per the rollback-expiry fix)
test_content_cli.py: 2/2 passed
test_content_ad7_regression_guard.py: 1/1 passed (hardened)
Full suite (same exclusion pattern as pre-review): 143/143 passed, zero regressions
Content-module files together in isolation: 18/18 passed
test_database_schema.py (isolated): 16/16 passed
test_skill_progress.py (isolated): 7/7 passed
```

Status → `done`.

### Completion Notes List

**Implemented (2026-07-10):**
- `backend/app/content/youtube_client.py` (NEW): `QuotaExceededError`, `search_videos`, `get_video_durations` — thin `requests`-based REST wrapper, no new dependency.
- `backend/app/content/repository.py` (MODIFIED): `list_all_skills()` — the documented, narrow AD-1 exception (Scope Note 2) for enumerating Skills to search YouTube for.
- `backend/app/content/schemas.py` (MODIFIED): `ManualContentCreate` for the manual-seed CLI path.
- `backend/app/content/service.py` (MODIFIED): `_build_embedding_text` (closes Story 2.2's deferred truncation item), `ingest_content_for_skill`, `run_ingestion_job`, `manual_seed_content`.
- `backend/app/content/cli.py` (NEW): `python -m app.content.cli {ingest,seed}` — no new HTTP route, no scheduler wiring (both deliberately out of scope per Scope Notes 6/7).
- `backend/app/core/config.py` (MODIFIED): `YOUTUBE_API_KEY: str | None = None` — optional, app boots fine without it.
- `backend/.env.example` (MODIFIED): documented placeholder.
- 4 new test files: `test_youtube_client.py` (5 tests), `test_content_ingestion.py` (8 tests), `test_content_cli.py` (2 tests), `test_content_ad7_regression_guard.py` (1 test) — 16 new tests total, all TDD red-green.

**Key implementation decisions:**
1. **Quota detection via the API's real 403 signal, not a local counter** (Scope Note 5) — `search_videos` raises `QuotaExceededError` only on a 403 with `reason == "quotaExceeded"`; `get_video_durations` never raises it (different quota bucket), verified by a dedicated test (`test_get_video_durations_never_raises_quota_exceeded_on_403`).
2. **`run_ingestion_job` stops all remaining Skills the instant any Skill hits `QuotaExceededError`** — quota is shared across the whole API key. Non-quota per-Skill exceptions are caught, logged via `logger.exception`, and the loop continues (AC4) — verified both paths with dedicated tests.
3. **Per-skill commit inside `ingest_content_for_skill`**, not one commit at the end of `run_ingestion_job` — so a later Skill's failure (quota or otherwise) doesn't roll back an earlier Skill's already-successful inserts.
4. **De-dup done in Python** against `list_content_by_skill`'s existing results (Scope Note 3) — no new SQL/JSON query, since `content_metadata` is plain `JSON` (not `JSONB`) and this is a low-volume batch job.
5. **`manual_seed_content` never imports/calls `youtube_client`** — proven directly by a test that monkeypatches both `youtube_client` functions to raise `AssertionError` if called, then exercises the full manual-seed path successfully.
6. **CLI, not an admin HTTP endpoint, for manual seeding** (Scope Note 6) — zero new authenticated/role-gated route surface; `content/router.py` is untouched.
7. **No scheduler (cron/APScheduler) wiring** (Scope Note 7) — `run_ingestion_job()`/CLI are the complete deliverable for this story; automatic recurring triggering is explicitly deferred, consistent with this project's local-only, no-production-deployment scope. Not wired into `main.py`'s `lifespan` (would run on every app restart, not daily, violating AD-7's batch-only intent).
8. **AD-7 regression guard kept in its own file** (`test_content_ad7_regression_guard.py`) rather than appended to `test_embedding.py` — same grep-based pattern as Story 2.2's `test_no_router_file_calls_embed_text_directly`, but guarding a different module's invariant (`content/` ingestion vs. `core/` embedding).

**Environment note carried forward, not a regression:** hit the already-documented `conftest.py`/`db_session` `drop_all()`-wipes-the-shared-dev-DB bug mid-session (see Debug Log References) — recovered via the established `DROP SCHEMA public CASCADE`/`alembic upgrade head`/re-seed procedure, and left the DB in a clean migrated+seeded state. This story does not fix that bug (out of file-change scope, same as every prior story that has hit it); it only follows the same isolation-run verification pattern already established (Story 2.2, 3.1, 3.3) to prove none of this story's own tests are the cause.

**Test Results (pre-review):**
```
test_youtube_client.py: 5/5 passed
test_content_ingestion.py: 8/8 passed
test_content_cli.py: 2/2 passed
test_content_ad7_regression_guard.py: 1/1 passed
test_config.py: 4/4 passed (1 new, for YOUTUBE_API_KEY default)
Full suite (excluding test_database_schema.py, test_skill_progress.py, and the
db_session-based content-module files per the established cross-file live-DB
exclusion pattern): 143/143 passed, zero regressions
Content-module files together in isolation (test_content_repository.py +
test_content_service.py + test_content_ingestion.py): 18/18 passed
test_database_schema.py (isolated): 16/16 passed
test_skill_progress.py (isolated): 7/7 passed
```

All acceptance criteria satisfied. Story sent to review.

### File List

**New Files:**
- `backend/app/content/youtube_client.py`
- `backend/app/content/cli.py`
- `backend/tests/test_youtube_client.py`
- `backend/tests/test_content_ingestion.py`
- `backend/tests/test_content_cli.py`
- `backend/tests/test_content_ad7_regression_guard.py`

**Modified Files:**
- `backend/app/content/repository.py` (added `list_all_skills`)
- `backend/app/content/schemas.py` (added `ManualContentCreate`, `source` pinned to `Literal["MANUAL"]` per review)
- `backend/app/content/service.py` (added `_build_embedding_text`, `ingest_content_for_skill`, `run_ingestion_job`, `manual_seed_content`; review patches: `db.rollback()` in both except branches, `ingest_content_for_skill` signature changed to plain `skill_id`/`skill_name`, `api_key` validated up front, `MAX_RESULTS_PER_SKILL` constant used)
- `backend/app/content/youtube_client.py` (review patches: `status_code` checked before `.json()`, `None`/missing `videoId` guarded)
- `backend/app/content/cli.py` (review patch: `--source` flag removed, matching the pinned schema)
- `backend/app/core/config.py` (added `YOUTUBE_API_KEY: str | None = None`)
- `backend/.env.example` (documented `YOUTUBE_API_KEY` placeholder)
- `backend/tests/test_config.py` (added `test_youtube_api_key_defaults_to_none_app_boots_without_it`)
- `backend/tests/test_content_ingestion.py` (review-driven fix: capture `skill.name` before calling `run_ingestion_job`, since its internal rollback expires ORM attributes)
- `backend/tests/test_content_ad7_regression_guard.py` (review patch: hardened against aliased-import bypass)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (2-3 status: backlog → ready-for-dev → in-progress → review → done)
- `_bmad-output/implementation-artifacts/deferred-work.md` (7 new deferred items from code review)

**Unchanged (as expected):**
- `backend/app/content/router.py` (still gated, no new routes — AC6/AD-7)
- `backend/app/main.py` (no lifespan/scheduler wiring — Scope Note 7)
- `backend/app/assignments/models.py`
- `backend/app/core/embedding.py`
- No frontend/UI files (no client-visible surface for this story)

## Change Log

- 2026-07-10: Story 2.3 created (`bmad-create-story`) — no prior story file existed; sprint-status showed `2-3-...` as `backlog` despite `2-2-...` being `done`.
- 2026-07-10: Story 2.3 implemented (`bmad-dev-story`) — `content/youtube_client.py` (YouTube Data API v3 wrapper with quota-aware error handling), `content/service.py` ingestion/manual-seed orchestration, `content/cli.py` manual trigger entrypoint, `content/repository.py::list_all_skills` (documented AD-1 exception), `content/schemas.py::ManualContentCreate`, `core/config.py::YOUTUBE_API_KEY`. Closes Story 2.2's deferred embedding-text-truncation item. 16 new tests, all TDD red-green, zero regressions (143/143 main suite + 18/18 content-module isolation + 16/16 and 7/7 for the two already-known cross-file live-DB exclusions). No scheduler/cron wiring — explicitly deferred per Scope Note 7.
- 2026-07-10: Code review completed (`bmad-code-review`, 3 parallel adversarial layers — Blind Hunter, Edge Case Hunter, Acceptance Auditor). 1 decision resolved (`ManualContentCreate.source` pinned to `"MANUAL"`), 8 patches applied (most severe: missing `db.rollback()` could cascade one skill's failure into the whole batch run, independently confirmed by 2 of 3 layers; discovered and fixed a follow-on `MissingGreenlet` bug the rollback fix itself introduced, caught by re-running this story's own tests, not by the review), 7 deferred (`deferred-work.md`), 4 dismissed as noise. 143/143 passing, zero regressions. Status → `done`.
