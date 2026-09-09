# Implementation Steps for Story 6-1: `skills/` Module Foundation — Data Model, Migration & Embeddings

**Story Key:** 6-1-skills-module-foundation-data-model-migration-embeddings
**Epic:** 6 (Admin-Assisted Content Sourcing)
**Status:** ✅ DONE
**Completed Date:** 2026-09-09

---

## Overview

Story 6-1 gives the `skills` table a real owning module for the first time. Before this story, `Skill`'s ORM model physically lived inside `assignments/models.py` (no owning module existed), and `content/repository.py` carried two narrow, documented direct-access exceptions into it (`list_all_skills()` from Story 2.3, `get_skill_embedding()` from Story 2.4). This story:

- **Creates** the `skills/` module (`router.py`, `service.py`, `repository.py`, `models.py`, `schemas.py`), the sole owner of the `skills` table per architecture decision AD-11
- **Relocates** the `Skill` ORM model out of `assignments/models.py` into `skills/models.py` — the first table this codebase has ever physically moved to its owning module, rather than following `ContentCatalog`'s established "stays co-located, only logically owned elsewhere" convention
- **Retires** both of `content/`'s direct-`Skill`-access exceptions in favor of `skills.service` calls
- **Adds** the embedding-write helper (`_build_embedding_text`) Story 6.2 (create) and 6.3 (rename) will share
- **Verifies, but does not redo**, migrations 004 (`skills.ever_assigned` column + backfill) and 005 (`admin_api_keys` table), which already existed on this branch from an earlier ad hoc commit

A full adversarial code review pass followed, which found and fixed a real cross-module import-ordering bug and a silently-still-working old import path that undermined the relocation's own point.

---

## Agents Invoked

### 1. **Blind Hunter (Code Review Agent)**

**Purpose:** Adversarial general review — bugs, logic errors, contradictions with the story's own claims, architectural violations.

**When Invoked:** Step 02 of `/bmad-code-review` skill workflow
**Model Capability:** Sonnet 5 (session model)
**Input:** Full uncommitted diff (26 files, +589/−89) via a saved diff file, plus repo-root context for reading any file in full

**Key Findings Identified:**
- `from app.assignments.models import Skill` still worked after the "relocation" — `assignments/models.py`'s `from app.skills.models import Skill` re-bound the name in its own namespace, silently keeping the old import path alive and undermining the AD-1 enforcement boundary the story exists to establish
- Cross-module import-ordering fragility: `skills/models.py`'s `content_items`/`assignments` relationships only resolve if `app.assignments.models` happens to already be imported somewhere in the process — no guarantee existed in `skills/models.py` itself
- `skills/service.py::_build_embedding_text` claimed to mirror `content/service.py`'s helper "exactly," but the two had already diverged (content's version logs on truncation, skills' didn't)
- No automated guard verified the actual architectural invariant this story establishes — that `content/` never re-acquires direct `Skill`/`skills`-table access
- Story file's Architecture Compliance section asserted "only `skills/repository.py` queries it directly" before immediately conceding a live exception
- Story file's Task 6 title ("~10 broken import sites") overstated what happened — none of those sites would have raised `ImportError` if left untouched
- Several lower-value observations (engine disposal, shared dev-DB state, unverifiable prose claims) — all dismissed as matching this codebase's own established, already-documented conventions, not new problems

**Output:** 12 findings; after triage, contributed to 6 of the 9 applied patches (2 independently co-confirmed with Edge Case Hunter, 2 with the Acceptance Auditor) plus 2 deferred and 3 dismissed items

---

### 2. **Edge Case Hunter (Code Review Agent)**

**Purpose:** Boundary conditions, ordering/registration hazards, coverage gaps in new tests.

**When Invoked:** Step 02 of `/bmad-code-review` skill workflow (parallel with Blind Hunter)
**Model Capability:** Sonnet 5 (session model)
**Input:** Same saved diff file + repo-root context

**Key Findings Identified:**
- Independently found the same import-ordering fragility as Blind Hunter: `skills/models.py`'s relationship strings (`"ContentCatalog"`, `"Assignment"`) would raise `InvalidRequestError` at first mapper configuration in a hypothetical isolated import (a standalone script, a narrower test, a router mounted before other routers) — every current entry point avoids it only by accident, via a transitive `core.seeds` → `assignments.models` import chain
- `test_skills_ever_assigned_column_is_a_non_nullable_boolean_defaulting_false`'s name/docstring promised "default false" coverage but the test body only asserted `nullable`/`type`, never `.default`/`.server_default`

