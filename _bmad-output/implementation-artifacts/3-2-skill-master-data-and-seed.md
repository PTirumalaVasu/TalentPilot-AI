---
baseline_commit: abebe3b34dcdcc46e906da7e5a8781f037875d46
---

# Story 3.2: Skill Master Data & Seed

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **developer**,
I want to verify the Skills master table is seeded correctly with real embeddings computed via the shared embedding utility,
so that HR Admins can assign from a defined list and semantic content-matching (Epic 2) has real vectors to match against.

## Acceptance Criteria

1. **Given** the TalentPilot MVP scope, **when** the app starts for the first time, **then** a seed script populates the `skills` table with core skills from the Product Brief / design-thinking discovery, at least 5–10 starter skills — **already true today**: `backend/app/core/seeds.py::seed_skills()` (built in Story 1.7, refactored in Story 2.2) seeds exactly 5 skills (Data Visualization, Salesforce Admin, Python Programming, SQL & Databases, Communication Skills), matching the epic's own examples. This AC is verify-only; no new seed logic is expected. [Source: _bmad-output/planning-artifacts/epics.md#Story 3.2]
2. **And** each Skill has `id` (UUID), `name` (string, unique), `description` (optional text), `embedding` (pgvector 384-dim, computed from skill name) — confirmed present in `Skill` (`backend/app/assignments/models.py`) with a `UniqueConstraint` on `name`, and populated by `seed_skills()`.
3. **And** the seed is idempotent (can run multiple times without duplication) — confirmed: `seed_skills()` checks for `SKILL_DATA_VIZ_ID`'s existence before inserting and returns early if already seeded.
4. **And** the embedding is genuinely computed via the shared `embed_text()` utility (Story 2.2), not a leftover inline `SentenceTransformer` call or a stub/zero vector — `seed_skills()` was refactored during Story 2.2 to call `embed_text(f"{name}: {description}")` per skill; this AC verifies that refactor actually produces real, correctly-shaped (384-dim) embeddings end-to-end, not just that the function call compiles. This is the AC with genuine new test-writing work: existing coverage (`test_database_schema.py::test_seed_skills_exist`) only asserts a loose row count (`>= 5`), never per-skill name/uniqueness/embedding-shape correctness — mirroring the exact gap Story 3.3 found and closed for Employees (AC5 there).

## Tasks / Subtasks

