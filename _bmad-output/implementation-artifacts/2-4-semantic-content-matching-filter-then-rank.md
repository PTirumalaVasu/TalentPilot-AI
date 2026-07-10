---
baseline_commit: abebe3b
---

# Story 2.4: Semantic Content Matching (Filter-then-Rank)

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **developer**,
I want to implement semantic content matching using pgvector cosine similarity,
so that relevant (but not exact-tag-matched) content is surfaced for a Skill.

## Scope Notes (read before starting)

1. **Story 2.3 (Batch Content Ingestion) is still `backlog`** — no real YouTube-ingested Content exists yet. This does NOT block this story: `content/repository.py::create_content` (Story 2.1) already supports manual content inserts, and this story's own tests populate `content_catalog` directly (via that function or direct ORM inserts) rather than waiting on a real ingestion job. AD-7 explicitly separates the two concerns: ingestion populates the table (2.3's job); matching queries whatever is already there (this story's job) — the matching logic has zero dependency on how a Content row got there.

2. **Skill embeddings already exist and this story never computes a new one.** Story 1.7 seeded 5 Skills with 384-dim embeddings. This story only *reads* `Skill.embedding` and `ContentCatalog.embedding` — both are assumed already computed and stored elsewhere. It does **not** call `embed_text` (Story 2.2's function) at all. This narrows Story 2.2's code-review-deferred "no text-truncation handling" item to Story 2.3's ingestion job only — that item's own text names both 2.3 and 2.4 as inheritors, but this story never calls `embed_text`, so it does not actually inherit that gap. Don't re-flag it here.

3. **No formal "skills" module/service exists yet** (Story 3.2, "Skill Master Data & Seed," is still `backlog`) — there is no `skills/repository.py` or `skills/service.py` to call for a Skill's embedding. Follow the exact precedent Story 2.1 already set for `ContentCatalog` (physically defined in `assignments/models.py` but logically owned/queried only by `content/`): `content/repository.py` may import `Skill` directly from `app.assignments.models` for this one **read-only, single-column** lookup. This is not a violation of AD-1 in spirit — no module owns a "Skill embedding lookup" service today, and this story writes nothing to `skills`. Don't generalize from it (see Dev Notes).

4. **No new FastAPI route in this story.** The epic AC describes matching logic only, with no endpoint mentioned. The deliverable is a `content/service.py` function that a **future** story (Story 3.4/3.5, Assignment creation) will call server-side to populate `Assignment.content_id`. `assignments/service.py::create_assignment_service` already has an explicit comment that `content_id` is not yet wired and names Story 3.4/3.5 as the place that adds it (see Previous Story Intelligence) — do not add a router endpoint "to expose" this story's work; there is no consumer for one yet.

5. **The pgvector `ivfflat` index on `content_catalog.embedding` was created without an operator class** (`idx_content_embedding`, `backend/alembic/versions/001_initial_schema.py:92` — no `postgresql_ops`), so it defaults to `vector_l2_ops` (Euclidean), not `vector_cosine_ops`. This story's queries use `.cosine_distance()` (the `<=>` operator), which that index does not accelerate — Postgres falls back to a sequential scan. Not a correctness bug (results are still exact) and immaterial at pilot scale (a handful of rows per Skill). Do not "fix" the index in this story — it's an indexing/performance concern, not a matching-logic concern. Flag it as deferred (see Dev Agent Record guidance), don't silently leave it undocumented and don't silently fix it either.

6. **`backend/tests/conftest.py`'s shared `db_session`/`test_engine` fixtures are a known, still-unfixed landmine.** `test_engine`'s teardown runs `Base.metadata.drop_all()` against the real dev database (not an isolated test DB), wiping every table app-wide after every single test that uses `db_session`. Logged in `deferred-work.md` as unfixed (blocked on Story 2.1's own tests using this fixture while Story 2.1 is still `review`, not `done`). **Do not use `db_session`/`test_engine` for this story's new test file.** Follow the pattern every live-DB test file added after that discovery uses instead (`test_assignments_repository.py`, `test_assignments_service.py`, `test_seed_employee_identity_alignment.py`): open a private `create_async_engine(settings.DATABASE_URL)` / session directly inside the test file, and clean up only the specific rows this story's tests create — never a blanket `drop_all()`.

## Acceptance Criteria

### AC1 — Pre-filter: Content is scoped to the target Skill before ranking

**Given** a Skill with one or more Content rows in `content_catalog`
**When** matching is requested for that Skill
**Then** only Content rows where `content_catalog.skill_id == <the Skill's id>` are considered — Content belonging to any other Skill is never returned, ranked, or compared, regardless of how similar its embedding might be

### AC2 — Rank: cosine similarity computed via pgvector, in the database

**Given** the pre-filtered set of Content rows for a Skill
**When** ranking them
**Then** cosine similarity between the Skill's `embedding` and each candidate Content's `embedding` is computed using pgvector's cosine-distance operator (`<=>`, via the `Vector` column's `.cosine_distance()` comparator) — evaluated by Postgres/pgvector, not by pulling all embeddings into Python and computing similarity there

### AC3 — Threshold: below-threshold matches are excluded

**Given** the ranked candidates
**When** the top-ranked candidate's similarity is `<= 0.7`
**Then** no Content is returned (`None`) even if candidates exist for that Skill — a below-threshold candidate is never returned as a fallback

### AC4 — Sort + return top 1

**Given** one or more candidates clear the `> 0.7` similarity threshold
**When** selecting the result
**Then** they are ranked by similarity descending and exactly the single highest-similarity Content item is returned (never a list, never more than one)

### AC5 — No qualifying match returns null, not an error or a guess

**Given** a Skill has Content rows but none clears the threshold, or has zero Content rows at all
**When** matching is requested
**Then** the function returns `None` (no exception, no default/fallback Content, no arbitrary pick) — an absent recommendation must be distinguishable by callers from a Skill/Content lookup error

### AC6 — Deterministic and repeatable

**Given** the same Skill and the same underlying `content_catalog`/`skills` data
**When** matching is requested multiple times (including across process restarts)
**Then** the same Content item is returned every time — including when two candidates' similarity scores tie exactly (a stable, explicit tie-break, not incidental row-fetch order) — until ingestion changes the underlying data

### AC7 — Nonexistent Skill fails safely

**Given** a `skill_id` that does not exist in `skills`
**When** matching is requested for it
**Then** the function returns `None` rather than raising an unhandled exception — there is no HTTP layer in this story to translate an error into a 404; the caller (e.g. a future assignment-creation story) decides whether a missing Skill is itself an error at its own layer

## Tasks / Subtasks

- [x] Task 1: Repository — Skill embedding lookup (AC: #7)
  - [x] `content/repository.py`: add `get_skill_embedding(db: AsyncSession, skill_id: UUID) -> list[float] | None` — `select(Skill.embedding).where(Skill.id == skill_id)`, `scalar_one_or_none()`, returns `None` if no matching row
  - [x] Import `Skill` from `app.assignments.models` (same module `ContentCatalog` is already imported from — Scope Note 3)

- [x] Task 2: Repository — single-query filter-then-rank (AC: #1, #2, #3, #4, #6)
  - [x] `content/repository.py`: add `SIMILARITY_THRESHOLD = 0.7` module constant (mirrors `core/embedding.py`'s `MODEL_NAME`/`EMBEDDING_DIM` plain-constant pattern — not wired into `Settings`/env, since no other module-tunable numeric constant is either)
  - [x] Add `find_best_matching_content(db: AsyncSession, skill_id: UUID, skill_embedding: list[float], threshold: float = SIMILARITY_THRESHOLD) -> ContentCatalog | None`
  - [x] Build the query as **one** statement, computing the cosine-distance expression once and reusing that same expression object in `WHERE`, `ORDER BY`, and the result label (don't call `.cosine_distance()` three separate times per row):
    ```
    distance = ContentCatalog.embedding.cosine_distance(skill_embedding)
    stmt = (
        select(ContentCatalog)
        .where(ContentCatalog.skill_id == skill_id, distance < (1 - threshold))
        .order_by(distance.asc(), ContentCatalog.id.asc())  # id tie-break for AC6 determinism
        .limit(1)
    )
    ```
  - [x] Return the matched `ContentCatalog` ORM instance, or `None` if the query returns no rows

- [x] Task 3: Service — public matching entrypoint (AC: #5, #7)
  - [x] `content/service.py`: add `match_content_for_skill(db: AsyncSession, skill_id: UUID) -> ContentResponse | None`
  - [x] Call `repository.get_skill_embedding`; if `None` (Skill doesn't exist), return `None` (AC7)
  - [x] Call `repository.find_best_matching_content` with the fetched embedding; if `None` (no qualifying match), return `None` (AC5)
  - [x] Convert the winning `ContentCatalog` to `ContentResponse` via `.model_validate()` (established Story 2.1 pattern) and return it

- [x] Task 4: Tests (AC: #1-#7)
  - [x] New file `backend/tests/test_content_matching.py` — private engine/session helper per Scope Note 6, **not** the shared `db_session` fixture
  - [x] Pre-filter (AC1): two Skills, each with Content; construct a Skill-B Content row with a raw embedding closer to Skill A than Skill A's own Content — assert it is never returned when matching Skill A
  - [x] Rank + top-1 (AC2, AC4): one Skill, 3+ Content rows with distinct, hand-crafted embeddings at controlled similarity levels — assert the highest-similarity row wins, not the first-inserted or an arbitrary one
  - [x] Threshold (AC3): a Skill whose only Content is constructed to score `<= 0.7` — assert `None`, not a best-of-a-bad-set fallback
  - [x] Boundary precision: Content rows constructed just-above and just-at/below the `0.7` similarity cutoff — assert the transition is exact (`> 0.7` passes; `== 0.7` does not, per AC3's `<=`) — see Dev Agent Record for why bit-exact `== 0.7` isn't tested
  - [x] Null cases (AC5): (a) Skill exists with zero Content rows, (b) Skill exists with Content rows but none clearing threshold — both assert `None`
  - [x] Nonexistent Skill (AC7): random UUID not present in `skills` — assert `None`, no exception raised
  - [x] Determinism (AC6): call `match_content_for_skill` twice against identical data — assert the identical `id` is returned both times; a dedicated tie test with two Content rows constructed to have byte-identical cosine distance — assert the same one wins every call (verifies the `ContentCatalog.id` tie-break, not incidental ordering)
  - [x] One test using real `embed_text`-derived embeddings (not hand-crafted) for a same-topic Skill/Content pair vs. an unrelated pair — confirms the SQL-level cosine query behaves correctly against real model output, not only synthetic vectors

### Review Findings

Code review completed 2026-07-10 (`bmad-code-review`, 3 parallel adversarial layers — Blind Hunter, Edge Case Hunter, Acceptance Auditor). The Acceptance Auditor ran the live test suite directly (12/12 passing) and found zero AC/spec violations. 0 decision-needed, 0 patches, 5 deferred, 12 dismissed.

- [x] [Review][Defer] No dimensionality validation on the embedding passed into matching — a wrong-sized vector (future model swap, upstream bug) surfaces as a raw pgvector/asyncpg error instead of a clean handled failure [backend/app/content/repository.py:84] — deferred, pre-existing
- [x] [Review][Defer] `threshold` parameter has no domain validation — e.g. `threshold=1.0` silently makes even a perfect match unreachable, out-of-range values silently match everything/nothing [backend/app/content/repository.py:88] — deferred, pre-existing
- [x] [Review][Defer] `find_best_matching_content` accepts `skill_id`/`skill_embedding` as independent parameters with no invariant enforced that the embedding actually belongs to that skill — a future direct caller passing mismatched values would silently rank against the wrong vector while filtering by the right skill_id [backend/app/content/repository.py:84-89] — deferred, pre-existing
- [x] [Review][Defer] `threshold: float = SIMILARITY_THRESHOLD` binds the module constant's value at import time (normal Python default-argument semantics) — a future `monkeypatch.setattr(repository, "SIMILARITY_THRESHOLD", ...)` (a pattern already used elsewhere in this project, e.g. Story 1.2's settings-singleton tests) would silently not affect calls that omit `threshold=` [backend/app/content/repository.py:88] — deferred, pre-existing
- [x] [Review][Defer] The three distinct "no match" reasons (Skill doesn't exist / Skill has zero Content / Skill has Content but none clears threshold) all collapse into an unlogged `None` — satisfies AC5/AC7 exactly, but leaves no diagnostic trail if a future caller needs to ask "why didn't this skill get a recommendation" [backend/app/content/repository.py:111, backend/app/content/service.py:57-65] — deferred, pre-existing

## Dev Notes

### Why this story has almost no new plumbing to build

Stories 2.1 (schemas/repository/service skeleton) and 2.2 (`embed_text`, warm model) did the heavy lifting. This story is narrow by design: one new repository query (filter+rank+threshold, expressed as a single SQL statement via pgvector operators) and one new service function wrapping it. Resist adding anything beyond AC1-7 — no new schemas (reuse `ContentResponse` from 2.1), no new router, no ingestion logic (2.3's job), no `skills` CRUD (3.2's job).

### `cosine_distance` vs. cosine similarity — get the conversion right once

pgvector's `<=>` operator (exposed as `Column.cosine_distance(other)` on the `Vector` type — confirmed present in the installed `pgvector==0.3.0` at `backend/.venv/Lib/site-packages/pgvector/sqlalchemy/vector.py`) returns **cosine distance**, defined as `1 - cosine_similarity`. The epic's threshold is phrased in similarity terms ("cosine similarity > 0.7"). Convert consistently: filter `distance < (1 - threshold)`. Do not compare a distance value directly against a similarity threshold (or vice versa) — that inverts the filter and would keep the *least* similar results.

### Single query, not fetch-all-then-Python-sort

The epic's "Pre-filter → Rank → Threshold → Sort → top 1" steps map onto **one** SQL statement (Task 2), not four sequential passes over Python data. This both matches the epic's explicit "using pgvector" instruction and avoids pulling every candidate's 384-dim embedding into the app process just to re-derive what Postgres already computes.

### Skill embedding access is a narrow, deliberate exception — don't generalize it

Scope Note 3 explains why `content/repository.py` reads `Skill` directly. If a future story needs to *write* to `skills`, or needs a different read shape (e.g., listing all Skills for an HR assignment-flow dropdown), that's Story 3.2's job to formalize as a real service — not more ad hoc reads bolted onto `content/repository.py`.

### Test data: hand-crafted vectors for precision, `embed_text` for realism

Threshold-boundary and tie-break tests need exact, reproducible cosine distances — construct 384-dim vectors directly (e.g. two unit vectors at a known angle, or simple patterned floats) rather than relying on `embed_text`'s real model output, which can't be dialed to an exact similarity value. Reserve one test using real `embed_text` output for a plausible same-Skill vs. different-Skill content pair, to catch any real integration issue (e.g. a malformed bind parameter or list/ndarray mismatch) that a fully synthetic suite could miss.

### Forward reference for Story 3.4/3.5 (binding guidance, same pattern Story 1.3 left for Story 2.x/3.x)

`assignments/service.py::create_assignment_service`'s existing docstring already says `content_id` is not yet wired and names Story 3.4/3.5 as the place that adds it. When that story is built: call `content.service.match_content_for_skill(db, skill_id)` and treat a `None` result as "no recommendation yet" (leave `content_id` null), not an error to surface to HR. This story does not touch `assignments/` at all — recorded here so whoever builds 3.4/3.5 doesn't have to rediscover this function or re-derive its `None`-means-no-recommendation contract.

### Known, deliberately-unfixed indexing gap (Scope Note 5)

Worth a one-line mention in this story's Dev Agent Record / deferred-work.md when implemented: the `ivfflat` index lacks a `vector_cosine_ops` opclass, so cosine queries seq-scan. Correct results, just not index-accelerated. Not this story's fix.

## Project Structure Notes

Changes land in:
- `backend/app/content/repository.py` (MODIFIED: adds `get_skill_embedding`, `find_best_matching_content`, `SIMILARITY_THRESHOLD`)
- `backend/app/content/service.py` (MODIFIED: adds `match_content_for_skill`)
- `backend/tests/test_content_matching.py` (NEW)

No changes to:
- `backend/app/content/schemas.py` (reuses `ContentResponse` from Story 2.1 — no new schema needed)
- `backend/app/content/router.py` (no HTTP endpoint in this story — Scope Note 4)
- `backend/app/content/models.py` (empty; `ContentCatalog`/`Skill` remain defined in `assignments/models.py`, unchanged)
- `backend/app/assignments/*` (Story 3.4/3.5's job to call this story's new function — Dev Notes forward reference)
- Any frontend/`frontend/` code (no UI surface — backend service function with no consumer wired up yet)

## Library/Framework Requirements

- **pgvector 0.3.0** (already installed) — `Column.cosine_distance(other)` on the `Vector` SQLAlchemy type, confirmed present in the installed package
- **SQLAlchemy 2.0.51 async** (already installed) — `select()` with a filter/order expression reused across clauses
- **No new dependencies.**

## Testing Requirements

- Test framework: `pytest` + `pytest-asyncio` (existing)
- Live database required (Postgres + pgvector, Docker Compose port 5433) — cosine-ranking correctness must be verified against real pgvector query execution, not mocked
- **Do not use the shared `db_session`/`test_engine` fixtures from `conftest.py`** (Scope Note 6) — use a private engine/session in this story's test file, following `test_assignments_repository.py`'s precedent
- Clean up only what each test creates (delete by the specific Skill/Content IDs the test inserted) — never trigger a blanket `drop_all()`

Test coverage expectations:
- Pre-filter correctness (cross-skill isolation)
- Cosine ranking correctness (highest similarity wins)
- Threshold boundary (exact `> 0.7` cutoff, not `>=`)
- Null-result paths (no content, no qualifying content, nonexistent skill)
- Determinism, including an exact-tie case
- One real-embedding integration test

## Previous Story Intelligence

From Story 2.2 (`2-2-embedding-model-integration-sentence-transformers.md`, status `done`):
- `embed_text(text: str) -> list[float]` exists at `app.core.embedding`, returns exactly 384 floats, deterministic — **not called by this story** (Scope Note 2); this story only reads embeddings other stories already computed and stored
- The deferred "no text-truncation for >~256 tokens" item is binding guidance for **Story 2.3's ingestion job**, not this one — clarified in Scope Note 2 since the original deferred note's phrasing named both 2.3 and 2.4

From Story 2.1 (`2-1-content-catalog-data-model-and-schema.md`, status `review`):
- `content/repository.py` already has `get_content_by_id`, `list_content_by_skill`, `create_content`; `content/service.py` already has `get_content`, `list_content_for_skill` — this story adds to both files, doesn't replace anything
- `ContentResponse` (no embedding field) is the established public schema shape; `.model_validate()` is the established ORM→Pydantic conversion pattern — reuse both as-is
- Established precedent: `content/repository.py` imports `ContentCatalog` directly from `app.assignments.models` despite `content/` being the "logical" owner — this story's `Skill` import follows the identical precedent (Scope Note 3)
- Manual content seeding already works today via `repository.create_content` — this story's tests use it (or direct ORM inserts) rather than waiting on Story 2.3

From Story 3.1 (`3-1-assignments-data-model-and-hr-admin-scope.md`, status `done`, per `deferred-work.md`):
- `assignments/service.py::create_assignment_service` always passes `content_id=None` today with an explicit comment that Story 3.4/3.5 adds the real lookup — confirms the forward-reference guidance above is accurate, not speculative

## Architecture Compliance

**AD-7 — Content ingestion is batch-only; matching is filter-then-rank with a threshold:**
- This story implements the "matching is filter-then-rank with a threshold" half exactly as specified: metadata pre-filter (skill_id) → pgvector cosine rank → threshold → top-1
- ✅ No live per-request YouTube search introduced (that's AD-7's ingestion half, Story 2.3 — untouched here)

**AD-1 — Single-owner data modules:**
- `content/` remains the sole module querying `content_catalog` (this story adds only read queries, no new writers)
- The `Skill` read is a narrow, documented exception (Scope Note 3) — no other module's data is written by this story

**AD-8 — Module dependency direction:**
- `content/` depends on `core/` (DB session) only; this story adds no new dependency on `assignments/`, `progress/`, or `dashboard/` beyond the pre-existing `Skill`/`ContentCatalog` ORM import from `assignments/models.py` (already an established AD-1 exception, not a new one)

**Stack compliance:**
- pgvector cosine operator (`<=>`) — exactly the mechanism the spine's Stack table and AD-7 specify; no alternative similarity library introduced

## References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 2.4] — full AC text
- [Source: _bmad-output/planning-artifacts/architecture/architecture-TalentPilot-AI-2026-07-09/ARCHITECTURE-SPINE.md#AD-7] — filter-then-rank + threshold rule, ingestion/matching split
- [Source: backend/.venv/Lib/site-packages/pgvector/sqlalchemy/vector.py] — confirmed `cosine_distance` comparator method on the installed pgvector version
- [Source: backend/app/assignments/models.py:41-76] — `Skill`, `ContentCatalog` ORM definitions (embedding columns, index)
- [Source: backend/alembic/versions/001_initial_schema.py:92] — `idx_content_embedding` created without an opclass (Scope Note 5)
- [Source: backend/app/content/repository.py, service.py, schemas.py] — existing Story 2.1 code this story extends
- [Source: backend/app/assignments/service.py:10-37] — `create_assignment_service`'s `content_id=None` forward reference to Story 3.4/3.5
- [Source: _bmad-output/implementation-artifacts/deferred-work.md] — `conftest.py` `db_session`/`test_engine` `drop_all()` landmine (Scope Note 6); Story 2.2's text-truncation deferred item (Scope Note 2)

## Git Intelligence

Recent commits (`abebe3b` Story 2.2 merge, `0e1cab3` Merge from Main, `b2671f7` Story 4-2, `4ab8dba` Story 2.2):
- Epic 2 and Epic 4 have progressed in parallel branches, each merged independently — consistent with this project's established pattern of epics advancing out of strict numeric order
- Current branch `feature/story-2.4` already exists, is checked out, and has a clean working tree — implement directly on it, no new branch needed
- Established pattern: implement → tests green → PR → merge to `main` → next story branches from updated `main`

Expected workflow for this story:
1. Implement on the existing `feature/story-2.4` branch
2. TDD: write `test_content_matching.py` first (RED against not-yet-existing repository/service functions), then implement
3. Run `pytest backend/tests/test_content_matching.py -v`, then a full-suite regression pass — this story's own tests use a private engine (Scope Note 6) so they should not need excluding themselves from the full-suite run, unlike the pre-existing `conftest.py`-dependent files
4. Mark story status: `backlog` → `ready-for-dev` → `in-progress` → `review` → `done`

## Dev Agent Record

### Implementation Plan

1. **Task 1+2 (repository)**: Added `get_skill_embedding` and `find_best_matching_content` to `content/repository.py`, plus the `SIMILARITY_THRESHOLD = 0.7` module constant, exactly per the story's prescribed query shape (one `cosine_distance` expression reused in `WHERE`/`ORDER BY`, `ContentCatalog.id` tie-break).
2. **Task 3 (service)**: Added `match_content_for_skill` to `content/service.py`, composing the two repository calls and converting the winning ORM row to `ContentResponse` via the established `.model_validate()` pattern.
3. **Task 4 (tests)**: Wrote `backend/tests/test_content_matching.py` (12 tests) using the Story 3.1 private-engine pattern (Scope Note 6) — confirmed all 12 pass on the first run against the already-implemented functions above.

### Completion Notes

**Implemented (2026-07-10):**
- `backend/app/content/repository.py` (MODIFIED): `SIMILARITY_THRESHOLD` constant, `get_skill_embedding`, `find_best_matching_content`.
- `backend/app/content/service.py` (MODIFIED): `match_content_for_skill`.
- `backend/tests/test_content_matching.py` (NEW): 12 tests covering AC1-AC7 plus a real-`embed_text` integration check.

**Key implementation decisions:**
1. **`get_skill_embedding` converts the fetched embedding to a plain `list[float]`** (`.tolist()`) rather than returning pgvector's raw `numpy.float32` ndarray (confirmed via `pgvector/utils/vector.py` that `Vector._from_db` returns an ndarray for a fresh `SELECT`, not a list) — matches the story's declared `list[float]` return type and keeps the storage/driver detail from leaking past the repository boundary.
2. **`find_best_matching_content` returns a single `ContentCatalog | None`, not a `(content, similarity)` tuple** — no AC or consumer needs the numeric similarity score exposed, and every other function in this repository (`get_content_by_id`, `list_content_by_skill`) already returns plain ORM instances or `None`; a tuple return here would be an unnecessary, inconsistent one-off.
3. **Boundary-precision testing does not attempt bit-exact equality at `similarity == 0.7`.** pgvector stores vector components as **float32** (confirmed in `pgvector/utils/vector.py`: `np.asarray(value, dtype='>f4')`), so a hand-crafted double-precision "exactly 0.7" cosine similarity picks up ~1e-7 relative rounding noise on write/read — which side of the boundary it lands on isn't controllable. Tested `0.71` (passes) and `0.69` (fails) instead — a 1% margin, far beyond float32 noise, that still directly exercises the `>` (not `>=`) semantics AC3 requires. Documented in the test file's `_vector_at_similarity` docstring so a future reader doesn't "fix" the test to chase an impossible bit-exact assertion.
4. **The real-`embed_text` integration test asserts ranking, not threshold-clearing**, using `threshold=0.0` to bypass the 0.7 cutoff for that one test — real sentence-transformers cosine scores for related-but-not-identical short phrases aren't reliably above 0.7, so asserting a hard pass/fail there would be flaky. The test still validates what AC2 actually requires: the SQL-level cosine query correctly ranks real model output, not just synthetic vectors.
5. **Confirmed, not just assumed: this story's own tests never touch `conftest.py`'s shared `db_session`/`test_engine` fixtures** (Scope Note 6) — `test_content_matching.py` uses its own `create_async_engine` and only ever `flush()`s + `rollback()`s, never `commit()`s beyond `run_seeds()`'s idempotent internal commit, so it cannot itself trigger or be affected by the documented `drop_all()`-wipes-the-whole-DB bug.

**Regression verification (full backend suite) — discovered the documented DB-wipe bug live, confirmed pre-existing:**
Running the full suite (`pytest tests/ --deselect test_database_schema.py --deselect test_skill_progress.py`, matching Story 2.2's exclusion pattern) surfaced 15 unrelated failures in `test_db.py` and `test_seed_employee_identity_alignment.py` — all `UndefinedTableError: relation "employees" does not exist`. Verified via direct DB inspection (`SELECT tablename FROM pg_tables`) that the dev database had been reduced to just `alembic_version`, and confirmed via isolated runs that `test_content_repository.py`/`test_content_service.py` (Story 2.1's pre-existing tests, unmodified by this story) are the actual cause — their `conftest.py` `db_session`/`test_engine` fixture runs `Base.metadata.drop_all()` on teardown, exactly as already documented in `deferred-work.md`'s "CRITICAL, blocks the full test suite" entry from Story 3.3. **Not a regression introduced by this story** — confirmed by running only those two pre-existing files in isolation and observing the same wipe with zero code from this story involved. Recovered via the documented procedure (`DROP TABLE alembic_version` + `alembic upgrade head`).

With **all four** now-known cross-file-conflicting live-DB test files excluded (`test_database_schema.py`, `test_skill_progress.py` — separately confirmed to corrupt each other via the shared `app.core.db.engine` pool, each passing 16/16 and 7/7 in isolation; `test_content_repository.py`, `test_content_service.py` — the `drop_all()` wipe, each passing 10/10 in isolation), the full suite is clean:

```
tests/test_content_matching.py: 12/12 passed (standalone)
Full suite (4 known-conflicting files excluded): 146 passed, 33 deselected, zero regressions
test_database_schema.py (isolated): 16/16 passed
test_skill_progress.py (isolated): 7/7 passed
test_content_repository.py + test_content_service.py (isolated): 10/10 passed
```

**Deferred** (`deferred-work.md`): the `idx_content_embedding` ivfflat index has no `vector_cosine_ops` opclass (Scope Note 5) — this story's cosine queries seq-scan instead of using the index. Correct results, immaterial at pilot scale; not this story's fix.

All acceptance criteria satisfied. Story sent to review.

## File List

**New Files:**
- `backend/tests/test_content_matching.py`

**Modified Files:**
- `backend/app/content/repository.py` (added `SIMILARITY_THRESHOLD`, `get_skill_embedding`, `find_best_matching_content`)
- `backend/app/content/service.py` (added `match_content_for_skill`)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (2-4 status: backlog → ready-for-dev → in-progress → review)
- `_bmad-output/implementation-artifacts/deferred-work.md` (1 new deferred item: ivfflat index opclass gap)

**Unchanged (as expected):**
- `backend/app/content/schemas.py` (reuses `ContentResponse` from Story 2.1)
- `backend/app/content/router.py` (no HTTP endpoint in this story)
- `backend/app/assignments/*` (Story 3.4/3.5's job to call the new service function)
- No frontend/UI files

## Change Log

- 2026-07-10: Story 2.4 created (`bmad-create-story`) — user chose 2.4 over 2.3 (2.3 still backlog); not a blocker per AD-7.
- 2026-07-10: Story 2.4 implemented (`bmad-dev-story`) — `content/repository.py` gained `get_skill_embedding`/`find_best_matching_content`/`SIMILARITY_THRESHOLD`, `content/service.py` gained `match_content_for_skill`, 12 new tests in `test_content_matching.py` (private-engine pattern, no shared fixture). Full regression pass confirmed zero new failures; discovered and confirmed pre-existing (not caused by this story) the documented `conftest.py` `drop_all()` DB-wipe bug and the `test_database_schema.py`/`test_skill_progress.py` shared-engine cross-file corruption, both already logged in `deferred-work.md`. Status → `review`.
