# Implementation Steps for Story 6-2: Skill Creation Endpoint (FR-20)

**Story Key:** 6-2-skill-creation-endpoint
**Epic:** 6 (Admin-Assisted Content Sourcing)
**Status:** ✅ DONE
**Completed Date:** 2026-09-09

---

## Overview

Story 6-2 adds the first real CRUD endpoint on top of the `skills/` module Story 6.1 scaffolded: `POST /api/admin/skills`. An HR Admin can create a new Skill by name (with an optional description); the service computes and stores its embedding, defaults `ever_assigned` to `false`, and rejects a case-insensitive duplicate name with a `409 Conflict` that carries the existing Skill's `id`/`name` (for the frontend's future "Use existing skill" affordance, Story 6.10). An EMPLOYEE session gets `403 Forbidden`.

This story started life as a **code review request for work that didn't exist yet** — the session was asked to review Story 6-2, but the story was still `backlog` with no story file and an empty `router.py` stub. Rather than stop there, the session:

1. Created the story file (`/bmad-create-story`)
2. Implemented it end-to-end
3. Ran a full adversarial code review pass, which found and fixed a real concurrency bug (a TOCTOU race in the duplicate-name check) and closed it at the database level with a new migration, not just papered over in the application layer

---

## Agents Invoked

### 1. **Blind Hunter (Code Review Agent)**

**Purpose:** Adversarial general review — bugs, logic errors, contradictions with the code's own claims, architectural violations.

**When Invoked:** Step 02 of `/bmad-code-review` skill workflow
**Model Capability:** Sonnet 5 (session model)
**Input:** Full uncommitted diff (8 tracked files + 2 new files, +235/−19) via a saved diff file, plus repo-root context for reading any file in full

**Key Findings Identified:**
- The case-insensitive duplicate check (`SELECT` then `INSERT`, non-atomic) has a real TOCTOU race — two concurrent requests for different-case names (`"Python"` vs `"PYTHON"`) can both pass the pre-check and both get inserted, since the DB's plain `UNIQUE(name)` constraint is case-sensitive only
- Even an exact-case race isn't handled — the resulting `IntegrityError` was never caught, surfacing as a raw 500 instead of the documented clean 409
- `db.commit()` was called explicitly in `create_skill_service`, contradicting `core/db.py::get_db`'s documented "services flush, not commit" convention — and contradicting the service's own docstring, which claimed to mirror `assignments/service.py::create_assignment_service` (which correctly uses flush-only)
- No `max_length` on `CreateSkillRequest.name` while the DB column is `String(255)` — an over-limit name would fail at insert time with an unhandled 500 instead of a clean 422
- `AppException`'s new `extra` field (added this story, to carry the 409's `existing_skill` payload) had no guard against a future caller choosing a key that collides with the reserved response envelope (`status`/`code`/`message`/`timestamp`)
- The router docstring's claim that `/api/admin/...` follows an existing "convention" doesn't hold up against `main.py` — `dashboard_router` (the other admin-gated router) is mounted at `/api/dashboard`, not `/api/admin/dashboard`; this is actually the first route ever mounted under that prefix
- Several lower-value observations (no audit logging, redundant double-auth-dependency, no direct regression test of the shared error handler) — dismissed as matching existing codebase precedent, not new problems

**Output:** 16 findings; after triage, contributed to 4 of the 5 applied patches (2 independently co-confirmed with Edge Case Hunter, 1 with the Acceptance Auditor) plus 2 deferred and most of the 7 dismissed items

---

### 2. **Edge Case Hunter (Code Review Agent)**

**Purpose:** Boundary conditions, ordering/registration hazards, coverage gaps.

**When Invoked:** Step 02 of `/bmad-code-review` skill workflow (parallel with Blind Hunter)
**Model Capability:** Sonnet 5 (session model)
**Input:** Same saved diff file + repo-root context