- [x] Task 1: Verify existing seed data and models satisfy AC1–AC3 (AC: 1, 2, 3)
  - [x] Subtask 1.1: Read `backend/app/core/seeds.py::seed_skills()` and `backend/app/assignments/models.py::Skill` and confirm field list, seeded values (5 skills, unique names), and the idempotency check match the epic AC exactly; document confirmation in Dev Agent Record — do not edit either file unless a real gap is found
  - [x] Subtask 1.2: Confirm live DB already has the 5 seeded skills via the live-DB test suite (Task 3/4) rather than a standalone `psql` query — `docker exec ... psql` calls have previously produced no captured stdout in this sandbox despite exit code 0 (see Story 3.3's Dev Agent Record); `test_database_schema.py`'s existing `test_seed_skills_exist` passing is equivalent, stronger evidence
- [x] Task 2: Add precise per-skill and embedding-correctness test coverage (AC: 2, 4) — write failing tests first
  - [x] Subtask 2.1: New `backend/tests/test_seed_skill_data_quality.py` (live-DB) — red tests: exactly 5 skills seeded with the exact expected names (not just a count); each skill's `embedding` is a 384-dim vector (matches `core/embedding.py::EMBEDDING_DIM`); embeddings are non-zero/non-degenerate (not all-zero, which would indicate a stub/fallback path silently firing instead of the real model); the `name` `UniqueConstraint` is enforced at the DB level (inserting a duplicate name raises `IntegrityError`)
  - [x] Subtask 2.2: Confirmed green as expected — **8/8 passed** on first run, no misalignment found. `embed_text()`'s integration into `seed_skills()` produces real, correctly-shaped, non-degenerate 384-dim embeddings for all 5 skills.
- [x] Task 3: Confirm idempotency at the unit level, not just the full-`run_seeds()` level (AC: 3)
  - [x] Subtask 3.1: Added `test_seed_skills_is_idempotent_at_the_function_level`, copying Story 3.3's final (twice-review-fixed) pattern directly — delete-first-in-own-transaction, `IntegrityError`-guarded skip, `rowcount in (0, 5)` assertion. Verified passing both standalone (rowcount=0 path) and as part of the full file (rowcount=5 path).
- [x] Task 4: Full regression pass (AC: all)
  - [x] Subtask 4.1: Docker/Postgres was reachable throughout. Full suite grew significantly since this story's baseline count (137) due to parallel work landing on `main` (Stories 1.8, 2.2, 4.1, 4.2) — actual current baseline re-verified at session start, not assumed. **Found 2 pre-existing, unrelated failures** in `tests/test_skill_progress.py` (from parallel Story 4.x work, not touched by this story) — `test_skill_progress_table_has_unique_assignment_id`, `test_ac1_skill_progress_table_schema` — confirmed pre-existing via isolation run (7/7 pass standalone; same cross-module-loop live-DB engine-sharing bug already documented in `deferred-work.md`, now also hitting this newer file). Excluded from the zero-regressions comparison, consistent with the established pattern (Story 2.2 used `git stash` to confirm an analogous pre-existing failure; here isolation-run confirmation served the same purpose).
  - [x] Subtask 4.2: **156 passed, 19 deselected** excluding `test_content_repository`/`test_content_service` (Story 3.3's known `conftest.py` `drop_all()` bug) and `test_skill_progress` (pre-existing, confirmed above). Also ran the full suite *including* `test_skill_progress` to confirm exactly the same 2 pre-existing failures and no new ones: 163 passed, 2 failed (both pre-existing), 10 deselected. Zero regressions from this story's changes.

### Review Findings

- [x] [Review][Patch] The "non-degenerate embedding" check (`assert any(component != 0.0 for component in skill.embedding)`) is too weak to actually distinguish a real sentence-transformer embedding from a stub — a one-hot vector, a hash-based pseudo-embedding, or a constant-fill vector with a single non-zero component would all pass it. AC4's stated goal is "genuinely computed... not a stub," which this assertion doesn't actually prove. Caught by Blind Hunter. **Fixed**: added a cross-skill distinctness check — two different skills' embeddings must not be identical (or near-identical), which a real semantic model guarantees for genuinely different input text but any degenerate/stub/constant-fill path would fail.
- [x] [Review][Patch] No test proved `Skill.description` is genuinely nullable end-to-end, despite AC2 explicitly listing `description (optional text)` as part of what this story confirms — the existing 5 seeded skills all have a description, so the nullable path was never exercised. Caught by Blind Hunter. **Fixed**: added `test_skill_description_is_genuinely_nullable`, inserting and reading back a `Skill` with `description=None`.
- [x] [Review][Patch] `scalar_one()` calls in the parametrized embedding test had no guard — a missing skill would raise a raw `NoResultFound` instead of a clear, skill-identifying assertion message. Caught by Edge Case Hunter. **Fixed**: switched to `scalar_one_or_none()` with an explicit `assert ... is not None, f"{expected_name} not seeded"`.
- [x] [Review][Defer] `_EXPECTED_SKILL_NAMES` is a hand-maintained copy of `seeds.py::seed_skills()`'s internal `skill_definitions` list rather than derived from it — the same class of drift risk Story 3.3 fixed for `_DEMO_ACCOUNTS`/`_MOCK_ACCOUNTS`. Unlike that case, `skill_definitions` is a local variable inside `seed_skills()`, not an importable module-level constant, so closing this gap would require refactoring `seeds.py` — explicitly out of this story's scope ("do not edit `seeds.py` unless a real gap is found"). Logged in `deferred-work.md` as a suggestion for a future story that touches `seeds.py` anyway.
- [x] [Review][Dismiss] Several findings restated already-accepted, documented trade-offs shared with Stories 3.1/3.3 (`_seeded_session()`'s real commit via `run_seeds()`; the idempotency test's declaration-order dependency; the duplicate-name test using a literal embedding instead of `embed_text()`) — no new information, not re-litigated.
- [x] [Review][Dismiss] Blind Hunter's suspicion that the story's quantitative claims (test counts, the 2 pre-existing `test_skill_progress.py` failures) were unverified/"self-congratulatory" was directly refuted by the Acceptance Auditor independently re-running every cited command and reproducing identical results, including the exact two failing test names.

Full suite after fixes: 158/158 passing (156 + 2 new patch tests; excl. Story 3.3's `conftest.py` bug + the pre-existing `test_skill_progress.py` failures), stable.

## Dev Notes

- **This story is verification + precision-test-coverage work, not new implementation — same shape as Story 3.3.** `seed_skills()` already satisfies AC1–AC3 completely (built in Story 1.7, refactored in Story 2.2 to use the shared `embed_text()`). **Do not rewrite or restructure `seed_skills()`** unless Task 1's verification finds a real, specific gap against the epic AC text — if so, stop and document exactly what's missing before touching the function.
- **AC4 is this story's real new work**, directly analogous to Story 3.3's AC5. Story 2.2's code review already hardened `embed_text()` itself extensively (network-error handling, corrupted-cache detection, concurrency lock, startup shape-check, 8 dedicated tests) — that work does **not** need to be re-verified here. What's never been tested is the **integration point**: does `seed_skills()`'s specific call (`embed_text(f"{name}: {description}")`) actually produce a correctly-shaped, non-degenerate embedding for each of the 5 real skill definitions, end-to-end, when run through the real seed pipeline? A stub, a caching bug, or a silent fallback to a zero-vector would pass today's loose `test_seed_skills_exist` (which only counts rows) without being caught.
- **`EMBEDDING_DIM` (384) is already defined as a named constant in `core/embedding.py`** — import and use it in the new test file's dimension assertions rather than hardcoding the literal `384`, so a future model change that updates `EMBEDDING_DIM` doesn't leave a stale test assertion behind.
- **Story 3.3's idempotency test needed two rounds of review to get right — inherit the final, fixed version's shape directly, don't rediscover the same bugs.** Round 1 found: naively calling `seed_skills()` twice without first deleting existing rows tests nothing (both calls hit the no-op branch, since other tests in the same module already committed seed data via `run_seeds()`). Round 2 (re-review) found: the delete-first fix introduces a real `IntegrityError` risk against the shared dev DB (FK RESTRICT from `content_catalog`/`assignments`), needing a `try/except` skip guard; and the delete needs a `rowcount in (0, 5)` assertion to actually distinguish the insert-path and no-op-path scenarios it's meant to test. **Copy `test_seed_employee_identity_alignment.py::test_seed_employees_is_idempotent_at_the_function_level`'s final structure directly** — same delete-guard-rowcount-assert shape, applied to `Skill`/`skill_ids` instead of `Employee`/`employee_ids`. [Source: _bmad-output/implementation-artifacts/3-3-employee-master-data-and-seed.md#Review Findings, #Review Findings — Round 2]
- **No models.py, router.py, or migration changes expected** — same pattern as Stories 3.1/3.3. This story only adds test coverage; if `Task 1`'s verification somehow finds `seeds.py` itself needs a fix, treat that as a scope-widening discovery to flag explicitly, not something to quietly absorb.
- **Live-DB test pattern**: use the private-engine pattern established in `test_assignments_repository.py` (Story 3.1) and `test_seed_employee_identity_alignment.py` (Story 3.3) — `create_async_engine(settings.DATABASE_URL)` local to the test file, not the shared `app.core.db.engine` singleton, and not the dead `conftest.py` `db_session`/`test_engine` fixtures (which have a separate, serious, already-logged bug — `Base.metadata.drop_all()` on teardown wipes the whole shared DB; do not use these fixtures under any circumstances). `pytestmark = pytest.mark.asyncio(loop_scope="module")` required alongside the private engine.
- **`seed_skills()` loads the real `all-MiniLM-L6-v2` model on first call in a fresh process** (via `embed_text()` → `_get_model()`), which is slow (~seconds) and memory-heavy (~100MB) the first time. This is expected, not a bug — don't add a mock/stub for the embedding call in these tests, since the whole point of AC4 is verifying the *real* embedding path works, not a mocked one. Subsequent calls in the same test session reuse the cached singleton and are fast.
- **Environment reminder (recurring across Stories 1.6/1.7/3.1/3.3):** `backend/.venv` has repeatedly been found missing `pgvector`/`sentence-transformers`/`alembic`/`torch` despite being in `requirements.txt` — if test collection fails with `ModuleNotFoundError`, run `pip install -r requirements.txt` before assuming a real regression. Docker Desktop has also been observed going fully down mid-session (not just the container) in this sandbox — if live-DB tests fail with `ConnectionRefusedError`, check `docker version` before assuming a code bug; if the volume was recreated fresh, `alembic upgrade head` + re-seed are required before tests will pass.

### Project Structure Notes

- Files this story is expected to change: none in `backend/app/` (verification only) — unless Task 1 finds a genuine gap, in which case document it and treat as new discovered scope.
- New files expected: `backend/tests/test_seed_skill_data_quality.py`.
- No variance detected from AD-1 (single-owner modules) or AD-8 — this story doesn't add cross-module coupling; it only adds tests that call `core/seeds.py` and `core/embedding.py`'s existing public functions.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 3.2: Skill Master Data & Seed] (lines 1038–1058) — full AC text this story implements
- [Source: backend/app/core/seeds.py] — existing `seed_skills()`, already satisfies AC1–AC3, refactored in Story 2.2 to use `embed_text()`
- [Source: backend/app/core/embedding.py] — `embed_text()`, `EMBEDDING_DIM` constant, Story 2.2's hardened embedding utility
- [Source: backend/app/assignments/models.py] — `Skill` ORM model (verify, don't redefine); `content_catalog.skill_id`/`assignments.skill_id` FK-reference `skills.id` with no cascade — relevant to Task 3's delete-guard
- [Source: backend/tests/test_database_schema.py] — existing loose seed-count test (`test_seed_skills_exist`) this story's tests complement, not duplicate
- [Source: _bmad-output/implementation-artifacts/3-3-employee-master-data-and-seed.md] — the direct structural template for this story: same verify-only shape, same "AC5"-equivalent precision-test gap, same idempotency-test pattern (including both review rounds' fixes)
- [Source: _bmad-output/implementation-artifacts/deferred-work.md] — current exclusion list for live-DB test files if Docker/Postgres is unreachable; also documents the `conftest.py` `drop_all()` bug (do not use those fixtures)

## Dev Agent Record

### Agent Model Used

Claude Sonnet 5 (claude-sonnet-5), via Amelia/bmad-dev-story

### Debug Log References

- `pytest -q -k "not test_content_repository and not test_content_service and not test_skill_progress"` → `156 passed, 19 deselected`
- `pytest -q -k "not test_content_repository and not test_content_service"` (includes `test_skill_progress`) → `163 passed, 2 failed, 10 deselected` — both failures confirmed pre-existing (isolation run: `pytest tests/test_skill_progress.py` → `7 passed`)
- `pytest tests/test_seed_skill_data_quality.py::test_seed_skills_is_idempotent_at_the_function_level` (standalone) → `1 passed` — confirms the rowcount=0 code path works independent of test-file execution order

### Completion Notes List

- **AC1–AC3 confirmed already satisfied** by `core/seeds.py::seed_skills()` (Story 1.7, refactored in Story 2.2 to use `embed_text()`) — no changes made to `seeds.py`, `models.py`, or any migration, exactly as the story's own Dev Notes anticipated.
- **AC4 (the story's real deliverable) confirmed true**: each of the 5 seeded skills has a real, correctly-shaped (384-dim, matching `core/embedding.py::EMBEDDING_DIM`), non-degenerate embedding produced by the real `embed_text()` call — not a stub or zero-vector. New test file: `backend/tests/test_seed_skill_data_quality.py` (8 tests).
- **AC2's name-uniqueness constraint verified at the DB level**, not just assumed from the model definition — `test_skill_name_uniqueness_enforced_at_db_level` inserts a real duplicate-name row and confirms `IntegrityError`.
- **AC3's idempotency guarantee now has a function-level test**, copying Story 3.3's final (twice-review-fixed) pattern directly rather than rediscovering its two known pitfalls (vacuous no-op-only test; unguarded FK-violation risk against the shared dev DB). Verified working in both the standalone (rowcount=0) and full-file (rowcount=5) execution contexts.
- **Found 2 pre-existing, unrelated test failures** in `tests/test_skill_progress.py` (parallel Story 4.x work) — confirmed via isolation run, not caused by this story, excluded from the regression comparison and documented rather than silently ignored.
- Full suite: 156 passed (excl. Story 3.3's known `conftest.py` bug + the pre-existing `test_skill_progress.py` failures), 163 passed/2 pre-existing-failed when `test_skill_progress.py` is included — zero regressions from this story's own changes.
- **Code review (2026-07-10, 3 parallel layers) found no AC violations; 3 patches applied, 1 deferred.** Strengthened the "non-degenerate embedding" check — the original `any(component != 0.0 ...)` would still pass for a one-hot or constant-fill stub — with a new cross-skill distinctness test (`test_different_skills_have_distinct_embeddings`); added `test_skill_description_is_genuinely_nullable` to close a real AC2 coverage gap (the 5 real skills all have a description, so the nullable path was never exercised); hardened the parametrized embedding test's `scalar_one()` into a guarded `scalar_one_or_none()` with a clear failure message. Deferred: the test's `_EXPECTED_SKILL_NAMES` is hand-duplicated from `seeds.py`'s internal (non-importable) `skill_definitions` list — same drift-risk class Story 3.3 fixed, but closing it here would require refactoring `seeds.py`, out of scope. Blind Hunter's suspicion that the story's quantitative claims were unverified was directly refuted by the Acceptance Auditor independently re-running every cited command and reproducing identical results.

### File List

- `backend/tests/test_seed_skill_data_quality.py` (new; 3 tests added during code review)

## Change Log

- 2026-07-10: Implemented Story 3.2 — verified AC1–AC3 already satisfied by `core/seeds.py::seed_skills()` (no code changes needed); added `test_seed_skill_data_quality.py` (8 tests) proving AC4's precise embedding correctness (real 384-dim, non-degenerate vectors via `embed_text()`) plus AC2's DB-level name-uniqueness and AC3's function-level idempotency, the latter copying Story 3.3's twice-review-fixed pattern directly. Found and documented 2 pre-existing, unrelated `test_skill_progress.py` failures from parallel Story 4.x work (confirmed via isolation, excluded from regression comparison). Full suite: 156/156 passing (excl. Story 3.3's `conftest.py` bug and the pre-existing `test_skill_progress.py` failures), zero regressions. Status → review.
- 2026-07-10: Code review (Blind Hunter, Edge Case Hunter, Acceptance Auditor) found zero AC violations; 3 patches applied (embedding-distinctness test, `description`-nullable test, guarded assertion), 1 deferred (`_EXPECTED_SKILL_NAMES` hand-duplication, logged in `deferred-work.md`). Full suite: 158/158 passing (excl. Story 3.3's `conftest.py` bug and the pre-existing `test_skill_progress.py` failures), stable across 2 runs. Status → done.
