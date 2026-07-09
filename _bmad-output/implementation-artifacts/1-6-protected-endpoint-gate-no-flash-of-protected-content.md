---
baseline_commit: adf1c2a
---

# Story 1.6: Protected Endpoint Gate — No Flash of Protected Content

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **developer**,
I want protected endpoints to reject unauthenticated requests before rendering any data,
so that no confidential Assignment/Content/Watch Progress data leaks before a redirect.

## Scope Notes (read before starting)

1. **Backend scope only — no frontend exists yet.** The epic's "frontend receives 401 and redirects to login" is frontend routing behavior. There is no frontend project in this repo (same precedent as Stories 1.4/1.5). This story's job ends at the server rejecting unauthenticated requests to the right routers; a future frontend must handle the redirect.
2. **`assignments/`, `content/`, `progress/`, and `dashboard/` routers are still empty `APIRouter()` stubs — zero real routes exist under them today.** Epic 2 (content), Epic 3 (assignments), Epic 4 (progress), and Epic 5 (dashboard) are what add real data endpoints later. **This story's job is to wire the AD-6 session gate onto these routers NOW, structurally, so that every route those future stories add is gated automatically** — closing a gap `deferred-work.md`'s consolidated Stories 1.2–1.4 review explicitly flagged: *"`get_current_user`/`request.state.current_user` are unused today because nothing exists yet to protect... Story 1.6 and Epic 2-5 are where this gets wired in, not a regression."* Do **not** build any real data endpoint in this story — that is out of scope.
3. **Reuse `get_current_user` (Story 1.3) as the gate — do not build a new/parallel auth mechanism.** It already composes `get_current_token_payload` (Story 1.2's JWT decode + Story 1.5's revocation check), so wiring it in gets expired-token rejection, tampered-signature rejection, and logged-out-token rejection for free, satisfying AD-6(a)/(b) with zero new logic.
4. **Do not add role-based restriction in this story** (e.g., making `dashboard/` HR-only). `get_current_user` accepts both `HR_ADMIN` and `EMPLOYEE` — that is correct here. Endpoint-specific authorization (e.g., "only HR_ADMIN may call this dashboard route") is the job of whichever Epic 2/3/4/5 story builds that specific endpoint, mirroring the split Story 1.3 already established between generic session/role validation (this layer) and endpoint-specific access rules (repository/service layer, later).
5. **Two FastAPI mechanisms could plausibly wire this gate — read Dev Notes for which one and why.** `APIRouter(dependencies=[...])` (module's own constructor) and `include_router(..., dependencies=[...])` (in `main.py`) were both empirically verified (this installed FastAPI, 0.139.0) to protect routes added to a router *after* it was included — this version's route resolution is lazy, not an eager one-time copy. Both work here. The story still picks one, for a discoverability reason, not a correctness one — see Dev Notes.

## Acceptance Criteria

1. **AC1 — The four protected routers declare the gate at construction.** `assignments/router.py`, `content/router.py`, `progress/router.py`, and `dashboard/router.py` each construct their router as `APIRouter(dependencies=[Depends(get_current_user)])`. `main.py`'s `app.include_router(...)` calls for these four are **not** changed to carry a `dependencies=` argument — not because it wouldn't work (it would; see Dev Notes), but to keep the gate visible in the same file as the routes it protects, per this codebase's "open one folder to understand a feature" convention (AD-1).
2. **AC2 — `auth/router.py` is explicitly excluded.** `auth_router` (`/login`, `/logout`) keeps `router = APIRouter()` with no dependency — unauthenticated users must still be able to log in.
3. **AC3 — Unauthenticated requests are rejected before the route handler runs.** A request to any route under a gated router, with no session cookie, returns 401 Unauthorized and the route handler body never executes. Proven via a diagnostic route added to a router built with the same `APIRouter(dependencies=[Depends(get_current_user)])` pattern, added to the router *after* construction — mirroring exactly how Epic 2–5 will add their real routes to the already-constructed `assignments_router`/`content_router`/etc. (No real data route exists yet to test this against directly — see Scope Note 2.)
4. **AC4 — The gate rejects the same failure modes `get_current_user` already rejects.** Expired token, signature-tampered/invalid token, and a revoked (logged-out, Story 1.5) token each return 401 through the router-level gate — proving it is the same validation chain, not a new one.
5. **AC5 — A valid, non-revoked session passes the gate.** The route handler executes, returns 200, and `request.state.current_user` is populated (per Story 1.3's existing contract).
6. **AC6 — No partial data or extra information leaks in the 401.** The 401 response uses the existing centralized error contract (`status`, `code`, `message`, `timestamp`) with no echoed request data — guaranteed structurally by the dependency raising before any handler code runs, not by new redaction logic.

## Tasks / Subtasks

- [x] Task 1: Wire the gate onto the four protected routers (AC: #1, #2)
  - [x] `backend/app/assignments/router.py`: extend the existing `from fastapi import APIRouter` line to `from fastapi import APIRouter, Depends`; add `from app.auth.service import get_current_user`; change `router = APIRouter()` to `router = APIRouter(dependencies=[Depends(get_current_user)])`
  - [x] `backend/app/content/router.py`: same change
  - [x] `backend/app/progress/router.py`: same change
  - [x] `backend/app/dashboard/router.py`: same change
  - [x] `backend/app/auth/router.py`: **no change** — left `router = APIRouter()` as-is
  - [x] `backend/app/main.py`: **no change** — no `dependencies=` added to any `include_router(...)` call
- [x] Task 2: Structural tests proving the real router objects are configured correctly (AC: #1, #2)
  - [x] New file `backend/tests/test_protected_router_gate.py`
  - [x] For each of `assignments_router`, `content_router`, `progress_router`, `dashboard_router`: import the real router object and assert `any(dep.dependency is get_current_user for dep in router.dependencies)`
  - [x] For `auth_router`: assert `auth_router.dependencies == []` — regression guard so a future edit can't silently gate `/login`/`/logout`
- [x] Task 3: Mechanism-proof tests for runtime behavior (AC: #3, #4, #5, #6)
  - [x] In the same test file, build an isolated FastAPI test app following the established `_build_protected_test_app`/`_build_current_user_test_app` pattern: construct `probe_router = APIRouter(dependencies=[Depends(get_current_user)])`, **then** add `@probe_router.get("/probe")` *after* construction (deliberately, to prove the dependency applies to routes registered later — the same order Epic 2–5 will follow), mount into a fresh `FastAPI()` app with `register_exception_handlers`
  - [x] No cookie → 401, error-contract body asserted (`status`, `code`, `timestamp` present, no leaked fields)
  - [x] Expired token → 401 (reuse `create_access_token(..., expires_in_hours=-1)`, same as `test_auth_service.py`)
  - [x] Tampered/invalid-signature token → 401 (reuse the signature-flip helper pattern from `test_auth_service.py`)
  - [x] Revoked (logged-out) token → 401 (mirror `test_logout.py`'s approach: mint a real token, revoke it, present it)
  - [x] Valid token → 200, handler body executed, response confirms `request.state.current_user` populated (mirror `test_current_user.py`'s `/whoami` pattern)
- [x] Task 4: Full regression run
  - [x] Run the full suite (`pytest backend/tests/`) — confirm all pre-existing tests still pass alongside the new file

### Review Findings

- [x] [Review][Patch] Hardcoded cookie name diverges from the established `settings.SESSION_COOKIE_NAME` convention [backend/tests/test_protected_router_gate.py:80,96,108,119] — all four mechanism-proof tests (`client.cookies.set("access_token", ...)`) hardcode the literal `"access_token"` instead of importing `settings.SESSION_COOKIE_NAME`, matching `test_auth_service.py`'s older precedent rather than the newer, more robust convention already established in `test_current_user.py`/`test_logout.py`. Today it passes because `SESSION_COOKIE_NAME` defaults to `"access_token"`, but if that setting is ever overridden, the expired/tampered/revoked "reject" tests would silently start testing "no cookie sent" instead of the actual gate logic, and the valid-token test would fail for the wrong reason. Flagged independently by two review layers (Blind Hunter, Edge Case Hunter). **Fixed:** all four `client.cookies.set(...)` calls now use `settings.SESSION_COOKIE_NAME`.
- [x] [Review][Patch] Tautological assertion gives false confidence in the no-leak proof [backend/tests/test_protected_router_gate.py:72] — `assert "user_id" not in body` in `test_no_cookie_returns_401_before_handler_runs` can never fail: `core/errors.py`'s `_error_body()` unconditionally returns only `status`/`code`/`message`/`timestamp` on every error path, regardless of whether the auth gate ran at all. The assertion looks like it verifies AC6 (no leaked fields) but would still pass even if the gate were completely broken. **Fixed:** replaced with `assert set(body.keys()) == {"status", "code", "message", "timestamp"}`, which actually fails if any field is ever added or leaked.
- [x] [Review][Patch] AC3's "handler body never executes" claim is inferred structurally, not proven empirically [backend/tests/test_protected_router_gate.py:45-50,63-72] — the probe handler in `_build_probe_app()` has no observable side effect (e.g. a call counter) that the no-cookie test could assert stayed untouched; it only checks the shape of the 401 response and infers non-execution rather than proving it directly. **Fixed:** `_build_probe_app()` now returns `(app, call_count)`, where `call_count` is incremented inside the handler; `test_no_cookie_returns_401_before_handler_runs` asserts `call_count[0] == 0`, and the same assertion (plus `== 1` on the valid-token test) was added to the other four mechanism tests for consistent proof. Verified: 75 passed, 16 deselected, zero regressions.
- [x] [Review][Defer] Load-bearing "route added after `include_router()` already ran" claim has no permanent regression test [backend/tests/test_protected_router_gate.py:39-55] — the Dev Notes' empirical claim (verified via a throwaway standalone script, not committed) is that a route added to a router *after* `app.include_router()` has already run still inherits the gate. `_build_probe_app()` actually tests a different order (route added, *then* included) — deferred, pre-existing test-completeness gap, not a current correctness bug: this codebase always adds routes via `@router.get(...)` decorators inside each module's `router.py`, which execute at import time, before `main.py`'s `include_router()` calls run — so the order this test *does* cover matches how Epic 2–5 will actually add routes. No automated guard exists if that import pattern or FastAPI's internals ever change; Dev Notes already flag "re-verify empirically" on FastAPI upgrade with no automated way to do so.
- [x] [Review][Defer] Signature-tampering helper duplicated from `test_auth_service.py` [backend/tests/test_protected_router_gate.py:88-92] — deferred, matches an already-accepted pattern (Story 1.5's review already logged a third near-duplicate test helper as deferred test-hygiene debt across this same set of files).



- **Why this story exists even though the four routers have zero real routes:** `get_current_user` and `request.state.current_user` (Story 1.3) have been sitting unused since that story shipped — `deferred-work.md`'s consolidated Stories 1.2–1.4 review note explicitly named this as expected, not a gap: *"Story 1.6 and Epic 2-5 are where this gets wired in."* This story closes that loop structurally, ahead of time, so no future epic has to remember to add the auth dependency to its own routes.
- **Which FastAPI mechanism to use, and why — verified empirically, not assumed:** two mechanisms could plausibly wire this gate so it also covers routes Epic 2–5 add later: (a) `APIRouter(dependencies=[Depends(get_current_user)])` set on each module's own router **constructor**, or (b) `dependencies=[Depends(get_current_user)]` passed to `app.include_router(...)` in `main.py`. In older FastAPI versions (a) was the only one that worked, because `include_router` used to eagerly copy whatever routes existed on the child router *at that exact call* — a route added to the child router afterward wouldn't inherit it. **That is not how this installed version behaves.** FastAPI here (0.139.0) resolves included routes lazily through an `_IncludedRouter`/`_EffectiveRouteContext` mechanism with route-list version tracking (`fastapi/routing.py`, `_RouterIncludeContext`/`effective_candidates`) — it re-derives the effective route table (and reapplies `include_router`-level dependencies) whenever the child router's routes change. This was confirmed with a standalone script: both `include_router(child, dependencies=[Depends(gate)])` with a route added to `child` *afterward*, and `APIRouter(dependencies=[Depends(gate)])` with a route added *afterward*, returned 401 for the new route in both cases.
  - **Given both work, use (a) — constructor-level, in each module's own `router.py` (AC1).** The reason is discoverability, not correctness: AD-1's "a feature is understood by opening one folder" convention means a developer opening `assignments/router.py` to add Epic 3's first real route should see the gate right there, without needing to cross-check `main.py`. Do not treat this as "the only mechanism that technically works" when explaining it — it isn't; state the actual reason (discoverability/consistency with AD-1), since a future FastAPI-version claim here should be re-verified, not assumed from this note.
  - **If FastAPI is ever upgraded, re-verify this empirically** rather than trusting either this note or prior assumptions — the lazy-resolution behavior observed here is itself evidence that "how include_router interacts with routes added later" is not a stable, assume-it API contract across versions.
- **No role-based restriction here.** `get_current_user` accepts both roles; endpoint-specific authorization (e.g. dashboard being HR-only) belongs to whichever future story builds that endpoint — do not add `if current_user.role != Role.HR_ADMIN` anywhere in this story.
- **No new data endpoints.** This story's entire footprint is: one import + one constructor argument change in 4 files, plus tests. Resist the urge to stub out placeholder GET routes on `assignments`/`content`/`progress`/`dashboard` "to have something to test against" — that would be inventing scope Epic 2–5 own.
- **"No flash of protected content" needs no new mechanism.** FastAPI resolves dependencies (and can raise from them) before the endpoint function body ever executes — this is inherent to the framework, already proven by Story 1.3's own tests. This story's job is attaching the existing gate to the right object, not building a new no-flash mechanism.
- **Frontend redirect-on-401 is out of scope** — no frontend project exists in this repo yet (same precedent as Stories 1.4/1.5).
- **A pre-existing, unrelated tracking gap was found while creating this story:** `sprint-status.yaml` currently shows `1-7-database-schema-initialization-and-migration: backlog`, but that work was actually implemented and merged to `main` (commit `1c99463`, PR #28) without ever going through `create-story`. This is being corrected separately, outside this story — do not let it affect how Epic 1 / this story's own status transitions are handled.

### Project Structure Notes

- Changes land in exactly 4 files: `backend/app/assignments/router.py`, `backend/app/content/router.py`, `backend/app/progress/router.py`, `backend/app/dashboard/router.py` (each gains 2 imports + a constructor argument on the existing `router = APIRouter()` line).
- No changes to `backend/app/auth/router.py`, `backend/app/main.py`, any `core/*` file, or any `service.py`/`repository.py`/`models.py`/`schemas.py` in any module.
- New test file: `backend/tests/test_protected_router_gate.py`.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.6: Protected Endpoint Gate — No Flash of Protected Content] — full epic AC text
- [Source: _bmad-output/planning-artifacts/architecture/architecture-TalentPilot-AI-2026-07-09/ARCHITECTURE-SPINE.md#AD-6] — server-side session/role/identity gate on every request; "no flash of protected content before redirect" phrasing originates here
- [Source: _bmad-output/implementation-artifacts/1-3-role-and-identity-scoping-on-every-request.md] — `get_current_user`'s existing behavior, `request.state.current_user` contract, and the generic-validation-vs-endpoint-specific-authorization split this story continues
- [Source: _bmad-output/implementation-artifacts/1-5-sign-out-and-session-invalidation.md] — revocation check inherited via `get_current_token_payload`
- [Source: _bmad-output/implementation-artifacts/deferred-work.md#Deferred from: consolidated code review of Stories 1.2, 1.3, 1.4] — the explicit note naming Story 1.6 as where this gets wired in
- [Source: backend/app/auth/service.py] — `get_current_user`, `get_current_token_payload` implementations this story reuses unmodified
- [Source: backend/tests/test_current_user.py, backend/tests/test_auth_service.py, backend/tests/test_logout.py] — established isolated-test-app patterns and token-crafting helpers (expired, tampered, revoked) to reuse rather than reinvent

## Library/Framework Requirements

No new dependencies. Uses FastAPI's existing `APIRouter(dependencies=...)` constructor argument and `Depends`, both already in use elsewhere in this codebase.

## Testing Requirements

- `pytest` + `httpx` + `pytest-asyncio`, consistent with prior stories.
- New file `backend/tests/test_protected_router_gate.py` needs no live database (mirrors `test_current_user.py`, not `test_database_schema.py`).
- Structural tests (no HTTP call) assert the real router objects' `.dependencies` attribute per Task 2 — this directly verifies the production router configuration, not a lookalike.
- Mechanism tests (Task 3) use an isolated test app, following the codebase's established convention of not mutating shared production router/app objects for test-only routes.
- Reuse existing token-crafting helpers/patterns (expired token, tampered signature, revoked token) from `test_auth_service.py` and `test_logout.py` rather than reimplementing them.
- `conftest.py`'s autouse `_clear_revoked_tokens` fixture already isolates revoked-token state between tests — no additional cleanup needed for the revoked-token test case.

## Previous Story Intelligence

From Story 1.5 (`1-5-sign-out-and-session-invalidation.md`, status `done`):
- Established/reinforced: don't add speculative hardening beyond what the AC asks for; use isolated, test-file-local FastAPI apps rather than mutating `main.py`'s shared `app` object or adding debug-only routes to production routers for testing purposes. This story follows that convention for its mechanism-proof tests (Task 3), while additionally asserting directly against the real router objects' `.dependencies` attribute (Task 2) — appropriate here because, uniquely for this story, the property under test *is* a configuration fact about the real production router objects themselves, not just a dependency function's runtime behavior.
- `deferred-work.md`'s consolidated-review note (logged during the Stories 1.2–1.4 review) explicitly anticipated this story by name — confirms this is expected, planned work, not scope creep discovered late.

## Git Intelligence Summary

Recent commits: `adf1c2a Feature/story1.5 (#29)` (merged to `main`, Story 1.5 done). Established pattern: one implementation commit/PR per story on a `feature/story1.X` branch, `sprint-status.yaml` updated alongside. This story should follow the same pattern (`feature/story1.6`) unless directed otherwise.

Note: `git log --all` shows no commit ever added a `1-7-*.md` story file, yet commits `fbbd238`/`1c99463` (PR #28, "Story1.7 db migration") implemented and merged the actual Story 1.7 work (models, Alembic migration, seed data) directly, bypassing `create-story`. This is a separate, pre-existing gap being corrected outside this story (see Dev Notes) — not something Story 1.6's implementation needs to account for.

## Dev Agent Record

### Agent Model Used

claude-sonnet-5

### Debug Log References

- Discovered `backend/.venv` was missing `pgvector`, `sentence-transformers`, and `alembic` (all present in `requirements.txt` since Story 1.7 but never installed into this checkout's venv) — `conftest.py` failed to import at collection time (`ModuleNotFoundError: No module named 'pgvector'`) before any test could run. Fixed via `pip install -r requirements.txt`; unrelated to this story's own change, but blocking to run any test in the suite.
- `backend/.venv/Scripts/python.exe -m pytest tests/test_protected_router_gate.py -v` → red (pre-implementation): 4/10 failed — exactly the 4 structural tests (`assignments_router`/`content_router`/`progress_router`/`dashboard_router` each asserted missing `get_current_user`); the other 6 (auth_router regression guard + 5 mechanism-proof tests) already passed since they build their own isolated router and don't depend on Task 1's changes.
- After implementing Task 1: `pytest tests/test_protected_router_gate.py -v` → green, 10/10 passed.
- `pytest tests/ -v -k "not test_database_schema"` (full suite minus live-DB integration tests, same exclusion pattern established since Story 1.1) → 75 passed, 16 deselected, zero regressions.
- `docker compose ps` confirmed the Docker daemon is still unreachable in this sandbox (same documented limitation since Story 1.1/1.7) — `test_database_schema.py`'s live-DB tests could not be run; this story makes no DB-related changes, so this is expected, not a gap.

### Completion Notes List

- Wired `Depends(get_current_user)` onto `assignments_router`, `content_router`, `progress_router`, `dashboard_router` via each module's own `APIRouter(dependencies=[Depends(get_current_user)])` constructor (not via `main.py`'s `include_router()`), exactly as scoped in Dev Notes — verified this doesn't break `auth_router`'s unauthenticated `/login`/`/logout` routes (`test_auth_router_is_not_gated`, plus the full pre-existing `test_login.py`/`test_logout.py` suites still pass unmodified).
- No new data endpoints were added anywhere, per Scope Note 2/Dev Notes — the only production-code footprint is the import + constructor-argument change in the 4 router files.
- All 6 acceptance criteria verified: AC1/AC2 via structural tests asserting the real router objects' `.dependencies` attribute (not a lookalike); AC3–AC6 via mechanism-proof tests against an isolated probe router built with the identical `APIRouter(dependencies=[Depends(get_current_user)])` pattern, with a route registered *after* construction to mirror how Epic 2–5 will add real routes later.
- No real data route exists yet under any of the 4 gated routers (confirmed unchanged — Epic 2–5 own that), so AC3's "before the route handler runs" claim is proven against the isolated probe router rather than a live `/api/assignments` call, consistent with the story's own Scope Note 2 and the same precedent Stories 1.2/1.3/1.5 used for pre-route dependency verification.

### File List

- `backend/app/assignments/router.py` (modified — added `Depends` import + `get_current_user` import; `router = APIRouter()` → `router = APIRouter(dependencies=[Depends(get_current_user)])`)
- `backend/app/content/router.py` (modified — same change)
- `backend/app/progress/router.py` (modified — same change)
- `backend/app/dashboard/router.py` (modified — same change)
- `backend/tests/test_protected_router_gate.py` (new — 10 tests: 4 structural router-configuration tests, 1 auth-router regression guard, 5 mechanism-proof gate tests)

## Change Log

- 2026-07-09: Implemented Story 1.6 — wired `Depends(get_current_user)` onto `assignments/`, `content/`, `progress/`, `dashboard/` routers via their own `APIRouter(dependencies=[...])` constructors, so any route Epic 2–5 add later is gated automatically. `auth_router` (`/login`, `/logout`) explicitly left ungated. New test file `backend/tests/test_protected_router_gate.py` (10 tests: structural router-configuration checks + mechanism-proof runtime checks for no-cookie/expired/tampered/revoked/valid-token cases). TDD: structural tests confirmed red (4/10 failing) before implementation, green (10/10) after. Full suite: 75 passed, 16 deselected (live-DB tests, Docker unreachable in this sandbox — pre-existing, unrelated to this story). Status → `review`.
- 2026-07-09: Code review (`bmad-code-review`, 3 parallel adversarial layers — Blind Hunter, Edge Case Hunter, Acceptance Auditor). 3 patches applied (test file only, no production-code change): mechanism tests now use `settings.SESSION_COOKIE_NAME` instead of a hardcoded literal; the tautological no-leak assertion was replaced with an exact-keys check; a `call_count` cell was added to `_build_probe_app()` so AC3's "handler body never executes" claim is proven empirically instead of inferred. 2 items deferred (`deferred-work.md`): the Dev Notes' "route added after `include_router()` already ran" empirical claim still has no permanent regression test (verified today's actual import order makes this safe, but no automated guard against drift); a fourth near-duplicate signature-tampering test helper. 8 findings dismissed as noise or already explicitly scoped by the story itself. Zero regressions: 75 passed, 16 deselected. Status → `done`.