**Output:** 2 findings, both confirmed real and merged with matching findings from the other two layers

---

### 3. **Acceptance Auditor (Code Review Agent)**

**Purpose:** Verify the diff against Story 6-1's literal Given/When/Then acceptance criteria and the story file's own Scope Notes/Dev Notes claims.

**When Invoked:** Step 02 of `/bmad-code-review` skill workflow (parallel with the other two layers)
**Model Capability:** Sonnet 5 (session model)
**Input:** Story spec file (full) + saved diff file + repo-root context

**Key Validations Performed:**
- AC1 (Skill relocation + `ever_assigned` column/migration): ✅ satisfied, migration 004 verified unchanged and correct
- AC2 (`content/repository.py::list_all_skills()` replaced, `content/` no longer imports `Skill`): ✅ satisfied — also confirmed the judgment call to relocate `get_skill_embedding()` too (not literally named in the AC) is consistent with the AC's own blanket end-state clause
- AC3 (embedding-write helper calls `embed_text()` and stores the vector): ⚠️ flagged — the diff ships only the text-truncation half; the actual `embed_text()` call/write happens in Story 6.2/6.3, out of this story's own scope, which the AC text doesn't cleanly account for
- Out-of-Scope boundary (no CRUD endpoints): ✅ respected — `skills/router.py`/`schemas.py` are genuine stubs, `main.py` untouched
- Scope Note 4's own stated rationale for leaving `assignments/repository.py::list_skills()` unmigrated: found to be imprecise (misattributed which future story would own that fix)
- `_build_embedding_text`'s "mirrors content/'s helper exactly" claim: not byte-identical (same divergence Blind Hunter found)
- Migration/backfill "not redone here" claim: ✅ verified accurate against the real migration file

**Output:** 1 AC-level ambiguity (routed to decision-needed), 4 lower-severity findings (2 merged with the other layers, 2 unique)

---

## Skills Invoked

### 1. **`/bmad-agent-dev` Skill**

**Purpose:** Activate the Amelia (Senior Software Engineer) persona for story execution.

**When Invoked:** Session start, user request: "start development for the story 6-1-skills-module-foundation-data-model-migration-embeddings refer the ux design if required"
**Outcome:** Persona activated; dispatched directly to story creation + implementation since the user's intent was unambiguous

---

### 2. **`/bmad-create-story` Skill**

**Purpose:** Generate a comprehensive story file with full context before implementation.

**When Invoked:** Immediately after Amelia activation — no story file existed yet for `6-1-skills-module-foundation-data-model-migration-embeddings` (confirmed `backlog` in `sprint-status.yaml`)
**Workflow Steps Executed:**
1. Discovered the target story from the user's explicit story key
2. Loaded epics.md's full Story 6.1 AC text, the architecture spine's AD-11 (plus AD-1/AD-7/AD-8/AD-10 for surrounding context), and the UX spec (`04.1-skills-content-sourcing.md`) to confirm no additional Skill fields were UX-required
3. Investigated the existing codebase state directly (not just docs): found migrations 004/005 already applied live from an earlier ad hoc commit, read `content/`'s repository/service/schemas files and `core/embedding.py`/`core/seeds.py` to establish the exact conventions to mirror
4. Generated the story file with literal AC text, Scope Notes documenting judgment calls made during authoring, and forward-looking Dev Notes

**Output File:** `_bmad-output/implementation-artifacts/6-1-skills-module-foundation-data-model-migration-embeddings.md`

---

### 3. Direct TDD Implementation (Amelia, no separate `/bmad-dev-story` invocation)

**Purpose:** Implement the story per its own tasks, test-first where practical.

**Workflow Steps Executed:**
1. Created the `skills/` module scaffold (`__init__.py`, `models.py`, `repository.py`, `service.py`, `schemas.py`/`router.py` stubs)
2. Relocated `Skill` out of `assignments/models.py`; added the back-import for FK relationship registration
3. Retired `content/repository.py`'s `list_all_skills()`/`get_skill_embedding()` exceptions, moved to `skills/`, rewired `content/service.py`'s call sites
4. Added the embedding-write helper (`_build_embedding_text`)
5. Fixed every import site broken by the relocation across app code and 10 test files
6. Wrote new tests (`test_skills_repository.py`, `test_skills_service.py`), moving/adapting the two tests that used to live in `test_content_ingestion.py`/`test_content_matching.py`
7. Found and fixed one incidental pre-existing gap (`test_all_tables_defined` pinned at 7 tables, silently broken since migration 005 landed)
8. Ran the full backend suite before and after, using `git stash`/`git stash pop` to independently confirm 3 failing tests were pre-existing dev-DB state issues, not regressions

