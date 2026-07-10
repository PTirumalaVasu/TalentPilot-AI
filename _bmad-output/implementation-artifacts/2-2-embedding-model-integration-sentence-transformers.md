---
baseline_commit: fa59624
---

# Story 2.2: Embedding Model Integration (Sentence-Transformers)

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **developer**,
I want to integrate a local embedding model (sentence-transformers),
so that Skill names and Content descriptions can be vectorized for semantic matching.

## Scope Notes (read before starting)

1. **A model instance is already loaded ad hoc in `backend/app/core/seeds.py`** (`SentenceTransformer("all-MiniLM-L6-v2")`, line 72) — but it's a one-off local variable created fresh inside `seed_skills()`, not a shared, reusable, once-per-process singleton. This story extracts a proper `core/embedding.py` module with a module-level cached model and a public `embed_text(text: str) -> list[float]` function that both `seeds.py` and Story 2.3/2.4 (batch ingestion, semantic matching) will call. **Refactor `seeds.py` to use the new shared function instead of instantiating its own model** — do not leave two independent model-loading code paths.

2. **This is a `core/` concern, not a `content/` concern.** The embedding model itself has no knowledge of skills or content — it's a generic text→vector utility. Per architecture AD-8 (module dependency direction), `core/` sits below every feature module and has no dependencies on `content/`, `assignments/`, etc. `content/` module code (Story 2.3/2.4) will import `embed_text` from `core/embedding.py`, not the other way around. The `content_catalog` table's `embedding` column (owned by `content/` per AD-1) is unaffected by this story — no schema changes here.

3. **Story 2.1 already created the internal schemas this story will wire up**: `EmbeddingInput`/`EmbeddingOutput` in `backend/app/content/schemas.py` (lines ~32-44) are marked "internal use, Story 2.2" but are currently unused by any code. This story does NOT need a FastAPI route to use them — they exist for Story 2.3/2.4 to build a debug/admin endpoint later if needed. This story's own deliverable is the `core/embedding.py` utility function itself; wiring `EmbeddingInput`/`EmbeddingOutput` into an actual call site is optional here and explicitly deferred to whichever of 2.3/2.4 first needs it (do not invent a router endpoint just to "use" the schemas — that would be scope creep).