**Key Findings Identified:**
- Independently found the same TOCTOU race and uncaught-`IntegrityError` gaps as Blind Hunter
- `name` longer than 255 chars — same `max_length` gap Blind Hunter found
- Unicode NFC vs. NFD normalization / casefold gap — two visually-identical names in different Unicode forms could both be created, bypassing the "case-insensitive" guarantee
- NUL byte / control character in `name`/`description` would crash the insert with an unhandled DB error rather than a validation error
- `AppException.extra` key-collision risk — same finding as Blind Hunter, independently confirmed
- `embed_text()` raising mid-request (wrong-shape vector, model-load error) falls through to a generic 500 with no distinguishing error code

**Output:** 7 structured findings (JSON, with location/trigger/guard/consequence per item); 3 merged with the other layers, 2 deferred, 2 dismissed as consistent with existing codebase-wide precedent

---

### 3. **Acceptance Auditor (Code Review Agent)**

**Purpose:** Verify the diff against Story 6-2's literal Given/When/Then acceptance criteria and its own Scope Notes/Dev Notes claims.

**When Invoked:** Step 02 of `/bmad-code-review` skill workflow (parallel with the other two layers)
**Model Capability:** Sonnet 5 (session model)
**Input:** Story spec file (full) + saved diff file + repo-root context

**Key Validations Performed:**
- AC1 (create + 409 on duplicate + embedding + `ever_assigned: false` + full `SkillResponse`): ✅ satisfied for the non-racing case; ⚠️ flagged the same TOCTOU race the other two layers found, framed explicitly as an AC1 violation risk under concurrency
- AC2 (EMPLOYEE → 403): ✅ satisfied — `require_hr_admin` runs before the duplicate-name check, so role is enforced regardless of name collision
- Scope Note 4 (case-insensitive check, DB constraint case-sensitivity gap): ✅ correctly implemented at the single-request level
- Scope Note 5 (409 response shape resolution): ✅ the `AppException.extra` approach is "a legitimate, minimal resolution consistent with the Dev Notes' guidance"
- Scope Note 6 (service-layer `require_hr_admin` gate, not router `Depends`): ✅ confirmed, matches `assignments/service.py`'s pattern exactly
- Router mount prefix, `SkillResponse` module-ownership, no `PATCH`/`DELETE` added, no `models.py`/migration changes: all ✅ confirmed against the story's own Project Structure Notes
- Router-tags cosmetic deviation from `assignments/router.py`'s exact construction pattern: flagged as low-value, no functional impact