**Output:** Story file updated with Dev Notes, Project Structure Notes, Architecture Compliance, and a Dev Agent Record; status set to `review`

---

### 4. **`/bmad-code-review` Skill**

**Purpose:** Adversarial review of the diff against the story's own spec, structured triage, and patch application.

**When Invoked:** User request: "do the code review for story 6-1-skills-module-foundation-data-model-migration-embedding"
**Workflow Steps Executed:**

- **Step 01 (Gather Context):** Explicit story-key argument resolved to Tier 1; diff source determined to be uncommitted changes (`git diff HEAD`), since the story's `baseline_commit` matched current `HEAD` exactly. Checkpoint presented and confirmed by the user before launching review agents.
- **Step 02 (Review):** Launched Blind Hunter, Edge Case Hunter, and Acceptance Auditor in parallel background subagents (`review_mode = "full"`, story file as spec), each pointed at a saved diff file plus repo-root context.
- **Step 03 (Triage):** Normalized 19 raw findings from the 3 layers, deduplicated 4 pairs of independently-converged findings down to 4 merged findings, read the actual source at every finding's location before rating (not from diff hunks alone), and routed the result into 1 decision-needed, 9 patch, 2 defer, 3 dismiss.
- **Step 04 (Present and Act):** Findings written to the story file's new "Review Findings" subsection; summary presented to the user; the 1 decision-needed item (AC3's embedding-write-helper scope) resolved by the user (leave as-is, matches `content/`'s inline-composition precedent); user chose "apply every patch" for the 9 patch findings.

**Patches Applied:**
1. Closed the old `from app.assignments.models import Skill` import path — switched `assignments/models.py` to a whole-module `import app.skills.models` (verified via grep that zero call sites depended on the old path first)
2. Closed the cross-module import-ordering fragility — added a mirroring whole-module `import app.assignments.models` to `skills/models.py`; verified safe across all 3 possible import orders (skills-first, assignments-first, skills-only) by running each in a fresh subprocess
3. Added truncation logging to `_build_embedding_text` to genuinely match `content/`'s pattern
4. Added a new static regression-guard test (`test_content_ad1_skills_regression_guard.py`, mirroring the existing `test_content_ad7_regression_guard.py` pattern) verifying `content/` never re-acquires direct `Skill` access
5. Strengthened the under-asserting `ever_assigned` schema test to also check `.default`/`.server_default`, not just `nullable`/`type`
6. Added AD-1 exception language to `assignments/repository.py::list_skills()`'s own docstring, not just the import comment above it
7. Reworded Scope Note 4's misattributed rationale for leaving `list_skills()` unmigrated
8. Reworded the Architecture Compliance section to state the known `list_skills()` exception upfront rather than assert-then-contradict
9. Reworded Task 6's "~10 broken import sites" framing (now literally accurate, since patch #1 closed the gap that made it previously false)

**Output:** Story status → `done`; full suite re-verified at 386 passed (2 new tests) / 2 skipped / same 3 pre-existing unrelated failures; `app.main` confirmed importing cleanly

**Documentation Generated:**
- Code review findings + resolutions written directly into the story file's Review Findings subsection
- 2 deferred items logged to `deferred-work.md` under a new dated heading
- Sprint status synced (`epic-6`: `backlog` → `in-progress`; `6-1-...`: `backlog` → `review` → `done`)
- `project-context.md` updated twice (initial implementation, then code-review outcome)

---

## Files Created/Updated

### Backend — New Files

| File | Purpose |
|------|---------|
| `backend/app/skills/__init__.py` | Package marker |
| `backend/app/skills/models.py` | `Skill` ORM (relocated from `assignments/models.py`), plus the mirroring `import app.assignments.models` registration fix from code review |
| `backend/app/skills/repository.py` | `list_all_skills`, `get_skill_embedding` (relocated from `content/repository.py`) |
| `backend/app/skills/service.py` | Service API wrappers + `_build_embedding_text` embedding-write helper (with truncation logging added in code review) |
| `backend/app/skills/schemas.py` | Documented stub — Story 6.2/6.3 add real schemas |
| `backend/app/skills/router.py` | Documented stub, unmounted — Story 6.2 adds the first route + `main.py` wiring |
| `backend/tests/test_skills_repository.py` | `list_all_skills`, `get_skill_embedding`, `ever_assigned` default-false coverage |
| `backend/tests/test_skills_service.py` | `_build_embedding_text` truncation/None-description tests, Service API smoke tests |
| `backend/tests/test_content_ad1_skills_regression_guard.py` | Code review addition — static guard against `content/` re-acquiring direct `Skill` access |

### Backend — Modified Files

| File | Purpose |
|------|---------|
| `backend/app/assignments/models.py` | `Skill` class removed; registers `app.skills.models` via whole-module import (code review: closed the old-import-path loophole); `AdminApiKey` docstring corrected |
| `backend/app/assignments/repository.py` | `Skill` import repointed to `app.skills.models`; `list_skills()` flagged as a documented, out-of-scope exception (code review: exception language added to the function's own docstring) |
| `backend/app/content/repository.py` | `list_all_skills`/`get_skill_embedding` removed, no more `Skill` import |
| `backend/app/content/service.py` | Calls `skills_service.list_all_skills`/`get_skill_embedding` instead of `repository.*` |
| `backend/app/core/seeds.py` | `Skill` import repointed to `app.skills.models` |
| `backend/tests/conftest.py`, `test_antiflow_validation.py`, `test_content_discovery.py`, `test_content_ingestion.py`, `test_content_matching.py`, `test_content_repository.py`, `test_content_service.py`, `test_position_retrieval.py`, `test_seed_skill_data_quality.py` | `Skill` import repointed to `app.skills.models` |
| `backend/tests/test_schema_definition.py` | `Skill` import repointed; `ever_assigned` column coverage added (code review: strengthened to assert `default`/`server_default`); `test_all_tables_defined` fixed to expect 8 tables (pre-existing `admin_api_keys` gap) |

### Documentation & Configuration Files

| File | Purpose |
|------|---------|
| `_bmad-output/implementation-artifacts/6-1-skills-module-foundation-data-model-migration-embeddings.md` | Story file — ACs, Scope Notes, Dev Notes, Review Findings, Dev Agent Record |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | `epic-6`: `backlog` → `in-progress`; `6-1-...`: `backlog` → `review` → `done` |
| `_bmad-output/implementation-artifacts/deferred-work.md` | 2 items added under a new "Deferred from: code review of 6-1-..." heading |
| `_bmad-output/project-context.md` | 2 entries appended — implementation summary, then code-review outcome |
| `documentation/ImplementationStepsForStory6-1.md` | This file |

### Not Changed (by design)

- `backend/alembic/versions/004_add_skills_ever_assigned.py`, `005_add_admin_api_keys.py` — pre-existing, verified live against the running Docker Postgres, not redone
- `backend/app/main.py` — `skills/router.py` not mounted; no endpoints exist yet

---

## Implementation Workflow Summary

### Phase 1: Story Creation
**Skill:** `/bmad-create-story`
- Investigated the live codebase and DB state directly rather than trusting prior commit messages
- Generated the story file with literal epic AC text, judgment-call Scope Notes, and forward-looking Dev Notes

### Phase 2: Implementation
Direct TDD implementation (Amelia)
- Module scaffold, `Skill` relocation, `content/` exception retirement, embedding-write helper
- 10 import sites fixed across app + test code
- New/moved tests; full regression pass with `git stash`-verified pre-existing-failure baseline
- Output: 384 passed, 2 skipped, 3 pre-existing failures; story marked `review`

### Phase 3: Code Review
**Skill:** `/bmad-code-review`
- 3 parallel adversarial layers (Blind Hunter, Edge Case Hunter, Acceptance Auditor), single pass
- **Findings:** 19 raw → 15 after dedup → 1 decision-needed, 9 patch, 2 defer, 3 dismiss
- **Top issues:** a real cross-module import-ordering bug (independently found by 2 layers) and a silently-still-working old import path that undermined the story's own central claim
- **Action:** All 9 patches applied; decision resolved by the user
- Output: 386 passed (2 new), 2 skipped, same 3 pre-existing failures; story marked `done`

---

## Test Coverage

### New Test Files (10 tests)
- `test_skills_repository.py` — 5 tests: `list_all_skills` (seeded + freshly-created), `get_skill_embedding` (nonexistent + real vector round-trip), `ever_assigned` defaults to `False`
- `test_skills_service.py` — 5 tests: `_build_embedding_text` truncation/`None`-description, Service API wrappers for `list_all_skills`/`get_skill_embedding`

### Code-Review-Added Test File (2 tests)
- `test_content_ad1_skills_regression_guard.py` — static guard: `content/` never imports/queries `Skill` directly; `content/service.py` reaches its replacements via `skills_service.*`

### Strengthened Existing Test
- `test_schema_definition.py::test_skills_ever_assigned_column_is_a_non_nullable_boolean_defaulting_false` — now asserts `.default`/`.server_default`, not just `nullable`/`type`

### Regression Verification
- Full suite run before and after all patches, plus a `git stash`/`git stash pop` comparison against the pre-Story-6.1 baseline (commit `4e99d275`) to independently confirm the 3 failing tests are pre-existing (identical `ForeignKeyViolationError`s against the same real dev-DB row IDs), not introduced by this story

---

## Architecture Decisions Implemented

| Decision | Implementation | Files Affected |
|----------|---|---|
| **AD-1: Single-Owner Data Modules** | `skills` now has a real owning module; `content/`'s two former direct-access exceptions retired; one pre-existing exception (`assignments/repository.py::list_skills()`) flagged and left, out of this story's scope | `skills/models.py`, `content/repository.py`, `content/service.py`, `assignments/repository.py` |
| **AD-8: Module Dependency Direction** | `content/` now depends on `skills/`'s Service API exclusively, matching the spine's diagram (`Content -. depends on .-> Skills`) | `content/service.py` |
| **AD-11: `skills/` Sole Ownership + Local Lock Flag** | Module created, `Skill` relocated, `ever_assigned` present (migration pre-existing, verified live), embedding-write helper in place for Story 6.2/6.3 | `skills/models.py`, `skills/service.py` |

---

## Key Technical Achievements

✅ **First physical table relocation in this codebase** — `Skill` moved out of `assignments/models.py`, not just logically reassigned like `ContentCatalog`
✅ **Two `content/` exceptions retired, not just one** — the AC named only `list_all_skills()`, but its own end-state clause was read as covering `get_skill_embedding()` too
✅ **Real cross-module import-ordering bug found and fixed** — independently converged on by 2 review layers, verified fixed across all 3 possible import orders via direct subprocess testing
✅ **Real AD-1 enforcement gap closed** — the old `from app.assignments.models import Skill` path was silently still working; closed via a whole-module import, verified via a full-codebase grep first
✅ **New regression-guard test matching an existing codebase precedent** — `test_content_ad1_skills_regression_guard.py` mirrors the established AD-7 guard pattern
✅ **Zero regressions, independently verified** — `git stash`-based before/after comparison against the real pre-Story-6.1 baseline, not just a single test run

---

## Deferred Items (Pre-existing, Not Story 6-1 Scope)

1. **`test_all_tables_defined`'s hardcoded exact-table-count set** — brittle pattern likely to collide with Story 6.5 (`org_api_credentials`)/6.8 (`content_catalog` changes) editing the same set; fixing the anti-pattern itself is out of this story's scope
2. **Shared, stateful dev Postgres with accumulated cross-session row state** — the 3 pre-existing test failures are a symptom of the same root cause already tracked since Story 1.7/the Epic 4 retro (the `conftest.py` `drop_all()` landmine, cross-file asyncpg pool-corruption pattern), not a new instance

---

## Conclusion

Story 6-1 is **✅ DONE** after one full adversarial code review pass:
- All 3 acceptance criteria satisfied (1 decision-needed item resolved as consistent with existing precedent, not a gap)
- 2 real bugs found and fixed during review (import-ordering fragility, silently-reopened old import path) — both independently verified, not just patched on faith
- Zero regressions — confirmed via `git stash` baseline comparison, not assumed
- New architectural regression-guard test added, matching this codebase's own established convention
- 2 pre-existing, out-of-scope issues explicitly deferred rather than silently absorbed or silently ignored

**Ready for:** Story 6.2 (Skill Creation Endpoint, FR-20) to build on this foundation.
