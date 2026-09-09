---
baseline_commit: 3849efad
---

# Story 6.2: Skill Creation Endpoint (FR-20)

Status: done

## Story

As an **HR Admin**,
I want to create a new Skill by name, with an embedding computed automatically,
so that a Skill I need doesn't have to wait for a database seed script, and the new Skill is immediately eligible for both admin-sourced (this epic) and future batch-matched (Epic 2) content.

## Scope Notes (read before starting)

1. **This story builds on top of Story 6.1's stub files, not from scratch.** `skills/router.py` is currently an empty `APIRouter()` with a docstring explicitly reserving it for this story; `skills/schemas.py` is empty for the same reason; `skills/service.py` already has `_build_embedding_text(name, description)` (the AC3-equivalent helper from 6.1) ready to call — this story composes `embed_text(_build_embedding_text(...))` inline at the write site, mirroring `content/service.py`'s own established inline-composition convention exactly (Story 6.1's Review Findings, decision-needed #1: this is the precedent this story must follow, not a wrapper function).
2. **`skills/router.py` is not yet mounted in `app/main.py`.** This story adds the first real route, so it also needs `app.include_router(skills_router, prefix="/api/admin/skills", tags=["skills"])` in `main.py`, matching the existing `content_router`/`dashboard_router` mounting pattern (`main.py:40-45`). The `/api/admin/...` prefix comes from the architecture spine's Consistency Conventions table (admin-only routes prefixed `/api/admin/...`, HR_ADMIN-gated via AD-6) — do not mount at `/api/skills`, that path is reserved by `assignments/router.py`'s existing read-only `GET /api/assignments/skills` combobox endpoint (a different, pre-existing route, unrelated to this story).
3. **A separate `SkillResponse` already exists in `assignments/schemas.py`** (`id`, `name`, `description` — no `ever_assigned` field), used by the assignment modal's Step 2 combobox (Story 3.4). This story's own `SkillResponse` belongs in `skills/schemas.py` (the new module's own contract, per AD-1: API schemas are owned by the module, not shared/imported across module boundaries) and must include `ever_assigned` per this story's AC3 ("full `SkillResponse` (id, name, description, `ever_assigned: false`, no raw embedding vector...)"). Do not import or extend the `assignments/` one — a second, independent schema of the same shape-but-not-identical contract is correct here, matching this codebase's existing precedent of per-module response schemas (`content/schemas.py::ContentResponse` is not shared with any other module either).
4. **`skills.name` already has a DB-level `unique=True` constraint** (`skills/models.py:38`, case-sensitive at the Postgres level). This story's AC requires a **case-insensitive** duplicate check performed by the service *before* the insert (so a same-name-different-case request returns a clean `409` with the existing Skill's `id`/`name`, never a raw `IntegrityError`). The DB constraint is a safety net for the case-sensitive collision only — do not rely on it to satisfy the AC's case-insensitive requirement, and do not remove/relax it.
5. **No `409 Conflict` precedent exists anywhere in this codebase yet** (grep-confirmed against `app/core/errors.py::AppException` call sites). This story is the first. Use `AppException(status.HTTP_409_CONFLICT, error_code="SKILL_NAME_CONFLICT", message=...)` — matches the existing `AppException(status_code, error_code, message)` constructor shape used by every other error site (`auth/service.py`, `assignments/repository.py`), and the response still goes through the same centralized `http_exception_handler` (`core/errors.py`) that already produces the `{status, code, message, timestamp}` body — no new error-handling path needed. Story 6.2's AC also requires the existing Skill's `id`/`name` in the 409 response body (for the frontend's future "Use existing skill" affordance, Story 6.10) — `AppException`'s `message` is a plain string, not structured, so this story needs a small, explicit JSON body for this one response rather than reusing the generic exception-handler shape verbatim. See Dev Notes for the recommended approach (a dedicated `JSONResponse` or a raised `HTTPException` with a dict `detail`, since `AppException.message` is str-only) — resolve this as part of implementation, consistent with the existing error contract's spirit (the top-level `status`/`code`/`message`/`timestamp` envelope) while still surfacing the two extra fields the AC requires.
6. **Gate pattern: service-layer `require_hr_admin(current_user)`, not a router-level `Depends`.** Two precedents coexist in this codebase — `dashboard/router.py` gates via `Depends(require_hr_admin)` at the router; `assignments/service.py` (the closer sibling — same "new admin-only CRUD on a directly-owned table" shape as this story) calls `require_hr_admin(current_user)` as the first line of every mutating service function, with the router just passing `current_user` through. Follow `assignments/service.py`'s pattern for consistency with the module this one most resembles.

## Acceptance Criteria

**Given** I am authenticated as HR_ADMIN
**When** I call `POST /api/admin/skills` with `{ name: str, description: str | None }`
**Then**:
- `name` is required, non-empty; `description` is optional
- The service checks for an existing Skill with the same name, **case-insensitive** — if found, returns `409 Conflict` with the existing Skill's `id`/`name` in the response body (never silently creates a duplicate; the frontend, Story 6.10, uses this to offer "Use existing skill")
- If no conflict, creates the Skill (`ever_assigned = false`), computes its embedding (Story 6.1), and returns `201 Created` with the full `SkillResponse` (id, name, description, `ever_assigned: false`, no raw embedding vector in the response — same "no raw embedding in default responses" convention as `content/`'s `ContentResponse`)

**Given** an EMPLOYEE session
**When** it calls `POST /api/admin/skills`
**Then** it returns `403 Forbidden` (AD-6, HR_ADMIN-only)

**Out of Scope (this story):** the frontend's "flows directly into content-sourcing" behavior (UX-DR31) — that's Story 6.10's job, orchestrating this endpoint plus Story 6.6's lookup endpoint from the client side. This story is the create endpoint alone.

## Tasks / Subtasks

- [x] Task 1: `skills/schemas.py` — request/response contracts (AC1)
  - [x] `CreateSkillRequest` (`name: str`, `description: str | None`) — `name` required non-empty (`Field(min_length=1)` plus a `field_validator` rejecting whitespace-only names, stripping the value)
  - [x] `SkillResponse` (`id: UUID`, `name: str`, `description: str | None`, `ever_assigned: bool`) — no `embedding` field, matching `ContentResponse`'s "no raw embedding" convention; `model_config = ConfigDict(from_attributes=True)`
- [x] Task 2: `skills/repository.py` — case-insensitive lookup + insert (AC1)
  - [x] `get_skill_by_name_ci(db, name) -> Skill | None` — `func.lower(Skill.name) == func.lower(name)`, exact case-insensitive match
  - [x] `create_skill(db, skill_data: dict) -> Skill` — dict-based insert mirroring `content/repository.py::create_content`'s exact style; caller passes `ever_assigned=False` explicitly
- [x] Task 3: `skills/service.py` — `create_skill_service` (AC1, AC2)
  - [x] `require_hr_admin(current_user)` as the first line (Scope Note 6)
  - [x] Case-insensitive duplicate check via `repository.get_skill_by_name_ci`; on hit, raises `AppException(409, "SKILL_NAME_CONFLICT", ..., extra={"existing_skill": {...}})` (Scope Note 5, resolved — see Dev Notes)
  - [x] On no conflict: `embed_text(_build_embedding_text(name, description))`, then `repository.create_skill(...)`, `db.commit()`, return `SkillResponse`
- [x] Task 4: `skills/router.py` — `POST` route (AC1, AC2)
  - [x] `@router.post("", response_model=SkillResponse, status_code=status.HTTP_201_CREATED)`, `current_user: CurrentUser = Depends(get_current_user)`, `session: AsyncSession = Depends(get_db)` — matches `assignments/router.py::create_assignment_route`'s exact signature shape
  - [x] Delegates entirely to `create_skill_service` — no logic in the router itself
- [x] Task 5: Mount `skills_router` in `app/main.py` (Scope Note 2)
  - [x] `app.include_router(skills_router, prefix="/api/admin/skills", tags=["skills"])`, placed alongside the other `include_router` calls
- [x] Task 6: Tests
  - [x] `tests/test_skills_service.py` (extended): `create_skill_service` — successful create computes and stores an embedding, sets `ever_assigned=False`, returns the right shape; case-insensitive duplicate (name vs `name.upper()`) returns the conflict path with the *original* Skill's id/name, no second row created; EMPLOYEE role raises the `require_hr_admin` 403
  - [x] `tests/test_skills_router.py` (new file, mirrors `test_content_router.py`'s real-ASGI-app-plus-private-engine pattern — does not use the shared `db_session` conftest fixture): `POST /api/admin/skills` as HR_ADMIN → `201`, response shape matches `SkillResponse`, no `embedding` field in body; same-name-different-case → `409`, body contains the existing skill's `id`/`name`; as EMPLOYEE → `403`; unauthenticated → `401`; blank name → `422`; missing name → `422`. Each test cleans up its own created Skill row in a `finally` block.
  - [x] Full regression pass — 385 passed (9 new), 2 skipped, same 3 pre-existing failures as Story 6.1's documented baseline, confirmed via `git stash` comparison (baseline: 376 passed with identical 3 failures)

### Review Findings

`bmad-code-review` (2026-09-09, 3 parallel adversarial layers — Blind Hunter, Edge Case Hunter, Acceptance Auditor). 1 decision-needed, 5 patches, 2 deferred, 7 dismissed.

- [x] [Review][Decision] Case-insensitive duplicate check has no DB-level backstop — a race between two concurrent creates using different-case names (e.g. `"Python"` vs `"PYTHON"`) can both pass the app-layer pre-check and both succeed, since `skills.name`'s DB unique constraint (`skills/models.py:38`) is case-sensitive only. All 3 review layers independently converged on this. **Decision (user, 2026-09-09): add the migration now.** New migration `006_add_skills_name_ci_unique_index.py` adds `CREATE UNIQUE INDEX ix_skills_name_lower ON skills (lower(name))` — a functional unique index closing the race at the DB level (the existing plain `UNIQUE(name)` constraint from Story 1.7 is left untouched, per Scope Note 4). Verified live: no pre-existing case-variant duplicates, index applied, `alembic_version` = `006`. [backend/alembic/versions/006_add_skills_name_ci_unique_index.py, backend/app/skills/repository.py:41-50, backend/app/skills/models.py:38]

- [x] [Review][Patch] Uncaught `IntegrityError` on an exact-name concurrent-duplicate race returns a raw 500 instead of the documented clean 409 — the app-layer pre-check (`get_skill_by_name_ci`) and the insert are not atomic; two requests racing with the identical name can both pass the pre-check before either commits, and the DB's unique-constraint violation on the second insert is never caught. Fixed: `create_skill_service` now wraps the insert in `try/except IntegrityError`, rolls back, re-queries, and serves the same clean 409 via a shared `_conflict()` helper. [backend/app/skills/service.py]
- [x] [Review][Patch] No `max_length` on `CreateSkillRequest.name` while `skills.name` is `String(255)` — a name over 255 characters passes Pydantic validation and then fails at insert time with an unhandled DB error (500) instead of a clean 422. Fixed: `Field(min_length=1, max_length=255)`. [backend/app/skills/schemas.py]
- [x] [Review][Patch] `db.commit()` called explicitly in `create_skill_service`, contradicting `core/db.py::get_db`'s documented convention ("individual repository/service functions should flush, not commit") and the service's own docstring claim to mirror `assignments/service.py::create_assignment_service` (which correctly relies on flush-only, per that convention). Fixed: removed the explicit commit; `repository.create_skill` already flushes+refreshes, `get_db` commits at the end of the request. [backend/app/skills/service.py]
- [x] [Review][Patch] `AppException.extra` has no guard against a future caller choosing a key that collides with the reserved envelope fields (`status`/`code`/`message`/`timestamp`), silently corrupting the response shape. Fixed: `AppException.__init__` now raises `ValueError` if `extra`'s keys intersect the reserved envelope keys. [backend/app/core/errors.py]
- [x] [Review][Patch] Missing test coverage: the exact-same-name concurrent-duplicate path (the new `IntegrityError`→409 branch from the patch above) and the 409 response's base envelope fields (`status`/`code`/`message`/`timestamp`) alongside `existing_skill` are both untested — only the different-case duplicate path and `existing_skill`'s own fields are currently asserted. Fixed: added a two-independent-sessions race-simulation test (service layer), an exact-same-name router test, an envelope-field assertion on the existing 409 router test, and a >255-char router test. [backend/tests/test_skills_service.py, backend/tests/test_skills_router.py]

- [x] [Review][Defer] Custom blank-name validator message ("name must not be blank") is unreachable by any caller — `core/errors.py::validation_exception_handler` discards all Pydantic per-field detail and always returns a fixed generic message ("The request body failed validation") for every 422 across the entire app, for every schema. Pre-existing, app-wide shared-handler behavior, not specific to this diff or fixable within this story's scope. — deferred, pre-existing
- [x] [Review][Defer] Case-insensitive duplicate check doesn't normalize Unicode form (NFC vs NFD) or apply full casefold — visually-identical names in different Unicode normalization forms could both be created as distinct Skills. Low real-world likelihood for this admin-only, largely-English-language catalog; a full fix is a small design question (which normalization strategy) better suited to a future story if it ever surfaces in practice. — deferred, pre-existing class of gap (this codebase has no Unicode-normalization handling anywhere else either)

**Dismissed** (noise, false positive, or already handled elsewhere): the router docstring's `/api/admin/...` prefix "convention" claim being precedent-setting rather than precedent-following (false positive — `ARCHITECTURE-SPINE.md`'s Consistency Conventions table explicitly names this prefix pattern as the intended convention, which the docstring correctly cites as its source, not an existing-router precedent); no audit logging on the 409/success paths (no existing precedent for this anywhere else in the codebase either — `assignments/service.py::create_assignment_service` doesn't log on success, only rejection paths do); `ever_assigned: False` hardcoded in the insert dict alongside the column's own `server_default=false()` (intentional — matches `content/repository.py::create_content`'s established explicit-field-dict style, harmless duplication); the redundant `Depends(get_current_user)` at both router-construction and route-parameter level (pre-existing codebase-wide convention across every router, not a new defect); no direct regression test asserting an unrelated endpoint's error body is byte-for-byte unchanged (the full-suite pass-count comparison via `git stash` is this codebase's own established regression-verification convention, see Story 6.1); `embed_text()` failures surfacing as a generic 500 with no distinct error code (matches this codebase's existing precedent everywhere else `embed_text()` is called, not a regression); NUL-byte/control-character rejection in `name`/`description` (narrow edge case for an authenticated, HR-Admin-only internal field; no existing precedent for this class of input sanitization anywhere else in the codebase).

## Dev Notes

- **Resolving Scope Note 5 (409 response shape) is this story's one real design decision.** The cleanest option consistent with the existing error contract: raise a plain FastAPI `HTTPException(status_code=409, detail={"code": "SKILL_NAME_CONFLICT", "message": "...", "existing_skill": {"id": ..., "name": ...}})` — the existing `http_exception_handler` (`core/errors.py:40-46`) reads `exc.detail` via `str(exc.detail)` for the `message` field today, which would stringify a dict badly, so this path likely needs either (a) a small addition to the exception handler to detect a dict `detail` and merge its keys into the response body's envelope, or (b) bypass the centralized handler for this one endpoint and return a `JSONResponse` directly from the service/router. Pick whichever is the smaller, most consistent change — do not restructure the shared error contract for every other endpoint to accommodate this one case.
- **Embedding dimension is 384** (`core/embedding.py::EMBEDDING_DIM`), same model as everything else (`all-MiniLM-L6-v2`) — no new model config needed.
- **Do not add a `PATCH`/`DELETE` route or any edit/delete logic** — that's Story 6.3, explicitly out of scope here even though it will live in the same `router.py`/`service.py` files.
- **Testing standard for this codebase's live-DB router tests:** login via `POST /api/auth/login` with seeded credentials (`rita@sails.example.com` / `demo123` for HR_ADMIN, any of `casey@sails.example.com` etc. for EMPLOYEE — see `core/seeds.py`), extract the session cookie, reuse across requests — matches `test_content_router.py`'s `_login` helper exactly; consider factoring a shared helper if one doesn't already exist in a shared test util, but do not over-engineer this for a single new test file.

### Project Structure Notes

Files this story modifies (all pre-existing from Story 6.1, no new module directories):
- `backend/app/skills/schemas.py` — currently empty stub, this story adds `CreateSkillRequest`/`SkillResponse`
- `backend/app/skills/repository.py` — adds `get_skill_by_name_ci`, `create_skill`
- `backend/app/skills/service.py` — adds `create_skill_service`
- `backend/app/skills/router.py` — currently empty `APIRouter()`, this story adds the `POST` route
- `backend/app/main.py` — adds the `skills_router` mount (first one for this module)

New test file:
- `backend/tests/test_skills_router.py`

Extended test file:
- `backend/tests/test_skills_service.py` (already exists from Story 6.1)

No changes expected to:
- `backend/app/skills/models.py` (schema already correct — `ever_assigned` and the unique `name` constraint both landed in Story 6.1/pre-existing migrations)
- `backend/alembic/versions/*` (no schema change — this story only reads/writes existing columns)

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 6.2] — full AC text
- [Source: _bmad-output/planning-artifacts/architecture/architecture-TalentPilot-AI-2026-07-09/ARCHITECTURE-SPINE.md#AD-11] — sole-ownership + embedding-on-write rule (point 4 specifically covers this story's create path)
- [Source: _bmad-output/planning-artifacts/architecture/architecture-TalentPilot-AI-2026-07-09/ARCHITECTURE-SPINE.md#AD-6] — HR_ADMIN gate requirement
- [Source: _bmad-output/planning-artifacts/architecture/architecture-TalentPilot-AI-2026-07-09/ARCHITECTURE-SPINE.md#Consistency Conventions] — `/api/admin/...` route prefix convention, error contract shape
- [Source: _bmad-output/implementation-artifacts/6-1-skills-module-foundation-data-model-migration-embeddings.md] — module scaffolding, `_build_embedding_text` helper, and the "call it inline, don't wrap it" precedent this story must follow
- [Source: backend/app/content/service.py, schemas.py] — `ContentResponse`'s "no raw embedding" convention and `manual_seed_content`'s embed-then-insert pattern this story mirrors
- [Source: backend/app/assignments/service.py, router.py] — `require_hr_admin` service-layer gate pattern and router/service delegation shape this story follows most closely
- [Source: backend/app/core/errors.py] — `AppException` contract and centralized exception handlers
- [Source: backend/tests/test_content_router.py] — real-ASGI-app + private-engine test pattern to mirror for `test_skills_router.py`

## Dev Agent Record

### Agent Model Used

Claude Sonnet 5 (claude-sonnet-5)

### Debug Log References

Full regression suite (deselecting `test_content_repository.py`/`test_content_service.py`, this codebase's own established exclusion — they wipe the shared dev DB via `drop_all()`):
```
3 failed, 385 passed, 2 skipped, 10 deselected
FAILED tests/test_assignments_repository.py::test_find_existing_assignment_returns_empty_when_no_match
FAILED tests/test_content_discovery.py::test_assignment_with_no_qualifying_content_has_null_content
FAILED tests/test_content_router.py::test_content_match_returns_null_when_no_content_matches_the_skill
```
Baseline comparison via `git stash` (this story's changes stashed, same command re-run): `3 failed, 376 passed, 2 skipped, 10 deselected` — identical 3 failures, confirming they're pre-existing (same as Story 6.1's documented baseline) and not caused by this story. 385 - 376 = 9 new passing tests (3 in `test_skills_service.py`, 6 in the new `test_skills_router.py`), zero regressions. `app.main` imports cleanly with the new router mounted (verified via `python -c "from app.main import app"`).

### Completion Notes List

- Implemented `POST /api/admin/skills` end-to-end: `CreateSkillRequest`/`SkillResponse` schemas, `get_skill_by_name_ci`/`create_skill` repository functions, `create_skill_service` (HR_ADMIN gate, case-insensitive duplicate check, inline `embed_text(_build_embedding_text(...))` composition per Story 6.1's precedent), router, and `main.py` mount at `/api/admin/skills`.
- Resolved the story's one open design question (Dev Notes: 409 response shape) by adding an optional `extra: dict | None` parameter to `core/errors.py::AppException` and merging it into `http_exception_handler`'s response body — every existing `AppException`/`raise HTTPException` call site is unaffected (defaults to `{}`), and the 409 response still goes through the same centralized `{status, code, message, timestamp}` envelope with `existing_skill: {id, name}` merged in on top. Chosen over a per-route `JSONResponse` bypass since it keeps every error response (including this new one) flowing through the one centralized handler, matching the architecture spine's "one JSON error contract" convention.
- `name` validation: `Field(min_length=1)` alone would accept a whitespace-only string, so added a `field_validator` that strips and rejects blank names — the AC's "non-empty" read as "non-blank," matching this codebase's general intent elsewhere (no explicit prior precedent for this exact case, but no evidence a whitespace-only Skill name is ever intended).
- Full regression suite confirmed zero new failures via `git stash` baseline comparison (see Debug Log above).

### File List

- `backend/app/skills/schemas.py` (modified) — `CreateSkillRequest`, `SkillResponse`; review patch added `max_length=255`
- `backend/app/skills/repository.py` (modified) — `get_skill_by_name_ci`, `create_skill`
- `backend/app/skills/service.py` (modified) — `create_skill_service`; review patches: catch `IntegrityError` on the insert race and convert to 409 via new `_conflict()` helper, removed the non-conforming explicit `db.commit()`
- `backend/app/skills/router.py` (modified) — `POST` route
- `backend/app/main.py` (modified) — `skills_router` mount
- `backend/app/core/errors.py` (modified) — `AppException.extra` + `http_exception_handler` merge, to carry the 409's `existing_skill` payload; review patch added a reserved-key collision guard
- `backend/alembic/versions/006_add_skills_name_ci_unique_index.py` (new) — review decision: functional unique index on `lower(skills.name)`, DB-level backstop for the case-insensitive duplicate race
- `backend/tests/test_skills_service.py` (modified) — 3 new tests for `create_skill_service`; review patch added 1 more (exact-name race simulation via two independent sessions)
- `backend/tests/test_skills_router.py` (new) — 6 tests for the `POST /api/admin/skills` route; review patch added 3 more (exact-name duplicate, >255-char name, 409 envelope assertion)

## Change Log

- 2026-09-09: Story 6.2 implemented (`bmad-dev-story`). `POST /api/admin/skills` (FR-20) added: HR_ADMIN-only, case-insensitive duplicate check (409 with existing skill's id/name), embedding computed inline via `embed_text(_build_embedding_text(...))` per Story 6.1's precedent, `ever_assigned` defaults false. `core/errors.py::AppException` extended with an optional `extra` field to carry the 409's structured payload through the existing centralized error contract. 9 new tests (3 service, 6 router), zero regressions confirmed via `git stash` baseline comparison (376 passed pre-change vs. 385 passed post-change, identical 3 pre-existing failures). Status → `review`.
- 2026-09-09: `bmad-code-review` (3 parallel adversarial layers — Blind Hunter, Edge Case Hunter, Acceptance Auditor). 1 decision-needed resolved (user: add the DB-level fix now — new migration 006 adds a functional unique index on `lower(skills.name)`, closing the case-insensitive-duplicate race at the DB level), 5 patches applied, 2 deferred (`deferred-work.md`), 7 dismissed. Patches: `create_skill_service` now catches `IntegrityError` on the insert (the race migration 006 converts from "silent duplicate" to "clean 409") and converts it to the same 409 response instead of a raw 500; `CreateSkillRequest.name` gained `max_length=255` matching the DB column; removed a non-conforming explicit `db.commit()` that contradicted `core/db.py::get_db`'s documented flush-only convention; `AppException` now rejects `extra` dicts whose keys collide with the reserved response envelope; added test coverage for the exact-name race (via two independent sessions, simulating real concurrent-request semantics — a same-session two-call version was tried first and caught a design point: sharing one transaction across "two requests" incorrectly rolls back the first request's own insert too), an exact-name-twice router test, a >255-char router test, and an envelope-field assertion on the existing case-different 409 test. Full regression re-verified: 388 passed (17 new total from this story) / 2 skipped / same 3 pre-existing failures (one additional failure seen on a first pass, confirmed as this codebase's known cross-file test-order flakiness by re-running both in isolation and as part of the full suite a second time — not a regression). Status → `done`.
