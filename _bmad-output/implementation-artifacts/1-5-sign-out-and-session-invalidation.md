---
baseline_commit: 1bab6a094499448194402f4288e7a22d9f0c4fca
---

# Story 1.5: Sign Out & Session Invalidation

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an **HR Admin or Employee**,
I want to sign out,
so that my session is terminated and no one else can use my session token.

## Scope Notes (read before starting)

1. **Backend scope only — no frontend exists yet.** The epic's "I am redirected to the login page" and "if I use the browser back button, I cannot access a previously-open protected page" are frontend routing/cache-control behaviors (page navigation, `bfcache`). There is no frontend project in this repo (same situation Story 1.4 documented). This story's job ends at making the session cookie actually invalid server-side; a future frontend must (a) redirect to `/login` on receiving a 401, and (b) set `Cache-Control: no-store` on protected pages so the back button can't replay a cached render. Do not build frontend routing.
2. **"Even if the token itself hasn't expired yet" requires real server-side revocation, not just cookie clearing.** A JWT is self-contained and stateless — if you only delete the cookie, a copy of the raw token string (e.g. replayed manually via `curl -H "Cookie: access_token=<old token>"`) would still decode successfully and pass `get_current_token_payload` until its `exp` naturally elapses. The epic AC explicitly calls this out ("even if the token itself hasn't expired yet"), so cookie-clearing alone does not satisfy AC2 — you must also make the server reject that exact token string going forward. No source document (PRD, architecture spine, addendum) specifies *how*; the approach below is this story's own design decision, sized for this project's constraints (single local uvicorn process, no Redis — Story 1.1 already decided against a Redis service since nothing else calls for it).
3. **Sign out must be safe to call in any session state — that's a deliberate choice, not an oversight.** No `Depends(get_current_user)` / `Depends(get_current_token_payload)` gate on the logout route. If there's no cookie, or an already-expired/garbage one, logout still succeeds (204) and clears whatever cookie name is configured. This mirrors real sign-out UX (a stale tab's "Sign Out" button must still work) and keeps the endpoint idempotent — calling it twice in a row is not an error.

## Acceptance Criteria

1. **AC1 — Sign out invalidates the session server-side, not just client-side.** `POST /api/auth/logout` records the presented token (if any) as revoked, so a subsequent request presenting that *exact same token string* — even though its JWT `exp` hasn't elapsed — is rejected with 401 Unauthorized by `get_current_token_payload` (and therefore by everything built on top of it, e.g. `get_current_user`).
2. **AC2 — The response clears the session cookie (deleted, not just left to expire).** The `Set-Cookie` header on the logout response removes the cookie (`Max-Age=0` / an expiry in the past, empty value) using the **same** `key`, `path`, `httponly`, `secure`, and `samesite` attributes `set_session_cookie` (Story 1.2) used to set it — mismatched attributes mean a real browser won't actually delete it.
3. **AC3 — Logout is idempotent and safe with no active session.** Calling `POST /api/auth/logout` with no cookie present, or with an already-expired/invalid cookie value, still returns 204 (no error) and still clears the cookie header. Calling it twice in a row is not an error.
4. **AC4 — Revocation is per-token, not per-user.** After logout, the same user can log in again via `POST /api/auth/login` and receive a **new** token that works normally (a fresh login is a different token — different `iat`/signature — and is not affected by the previous token's revocation).
5. **AC5 — No response body leaks anything.** Logout returns `204 No Content` — no JSON body, no echoing of the revoked token or user identity.

## Tasks / Subtasks

- [x] Task 1: Server-side token revocation (AC: #1, #4)
  - [x] `auth/service.py`: add a module-level `_revoked_tokens: set[str] = set()`
  - [x] `auth/service.py`: add `logout(request: Request, response: Response) -> None` — reads the raw token string from the configured session cookie (`request.cookies.get(settings.SESSION_COOKIE_NAME)`); if present, adds it to `_revoked_tokens`; then deletes the cookie on `response` (see Task 2 for exact attributes)
  - [x] `auth/service.py`: in `get_current_token_payload`, after extracting the token and **before** (or instead of) decoding, reject if `token in _revoked_tokens` with `HTTPException(401, "Session has been signed out")` — this single check point means `get_current_user` inherits the rejection automatically, no changes needed there
- [x] Task 2: `POST /api/auth/logout` route (AC: #2, #3, #5)
  - [x] `auth/router.py`: new route, `status_code=204`, takes `request: Request, response: Response`, calls `logout(request, response)`, returns nothing
  - [x] Cookie deletion must mirror `set_session_cookie`'s attributes exactly: `key=settings.SESSION_COOKIE_NAME`, `path="/"`, `httponly=True`, `secure=settings.COOKIE_SECURE`, `samesite="lax"` (use `Response.delete_cookie(...)`, Starlette's built-in — do not hand-roll an expiry header)
  - [x] No `Depends` auth gate on this route (Scope Note 3) — do not require a valid session to sign out
- [x] Task 3: Prevent cross-test flakiness from the new global revoked-token state (AC: test correctness, not a product AC — see Dev Notes)
  - [x] `tests/conftest.py`: add an autouse fixture that clears `app.auth.service._revoked_tokens` before and after every test
- [x] Task 4: Tests (AC: #1, #2, #3, #4, #5)
  - [x] New `tests/test_logout.py`, tested against the real `app` (`from app.main import app`), same pattern as `test_login.py`
  - [x] Logout clears the cookie: `Set-Cookie` header shows `Max-Age=0` (or a past `expires`) and `Path=/` for the configured cookie name
  - [x] **Core AC1 proof**: login via the real app to get a genuine token; capture the raw token string; call logout; then present that *exact same token string* to a protected route (build a test-file-local `/protected` route depending on `get_current_token_payload`, same pattern as `test_auth_service.py`'s `_build_protected_test_app`) on a **fresh** client — assert 401. (Do not rely on httpx's automatic cookie jar for this assertion — it will drop the deleted cookie on its own, which proves nothing about server-side revocation. Manually set the old token string on a separate client instance.)
  - [x] Logout with no prior login (no cookie at all) → 204, no error
  - [x] Logout called twice in a row → both calls 204
  - [x] After logout, logging in again as the same user succeeds and the new token works against a protected route (proves per-token, not per-user, revocation)
  - [x] Logout response body is empty (204, no JSON)

### Review Findings

- [x] [Review][Defer] Same-second token collision can violate AC4 — `backend/app/auth/service.py:49` (revocation check) + `backend/app/core/security.py:16-17` (`create_access_token`'s whole-second `iat`/`exp`, no `jti`). Verified empirically by two independent review layers: two logins for the same `user_id`+`role` within the same wall-clock second produce a byte-identical JWT, so signing out one session silently revokes a concurrent sibling (e.g. two tabs opened together) — a real violation of AC4's "a fresh login... is not affected by the previous token's revocation" guarantee, not just a test-flakiness hazard. `test_logging_in_again_after_logout_issues_a_working_new_session` (`backend/tests/test_logout.py:126`) sleeps 1.1s specifically to dodge this exact window rather than proving AC4 holds through it. **Decision (2026-07-09):** accepted as a documented limitation — deferred, pre-existing-scope tradeoff. Reason: local single-process, five-user demo pilot; the odds of two same-second logins by the same user are low and the impact (an unexpected re-login) is minor, while fixing it would require touching `core/security.py` against this story's own explicit "don't touch" scope note.
- [x] [Review][Patch] AC2 test coverage gap: deleted-cookie attributes not asserted [backend/tests/test_logout.py:56-67] — `test_logout_clears_session_cookie` only asserted the cookie name, `Max-Age=0`, and `Path=/`; it never asserted `HttpOnly` or `SameSite=lax`, even though AC2 explicitly requires attribute parity with `set_session_cookie` and `test_login.py:46` already asserts `HttpOnly` for the equivalent set-cookie case. Implementation (`service.py:63-69`) was already correct; the test's proof was thin. **Fixed:** added `assert "HttpOnly" in set_cookie` and `assert "samesite=lax" in set_cookie.lower()`. Verified: 6/6 `test_logout.py` passing.
- [x] [Review][Patch] "Core AC1 proof" test asserts too little [backend/tests/test_logout.py:110-113] — `test_old_token_rejected_after_logout_even_though_not_expired` only checked `status_code == 401` and `json()["status"] == "error"`, never the actual message (`"Session has been signed out"`). As written it couldn't distinguish real server-side revocation from the cookie simply never arriving — exactly the class of bug this story's own Completion Notes describe hitting once during development (the `Secure`-cookie/plain-HTTP mismatch). **Fixed:** added `assert response.json()["message"] == "Session has been signed out"`. Verified: 6/6 `test_logout.py` passing.
- [x] [Review][Patch] Stale comment in `_login()` test helper [backend/tests/test_logout.py:42-49] — claimed "`COOKIE_SECURE` defaults True (no `backend/.env` in this checkout)", but a gitignored `backend/.env` (`COOKIE_SECURE=False`) already exists locally per this story's own Dev Agent Record. Cosmetic only (the manual `client.cookies.set(...)` already made the test pass regardless of the flag's value) but misled future readers. **Fixed:** reworded to note the value varies by checkout instead of asserting a specific default.
- [x] [Review][Defer] Unbounded, unauthenticated growth of `_revoked_tokens` [backend/app/auth/service.py:21,58-61] — deferred, pre-existing framing refined
- [x] [Review][Defer] Cookie attributes hand-duplicated between `set_session_cookie` and `logout`'s `delete_cookie` call [backend/app/auth/service.py:32-41,63-69] — deferred, pre-existing
- [x] [Review][Defer] Third near-duplicate `_build_protected_test_app()` test helper [backend/tests/test_logout.py:16-27] — deferred, pre-existing

## Dev Notes

- **Why cookie-clearing alone is insufficient, restated:** this is the crux of the story. `get_current_token_payload` currently trusts any cryptographically-valid, unexpired JWT — it has no concept of "this session was ended." Without a revocation check, "sign out" would only be a client-side courtesy that a compliant browser happens to follow; a copied-out token would keep working. AC1's "even if the token itself hasn't expired yet" phrasing is the tell — implement the in-memory revoked-token check, don't stop at cookie deletion.
- **Non-obvious test hazard — read before writing tests:** `create_access_token` (Story 1.1, `core/security.py`) encodes `iat`/`exp` as whole-second Unix timestamps. Two calls to `create_access_token(user_id="casey", role="EMPLOYEE")` within the same wall-clock second produce a **byte-identical token** (same header, payload, signature). Because `_revoked_tokens` is a module-level global that persists for the life of the test process, if Test A revokes a `casey`/`EMPLOYEE` token and Test B independently mints a `casey`/`EMPLOYEE` token in the same second, Test B's "fresh" token can already be sitting in `_revoked_tokens` — a flaky, order-dependent failure that has nothing to do with a real bug. This is exactly why Task 3's autouse `conftest.py` fixture is not optional polish — without it, this story's own tests (and potentially pre-existing ones, once revocation exists) can intermittently fail for a reason that looks like a logout bug but isn't.
- **Where the revocation check goes matters.** Put it in `get_current_token_payload` (checked before/alongside decode), not in `get_current_user`. `get_current_user` is built as a `Depends(get_current_token_payload)` layer on top (Story 1.3) — a single check in the lower layer is inherited everywhere for free, consistent with this codebase's existing "one gate" pattern (AD-6) rather than duplicating the check.
- **Known, accepted MVP limitation — flag, don't fix:** `_revoked_tokens` is an in-memory, per-process `set`. It is wiped on every app restart (previously-revoked-but-still-unexpired tokens become valid again after a restart) and has no pruning of entries whose `exp` has already passed (unbounded-but-tiny growth — bounded by logout actions during a single dev/demo run, five users, no persistence). This matches the architecture's local-single-process scope (AR-15, AR-16; Story 1.1's "no Redis service" decision) and is the same category of pragmatic, explicitly-documented tradeoff as the project's existing accepted risks (no CSRF token, no rate limiting on `/login`). Do not build a DB-backed or Redis-backed revocation store for this story — nothing in the PRD or architecture asks for one, and `accounts`/session tables don't exist yet (Story 1.7 is still backlog).
- **CSRF note (visibility, not a new requirement):** `/logout` is now the second cookie-authenticated, state-changing POST endpoint after `/login`. The existing CSRF deferred item (logged against Story 1.2, "revisit at first real state-changing endpoint") already covers this; no new mitigation is required here since no source document specifies one, but it's worth a one-line mention in this story's Change Log/deferred notes so the running list stays accurate.
- **Don't touch `core/security.py`.** This design deliberately avoids adding a `jti` claim or otherwise changing `create_access_token`/`decode_access_token` — revocation works by tracking the raw token *string*, which the logout handler already has from the cookie. No changes needed to token creation/decoding at all.

### Project Structure Notes

- Changes land in `auth/service.py` (new `_revoked_tokens` set + `logout()`; revocation check added to `get_current_token_payload`), `auth/router.py` (new `POST /logout` route), `tests/conftest.py` (new autouse fixture), and a new `tests/test_logout.py`. No changes to `main.py` (the `/api/auth` prefix mount already exists) and no changes to `core/security.py`, `auth/schemas.py`, or `auth/repository.py`.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.5: Sign Out & Session Invalidation] — full AC text
- [Source: _bmad-output/implementation-artifacts/1-2-jwt-token-generation-and-session-model.md] — `set_session_cookie`'s exact cookie attributes this story's cookie-deletion must mirror
- [Source: _bmad-output/implementation-artifacts/1-3-role-and-identity-scoping-on-every-request.md] — `get_current_user` layering on top of `get_current_token_payload`, why the revocation check belongs in the lower layer
- [Source: _bmad-output/implementation-artifacts/1-4-login-endpoint-and-credential-store-mock-for-mvp.md] — established pattern of testing real, permanent routes against `from app.main import app`; "no frontend exists yet" scope precedent
- [Source: _bmad-output/implementation-artifacts/deferred-work.md#Deferred from: consolidated code review of Stories 1.2, 1.3, 1.4] — pre-existing CSRF and `SameSite=Lax` deferred items this story's new endpoint adds visibility to, and the explicit note that "no logout endpoint exists because that's Story 1.5" confirming this was already anticipated as the next story
- [Source: _bmad-output/planning-artifacts/architecture/architecture-TalentPilot-AI-2026-07-09/ARCHITECTURE-SPINE.md#AD-6] — server-side session/role/identity gate on every request; single-gate enforcement pattern
- [Source: backend/app/auth/service.py] — current `get_current_token_payload`, `set_session_cookie`, `get_current_user` implementations this story extends

## Library/Framework Requirements

No new dependencies. Uses Python's built-in `set`, FastAPI's `Request`/`Response` injection, and Starlette's `Response.delete_cookie` (already available via the installed `fastapi`/`starlette`).

## Testing Requirements

- Test against the real `app` (`from app.main import app`) for the route-level behavior, following `test_login.py`'s established pattern.
- For the AC1 revocation proof specifically, combine the real app (to get a genuine login + logout) with a test-file-local `/protected` route depending on `get_current_token_payload` (the pattern already used in `test_auth_service.py` and `test_current_user.py`) — both share the same underlying `app.auth.service` module state, so revocation set there is visible to both.
- Add the autouse `conftest.py` fixture (Task 3) clearing `_revoked_tokens` before/after each test — required for correctness, not optional.
- Test framework: `pytest` + `httpx` + `pytest-asyncio`, consistent with prior stories.

## Previous Story Intelligence

From Story 1.4 (`1-4-login-endpoint-and-credential-store-mock-for-mvp.md`, status `done`):
- Established the precedent that a real, permanent route is tested against the actual `app` object, not a temporary test-file-local app — this story's `test_logout.py` follows that same pattern for the route-level tests, while still using the test-file-local-app pattern (from `test_auth_service.py`/`test_current_user.py`) specifically for the AC1 revocation proof, since no real protected endpoint exists yet to call after logout (`assignments/`, `content/`, `progress/`, `dashboard/` routers are all still empty `APIRouter()` stubs — confirmed by reading them directly).
- Reinforces: don't add speculative hardening (rate limiting, CSRF tokens, email format validation) that no AC or source document actually asks for — the deferred-work ledger already tracks known gaps for later, revisited together rather than fixed piecemeal per story.
- `deferred-work.md`'s note from the Stories 1.2–1.4 consolidated review explicitly names this story ("no logout endpoint exists because that's Story 1.5, the very next story in the backlog") — confirms `get_current_user`/`request.state.current_user` being currently unused elsewhere is expected, not a gap this story needs to address.

## Git Intelligence Summary

Recent commits: `1bab6a0 Implement Stories 1.2-1.4: JWT sessions, role scoping, login endpoint (#27)` (merged to `main`). Pattern established: one implementation commit per story (or small batch) with a descriptive body, PR merged via GitHub, sprint-status.yaml updated alongside. This story should follow the same one-story-per-branch/PR pattern (e.g. `feature/story1.5`) unless the user directs otherwise.

## Dev Agent Record

### Agent Model Used

claude-sonnet-5

### Debug Log References

- `backend/.venv/Scripts/python.exe -m pytest tests/test_logout.py -v` → red: 5/6 failed (404, no route existed yet); after implementation: 6/6 passed
- `backend/.venv/Scripts/python.exe -m pytest tests/ -v` → 51/51 passed (full suite, final run; 45 pre-existing + 6 new)
- Live end-to-end verification via `curl` against a running `uvicorn` instance (temporary local `.env` created, gitignored, `COOKIE_SECURE=False` for plain-HTTP curl testing): login → 200 with `Set-Cookie`; logout with that session → 204 with `Set-Cookie: access_token=""; expires=<past>; HttpOnly; Max-Age=0; Path=/; SameSite=lax`; logout with no cookie at all → 204 (idempotent); logout called twice in a row → 204, 204; fresh login as the same user after logout → 200 with a new working session. AC1's specific "old token rejected server-side" behavior has no live protected endpoint to demonstrate against yet (`assignments/`, `content/`, `progress/`, `dashboard/` routers are still empty stubs — confirmed by reading them), so that behavior is verified by `test_old_token_rejected_after_logout_even_though_not_expired` (pytest, test-file-local protected route) rather than live `curl` — consistent with how Story 1.2/1.3 verified pre-route dependency behavior before real protected routes existed.

### Completion Notes List

- Implemented server-side token revocation exactly as scoped: `auth/service.py` gained a module-level `_revoked_tokens: set[str]` and a `logout()` function; `get_current_token_payload` now rejects any token present in that set before attempting to decode it. `get_current_user` needed no changes — it inherits the rejection through its existing `Depends(get_current_token_payload)` layering, confirmed by the passing revocation test.
- `core/security.py` was not touched, per the story's explicit instruction — no `jti` claim was added; revocation keys off the raw token string already available from the cookie.
- `POST /api/auth/logout` (`auth/router.py`) has no auth dependency gate, is idempotent, and always clears the cookie with attributes mirroring `set_session_cookie` exactly (`path="/"`, `httponly=True`, `secure=settings.COOKIE_SECURE`, `samesite="lax"`), via Starlette's `Response.delete_cookie`.
- Added the autouse `tests/conftest.py` fixture clearing `_revoked_tokens` before/after every test, per Task 3 — required, not optional, given the whole-second-precision token-collision hazard the story's Dev Notes called out.
- **Found and fixed a real bug in my own first draft of the tests, not in the product code**: my initial `_login()` test helper relied on httpx's automatic cookie jar to resend the session cookie on a follow-up request within the same client. Since `settings.COOKIE_SECURE` defaults to `True` and this checkout has no `backend/.env`, the cookie is `Secure`-flagged, and a spec-compliant HTTP client (httpx included) will not resend a `Secure` cookie over the plain-`http://test` ASGI transport used by these tests — so `request.cookies` inside `logout()` never actually saw the token, and the very first run of the core AC1 test failed with `200` instead of `401`. Root-caused via a standalone debug script (not guessed), then fixed by having `_login()` parse the token directly out of the `Set-Cookie` response header and explicitly re-set it on the client's cookie jar (matching the existing `client.cookies.set(...)` pattern already used in `test_auth_service.py`/`test_current_user.py`), rather than depending on automatic jar persistence. This is a test-infrastructure fix only — no product code changed as a result.
- A second, related hazard surfaced while fixing the above: explicitly setting a cookie via `client.cookies.set(...)` on top of one the jar already populated automatically (with a different implicit domain) produced an `httpx.CookieConflict: Multiple cookies exist with name=access_token` on a later `.get()` call. Fixed by having `_login()` call `client.cookies.clear()` before setting the token explicitly, so each login leaves exactly one unambiguous cookie in the jar.
- For live `curl` verification, created a local, gitignored `backend/.env` (`COOKIE_SECURE=False`, matching `.env.example`'s own documented guidance for local plain-HTTP testing) — this file does not exist elsewhere in the repo/checkout and was not present before this story; noting it here since a fresh clone will need the same step before `uvicorn` can boot (fails fast with a clear message otherwise, per Story 1.1's `load_settings` error handling).
- All 5 acceptance criteria verified: AC1 (pytest, live protected-route stand-in), AC2/AC3/AC5 (pytest + live curl), AC4 (pytest + live curl).

### File List

- `backend/app/auth/service.py` (modified — added `_revoked_tokens`, `logout()`; added revocation check inside `get_current_token_payload`)
- `backend/app/auth/router.py` (modified — added `POST /logout` route)
- `backend/tests/conftest.py` (modified — added autouse `_clear_revoked_tokens` fixture)
- `backend/tests/test_logout.py` (new — 6 tests covering AC1–AC5)

## Change Log

- 2026-07-09: Implemented Story 1.5 — server-side token revocation (`_revoked_tokens` set, checked in `get_current_token_payload`), `POST /api/auth/logout` route (idempotent, no auth gate, mirrors `set_session_cookie`'s cookie attributes on deletion), autouse test-isolation fixture for the new global state. TDD: tests written first and confirmed red (404) before implementation. Found and fixed a self-inflicted test bug (not a product bug) caused by `COOKIE_SECURE` defaulting `True` with no local `.env` present, which silently prevented httpx from resending the session cookie across chained requests — fixed by parsing the token from the `Set-Cookie` header directly instead of relying on the automatic cookie jar. 51/51 tests passing (45 pre-existing + 6 new). Live-verified login/logout/re-login/idempotency end-to-end via `curl` against a running `uvicorn` instance. Status → `review`.
- 2026-07-09: CSRF exposure note (visibility only, no new mitigation): `/logout` is now the second cookie-authenticated, state-changing POST endpoint after `/login`, extending the existing CSRF deferred item logged against Story 1.2 — no source document requires mitigation yet, so none was added.
