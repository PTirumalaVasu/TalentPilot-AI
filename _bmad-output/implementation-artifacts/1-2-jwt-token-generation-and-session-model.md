---
baseline_commit: 49717295952b97a4f420c1529d37d5ee83c2aad3
---

# Story 1.2: JWT Token Generation & Session Model

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **developer**,
I want to implement JWT token generation and validation within the auth module,
so that sessions can be created and verified securely.

## Acceptance Criteria

1. **AC1 — Token creation/validation utilities (pre-existing, verify only, no changes).** `core/security.py`'s `create_access_token(user_id, role)` / `decode_access_token(token)` already satisfy this: HS256, `user_id`+`role` claims, `exp` defaulting to `JWT_EXPIRATION_HOURS` (24h, configurable via env). Built and unit-tested in Story 1.1 — do not recreate or duplicate this logic in `auth/`.
2. **AC2 — Session cookie is set correctly.** A helper sets the JWT into a cookie with `httponly=True`, `samesite="lax"`, and a **configurable** `secure` flag (see Dev Notes — hardcoding `secure=True` breaks local plain-HTTP browser testing). Never stored in `localStorage` or a URL param.
3. **AC3 — Token validated on every protected request.** A FastAPI dependency extracts the JWT from the session cookie and validates signature + expiration on each call. Missing cookie, expired token, and invalid/tampered signature **all reject with 401 Unauthorized** — through the centralized error contract (raise `HTTPException(401, ...)`, do not hand-roll a response body).
4. **AC4 — Scope boundary: no role/user_id enum validation here.** This story's dependency returns the raw decoded payload (or 401) — it does **not** validate `role` against `{HR_ADMIN, EMPLOYEE}`, does not check `user_id` presence, and does not populate `request.state.current_user`. That is Story 1.3's job, layered on top of this story's dependency.

## Tasks / Subtasks