4. **No frontend/UI work applies to this story.** This is a pure backend, server-side-only utility with no HTTP endpoint and no client-visible behavior (confirmed against Story 2.1's Dev Notes: "these schemas are marked as internal-only, not exposed via any router endpoint"). Do not add any frontend code for this story.

5. **"Loads into memory once per app startup"** (epic AC) means the model must be loaded eagerly when the FastAPI app starts — not lazily on first call, and not once per request. Use FastAPI's `lifespan` context manager on the `app` instance in `backend/app/main.py` to trigger the load at startup, with `core/embedding.py` caching the loaded `SentenceTransformer` instance in a module-level variable so repeated calls to `embed_text()` reuse it. `main.py` has no existing `lifespan` — this story adds the first one.

6. **This machine's sandbox has already downloaded/cached `all-MiniLM-L6-v2`** (Story 1.7 ran `seed_skills()` against it, and Story 2.1 imported `sentence-transformers`, which is already in `backend/requirements.txt`). No new dependency install should be needed; if the model cache is missing in a fresh environment, that's exactly the failure path AC's error-handling section specifies — implement the fail-fast diagnostics, don't just assume the cache is always warm.

## Acceptance Criteria

### AC1 — Model loads once at app startup and is cached in memory

**Given** the architecture locked a local, free embedding model
**When** the FastAPI app starts
**Then** it loads a pre-trained `sentence-transformers` model (`all-MiniLM-L6-v2`, 384-dim):
- Downloads/caches it locally via the `sentence-transformers` library's own HuggingFace cache (no API calls, no quota concerns)
- Loads into memory exactly once per app process lifetime (FastAPI `lifespan`, not per-request)
- Subsequent `embed_text()` calls within the same process reuse the cached in-memory model instance (no reload)

### AC2 — `embed_text(text: str) -> list[float]` utility function

**Given** Skill names and Content descriptions need to be vectorized
**When** I call `embed_text(text)` after the model is loaded
**Then** it returns a `list[float]` of exactly 384 elements
**And** the function is importable from `app.core.embedding`
**And** calling it before the model has been loaded (e.g. in a test/script context with no app lifespan) transparently loads the model on first use rather than raising — the shared cache works whether triggered by app startup or a direct call

### AC3 — Embedding is deterministic

**Given** the same input text
**When** `embed_text(text)` is called multiple times (including across process restarts, since the model itself is fixed/pre-trained with no random initialization at inference time)
**Then** it returns the same 384-dim vector every time (identical floats, not just similar)

### AC4 — Embeddings are pre-computed, never called per API-request

**Given** the epic's requirement that the model is never invoked live during a request
**When** reviewing all call sites of `embed_text`
**Then** it is called only from: the app startup `lifespan` (to warm the model), `core/seeds.py` (batch seed-time embedding), and future batch ingestion jobs (Story 2.3) — never from any `router.py` request-handling path in this story or any existing code
**And** no FastAPI route in this story calls `embed_text` synchronously inside a request handler

### AC5 — Fail-fast startup error handling for model load failures

**Given** app startup
**When** the `sentence-transformers` model fails to load (network error, DNS failure, repository unavailable, corrupted cache, or unexpected output shape)
**Then** the app fails fast (does not hang, does not silently continue with no model) with a clear, actionable, logged error message covering:
- Model download/network failure — logs the failure reason and suggests checking network connectivity, disk space, and manual `pip install sentence-transformers==<version>`
- Corrupted model file / checksum mismatch — logs guidance to delete the local HuggingFace cache and retry
- Wrong output shape (e.g. loaded model produces a dimension other than 384) — logs the actual vs. expected dimension and suggests checking model name/version
- Any other load-time exception (including OOM) — caught, logged with stack trace via `logging`, and re-raised so the ASGI server exits with a non-zero status rather than continuing in a half-initialized state (no zombie process serving requests without a model)

**And** on successful load, the loaded model's approximate memory footprint is logged (e.g. `"Embedding model loaded (~100MB memory, all-MiniLM-L6-v2, 384-dim)"`) so an operator can monitor it

### AC6 — Inference latency is acceptable for batch ingestion

**Given** the model is loaded and warm
**When** `embed_text('sample')` is called
**Then** a single-call inference completes in under 100ms on this environment (measured and asserted in a test — treat as a soft/documented threshold if the CI/dev machine is meaningfully slower than the reference hardware, but the test must run and report actual timing, not skip)

## Tasks / Subtasks

- [x] Task 1: `core/embedding.py` module — model loading + caching (AC: #1, #2, #3)
  - [x] Create `backend/app/core/embedding.py`
  - [x] Define `MODEL_NAME = "all-MiniLM-L6-v2"` and `EMBEDDING_DIM = 384` as module constants
  - [x] Implement a module-level cache (`_model: SentenceTransformer | None = None`) and a `_get_model()` accessor that lazily instantiates `SentenceTransformer(MODEL_NAME)` on first call and reuses it thereafter (lazy singleton — works whether triggered by `lifespan` at startup or a direct call in a script/test)
  - [x] Implement `load_embedding_model() -> None` — eagerly forces `_get_model()` to run (called by `lifespan` at startup so the load happens once, up front, not on the first real request)
  - [x] Implement `embed_text(text: str) -> list[float]` — calls `_get_model().encode(text).tolist()`, returns exactly 384 floats
  - [x] Validate output shape defensively: raise a clear `RuntimeError` if the encoded vector length != `EMBEDDING_DIM` (covers AC5's "wrong output shape" path)

- [x] Task 2: Fail-fast error handling and diagnostics (AC: #5)
  - [x] Wrap the `SentenceTransformer(MODEL_NAME)` instantiation in `_get_model()` in a `try/except` catching the load-time exception classes that can occur (network/HF-hub errors, OSError for corrupted cache files, generic `Exception` as a catch-all for OOM/other)
  - [x] On failure, `logger.error`/`logger.exception` a clear, actionable message per AC5's three failure categories (network/download, corrupted cache, wrong shape) with the specific diagnostics text from the epic AC
  - [x] Re-raise (do not swallow) so `lifespan` startup fails and the ASGI server does not start serving requests with no model loaded
  - [x] On success, `logger.info` the loaded-model confirmation message with approximate memory footprint

- [x] Task 3: Wire eager load into FastAPI `lifespan` (AC: #1, #4)
  - [x] Add a `lifespan` async context manager to `backend/app/main.py` that calls `load_embedding_model()` before `yield` (startup) and does any needed cleanup after `yield` (shutdown — a no-op for this story, since the model has no explicit close/dispose method)
  - [x] Pass `lifespan=lifespan` to the `FastAPI(...)` constructor
  - [x] Confirm no router or request-handling code path calls `embed_text` (AC4) — this story adds no new routes

- [x] Task 4: Refactor `core/seeds.py` to use the shared utility (Scope Note 1)
  - [x] Replace `seeds.py`'s local `SentenceTransformer("all-MiniLM-L6-v2")` instantiation and `model.encode(...).tolist()` call with `from app.core.embedding import embed_text` and `embed_text(f"{name}: {description}")`
  - [x] Remove the now-unused `from sentence_transformers import SentenceTransformer` import from `seeds.py`
  - [x] Re-run the existing seed flow (or its tests) to confirm skills still seed with valid 384-dim embeddings after the refactor — no behavior change, same output shape

- [x] Task 5: Tests (AC: #1, #2, #3, #4, #5, #6)
  - [x] `backend/tests/test_embedding.py`: `embed_text("some text")` returns a `list[float]` of length 384
  - [x] `backend/tests/test_embedding.py`: `embed_text` is deterministic — same input called twice returns identical vectors (`==`, not approximate)
  - [x] `backend/tests/test_embedding.py`: `load_embedding_model()` followed by `embed_text(...)` does not reload the model — assert the cached model instance is reused (e.g. patch/spy on `SentenceTransformer.__init__` or the module-level cache variable's identity across two calls)
  - [x] `backend/tests/test_embedding.py`: calling `embed_text` directly without calling `load_embedding_model()` first still works (lazy-load fallback, AC2)
  - [x] `backend/tests/test_embedding.py`: a single `embed_text('sample')` call completes in under 100ms once the model is warm (`time.perf_counter()` around the call; document actual measured time in the test output/assertion message)
  - [x] `backend/tests/test_embedding.py`: simulate a load failure (e.g. monkeypatch `SentenceTransformer` to raise) and assert `load_embedding_model()`/`embed_text()` re-raises rather than silently returning a placeholder, and that the error is logged
  - [x] `backend/tests/test_embedding.py`: simulate a wrong-shape model output (monkeypatch `.encode()` to return a non-384-length array) and assert `embed_text` raises `RuntimeError` with a message naming the actual vs. expected dimension
  - [x] Update/verify `backend/app/core/seeds.py`'s existing seed-related tests (if any target `seed_skills` directly) still pass after the refactor with no behavior change — verified via `test_database_schema.py`'s `test_seed_skills_exist`/`test_seed_script_idempotent` (16/16 passing, live DB)
  - [x] Bonus: added `test_app_lifespan_warms_the_model_at_startup` verifying AC1's "loads at app startup" behavior end-to-end through `app.router.lifespan_context`

### Review Findings

- [x] [Review][Patch] AC5's "wrong output shape" doesn't fail at startup — `load_embedding_model()` only instantiates the model, never calls `.encode()`, so a dimension mismatch surfaces on the first real `embed_text()` call, not at boot [backend/app/core/embedding.py:47-49]
- [x] [Review][Patch] `except OSError`/`except Exception` ordering conflates network failures with corrupted-cache failures — `requests.exceptions.ConnectionError`/HF-hub errors are `OSError` subclasses, so a real network failure gets the wrong "delete your cache" diagnostic message [backend/app/core/embedding.py:22-42]
- [x] [Review][Patch] No lock around the lazy singleton's check-then-set in `_get_model()` — two concurrent callers before first load can both pass `if _model is None` and double-load [backend/app/core/embedding.py:22-24]
- [x] [Review][Patch] Error message's suggested HF cache path (`~/.cache/huggingface/models/`) doesn't match the real on-disk layout (`~/.cache/huggingface/hub/models--...`) [backend/app/core/embedding.py:27]
- [x] [Review][Patch] No automated guard proving AC4 ("`embed_text` never called per-request") — true today only by manual grep, nothing catches a future regression [backend/tests/test_embedding.py]
- [x] [Review][Patch] `lifespan`'s synchronous multi-second model load isn't wrapped in `asyncio.to_thread` — blocks the event loop during startup [backend/app/main.py:14-17]
- [x] [Review][Patch] Failure-path test only asserts a generic substring match, not that the *correct* failure category's message was chosen — can't catch the OSError/Exception conflation above [backend/tests/test_embedding.py]
- [x] [Review][Defer] No truncation/length handling for text exceeding the model's max sequence length (~256 tokens) — silent degradation once Story 2.3/2.4 pass full content descriptions; today's only callers (skill names) are well under the limit [backend/app/core/embedding.py:58-71] — deferred, out of this story's scope; binding guidance for Story 2.3/2.4

## Dev Notes

### Why this exists even though embeddings already work in `seeds.py`

Story 1.7 needed *some* embeddings to prove the pgvector schema and seed data worked, so it inlined a `SentenceTransformer` call directly inside `seed_skills()`. That was accepted as sufficient for a database-init story, but it is not a reusable, testable, once-per-process-loaded utility — every future caller (`content/` ingestion in 2.3, `content/` matching in 2.4) would otherwise reinvent model loading, with no shared cache and no consistent error handling. This story promotes that inline call into the shared `core/embedding.py` module the rest of the app depends on, and retrofits `seeds.py` to use it instead of maintaining two independent code paths that could drift (e.g. one gets fail-fast diagnostics, the other doesn't).

### Module placement: `core/`, not `content/`

The architecture's module table (`ARCHITECTURE-SPINE.md` "Module set") lists `content/` as owning `content_catalog` (+ embeddings) — but "owning embeddings" means owning the *column* and the *decision to store one*, not owning the *model-loading utility itself*. The embedding model is a generic text→vector function with zero knowledge of skills, content, or any table — exactly the kind of cross-cutting, dependency-free utility `core/` is for (alongside JWT/security, config, error handlers). AD-8 (module dependency direction) has every feature module depending on `core/`, never the reverse — putting `embed_text` in `content/` would force `assignments/`'s future skill-embedding needs (if any) or `core/seeds.py` itself to import from `content/`, which is backwards. Confirmed by the fact that `core/seeds.py` already needs this function today and `core/` cannot depend on `content/`.

### Lazy-singleton vs. eager-at-startup — why both

AC1 says "loads into memory once per app startup," which implies eager loading. But `embed_text()` must also work correctly when called directly (from `seeds.py`, from a test, from a one-off script) without an ASGI app or `lifespan` ever running. The design here reconciles both: `_get_model()` is a lazy singleton (loads on first call, whoever that caller is), and `load_embedding_model()` is a thin eager-trigger that `lifespan` calls at startup specifically so the *first* caller is app startup, not the first real request. This means the same caching code correctly serves both "app boots and warms the model" and "a pytest test or seed script calls `embed_text` directly with no app running" — don't build two separate loading mechanisms for these two cases.

### `main.py` gets its first `lifespan` — read it before editing

`backend/app/main.py` currently has no `lifespan` parameter on its `FastAPI(...)` constructor (confirmed by reading the file: it's a flat sequence of `add_middleware`/`include_router` calls with no async context manager). This story adds the first one. Preserve every existing line — `CORSMiddleware`, `register_exception_handlers`, all 5 router includes, and the `GET /` health check — none of that changes; only a `lifespan` async context manager function is added above `app = FastAPI(...)` and wired in via the `lifespan=` kwarg.

### Test the failure paths for real, not just the happy path

The epic's own "ERROR HANDLING & DIAGNOSTICS" section is unusually detailed for a story this small — three distinct failure shapes (network/download, corrupted cache, wrong output shape) each with prescribed message content. Story 1.1's code review (still-referenced precedent in this codebase) established that error-handling code without a regression test guarding it tends to silently rot. Use `monkeypatch`/mocking to force each of the three failure shapes in `test_embedding.py` — don't just write the `try/except` and assume it works.

### Determinism note

`sentence-transformers` models in inference mode (no dropout, no training-time randomness) are deterministic for a fixed model version and fixed input — this is a property of the pre-trained model, not something this story's code needs to implement itself. The determinism test (AC3) is a regression guard against something *accidentally* introducing non-determinism later (e.g. a batching/padding change that affects floating-point output), not a defensive mechanism this story builds.

## Project Structure Notes

Changes land in:
- `backend/app/core/embedding.py` (NEW: model loading, caching, `embed_text`, error handling)
- `backend/app/main.py` (MODIFIED: add `lifespan` context manager calling `load_embedding_model()` at startup)
- `backend/app/core/seeds.py` (MODIFIED: replace inline `SentenceTransformer` usage with `embed_text` import)
- `backend/tests/test_embedding.py` (NEW: tests for all ACs)

No changes to:
- `backend/app/content/schemas.py` (`EmbeddingInput`/`EmbeddingOutput` already exist from Story 2.1, remain unused by any route — intentional per Scope Note 3)
- `backend/app/content/repository.py` / `service.py` / `router.py` (no content-module changes in this story)
- `backend/app/assignments/models.py` (`ContentCatalog.embedding` column already exists from Story 1.7, unaffected)
- Any frontend/`frontend/` code (no UI surface for this story — see Scope Note 4)

## Library/Framework Requirements

- **sentence-transformers 3.4.0** (already installed, in `backend/requirements.txt` since Story 1.7) — no version change
- **No new dependencies required.** This story wires up an already-installed library; do not add torch/numpy pins beyond what `sentence-transformers` already pulls in transitively.

## Testing Requirements

- Test framework: `pytest` + `pytest-asyncio` (existing)
- No live database or Docker dependency for this story's own tests — `embed_text` is a pure in-process function with no DB access. Tests should run standalone (`pytest backend/tests/test_embedding.py -v`) without requiring the Docker Postgres instance to be up.
- Use `monkeypatch` (pytest's built-in fixture) to simulate load failures and wrong-shape outputs — do not attempt to actually break the network or corrupt a real cache file
- Timing assertion (AC6) should use `time.perf_counter()` and report the measured duration in the assertion failure message, so a slow CI machine's failure is diagnosable rather than a bare `assert False`

Test coverage expectations:
- Model caching/singleton behavior (loaded once, reused across calls)
- Correct 384-dim output shape
- Determinism (identical output for identical input across repeated calls)
- All three fail-fast error paths from AC5
- Latency threshold from AC6
- No regression in `core/seeds.py`'s seeding behavior after the refactor

## Previous Story Intelligence

From Story 2.1 (`2-1-content-catalog-data-model-and-schema.md`, status `review`):
- `content/schemas.py` already defines `EmbeddingInput { text: str }` and `EmbeddingOutput { embedding: list[float], text: str }`, explicitly scoped as "internal-only, not exposed via any router endpoint in this story" and earmarked for Story 2.2 — this story's `embed_text()` is the function those schemas will eventually wrap, but wrapping them into a route is NOT this story's job (see Scope Note 3)
- Established pattern: service layer methods are the cross-module contract; repository/ORM details stay internal to the owning module — `core/embedding.py` follows the same "one small, focused module" philosophy even though `core/` isn't a data-owning module
- Established pattern: `.model_validate()` for ORM→Pydantic conversion — not directly relevant here since this story has no ORM/Pydantic boundary, but consistent with the codebase's "thin, explicit conversion functions" style

From Story 1.7 (`1-7-database-schema-initialization-and-migration.md`, status `done`):
- `sentence-transformers==3.4.0` added to `backend/requirements.txt` specifically to support embedding-based seeding — already installed, confirmed importable
- `core/seeds.py`'s `seed_skills()` is the only existing call site of `SentenceTransformer` in the codebase today — this story's Task 4 refactors that exact call site
- Established pattern: idempotent seed functions check for existing data before re-inserting — unaffected by this story's refactor, since only the embedding-computation line changes, not the idempotency check
- Environment fact: this machine's Python is 3.14.0 (not the architecture's assumed 3.12/3.13) — all Story 1.7-era packages were pinned to versions with `cp314` wheels; `sentence-transformers==3.4.0` already installs cleanly here, so no new wheel-availability risk from this story

From Story 1.1 (`1-1-project-structure-and-core-dependencies.md`, status `done`):
- Centralized `{status, code, message, timestamp}` error contract lives in `core/errors.py` — this story's fail-fast error handling (AC5) happens at *startup*, before any request is served, so it does NOT go through that HTTP error contract; it's a process-level `logger.exception` + re-raise, not an API error response. Don't conflate the two.
- `logging.getLogger(__name__)` is the established logging pattern across `core/` modules (see `core/errors.py`) — `core/embedding.py` should follow the same pattern rather than `print()` or a new logging setup.

## Architecture Compliance

**AD-8 — Module dependency direction:**
- `core/` has no dependencies on any feature module (`auth/`, `assignments/`, `content/`, `progress/`, `dashboard/`)
- `core/embedding.py` imports only `sentence-transformers` (third-party) and stdlib `logging` — zero intra-app imports
- `content/` (Story 2.3/2.4) will depend on `core/embedding.py`, never the reverse
- ✅ This story's placement in `core/` (not `content/`) is required by, not incidental to, AD-8

**Stack compliance ("Embedding model" row):**
- Local `sentence-transformers` (`all-MiniLM-L6-v2`, 384-dim) — free/offline, no API key — exactly as locked in the architecture spine's Stack table and `project-context.md`'s "two spine-era changes" note (supersedes the PRD addendum's paid `text-embedding-3-small`)
- ✅ This story implements that already-locked decision; it does not re-decide the model choice

**AD-7 — Content ingestion is batch-only (forward reference, not this story's scope):**
- AD-7 governs `content/`'s ingestion/matching batch-only rule (Story 2.3/2.4) — this story's AC4 ("never called per-request") is the `core/` half of the same principle applied one layer down: the embedding *primitive* itself must never be invoked inside a request handler, which is what makes AD-7's batch-only ingestion pattern possible for Story 2.3 to build on top of
- This story does not implement any batch job itself — only the utility function batch jobs will call

## References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 2.2] — full AC text including ERROR HANDLING & DIAGNOSTICS section
- [Source: backend/app/core/seeds.py:7,72,84] — existing inline `SentenceTransformer` usage to be refactored
- [Source: backend/app/content/schemas.py] — existing `EmbeddingInput`/`EmbeddingOutput` schemas from Story 2.1 (unused, earmarked for this story/later)
- [Source: backend/app/main.py] — current FastAPI app assembly, no `lifespan` yet
- [Source: backend/app/core/errors.py] — established `logging.getLogger(__name__)` pattern
- [Source: _bmad-output/planning-artifacts/architecture/architecture-TalentPilot-AI-2026-07-09/ARCHITECTURE-SPINE.md#AD-8] — module dependency direction
- [Source: _bmad-output/planning-artifacts/architecture/architecture-TalentPilot-AI-2026-07-09/ARCHITECTURE-SPINE.md#Stack] — locked embedding model decision
- [Source: _bmad-output/implementation-artifacts/2-1-content-catalog-data-model-and-schema.md] — predecessor story, schema definitions this story's utility will eventually feed

## Git Intelligence

Recent commits show:
- Story 3.1 and Story 4-0/4-1 (Epic 3/4 work) merged to `main` after Story 2.1 was created — Epic 2 stalled at Story 2.1 (`review` status) while other epics progressed in parallel
- Story 2.1 itself: commit `d8ffb98` on the (now-merged) `Epic2-stories` branch
- Current branch: `Story-2.2` (already created for this story, tracks `origin/Story-2.2`, currently identical to `main` — no divergent commits yet)
- Established pattern: implement on a story-specific branch, commit, push, merge via PR, then next story starts from updated `main`

Expected workflow for this story:
1. Implement on the existing `Story-2.2` branch
2. TDD: write failing tests first (`test_embedding.py`), then implement `core/embedding.py`
3. Run tests: `pytest backend/tests/test_embedding.py -v`
4. Run full regression: `pytest backend/tests/ -v` (excluding live-DB tests if Docker isn't reachable in this sandbox, consistent with prior stories' documented pattern)
5. Mark story status: `backlog` → `ready-for-dev` → `in-progress` → `review` → `done`
6. Merge via PR when code review passes

## Dev Agent Record

### Implementation Plan

Followed TDD (red-green-refactor) per task:
1. **Task 1+2 (embedding.py + error handling)**: Wrote `backend/tests/test_embedding.py` first (7 tests) against a not-yet-existing `app.core.embedding` module — confirmed RED (`ImportError`). Implemented `core/embedding.py` with a module-level lazy-singleton `_get_model()`, `load_embedding_model()` eager trigger, and `embed_text()` with output-shape validation and three-category fail-fast error logging (network/download, corrupted cache/`OSError`, wrong-shape `RuntimeError`). Confirmed GREEN (7/7).
2. **Task 3 (lifespan)**: Added an `asynccontextmanager`-based `lifespan` to `backend/app/main.py` calling `load_embedding_model()` before `yield`, wired via `FastAPI(..., lifespan=lifespan)`. Added a regression test (`test_app_lifespan_warms_the_model_at_startup`) driving the app's own `lifespan_context` directly and asserting the module-level cache is populated afterward. 8/8 passing.
3. **Task 4 (seeds.py refactor)**: Replaced `seeds.py`'s inline `SentenceTransformer("all-MiniLM-L6-v2")` instantiation + `.encode(...).tolist()` call with `from app.core.embedding import embed_text` and `embed_text(f"{name}: {description}")`. Removed the now-unused `sentence_transformers` import. Verified live against Docker Postgres (port 5433): ran `alembic upgrade head` + `run_seeds()` end-to-end, confirmed all 5 skills seeded with valid 384-dim vectors via `vector_dims(embedding)` query, then ran `test_database_schema.py`'s existing `test_seed_skills_exist`/`test_seed_employees_exist`/`test_seed_script_idempotent` (16/16 passing) — no behavior change from the refactor.
4. **Task 5 (tests)**: All test writing was done inline with Tasks 1-3 above per TDD; no separate implementation step needed.

### Completion Notes

**Implemented (2026-07-10):**
- `backend/app/core/embedding.py` (NEW): `MODEL_NAME`/`EMBEDDING_DIM` constants, `_get_model()` lazy singleton, `load_embedding_model()`, `embed_text(text) -> list[float]` with output-shape validation and 3-category fail-fast error handling/logging.
- `backend/app/main.py` (MODIFIED): added the app's first `lifespan` async context manager, calling `load_embedding_model()` at startup; `FastAPI(...)` now takes `lifespan=lifespan`. No other lines changed — all 5 existing router includes, CORS middleware, exception handler registration, and the `GET /` health check are untouched.
- `backend/app/core/seeds.py` (MODIFIED): `seed_skills()` now calls the shared `embed_text()` instead of instantiating its own `SentenceTransformer`; removed the now-dead `sentence_transformers` import. No change to idempotency logic or seed data.
- `backend/tests/test_embedding.py` (NEW): 8 tests covering AC1-AC6 (384-dim shape, determinism, singleton reuse, lazy-load fallback, <100ms warm latency, load-failure re-raise+logging, wrong-shape `RuntimeError`, and app-lifespan startup warming).

**Key implementation decisions:**
1. **Lazy singleton + eager trigger, not two separate mechanisms** — `_get_model()` lazily loads on first call (works for direct script/test callers with no app running); `load_embedding_model()` is a thin wrapper that forces that same lazy path to run, called by `lifespan` so app startup is normally the *first* caller. This satisfies both "loads once at app startup" (AC1) and "works when called directly from `seeds.py`/tests" (AC2) without maintaining two loading code paths.
2. **`core/`, not `content/`** — per AD-8 (module dependency direction), confirmed via Scope Note 2 reasoning: the embedding primitive has zero skill/content awareness and `core/seeds.py` (which cannot depend on `content/`) already needed it.
3. **`EmbeddingInput`/`EmbeddingOutput` schemas from Story 2.1 intentionally left unused** — no router endpoint was added in this story (Scope Note 3); those schemas remain earmarked for whichever of Story 2.3/2.4 first needs a debug/admin route.
4. **No frontend/UI changes** — confirmed no client-visible surface exists for this story (pure backend utility, no HTTP endpoint).
5. **Live-DB verification workaround**: this sandbox's Docker Postgres volume started empty this session (`alembic_version` had no rows) — ran `alembic upgrade head` + a one-off `run_seeds()` script to get a live, seeded database before verifying the `seeds.py` refactor end-to-end. Also independently confirmed a **pre-existing, already-documented bug** (`deferred-work.md`, from Story 1.7/3.1: "any second module-scoped-loop test file sharing the pooled `engine` singleton corrupts it") still applies — `test_database_schema.py` and `test_skill_progress.py` both pass 100% in isolation (16/16 and 7/7) but produce `InterfaceError`/`RuntimeError: Event loop is closed` failures when run in the same `pytest` session as other live-DB test files. Verified via `git stash` that this is not a regression introduced by this story — it reproduces identically on the unmodified baseline. Followed the same exclusion pattern prior stories (1.6, 3.1) used: full suite run with `--deselect tests/test_database_schema.py --deselect tests/test_skill_progress.py` (123/123 passing), plus both deselected files independently confirmed passing in isolation.

**Test Results (pre-review):**
```
backend/tests/test_embedding.py: 8/8 passed
Full suite (excluding pre-existing cross-file live-DB conflict, per established pattern): 123 passed, 23 deselected, zero regressions
test_database_schema.py (isolated): 16/16 passed
test_skill_progress.py (isolated): 7/7 passed
```

All acceptance criteria satisfied. Story sent to review.

### Code Review Follow-up (2026-07-10)

3 parallel adversarial layers (Blind Hunter, Edge Case Hunter, Acceptance Auditor) ran against the diff vs. `baseline_commit`. 0 decision-needed, 7 patch, 1 defer, ~14 dismissed as noise. All 7 patches applied:

1. **AC5 wrong-shape-at-startup gap fixed** — `load_embedding_model()` now calls `embed_text("startup shape check")` instead of just instantiating the model, so a dimension mismatch fails at boot, not on the first real request/job.
2. **Network vs. corrupted-cache error categories actually distinguished** — added explicit `except (RequestsConnectionError, HfHubHTTPError, LocalEntryNotFoundError)` branch *before* the generic `except OSError`, since `requests`/`huggingface_hub`'s network exceptions are themselves `OSError` subclasses (confirmed via `__mro__` inspection) and were previously swallowed by the corrupted-cache branch with the wrong diagnostic message. New dependencies `huggingface-hub==0.36.2`/`requests==2.34.2` pinned in `requirements.txt` (previously unpinned transitive deps of `sentence-transformers`, now imported directly).
3. **Added `threading.Lock` around `_get_model()`'s check-then-set** — a double-checked-locking pattern. Verified empirically (throwaway script, not just reasoning) that the unpatched version both double-loads *and* can crash with a real PyTorch `NotImplementedError` ("Cannot copy out of meta tensor") under concurrent first access — this was a real crash risk, not just a theoretical race.
4. **Fixed the cache-deletion path in the error message** — was `~/.cache/huggingface/models/` (never existed in current HF cache layout), now `~/.cache/huggingface/hub/models--sentence-transformers--<model>` (the real layout).
5. **Added `test_no_router_file_calls_embed_text_directly`** — greps every `backend/app/*/router.py` for `embed_text` and fails if any match; a permanent regression guard for AC4 instead of a one-time manual check.
6. **Wrapped the `lifespan` model load in `asyncio.to_thread`** — the synchronous multi-second `SentenceTransformer(...)` load no longer blocks the event loop during startup.
7. **Split the failure-path test into three category-specific tests** — network failure asserts "Network error" is logged and "corrupted" is NOT; corrupted-cache failure asserts "corrupted"+"delete cache" is logged and "Network error" is NOT; a new HF-hub-specific test confirms `HfHubHTTPError` is correctly routed to the network category despite subclassing `OSError`.

Also added `test_load_embedding_model_fails_fast_on_wrong_shape_at_startup_not_first_request` (regression guard for patch #1) and `test_concurrent_first_access_loads_model_exactly_once` (regression guard for patch #3, using a `time.sleep` inside a monkeypatched `__init__` to widen the race window).

**Deferred** (`deferred-work.md`): no truncation/length handling for text exceeding the model's max sequence length (~256 tokens) — not a live bug (only caller today is short skill names), binding guidance for Story 2.3/2.4 whose Content descriptions are far more likely to exceed it.

**Test Results (post-review):**
```
backend/tests/test_embedding.py: 13/13 passed (5 new: 2 category-specific failure tests replacing the old generic one, 1 HF-hub-specific test, 1 startup-shape-check test, 1 concurrency test)
Full suite (same exclusion as pre-review): 128 passed, 23 deselected, zero regressions
test_database_schema.py (isolated): 16/16 passed
```

Status → `done`.

## File List

**New Files:**
- `backend/app/core/embedding.py`
- `backend/tests/test_embedding.py`

**Modified Files:**
- `backend/app/main.py` (added `lifespan` context manager wrapping `load_embedding_model()` in `asyncio.to_thread`)
- `backend/app/core/seeds.py` (refactored `seed_skills()` to use shared `embed_text()`, removed direct `SentenceTransformer` import)
- `backend/requirements.txt` (pinned `huggingface-hub==0.36.2`, `requests==2.34.2` — now imported directly, not just transitively)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (2-2 status: backlog → ready-for-dev → in-progress → review → done)
- `_bmad-output/implementation-artifacts/deferred-work.md` (1 new deferred item from code review)

**Unchanged (as expected):**
- `backend/app/content/schemas.py` (`EmbeddingInput`/`EmbeddingOutput` remain unused, earmarked for Story 2.3/2.4)
- `backend/app/content/repository.py` / `service.py` / `router.py`
- `backend/app/assignments/models.py`
- No frontend/UI files (no client-visible surface for this story)

## Change Log

- 2026-07-10: Story 2.2 created (`bmad-create-story`) — no prior story file existed; sprint-status showed `2-2-...` as `backlog` despite Story 2.1 being in `review`.
- 2026-07-10: Story 2.2 implemented (`bmad-dev-story`) — `core/embedding.py` model-loading/caching utility, FastAPI `lifespan` startup hook, `core/seeds.py` refactored to the shared utility, 8 new tests all passing. No frontend/UI work required (confirmed no client-visible surface for this story).
- 2026-07-10: Code review completed (`bmad-code-review`, 3 parallel adversarial layers) — 7 patches applied (AC5 startup-shape-check gap, network/corrupted-cache error mislabeling, missing concurrency lock, wrong cache-deletion path in error message, missing AC4 regression guard, blocking event loop during startup, weak failure-path test assertions), 1 deferred (text-length truncation, binding guidance for Story 2.3/2.4), 0 decision-needed, ~14 dismissed as noise. 128/128 passing (up from 123), zero regressions. Status → `done`.
