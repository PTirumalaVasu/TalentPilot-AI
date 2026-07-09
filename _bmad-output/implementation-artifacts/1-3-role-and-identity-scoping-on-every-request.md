---
baseline_commit: 49717295952b97a4f420c1529d37d5ee83c2aad3
---

# Story 1.3: Role & Identity Scoping on Every Request

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **developer**,
I want to enforce role and identity scoping at the FastAPI dependency layer and repository layer,
so that every protected request is validated server-side before data access, and EMPLOYEE sessions are hard-scoped to prevent cross-employee data access (FR-14).

## ⚠️ Scope Carve-Out (read this before starting)

The epic's AC text spans two layers: (1) FastAPI-dependency-layer role/identity validation, and (2) repository-layer employee hard-scoping demonstrated against `GET /api/assignments`, `GET /api/content`, and `GET /api/assignments/{id}/progress/drill-down`.

**Only layer (1) is buildable right now.** `assignments/repository.py` and `content/repository.py` are still empty one-line-docstring stubs (verified by reading them directly) — their tables don't exist yet (owned by Story 3.1 and Story 2.1 respectively) and their endpoints don't exist yet (owned by Epic 2/3/5 stories). Writing hard-scoping query logic now would mean writing dead code against tables that don't exist, guessing at a schema Story 3.1/2.1 haven't defined yet, and very likely reworking it later — exactly the kind of forward-dependency violation the Implementation Readiness Assessment already flagged elsewhere in this project (`epics.md` Story 01.1.1 → 03.6 case).

**This story therefore delivers only the dependency-layer AC in full** (all 5 edge cases below) and explicitly defers the repository hard-scoping AC as **binding guidance for Epic 2/3, not optional follow-up** — see the "Forward-Reference: Repository Hard-Scoping" Dev Note. Do not attempt to stub or partially implement repository hard-scoping in this story.

## Acceptance Criteria

