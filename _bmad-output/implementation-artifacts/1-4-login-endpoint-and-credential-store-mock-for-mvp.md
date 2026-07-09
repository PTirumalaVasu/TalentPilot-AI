---
baseline_commit: 49717295952b97a4f420c1529d37d5ee83c2aad3
---

# Story 1.4: Login Endpoint & Credential Store (Mock for MVP)

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an **HR Admin or Employee**,
I want to log in with my credentials,
so that I can access Assignment, Content, and Watch Progress data.

## Scope Notes (read before starting)

1. **Backend scope only — no frontend exists yet.** The epic's "user is redirected to the role-appropriate entry point" is frontend routing behavior; there is no frontend project in this repo. This story's job ends at returning `role` in the response body so a future frontend can decide where to redirect. Do not build a redirect.
2. **The credential store is a hardcoded, in-Python dict — not the `accounts` DB table.** Story 1.7 ("Database Schema Initialization") — which creates the real `accounts` table — comes *after* this story in the epic's own build order, and this story's own AC explicitly says "mock credential store (hardcoded for MVP, not a real LDAP/SSO — see Open Question 9)." So there is nothing to query yet, and this story must not depend on Story 1.7 or Story 3.3 (which seeds `employees`) having run. Hardcode the 5 demo accounts in `auth/repository.py` as a plain dict.
3. **Demo account roster** (per `addendum.md`'s Prototype Implementation Notes, all password `demo123`): `rita@sails.example.com` → HR_ADMIN, user_id `rita`; `casey@sails.example.com`, `morgan@sails.example.com`, `jordan@sails.example.com`, `sam@sails.example.com` → EMPLOYEE, user_ids `casey`/`morgan`/`jordan`/`sam` respectively. These exact user_id slugs already appear throughout Stories 1.2/1.3's tests — keep using them for consistency.
4. **Plaintext password comparison is a deliberate, documented decision for this mock store, not an oversight.** Real password hashing would be theater for 5 hardcoded demo credentials with a shared password that exists only because PRD Open Question 9 declared this local-only, no-real-auth-backend approach acceptable for the MVP pilot. Do not add `bcrypt`/`passlib` — that's solving a problem this story doesn't have. Flagged explicitly so it isn't mistaken for a lapse.

## Acceptance Criteria

1. **AC1 — Login endpoint validates against the mock credential store.** `POST /api/auth/login` accepts `{email, password}`. Valid credentials for one of the 5 hardcoded demo accounts → success. (Endpoint path is `/api/auth/login`, matching the `auth_router`'s existing `/api/auth` prefix already mounted in `main.py` since Story 1.1 — the epic text's bare `/login` refers to the frontend page route, not this backend path.)
2. **AC2 — Successful login sets the session cookie and returns the role.** On success: a JWT is generated (`create_access_token(user_id, role)` — Story 1.1) and stored via `set_session_cookie` (Story 1.2, `HttpOnly`/`SameSite`/configurable-`Secure`). Response body returns the identity's `role` (and `user_id`) — **not** the raw token (token lives only in the cookie, never the JSON body).
3. **AC3 — Failed validation returns a generic error, without revealing which field was wrong.** Wrong password, unknown email, or any other credential mismatch → the same message: `"Email or password incorrect"`, same status code (401) — regardless of whether the email exists or the password was wrong. No timing/response-shape difference between "unknown email" and "wrong password" cases.
4. **AC4 — All 5 demo accounts authenticate correctly with their correct role.** `rita@sails.example.com` → `HR_ADMIN`; `casey@sails.example.com`/`morgan@sails.example.com`/`jordan@sails.example.com`/`sam@sails.example.com` → `EMPLOYEE`, each with their own distinct `user_id`.

## Tasks / Subtasks

- [x] Task 1: Mock credential store (AC: #1, #4)
  - [x] `auth/repository.py`: `_MOCK_ACCOUNTS` dict keyed by email, `find_account(email) -> dict | None`
- [x] Task 2: `LoginRequest`/`LoginResponse` schemas (AC: #1, #2)
  - [x] `auth/schemas.py`: `LoginRequest(email, password)`, `LoginResponse(role, user_id)`
- [x] Task 3: `authenticate` service function (AC: #1, #3, #4)
  - [x] `auth/service.py`: `authenticate(email, password) -> tuple[str, Role]` — single combined check (`account is None or account["password"] != password`), one raise site, one message
- [x] Task 4: `POST /api/auth/login` route (AC: #1, #2)
  - [x] `auth/router.py`: `LoginRequest` in, `authenticate` → `create_access_token(user_id, role.value)` → `set_session_cookie(response, token)` → `LoginResponse` out
- [x] Task 5: Tests (AC: #1, #2, #3, #4)
  - [x] Each of the 5 demo accounts logs in successfully with the correct `role`/`user_id` in the response (parametrized test)
  - [x] Successful login sets a `Set-Cookie` header with the configured cookie name + `HttpOnly`; response body contains no raw token/password field
  - [x] Wrong password for a real email → 401, `"Email or password incorrect"`
  - [x] Unknown email entirely → 401, **identical** message/status/code to the wrong-password case (asserted directly, not just separately)
  - [x] Tested against the real app (`from app.main import app`) — first story with a real, permanent `auth/router.py` endpoint

### Review Findings

- [x] [Review][Patch] **Case-sensitive email lookup rejects valid credentials** — `Rita@Sails.example.com` with the correct password `demo123` fails login, since `find_account` does a raw-string dict `.get()` with no normalization; verified empirically (curl against a running server) [backend/app/auth/repository.py:14-15] — **fixed**: `find_account` now does `email.strip().lower()` before lookup; `test_login_case_insensitive_email_still_succeeds` added and re-verified live
- [x] [Review][Patch] Password comparison uses plain `!=` instead of `secrets.compare_digest` — a timing side-channel with no real impact today (shared demo password, public in the PRD), but flagged as a bad pattern that must not be copied forward into Story 1.7's real `accounts`-table implementation [backend/app/auth/service.py:17-19] — **fixed**: now uses `secrets.compare_digest`
- [x] [Review][Patch] No test coverage for empty-string/missing-field payloads on the new `/login` endpoint — verified empirically the existing behavior is already safe (empty strings → 401 generic message; missing field → 422 validation contract, neither is a 500), but nothing regression-tests it [backend/tests/test_login.py] — **fixed**: `test_login_empty_credentials_returns_401_not_500` and `test_login_missing_password_field_returns_422_not_500` added
- [x] [Review][Defer] No `EmailStr`/format validation on `LoginRequest.email` — safe today (malformed email just 401s via the generic path, verified empirically), but a reasonable hardening item; not required by any AC [backend/app/auth/schemas.py]
- [x] [Review][Defer] No rate limiting/brute-force protection on `/login` — explicitly out of scope for a local-only MVP pilot per PRD Open Question 9's framing; revisit only if this becomes internet-facing [backend/app/auth/router.py]
- [x] [Review][Defer] No OpenAPI `responses=` documentation of the 401 failure shape — cheap docs polish, not blocking [backend/app/auth/router.py]
- [x] [Review][Defer] `authenticate()` doesn't set a custom `INVALID_CREDENTIALS` error code (unlike `get_current_user`'s `INVALID_ROLE`) — already explicitly decided against in this story's own Previous Story Intelligence section (AC3 only requires a message, no code); logged for visibility alongside the related Story 1.2 deferred item on generic `HTTP_ERROR` codes

## Dev Notes

- **This is the first story to give `auth/router.py` a real, permanent route.** Every prior Epic 1 story (1.1–1.3) deliberately built helpers/dependencies without wiring them into `main.py`, testing via temporary test-file-local FastAPI apps instead. That pattern doesn't apply here — `POST /api/auth/login` is real, permanent, user-facing API surface, so test it against the actual `app` object from `app.main`, the same way `test_main.py`'s `test_app_boots_and_root_health_responds` already does.
- **Why the credential store can't be DB-backed yet:** see Scope Note 2. `accounts` (Story 1.7) and `employees` (Story 3.3) don't exist. Don't add a database dependency to this story to "do it properly" — that directly contradicts the epic's own explicit "mock credential store (hardcoded for MVP)" AC text and the build-order sequencing (1.7 comes after 1.4).
- **Single failure path for AC3.** The most common way this AC gets silently violated is writing two different code paths (`account not found` vs `password mismatch`) that are *supposed* to produce identical output but drift apart during a later edit (e.g. someone adds a debug log to one branch, or a slightly different message string). Structure `authenticate` so there is exactly one place that raises the 401 — look up the account, then do a single combined check (`if account is None or account["password"] != password: raise ...`) — not two independent raises with duplicated message strings.
- **Response never contains the raw token.** `set_session_cookie` puts it in the cookie; `LoginResponse` only echoes back `role`/`user_id`. This is consistent with Story 1.2's whole reason for existing (cookie-only sessions, never `localStorage`/response-body tokens).
- **`create_access_token` expects `role: str`, not the `Role` enum directly** (see `core/security.py`'s signature from Story 1.1: `create_access_token(user_id: str, role: str, ...)`) — pass `role.value`, not the enum member itself, when calling it from the router.
- **401 status code for login failure is this story's own reasonable default, not something the epic text pins explicitly** — it only says "an error message is shown," not a status code. 401 was chosen for consistency with every other auth-rejection path already in this codebase (`get_current_token_payload`, `get_current_user`). Flagging as an assumption, not a locked spec fact.

### Project Structure Notes

- Changes land in `auth/repository.py` (new mock data + lookup), `auth/schemas.py` (new `LoginRequest`/`LoginResponse`), `auth/service.py` (new `authenticate`), `auth/router.py` (new real route — first non-empty router in the project). No changes to `main.py`: the `/api/auth` prefix mount already exists from Story 1.1.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.4: Login Endpoint & Credential Store (Mock for MVP)] — full AC text
- [Source: _bmad-output/planning-artifacts/prds/prd-TalentPilot-AI-2026-07-09/addendum.md#Prototype Implementation Notes] — demo account roster (Rita=HR, Casey/Morgan/Jordan/Sam=Employee, password `demo123`), and Open Question 9 (mock credential store, not real LDAP/SSO)
- [Source: _bmad-output/implementation-artifacts/1-1-project-structure-and-core-dependencies.md] — `create_access_token(user_id, role)` signature this story calls
- [Source: _bmad-output/implementation-artifacts/1-2-jwt-token-generation-and-session-model.md] — `set_session_cookie` this story calls
- [Source: _bmad-output/implementation-artifacts/1-3-role-and-identity-scoping-on-every-request.md] — `Role` enum this story's `LoginResponse`/`authenticate` use
- [Source: _bmad-output/implementation-artifacts/sprint-status.yaml] — story key `1-4-login-endpoint-and-credential-store-mock-for-mvp`

## Library/Framework Requirements

No new dependencies. Uses `create_access_token`/`set_session_cookie`/`Role` (all already built), FastAPI's `Response` injection for cookie-setting from a route handler.

## Testing Requirements

- Test against the real `app` (`from app.main import app`), not a temporary test-file-local app — this is the first story with a real, permanent route.
- All 5 demo accounts, both failure cases (wrong password, unknown email — asserting **identical** response), cookie presence, no-token-in-body.
- Test framework: `pytest` + `httpx`, consistent with prior stories.

## Previous Story Intelligence

From Story 1.3 (`1-3-role-and-identity-scoping-on-every-request.md`, status `done`):
- Its code review found a real bug (HR_ADMIN with missing `user_id` → unhandled 500) that the implementer's own completion notes had incorrectly rationalized as "by design" — retracted after review. Lesson carried forward: don't assume an asymmetric-looking check is intentional just because it matches the epic text's literal edge-case list; check whether the *general* AC statement (here, AC1's blanket requirement) is being under-applied.
- `Role` enum and `CurrentUser` schema now exist in `auth/schemas.py` — this story adds `LoginRequest`/`LoginResponse` alongside them, doesn't touch the existing ones.
- `core/errors.py`'s `AppException` (custom error code) exists if a distinguishable error code is ever needed — not required by this story's AC3 (which only specifies a message, no custom code), so plain `HTTPException(401, ...)` is sufficient here; don't add `AppException` unless a future need for a specific code arises.

## Git Intelligence Summary

Recent commits: `4971729 Implement Story 1.1: project structure and core dependencies (#25)` (merged). Stories 1.2/1.3 implemented in the same working session, not yet committed at story-creation time. Pattern established: one implementation commit per story with a descriptive body, PR merged via GitHub.

## Dev Agent Record

### Agent Model Used

claude-sonnet-5

### Debug Log References

- `backend/.venv/Scripts/python.exe -m pytest tests/ -v` → 42 passed (full suite, final run)
- Confirmed red: `test_login.py`'s 8 behavioral tests failed with 404 (no route existed yet) before implementation; the 9th ("wrong password and unknown email are indistinguishable") passed trivially pre-implementation since both cases 404'd identically — not a meaningful red signal for that one, but its post-implementation pass is meaningful
- Live end-to-end verification via `curl` against a running `uvicorn` instance: successful login (`rita@sails.example.com`) → 200, `Set-Cookie` with `HttpOnly`/`Max-Age`/`SameSite=lax`, body `{"role":"HR_ADMIN","user_id":"rita"}`; wrong password and unknown email both → byte-identical `{"status":"error","code":"HTTP_ERROR","message":"Email or password incorrect",...}`

### Completion Notes List

- First story to give `auth/router.py` a real, permanent endpoint — tested against the actual `app` object (`from app.main import app`), departing from the temporary-test-app pattern used in Stories 1.1–1.3 since there was no real route to test against until now.
- `authenticate()` uses a single combined boolean check (`account is None or account["password"] != password`) with one raise site, per the Dev Notes' explicit warning about AC3 drifting apart across two independently-maintained branches — verified via a dedicated test that directly compares the two failure responses for exact equality (status, message, and code), not just separately asserting each looks right.
- Followed the story's scope carve-out exactly: mock credential store is a plain dict in `auth/repository.py`, no DB dependency; no frontend redirect logic added; no password hashing library added.
- `create_access_token` is called with `role.value` (a plain string), not the `Role` enum member itself, per Story 1.1's function signature.

### File List

- `backend/app/auth/repository.py` (modified — added `_MOCK_ACCOUNTS`, `find_account`; review fix: case-insensitive lookup)
- `backend/app/auth/schemas.py` (modified — added `LoginRequest`, `LoginResponse`)
- `backend/app/auth/service.py` (modified — added `authenticate`; review fix: `secrets.compare_digest`)
- `backend/app/auth/router.py` (modified — added `POST /login` route, first real endpoint in the project)
- `backend/tests/test_login.py` (new; review fixes: added case-insensitivity, empty-credentials, and missing-field regression tests)

## Change Log

- 2026-07-09: Implemented Story 1.4 — mock credential store, `authenticate()`, `POST /api/auth/login` route, all test-first, live-verified end-to-end via curl. 42/42 tests passing (33 pre-existing + 9 new). Status → review.
- 2026-07-09: Code review — **found and fixed a real bug** (case-sensitive email lookup rejected valid credentials like `Rita@Sails.example.com`, confirmed by 2 review layers and verified live via curl before and after the fix) plus 2 other patches (`secrets.compare_digest` replacing plain `!=` for password comparison; 2 new regression tests confirming empty-credentials and missing-field payloads were already safely handled, not 500s). 4 findings deferred to `deferred-work.md`, 9 dismissed (mostly speculative robustness against a 100% hardcoded, non-externally-sourced mock dict). 4 new tests added. 45/45 tests passing. Status → done.