- [x] Task 1: Add cookie configuration to `core/config.py` (AC: #2)
  - [x] Add `COOKIE_SECURE: bool = True` (default matches architecture's stated intent; overridden to `False` in local `.env` for plain-HTTP dev — see Dev Notes)
  - [x] Add `SESSION_COOKIE_NAME: str = "access_token"`
  - [x] Document both in `backend/.env.example` with a comment explaining the local-HTTP caveat
- [x] Task 2: Session cookie set helper (AC: #2)
  - [x] `auth/service.py`: `set_session_cookie(response: Response, token: str) -> None` calling `response.set_cookie(key=settings.SESSION_COOKIE_NAME, value=token, httponly=True, secure=settings.COOKIE_SECURE, samesite="lax", max_age=settings.JWT_EXPIRATION_HOURS * 3600, path="/")`
  - [x] No cookie-clearing helper added — Story 1.5 owns that explicitly
- [x] Task 3: Token-validation dependency (AC: #3, #4)
  - [x] `auth/service.py`: `get_current_token_payload(request: Request) -> dict` — reads `request.cookies.get(settings.SESSION_COOKIE_NAME)`; if absent, raises `HTTPException(401, "No active session")`; else `decode_access_token(token)` inside `try/except jwt.PyJWTError`, raising `HTTPException(401, "Invalid or expired session")` on any decode failure; on success returns the decoded payload dict as-is (no role/user_id checks — AC4)
- [x] Task 4: Tests (AC: #2, #3, #4)
  - [x] Unit tests: `set_session_cookie` produces `HttpOnly`/`SameSite=lax` always, and `Secure` conditionally on `COOKIE_SECURE` (both True and False cases tested — the singleton loads `False` from local `.env` by design, so the True case is tested via `monkeypatch`)
  - [x] Integration tests (temporary protected route in `test_auth_service.py`, following Story 1.1's `_build_test_app_with_handlers` pattern — `main.py` untouched): missing cookie → 401; expired token → 401; tampered token → 401; valid token → 200 with payload accessible
  - [x] All 401s assert the centralized error contract shape (`{status, code, message, timestamp}`)

### Review Findings

- [x] [Review][Patch] Cookie tests don't assert `Max-Age`/`Path` attributes despite `set_session_cookie` explicitly setting both [backend/tests/test_auth_service.py] — fixed: assertions added to `test_set_session_cookie_sets_expected_attributes`
- [x] [Review][Patch] No test exercises `SESSION_COOKIE_NAME` configurability — every test hardcodes the literal `"access_token"` instead of the setting [backend/tests/test_auth_service.py] — fixed: `test_set_session_cookie_uses_configured_cookie_name` + `test_get_current_token_payload_uses_configured_cookie_name` added
- [x] [Review][Patch] No test for a malformed/non-JWT-shaped cookie value (garbage, empty string, wrong segment count) — behavior verified correct empirically during review (`PyJWT` wraps all as `DecodeError`→401) but no permanent regression test exists [backend/tests/test_auth_service.py] — fixed: `test_malformed_cookie_value_returns_401` added
- [x] [Review][Defer] Cookie `Max-Age` is tied to global `settings.JWT_EXPIRATION_HOURS`, independent of any per-token custom expiry (`create_access_token`'s `expires_in_hours` override) [backend/app/auth/service.py] — deferred, matches this story's AC2 exactly as specified; revisit only if a future story needs variable-expiry tokens (e.g. "remember me") paired with this cookie helper
- [x] [Review][Defer] `JWT_EXPIRATION_HOURS` has no bounds check (0/negative produces a degenerate cookie `Max-Age`) [backend/app/core/config.py] — deferred, duplicate of an existing Story 1.1 deferred item in `deferred-work.md`
- [x] [Review][Defer] Both 401 failure paths (missing cookie vs. invalid/expired token) collapse to the same generic `HTTP_ERROR` response code, giving frontend code nothing but a message-string match to distinguish them [backend/app/auth/service.py] — deferred, a real API-design enhancement but requires redesigning Story 1.1's whole error-contract scheme (per-exception-type error codes), out of this story's AC scope
- [x] [Review][Defer] No CSRF mitigation or discussion for the new cookie-based session mechanism (`SameSite=Lax` reduces but doesn't eliminate exposure) [backend/app/auth/service.py] — deferred, no source document (PRD/architecture spine) currently specifies a CSRF requirement; flag at the architecture level before Story 1.4 (login) ships a real state-changing endpoint using this cookie
- [x] [Review][Defer] `decode_access_token` uses zero clock-skew leeway (`jwt.decode` supports a `leeway=` param) [backend/app/core/security.py] — deferred, this story's own AC1/Dev Notes explicitly say not to touch `core/security.py`; flag for whoever next modifies that file

## Dev Notes

- **`core/security.py`'s `create_access_token`/`decode_access_token` already exist from Story 1.1 and are fully unit-tested** (round-trip, expired raises `jwt.ExpiredSignatureError`, tampered raises `jwt.InvalidSignatureError`, HS256-only). This story consumes them — it does not touch `core/security.py`. If you find yourself writing JWT encode/decode logic in `auth/`, stop: it already exists.
- **Real tension worth being deliberate about: `secure=True` on a cookie means the browser will not send it back over plain HTTP.** This project's local dev loop (`uvicorn` + Vite, no TLS) runs entirely over `http://localhost`. If `secure` is hardcoded `True`, the session will validate fine in `httpx`/`ASGITransport` tests (which don't enforce browser-grade Secure/HTTPS semantics) while silently never round-tripping in a real browser during actual local testing — a classic "tests green, feature dead" trap. Make it a `COOKIE_SECURE` setting (default `True` to match the architecture's stated production intent) and call out in `.env.example` that local manual/browser testing needs `COOKIE_SECURE=False` in `.env`.
- **`SameSite` policy isn't locked by any source document** — `addendum.md` only says "HttpOnly/Secure/SameSite cookie, not localStorage," without naming Lax vs Strict. `"lax"` is used here as the standard safe default (survives a top-level post-login redirect); this is a reasonable assumption, not a binding spec — flag it as such if this ever needs revisiting.
- **Do not implement role/user_id validation here (AC4).** Story 1.3 ("Role & Identity Scoping on Every Request") explicitly owns extracting/validating `role` against the `{HR_ADMIN, EMPLOYEE}` enum, checking `user_id` presence for EMPLOYEE sessions, and populating `request.state.current_user` — including its own specific 401/403/400 edge cases (missing role claim, invalid role value, EMPLOYEE missing `user_id`). Building any of that here would be rework the moment Story 1.3 lands. This story's dependency only proves cryptographic/temporal validity of the token — nothing about its claims' business meaning.
- **Do not wire a real `/login` endpoint or a permanent protected route into `main.py` in this story** — Story 1.4 ("Login Endpoint & Credential Store") owns issuing real tokens from real credentials. Test this story's helpers the same way Story 1.1 tested `core/errors.py`: build a temporary, test-file-local FastAPI app/route (see `backend/tests/test_main.py`'s `_build_test_app_with_handlers` for the established pattern) rather than touching `app/main.py`.
- **Raise `HTTPException`, don't hand-build a response.** Story 1.1's code review added a `StarletteHTTPException` handler to `core/errors.py` specifically so that `raise HTTPException(401, "...")` anywhere in the app automatically renders through the centralized `{status, code, message, timestamp}` contract. Use that — do not construct a `JSONResponse` manually in this story's dependency.
- **No new dependencies needed.** `PyJWT` (decode/encode) and FastAPI's own `Response.set_cookie`/`Request.cookies` are already sufficient and already installed (Story 1.1). Do not add `itsdangerous`, `fastapi-jwt-auth`, or similar — that would be an unrequested library addition requiring separate approval.

### Project Structure Notes

- New code in this story lives in `backend/app/auth/service.py` (the module's "session/role gate dependency" home per the architecture spine's source-tree comment) and `backend/app/core/config.py` (new settings). No new files needed — both modules already exist as stubs from Story 1.1.
- `auth/router.py`, `auth/repository.py`, `auth/models.py`, `auth/schemas.py` remain untouched stubs this story — Story 1.4 is the first to give `auth/router.py` a real route.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.2: JWT Token Generation & Session Model] — acceptance criteria origin
- [Source: _bmad-output/planning-artifacts/architecture/architecture-TalentPilot-AI-2026-07-09/ARCHITECTURE-SPINE.md#AD-6] — server-side session/role/identity gate invariant (this story implements the token-validity half; Story 1.3 implements the role/identity half)
- [Source: _bmad-output/planning-artifacts/architecture/architecture-TalentPilot-AI-2026-07-09/ARCHITECTURE-SPINE.md#Consistency Conventions] — "JWT in HttpOnly/Secure/SameSite cookie, verified server-side per request (AD-6)"
- [Source: _bmad-output/planning-artifacts/prds/prd-TalentPilot-AI-2026-07-09/addendum.md#Technical Stack (locked)] — "JWT in an HTTP-only/Secure/SameSite cookie, not localStorage"
- [Source: _bmad-output/implementation-artifacts/1-1-project-structure-and-core-dependencies.md] — previous story: `core/security.py` implementation this story builds on, and the `StarletteHTTPException` → centralized error contract pattern this story must use
- [Source: _bmad-output/implementation-artifacts/sprint-status.yaml] — story key `1-2-jwt-token-generation-and-session-model`

## Library/Framework Requirements

No new dependencies. Reuses what Story 1.1 already installed and verified working on this environment's Python (3.14, see `backend/requirements.txt`):

| Package | Version (already pinned) | Used for |
| --- | --- | --- |
| `pyjwt` | 2.13.0 | `jwt.PyJWTError` catch-all for decode failures |
| `fastapi` | 0.139.0 | `Response.set_cookie`, `Request.cookies`, `HTTPException` |

## Testing Requirements

- Unit test: `Set-Cookie` header attributes (`HttpOnly`, `SameSite=lax`, `Secure` when `COOKIE_SECURE=True`) — no DB dependency.
- Integration tests via a temporary test-file-local route (not `main.py`): missing cookie → 401; expired token → 401; tampered token → 401; valid token → 200. Follow Story 1.1's `_build_test_app_with_handlers` pattern in `backend/tests/test_main.py`.
- All 401 responses must assert the centralized error contract shape, not FastAPI's default `{"detail": ...}`.
- Do not write `/login` or DB-backed tests — Stories 1.4/1.7 own those respectively.
- Test framework: `pytest` + `httpx`, consistent with Story 1.1.

## Previous Story Intelligence

From Story 1.1 (`1-1-project-structure-and-core-dependencies.md`, status `done`):
- `core/security.py` already provides `create_access_token(user_id, role, expires_in_hours=None)` and `decode_access_token(token)`, both HS256-only, fully unit-tested — this story must not duplicate them.
- `core/errors.py` already has a `StarletteHTTPException` handler (added during that story's code review) that renders any `HTTPException` through `{status, code, message, timestamp}` — this story's 401s should be raised as plain `HTTPException` and rely on that handler, not construct their own response shape.
- Established test pattern: build isolated test-file-local FastAPI apps/routes for exercising auth/error behavior rather than adding debug/placeholder routes to `app/main.py` (see `_build_test_app_with_handlers` in `backend/tests/test_main.py`).
- Environment note carried forward: this sandbox's only Python is 3.14; if package versions ever need bumping, re-verify `cp314` wheel availability first (Story 1.1 hit this with `pydantic-core`).
- Code review in this project runs 3 parallel adversarial layers (Blind Hunter, Edge Case Hunter, Acceptance Auditor) and has already caught real issues in Story 1.1 (unconfigurable CORS, missing HTTPException handling, silent exception swallowing, leaked validation internals, unfriendly config-error tracebacks) — expect similar scrutiny on cookie security flags in this story.

## Git Intelligence Summary

Recent commits (`git log --oneline -5`): `4971729 Implement Story 1.1: project structure and core dependencies (#25)`, `71f3501` (same, pre-merge), `974a1ee`/`e7755d9` (sprint-status generation), `114d143` (readiness assessment fixes). Pattern established: one implementation commit per story with a descriptive multi-paragraph body covering what was built and what code review fixed, PR merged via GitHub (`#N` suffix), `backend/` already exists on `main` with the full Story 1.1 module skeleton intact — this story branches from that, not from scratch.

## Dev Agent Record

### Agent Model Used

claude-sonnet-5

### Debug Log References

- `backend/.venv/Scripts/python.exe -m pytest tests/ -v` → 19 passed (full suite, final run)
- Confirmed red before each implementation: `test_cookie_settings_defaults` failed with `AttributeError` before `core/config.py` had the new fields; `test_auth_service.py` failed at collection with `ImportError` before `auth/service.py` had the new functions
- Live `uvicorn app.main:app` boot on port 8125 after implementation, `GET /` → `200 {"status":"ok"}` — no regressions

### Completion Notes List

- Implemented both new pieces test-first: wrote failing tests for `COOKIE_SECURE`/`SESSION_COOKIE_NAME` config fields and for `set_session_cookie`/`get_current_token_payload`, confirmed red, then implemented to green.
- Hit and fixed two self-inflicted test bugs during TDD (both caught before considering the task done, not left in): (1) `test_cookie_settings_defaults` initially asserted `COOKIE_SECURE is True` against the process-wide `settings` singleton, which correctly loads `False` from the local `.env` (per this story's own AC2 design) — fixed by testing the class default via `load_settings(_env_file=None)` instead of the singleton; (2) same root cause for `test_set_session_cookie_sets_expected_attributes` — fixed by `monkeypatch`-ing `COOKIE_SECURE` explicitly per test case (added a second test for the `False` case too, for symmetry).
- Followed Story 1.1's established test pattern exactly: exercised `get_current_token_payload` via a temporary, test-file-local FastAPI app/route in `test_auth_service.py`, not by adding anything to `app/main.py` — `auth/router.py` remains an empty stub, correctly deferred to Story 1.4.
- Scope boundaries from Dev Notes were honored: no role/`user_id` enum validation added (`get_current_token_payload` returns the raw decoded payload dict), no cookie-clearing helper added (Story 1.5's job), no real `/login` route wired (Story 1.4's job).
- `backend/.env` (local, git-ignored) was updated with `COOKIE_SECURE=False` — deliberate, documented in-file, since this sandbox's dev loop runs over plain HTTP with no TLS.

### File List

- `backend/app/core/config.py` (modified — added `SESSION_COOKIE_NAME`, `COOKIE_SECURE`)
- `backend/app/auth/service.py` (modified — added `set_session_cookie`, `get_current_token_payload`)
- `backend/.env.example` (modified — documented new vars + local-HTTP caveat)
- `backend/.env` (modified, git-ignored — `SESSION_COOKIE_NAME`, `COOKIE_SECURE=False`)
- `backend/tests/test_config.py` (modified — added `test_cookie_settings_defaults`)
- `backend/tests/test_auth_service.py` (new)

## Change Log

- 2026-07-09: Implemented Story 1.2 — cookie configuration, `set_session_cookie`, `get_current_token_payload` dependency, all test-first. 19/19 tests passing (13 pre-existing + 6 new). Status → review.
- 2026-07-09: Code review — 3 patch findings applied (`Max-Age`/`Path` cookie-attribute assertions added, `SESSION_COOKIE_NAME` configurability now tested, malformed/garbage cookie value now has a permanent regression test), 5 findings deferred to `deferred-work.md`, 10 dismissed (2 verified empirically as false positives — malformed input already correctly raises `PyJWTError`→401, confirmed by direct interpreter check, not just review inference). 4 new tests added. 22/22 tests passing. Status → done.