1. **AC1 — Dependency extracts and validates role + identity.** A FastAPI dependency (`get_current_user`, layered on Story 1.2's `get_current_token_payload`) validates: `role` claim is present and ∈ `{HR_ADMIN, EMPLOYEE}`; `user_id` claim is present and non-null. On success, the validated identity is available via the dependency's return value **and** attached to `request.state.current_user`.
2. **AC2 — EDGE CASE: Missing role claim → 401.** JWT decodes successfully but has no `role` key → **401 Unauthorized**, message: `"JWT missing required 'role' claim"`.
3. **AC3 — EDGE CASE: Invalid role value → 403 with a distinguishable error code.** `role` is present but not in `{HR_ADMIN, EMPLOYEE}` (e.g. `"UNKNOWN"`, `"admin"`) → **403 Forbidden**, error **code `INVALID_ROLE`** (not the generic `HTTP_ERROR` — see Task 0), message: `"Role '{role}' not recognized. Expected: HR_ADMIN or EMPLOYEE"`.
4. **AC4 — EDGE CASE: EMPLOYEE missing user_id → 400.** `role == "EMPLOYEE"` but `user_id` is missing/null → **400 Bad Request**, message: `"EMPLOYEE role requires user_id claim; token rejected"`.
5. **AC5 — EDGE CASE: Valid HR_ADMIN and valid EMPLOYEE both pass.** Both roles with a present, valid `user_id` proceed past the dependency with the identity populated.
6. **AC6 — Non-goal this story (forward reference only).** Repository-layer employee hard-scoping (`assignments`/`content` queries filtered by `employee_id`, ignoring spoofed `?employee_id=` params, 403 on cross-employee drill-down access) is **not implemented here** — no such queries exist yet. This AC is carried forward as binding guidance for Story 2.x/3.x — see Dev Notes.

## Tasks / Subtasks

- [x] Task 0: Extend the error contract to carry a custom error code (AC: #3)
  - [x] `core/errors.py`: added `class AppException(StarletteHTTPException)` with an `error_code: str` attribute; updated the existing `http_exception_handler` to use `getattr(exc, "error_code", "HTTP_ERROR")` instead of the hardcoded `"HTTP_ERROR"` string — additive/backward-compatible, existing plain `HTTPException(401, ...)` call sites (Story 1.2) still return `"HTTP_ERROR"` via the fallback (tested explicitly)
- [x] Task 1: `Role` enum + `CurrentUser` schema (AC: #1)
  - [x] `auth/schemas.py`: `class Role(str, Enum): HR_ADMIN = "HR_ADMIN"; EMPLOYEE = "EMPLOYEE"` and `class CurrentUser(BaseModel): role: Role; user_id: str`
- [x] Task 2: `get_current_user` dependency (AC: #1, #2, #3, #4, #5)
  - [x] `auth/service.py`: `get_current_user(request: Request, payload: dict = Depends(get_current_token_payload)) -> CurrentUser` — implemented exactly per spec: missing role → 401; invalid role → `AppException(403, "INVALID_ROLE", ...)`; EMPLOYEE missing user_id → 400; success builds `CurrentUser`, sets `request.state.current_user`, returns it
- [x] Task 3: Tests (AC: #2, #3, #4, #5)
  - [x] Missing `role` claim → 401, centralized error contract shape
  - [x] Invalid `role` value (`"UNKNOWN"`) → 403, `code == "INVALID_ROLE"` specifically (not generic `HTTP_ERROR`)
  - [x] `role="EMPLOYEE"`, missing `user_id` → 400
  - [x] Valid `HR_ADMIN` → 200, `request.state.current_user` populated correctly (identity check, not just equality)
  - [x] Valid `EMPLOYEE` with `user_id` → 200, `request.state.current_user` populated correctly
  - [x] Used a temporary test-file-local FastAPI app/route (`test_current_user.py`) — `main.py` untouched

### Review Findings

- [x] [Review][Patch] **HR_ADMIN token with missing/null/empty `user_id` causes an unhandled 500** instead of a clean 4xx — the `not user_id` guard only fires `if role == Role.EMPLOYEE`, but `CurrentUser.user_id` is a required non-Optional `str`; verified empirically that `CurrentUser(role="HR_ADMIN", user_id=None)` raises an uncaught `pydantic.ValidationError` that falls through to the generic 500 handler [backend/app/auth/service.py:51-57] — confirmed by all 3 review layers independently, not a false positive — **fixed**: `not user_id` check now applies unconditionally to both roles, with `test_hr_admin_missing_user_id_returns_400_not_500` added as a regression test
- [x] [Review][Patch] `Role(role)` can raise `TypeError` (not just `ValueError`) if the `role` claim is a non-string type (list/dict from a malformed token), escaping the `except ValueError` clause and producing an unhandled 500 instead of 403 `INVALID_ROLE` [backend/app/auth/service.py:42-43] — **fixed**: now catches `(ValueError, TypeError)`, `test_non_string_role_claim_returns_403_not_500` added
- [x] [Review][Patch] None of the 3 rejection branches in `get_current_user` (missing role, invalid role, missing user_id) log anything, unlike `core/errors.py`'s handlers which log every rejection — a security-relevant blind spot for an identity-scoping boundary [backend/app/auth/service.py] — **fixed**: `logger.warning(...)` added to all 3 branches
- [x] [Review][Patch] `AppException`'s docstring misattributes the `HTTP_ERROR` fallback behavior to itself; the fallback actually lives in `core/errors.py`'s handler (`getattr(exc, "error_code", "HTTP_ERROR")`), not in `AppException` [backend/app/core/errors.py] — **fixed**: docstring reworded
- [x] [Review][Patch] `test_employee_missing_user_id_returns_400` only tests `user_id=None` explicitly present in claims, not `user_id` key entirely absent — same code path today, but untested as a distinct case [backend/tests/test_current_user.py] — **fixed**: `test_employee_absent_user_id_key_returns_400` added
- [x] [Review][Defer] `AppException.__init__`'s parameter order (`status_code, error_code, message`) is unconventional and risks a silent positional-arg mixup in a future call site (both are plain `str`, no type error would catch it) [backend/app/core/errors.py] — deferred, no live bug since all current call sites use keyword args
- [x] [Review][Defer] No `import-linter`/lint enforcement that `get_current_user` is the sanctioned way to access session/role logic (AD-1) — deferred, duplicate of an existing Story 1.1 deferred item in `deferred-work.md`

## Dev Notes

- **Builds directly on Story 1.2's `get_current_token_payload`** (`auth/service.py`) — that function already handles missing-cookie/expired/tampered-signature → 401 and returns the raw decoded payload dict. This story's `get_current_user` takes that payload as an input (via `Depends`) and adds the role/identity validation layer on top. Do not duplicate cookie-extraction or JWT-decode logic here.
- **Why Task 0 (custom error code) is in scope despite touching shared `core/errors.py`:** AC3 explicitly requires the response body's `code` field to be `INVALID_ROLE`, not a generic string — the current handler (from Story 1.1) hardcodes `"HTTP_ERROR"` for every `HTTPException`. The fix is additive (a new exception subclass + a `getattr` fallback), not a redesign, and every existing call site keeps working unchanged. Do not go further than this — do not invent a general-purpose error-code registry/taxonomy; that's out of scope.
- **Forward-Reference: Repository Hard-Scoping (binding guidance for Story 2.x/3.x, not this story's work).** When `assignments/repository.py` (Story 3.1) and `content/repository.py` (Story 2.1) get real query methods, they **must**:
  - Hard-scope every EMPLOYEE-session query by `employee_id` **in the repository layer itself** (the WHERE clause), not in the service or router layer — so an overlooked permission check elsewhere can't leak data.
  - Silently ignore any client-supplied `?employee_id=` override for EMPLOYEE sessions — return the caller's own data regardless of what was requested, with **no error message** (don't reveal the scoping mechanism exists).
  - Apply this via parameterized queries (SQLAlchemy's query builder does this by construction — don't hand-build SQL strings).
  - For a drill-down-style endpoint reached by assignment ID (not a list), check ownership at the controller/service layer and return **403 Forbidden** ("You do not have access to this assignment") if the assignment belongs to a different employee — without leaking whether the assignment exists at all to someone probing IDs.
  - HR_ADMIN sessions are **not** hard-scoped by identity — they get org-wide read access, filtered only by whatever the service layer's business logic dictates (e.g. AD-2's coaching-shaped reads), never by `employee_id`.
  - Whoever implements Story 3.1/2.1 should treat this Dev Note as a requirement even though it isn't restated in that story's own AC text — the dev-story workflow's own operating principle applies here: *"if a behavior is required for the feature to work correctly in the existing system, it is a requirement whether or not it is explicitly written in the story."*
- **Do not build a placeholder/stub hard-scoping helper "just in case."** There's no schema to scope against yet, and guessing at one now risks contradicting whatever Story 3.1 actually defines. Building nothing here is the correct call, not a shortcut.
- **`Role` as a `str, Enum`** (not a plain string constant) gives an idiomatic Python membership check (`role in Role.__members__` or `try: Role(role) except ValueError`) and Pydantic validates against it automatically if used as a field type elsewhere later — but note `CurrentUser.role` is typed `Role` only *after* this dependency's own manual validation passes; don't let Pydantic silently 422 on bad input before this story's specific 401/403/400 edge cases fire — do the manual `role not in {...}` check against the **raw string claim** first, then construct `CurrentUser` only once validation has already succeeded.

### Project Structure Notes

- Changes land in `auth/service.py` (new dependency), `auth/schemas.py` (new `Role`/`CurrentUser`), and `core/errors.py` (additive `AppException` + one-line handler change). No new modules or files.
- `assignments/`, `content/`, `progress/`, `dashboard/` remain untouched stubs this story.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.3: Role & Identity Scoping on Every Request] — full AC text, including the repository hard-scoping examples this story defers
- [Source: _bmad-output/planning-artifacts/architecture/architecture-TalentPilot-AI-2026-07-09/ARCHITECTURE-SPINE.md#AD-6] — "an Employee session is hard-scoped to its own identity... an HR Admin session may read org-wide but only through the coaching-shaped read methods of AD-2"
- [Source: _bmad-output/implementation-artifacts/1-2-jwt-token-generation-and-session-model.md] — previous story: `get_current_token_payload` this story builds on
- [Source: _bmad-output/implementation-artifacts/1-1-project-structure-and-core-dependencies.md] — `core/errors.py`'s existing `StarletteHTTPException` handler (hardcoded `"HTTP_ERROR"` code) that Task 0 extends
- [Source: _bmad-output/implementation-artifacts/sprint-status.yaml] — story key `1-3-role-and-identity-scoping-on-every-request`

## Library/Framework Requirements

No new dependencies. Uses FastAPI's `Depends()` (already installed) and Python's stdlib `enum.Enum`.

## Testing Requirements

- All 5 edge cases in AC2–AC5 need their own test, via a temporary test-file-local FastAPI app/route (`backend/tests/test_main.py`'s `_build_test_app_with_handlers` / `test_auth_service.py`'s `_build_protected_test_app` pattern) — do not touch `main.py`.
- The 403 test must assert `body["code"] == "INVALID_ROLE"` specifically, not just the status code — this is the one place this story changes shared error-contract behavior, so it needs its own explicit regression test in `test_config.py`/`test_main.py`-style coverage for `core/errors.py`'s new `AppException` path (a plain `HTTPException` without `error_code` must still fall back to `"HTTP_ERROR"` — test that too, so Task 0's change is provably backward-compatible).
- Do not write repository/hard-scoping tests — no such code exists this story.
- Test framework: `pytest` + `httpx`, consistent with Stories 1.1/1.2.

## Previous Story Intelligence

From Story 1.2 (`1-2-jwt-token-generation-and-session-model.md`, status `done`):
- `get_current_token_payload(request) -> dict` exists in `auth/service.py`, already 401s on missing/expired/tampered tokens — this story's `get_current_user` composes on top via `Depends(get_current_token_payload)`.
- Established pattern: exercise new auth behavior via a temporary test-file-local FastAPI app, never by modifying `main.py`.
- Code review in this project runs 3 parallel adversarial layers and does not take review-agent findings at face value — verify claims empirically (e.g. Story 1.2's review directly ran `decode_access_token` against malformed input in the venv rather than trusting a reviewer's inference).
- Story 1.2's code review deferred "both 401 paths collapse to the same generic HTTP_ERROR code" as an architecture-level gap — this story's Task 0 is the first concrete step toward closing that gap (for a different reason: AC3 requires it), so don't reintroduce the same flatness by hardcoding another generic string instead of using the new `error_code` mechanism.

## Git Intelligence Summary

Recent commits: `4971729 Implement Story 1.1: project structure and core dependencies (#25)` (merged), Story 1.2 work not yet committed at story-creation time. Pattern established: one implementation commit per story with a descriptive body, PR merged via GitHub. `backend/` on `main` currently only has Story 1.1's scaffold + whatever Story 1.2 lands as; this story branches from wherever Story 1.2's work ends up.

## Dev Agent Record

### Agent Model Used

claude-sonnet-5

### Debug Log References

- `backend/.venv/Scripts/python.exe -m pytest tests/ -v` → 30 passed (full suite, final run)
- Confirmed red before each implementation: `test_main.py`'s new `AppException` tests failed with `ImportError` before `core/errors.py` had it; `test_current_user.py` failed with `ImportError` before `auth/schemas.py`/`auth/service.py` had `Role`/`CurrentUser`/`get_current_user`
- Live `uvicorn app.main:app` boot on port 8126 after implementation, `GET /` → `200 {"status":"ok"}` — no regressions

### Completion Notes List

- Implemented test-first in dependency order: Task 0 (`AppException`) first since Task 2's 403 depends on it, then `Role`/`CurrentUser` schema, then `get_current_user`, each with failing tests confirmed red before implementation.
- **Scope carve-out from story creation was honored exactly as written:** implemented only the FastAPI-dependency-layer half of the epic's AC (all 5 edge cases). No repository/hard-scoping code was written — `assignments/repository.py` and `content/repository.py` remain untouched stubs, since their tables/endpoints genuinely don't exist yet (owned by Story 3.1/2.1). The story's Dev Notes already carry this forward as binding guidance for those stories.
- Task 0's `AppException` addition was verified backward-compatible with an explicit test (`test_plain_http_exception_falls_back_to_generic_error_code`) proving existing plain-`HTTPException` call sites (Story 1.2's 401s) are unaffected.
- `get_current_user` composes on `Depends(get_current_token_payload)` from Story 1.2 rather than re-extracting/re-decoding the cookie — no duplicated JWT logic.
- Tests use real JWTs crafted directly via `pyjwt.encode()` (bypassing `create_access_token`) for the two edge cases that need claims `create_access_token` doesn't allow constructing (a token with no `role` key at all, and an `EMPLOYEE` token with `user_id=None`) — this is deliberate and necessary, not a shortcut, since those exact malformed-claim shapes are what AC2/AC4 test.
- ~~HR_ADMIN-session-missing-user_id was not implemented as its own edge case: the epic's AC only specifies this check for EMPLOYEE sessions (asymmetric by design, matching the epic text exactly)~~ — **retracted, this was wrong.** Code review (all 3 layers independently, confirmed empirically) found this asymmetry was a real bug, not a deliberate design choice: an HR_ADMIN token missing `user_id` crashed with an unhandled `pydantic.ValidationError` (500) instead of a clean 4xx, since `CurrentUser.user_id` is a required `str`. Fixed post-review: the `not user_id` check now applies to both roles unconditionally, matching AC1's actual blanket statement ("user_id claim is present and non-null," not qualified by role) rather than over-reading AC4's EMPLOYEE-specific edge case as an exclusion.

### File List

- `backend/app/core/errors.py` (modified — added `AppException` class, updated `http_exception_handler` to use `getattr(exc, "error_code", "HTTP_ERROR")`; docstring fixed in review)
- `backend/app/auth/schemas.py` (modified — added `Role` enum, `CurrentUser` schema)
- `backend/app/auth/service.py` (modified — added `get_current_user` dependency; review fixes: `user_id` check applies to both roles, `(ValueError, TypeError)` caught, logging added to all rejection branches)
- `backend/tests/test_main.py` (modified — added `AppException`/backward-compat tests)
- `backend/tests/test_current_user.py` (new; review fixes: added `test_hr_admin_missing_user_id_returns_400_not_500`, `test_non_string_role_claim_returns_403_not_500`, `test_employee_absent_user_id_key_returns_400`; consolidated per-test local imports to module scope)

## Change Log

- 2026-07-09: Implemented Story 1.3 — `AppException` custom error codes, `Role`/`CurrentUser` schema, `get_current_user` dependency (all 5 edge cases), all test-first. Repository hard-scoping (AC6) deliberately not implemented — deferred as binding guidance for Story 2.x/3.x per the story's own scope carve-out. 30/30 tests passing (22 pre-existing + 8 new). Status → review.
- 2026-07-09: Code review — **found and fixed a real bug** (HR_ADMIN token missing `user_id` crashed with an unhandled 500 instead of a clean 400, confirmed by all 3 review layers and verified empirically before fixing) plus 4 other patches (TypeError now caught alongside ValueError for malformed role claims, logging added to all rejection branches, `AppException` docstring corrected, additional test coverage for the absent-vs-null `user_id` distinction). 2 findings deferred to `deferred-work.md`, 6 dismissed (matched spec exactly or were pure style). 5 new regression tests added. 33/33 tests passing. Status → done.