**Output:** 2 findings (1 real, co-confirmed as the story's central decision-needed item; 1 cosmetic, dismissed), plus an extensive confirmed-correct checklist covering every AC/Scope-Note clause

---

## Skills Invoked

### 1. **`/bmad-code-review` Skill — First Pass (Redirected)**

**Purpose:** The user's original request.

**When Invoked:** Session start, user request: "do the code review for story 6-2-skill-creation-endpoint"
**Outcome:** Step 01 (Gather Context) discovered the review target didn't exist to review — `6-2-skill-creation-endpoint` was `backlog` in `sprint-status.yaml`, no story file existed, and `skills/router.py` was an empty stub explicitly reserved for this story (per its own docstring). The working tree was clean — nothing to diff. Presented this to the user with three options (implement it first, review something else, cancel); user chose **implement it first**.

---

### 2. **`/bmad-create-story` Skill**

**Purpose:** Generate a comprehensive story file with full context before implementation.

**When Invoked:** Immediately after the redirect above
**Workflow Steps Executed:**
1. Pulled Story 6.2's full literal AC text from `epics.md`
2. Loaded Story 6.1's story file for previous-story intelligence — its Scope Notes, established patterns (`_build_embedding_text`, service-layer `require_hr_admin` gate), and the exact state it left `skills/router.py`/`schemas.py` in
3. Read the actual current code directly rather than trusting docs: `skills/{models,repository,service,schemas,router}.py`, `assignments/router.py` + `service.py` (for the `require_hr_admin` gate pattern precedent), `content/router.py` + `service.py` + `schemas.py` (for the embed-then-create pattern and `ContentResponse`'s "no raw embedding" convention), `core/errors.py` (for `AppException`'s shape, and confirming no `409` precedent existed anywhere yet), `core/db.py` (transaction convention), `core/embedding.py` (embedding dimension), and the architecture spine's AD-11/AD-6/Consistency Conventions sections
4. Generated the story file with 6 Scope Notes recording specific judgment calls (route prefix, separate `SkillResponse` schema, DB constraint case-sensitivity gap, no `409` precedent, gate pattern choice) and Dev Notes flagging the one open design question (409 response shape) for the dev agent to resolve

**Output File:** `_bmad-output/implementation-artifacts/6-2-skill-creation-endpoint.md`
**Sprint Status:** `6-2-skill-creation-endpoint`: `backlog` → `ready-for-dev`

---

### 3. **`/bmad-dev-story` Skill**

**Purpose:** Implement the story per its own tasks against the story file's guidance.

**When Invoked:** Immediately after story creation
**Workflow Steps Executed:**
1. Resolved Scope Note 5's flagged open question: extended `core/errors.py::AppException` with an optional `extra: dict | None` field, merged into `http_exception_handler`'s response body — every existing `AppException` call site unaffected (defaults to `{}`), the 409 still flows through the one centralized error contract
2. Implemented `skills/schemas.py` (`CreateSkillRequest` with a blank-name-rejecting validator, `SkillResponse`), `skills/repository.py` (`get_skill_by_name_ci`, `create_skill`), `skills/service.py` (`create_skill_service`, composing `embed_text(_build_embedding_text(...))` inline per Story 6.1's precedent), `skills/router.py` (the `POST` route)
3. Mounted `skills_router` in `main.py` at `/api/admin/skills`
4. Wrote 9 new tests (3 service-layer, 6 router-level via a real ASGI app + private engine, mirroring `test_content_router.py`'s established pattern)
5. Ran the full backend suite before and after, using a `git stash` comparison to independently confirm zero regressions against the real pre-existing baseline (376 passed → 385 passed, same 3 pre-existing unrelated failures)

**Output:** Story file updated with completed Tasks, Dev Agent Record, File List, Change Log; status set to `review`
**Sprint Status:** `6-2-skill-creation-endpoint`: `ready-for-dev` → `in-progress` → `review`

---

### 4. **`/bmad-code-review` Skill — Second Pass (The Actual Review)**

**Purpose:** Adversarial review of the finished implementation against the story's own spec, structured triage, and patch application.

**When Invoked:** User request: "do the code review for story 6-2-skill-creation-endpoint" (re-invoked now that there was something to review)
**Workflow Steps Executed:**

- **Step 01 (Gather Context):** Spec file resolved via Tier 1 (explicit story-key argument); `baseline_commit` found in the story's frontmatter, matching current `HEAD` exactly, so the diff source was the full working-tree diff against that baseline (8 modified + 2 new files, ~654 diff lines). Checkpoint presented and confirmed by the user before launching review agents.
- **Step 02 (Review):** Launched Blind Hunter, Edge Case Hunter, and Acceptance Auditor in parallel background subagents (`review_mode = "full"`, story file as spec), each pointed at a saved diff file plus repo-root context.
- **Step 03 (Triage):** Normalized 25 raw findings from the 3 layers, deduplicated the TOCTOU race (independently found by all 3 layers) and the `AppException.extra` collision gap (found by 2) into single merged findings, read the actual source and ran targeted verification at every finding's location before rating — including confirming live, via `docker exec ... psql`, that `dashboard_router` really is mounted at `/api/dashboard` (not `/api/admin/dashboard`) before accepting or rejecting the "docstring overclaims precedent" finding. Routed the result into 1 decision-needed, 5 patch, 2 defer, 7 dismiss.
- **Step 04 (Present and Act):** Findings written to the story file's new "Review Findings" subsection. The 1 decision-needed item — whether to close the case-insensitive race at the DB level now or defer it — was presented to the user with both options and their tradeoffs; **user chose to add the migration now**. User then chose "apply every patch" for the 5 patch findings.

**Decision Resolved:**
- Added `backend/alembic/versions/006_add_skills_name_ci_unique_index.py` — a functional unique index (`CREATE UNIQUE INDEX ix_skills_name_lower ON skills (lower(name))`), applied live against the running Docker Postgres after verifying no pre-existing case-variant duplicates existed. This closes the TOCTOU race at the database level rather than just narrowing its blast radius in the application layer.

**Patches Applied:**
1. `create_skill_service` now wraps the insert in `try/except IntegrityError`, rolls back, re-queries via `get_skill_by_name_ci`, and serves the same clean 409 (via a new shared `_conflict()` helper) instead of letting a race-triggered constraint violation surface as a raw 500
2. `CreateSkillRequest.name` gained `max_length=255`, matching the DB column
3. Removed the non-conforming explicit `db.commit()` from `create_skill_service` — `repository.create_skill` already flushes+refreshes, and `get_db` commits once the route handler completes, per the documented convention
4. `AppException.__init__` now raises `ValueError` if `extra`'s keys intersect the reserved envelope keys (`status`/`code`/`message`/`timestamp`)
5. Added test coverage for the exact-name concurrent-duplicate path and the 409 envelope's base fields — a genuine race-simulation test (via two independent sessions, mirroring how `get_db` actually gives each real request its own session/transaction), an exact-name-twice router test, a >255-char router test, and an envelope-field assertion on the existing case-different 409 test

**A design bug caught while writing the race test itself:** the first version of the race-simulation test shared one session across both "concurrent" create calls. That inadvertently caused `db.rollback()` (inside the new `except IntegrityError` handler) to roll back the *first* call's own still-uncommitted insert too — an artifact of sharing one transaction across what should be two independent requests, not a real production bug. Diagnosed via a standalone repro script isolating each variable (mock target, `require_hr_admin`, single- vs. two-session flow) until the root cause was found, then fixed by using two independent sessions from the shared engine, with the first committing before the second's race attempt — correctly mirroring how `get_db` gives every real HTTP request its own fresh session.

**Output:** Story status → `done`; full suite re-verified at 388 passed (17 new tests total from this story) / 2 skipped / same 3 pre-existing failures (one additional failure seen on a first pass, confirmed as this codebase's known cross-file test-order flakiness — not a regression — by re-running in isolation and as part of the full suite a second time)

**Documentation Generated:**
- Code review findings + resolutions written directly into the story file's Review Findings subsection
- 2 deferred items logged to `deferred-work.md` under a new dated heading
- Sprint status synced (`6-2-...`: `backlog` → `ready-for-dev` → `in-progress` → `review` → `done`)

---

## Files Created/Updated

### Backend — New Files

| File | Purpose |
|------|---------|
| `backend/alembic/versions/006_add_skills_name_ci_unique_index.py` | Code-review decision — functional unique index on `lower(skills.name)`, DB-level backstop for the case-insensitive duplicate race |
| `backend/tests/test_skills_router.py` | Router-level HTTP tests for `POST /api/admin/skills` (real ASGI app + private engine, mirrors `test_content_router.py`) |

### Backend — Modified Files

| File | Purpose |
|------|---------|
| `backend/app/skills/schemas.py` | `CreateSkillRequest` (blank-name validator, `max_length=255` from code review), `SkillResponse` |
| `backend/app/skills/repository.py` | `get_skill_by_name_ci`, `create_skill` |
| `backend/app/skills/service.py` | `create_skill_service`; code-review patches: `IntegrityError` → clean 409 via new `_conflict()` helper, removed the non-conforming explicit `db.commit()` |
| `backend/app/skills/router.py` | `POST` route, delegating entirely to `create_skill_service` |
| `backend/app/main.py` | `skills_router` mounted at `/api/admin/skills` |
| `backend/app/core/errors.py` | `AppException.extra` field + `http_exception_handler` merge (to carry the 409's `existing_skill` payload); code-review patch added a reserved-key collision guard |
| `backend/tests/test_skills_service.py` | 3 new tests for `create_skill_service`; code-review patch added a 4th (exact-name race simulation via two independent sessions) |

### Documentation & Configuration Files

| File | Purpose |
|------|---------|
| `_bmad-output/implementation-artifacts/6-2-skill-creation-endpoint.md` | Story file — ACs, Scope Notes, Dev Notes, Review Findings, Dev Agent Record |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | `6-2-...`: `backlog` → `ready-for-dev` → `in-progress` → `review` → `done` |
| `_bmad-output/implementation-artifacts/deferred-work.md` | 2 items added under a new "Deferred from: code review of 6-2-..." heading |
| `documentation/ImplementationStepsForStory6-2.md` | This file |

### Not Changed (by design)

- `backend/app/skills/models.py` — schema already correct from Story 6.1 (`ever_assigned`, the plain unique constraint); no ORM changes needed
- No `PATCH`/`DELETE` route added — that's Story 6.3, explicitly out of this story's scope even though it will live in the same `router.py`/`service.py` files

---

## Implementation Workflow Summary

### Phase 0: Redirect
**Skill:** `/bmad-code-review` (first invocation)
- Discovered there was nothing to review — story still `backlog`, no story file, `router.py` an empty stub
- User chose to implement the story first

### Phase 1: Story Creation
**Skill:** `/bmad-create-story`
- Read Story 6.1's completed story file and the live codebase directly to establish every pattern to mirror
- Generated the story file with 6 Scope Notes and one explicitly flagged open design question (409 response shape)

### Phase 2: Implementation
**Skill:** `/bmad-dev-story`
- Resolved the flagged design question (`AppException.extra`)
- Implemented schemas, repository, service, router; mounted the route
- 9 new tests; full regression pass with `git stash`-verified pre-existing-failure baseline
- Output: 385 passed, 2 skipped, 3 pre-existing failures; story marked `review`

### Phase 3: Code Review
**Skill:** `/bmad-code-review` (second invocation)
- 3 parallel adversarial layers (Blind Hunter, Edge Case Hunter, Acceptance Auditor), single pass
- **Findings:** 25 raw → 15 after dedup → 1 decision-needed, 5 patch, 2 defer, 7 dismiss
- **Top issue:** a real TOCTOU race in the case-insensitive duplicate check, independently found by all 3 layers, closed at the DB level via a new migration (user's explicit choice) plus an application-layer `IntegrityError`-to-409 conversion
- **Action:** Decision resolved (add the migration); all 5 patches applied
- A bug in the review's own race-simulation test (shared-session rollback artifact) was caught and fixed before the fix was accepted as verified
- Output: 388 passed (17 new total), 2 skipped, same 3 pre-existing failures; story marked `done`

---

## Test Coverage

### New/Extended Test Files (17 tests total)
- `test_skills_service.py` — 4 new tests: successful create (embedding computed, `ever_assigned` false), case-insensitive duplicate (409 with original id/name, no second row), exact-name concurrent-race simulation (409 via the new `IntegrityError` catch, not a 500), EMPLOYEE role → 403
- `test_skills_router.py` — 9 tests (new file): HR_ADMIN create → 201 with correct shape and no `embedding` field; case-different duplicate → 409 with `existing_skill` *and* the full standard envelope; exact-name-twice duplicate → 409; EMPLOYEE → 403; unauthenticated → 401; blank name → 422; missing name → 422; name over 255 chars → 422

### Regression Verification
- Full suite run before and after both phases (create+implement, then code review), plus a `git stash` comparison against the pre-existing baseline (376 passed) to independently confirm zero regressions — not assumed from a single run
- A transient extra failure seen on one full-suite pass was diagnosed as this codebase's known cross-file test-order flakiness (already tracked in `deferred-work.md` since Story 1.7/the Epic 4 retro) by re-running the specific test in isolation (passed) and the full suite again (matched baseline exactly)

---

## Architecture Decisions Implemented

| Decision | Implementation | Files Affected |
|----------|---|---|
| **AD-6: Server-side session/role/identity gate** | `create_skill_service` calls `require_hr_admin(current_user)` as its first line — service-layer gate, matching `assignments/service.py`'s established pattern | `skills/service.py` |
| **AD-11: `skills/` sole ownership + embedding-on-write** | Embedding computed inline via `embed_text(_build_embedding_text(...))` at the create write site, never in the router, never duplicated elsewhere — matches AD-11 point 4 exactly | `skills/service.py` |
| **Consistency Conventions (route prefix, error contract)** | First route ever mounted under `/api/admin/...` (as the architecture spine's own conventions table prescribes for admin-only routes); 409 response still flows through the single centralized `{status, code, message, timestamp}` error envelope, extended (not replaced) to carry the extra `existing_skill` payload | `main.py`, `core/errors.py` |

---

## Key Technical Achievements

✅ **Redirected a review request into a complete implementation-then-review cycle** — recognized the review target didn't exist yet rather than fabricating a review of nothing, and drove the full story lifecycle instead
✅ **First `409 Conflict` precedent in this codebase** — extended the shared `AppException`/`http_exception_handler` contract minimally (an optional `extra` field) rather than bypassing it, keeping every error response on one centralized path
✅ **Real concurrency bug found by 3 independent review layers and fixed at the right layer** — closed at the database level (a new migration) rather than only patched over in application code, per the user's explicit choice between the two options
✅ **A test bug caught before it could mask a real fix** — the first race-simulation test's shared-session design would have silently validated the wrong thing; diagnosed via systematic isolation (a disposable standalone repro script, not guesswork) and corrected to genuinely simulate two independent concurrent requests
✅ **Zero regressions, independently verified twice** — `git stash`-based comparison at the implementation phase, then a second full-suite re-run at the review phase to rule out flakiness in a transient extra failure

---

## Deferred Items (Pre-existing Class of Gap, Not Story 6-2 Scope)

1. **Custom blank-name validator message is unreachable** — `core/errors.py::validation_exception_handler` discards all Pydantic per-field detail for every 422 across the entire app, for every schema; fixing it means redesigning a cross-cutting shared handler, well beyond this story's scope
2. **Case-insensitive duplicate check doesn't normalize Unicode form (NFC vs. NFD)** — low real-world likelihood for this admin-only, largely-English-language catalog; this codebase has no Unicode-normalization handling anywhere else either

---

## Conclusion

Story 6-2 is **✅ DONE** after one full adversarial code review pass, on top of a from-scratch story-creation-and-implementation cycle triggered by a review request for work that didn't exist yet:

- Both acceptance criteria satisfied, including under concurrency (the one real gap found)
- 1 real concurrency bug found by all 3 review layers, resolved via an explicit user decision (DB-level migration) rather than a unilateral judgment call
- 5 patches applied, including a genuine test-design bug caught and fixed mid-review before the fix it was meant to validate could be trusted
- Zero regressions — confirmed twice, via `git stash` comparison and a second full-suite re-run
- 2 pre-existing, out-of-scope issues explicitly deferred rather than silently absorbed or ignored

**Ready for:** Story 6.3 (Skill Edit & Delete — Permanent Lock Enforcement, FR-21/22) to build on the same `router.py`/`service.py` files.
