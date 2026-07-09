---
baseline_commit: e7755d9e75d87e3955a99daf4168c7e035dd3a54
---

# Story 1.1: Project Structure & Core Dependencies

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **developer**,
I want to initialize the FastAPI project structure with core dependencies (uvicorn, SQLAlchemy, asyncpg, Pydantic, JWT libraries),
so that I have a foundation for building the modular monolith.

## Acceptance Criteria

1. **AC1 — App entry point exists.** `backend/app/main.py` is a FastAPI application with: CORS middleware (explicit allowed origins — local dev + built SPA origin — never `*` with credentials), centralized exception handlers producing the JSON error contract, and mounts for each module's router.
2. **AC2 — Async DB engine configured.** SQLAlchemy 2.0 `AsyncEngine` + `asyncpg` driver, connection string from `DATABASE_URL` env var, `postgresql+asyncpg://` dialect. An `async_sessionmaker`/`get_db` dependency is importable from `core/`.
3. **AC3 — JWT utilities exist.** `core/security.py` (or `auth/`) exposes token-generation and token-validation functions using HS256 (locked in addendum.md — no RS256, no algorithm negotiation). Not wired to a login endpoint yet (that's Story 1.2/1.4) — just the utilities and their unit tests.
4. **AC4 — Centralized error contract.** A FastAPI exception handler returns `{status, code, message, timestamp}` JSON for at least `RequestValidationError` (422) and unhandled `Exception` (500). No endpoint-specific ad-hoc error shapes.
5. **AC5 — Docker Compose for local Postgres+pgvector.** `docker-compose.yml` at repo root brings up a `postgres` service using a `pgvector/pgvector` image (not plain `postgres`, since `content_catalog`/`skills` need the extension from Epic 2 onward). No Redis service — nothing in the epics/architecture calls for one; the "if used" in the epic text is not a requirement, don't add unused infrastructure.
6. **AC6 — Module skeleton matches the spine's source tree exactly.** `backend/app/{core,auth,assignments,content,progress,dashboard}/` each contain `router.py`, `service.py`, `repository.py`, `models.py`, `schemas.py` as empty-but-importable stubs (`dashboard/` has no `models.py` — it owns no table, per spine). No other layout is acceptable — this is the one structural fact every later story depends on.
7. **AC7 — Env vars externalized.** `.env.example` at repo root with `DATABASE_URL`, `JWT_SECRET`, `JWT_EXPIRATION_HOURS` (default 24, per Story 1.2 spec) placeholders. `.env` itself is git-ignored. Settings loaded via `pydantic-settings` `BaseSettings` in `core/config.py`.
8. **AC8 — App boots.** `uvicorn app.main:app` starts without error against the Docker Compose Postgres (no DB tables required yet — that's Story 1.7's schema init).

## Tasks / Subtasks

- [x] Task 1: Scaffold `backend/` project skeleton (AC: #1, #6)
  - [x] Create `backend/app/{core,auth,assignments,content,progress,dashboard}/` with `__init__.py` in each
  - [x] Add `router.py`, `service.py`, `repository.py`, `schemas.py` stubs to every module; `models.py` to every module except `dashboard/`
  - [x] Create `backend/app/main.py` with FastAPI app instance, CORS middleware, router includes (routers can be empty `APIRouter()` for now)
  - [x] Create `backend/requirements.txt` pinning: `fastapi`, `uvicorn[standard]`, `sqlalchemy[asyncio]>=2.0`, `asyncpg`, `pydantic>=2`, `pydantic-settings`, `pyjwt`, `python-dotenv` (see Library/Framework Requirements below for pinned versions)
- [x] Task 2: Async DB engine + config (AC: #2, #7)
  - [x] `core/config.py`: `Settings(BaseSettings)` reading `DATABASE_URL`, `JWT_SECRET`, `JWT_EXPIRATION_HOURS` from env
  - [x] `core/db.py`: `create_async_engine(settings.DATABASE_URL)`, `async_sessionmaker`, and a `get_db()` FastAPI dependency (`AsyncGenerator[AsyncSession, None]`)
  - [x] `.env.example` with all three keys documented; confirm `.env` is in `.gitignore`
- [x] Task 3: JWT security utilities (AC: #3)
  - [x] `core/security.py`: `create_access_token(user_id: str, role: str) -> str` and `decode_access_token(token: str) -> dict`, both HS256, using `settings.JWT_SECRET` and `settings.JWT_EXPIRATION_HOURS`
  - [x] Unit tests: valid token round-trips; expired token raises; tampered signature raises
- [x] Task 4: Centralized error contract (AC: #4)
  - [x] `core/errors.py`: exception handlers for `RequestValidationError` → 422 and generic `Exception` → 500, both returning `{status, code, message, timestamp}`
  - [x] Register handlers on the `FastAPI()` app instance in `main.py`
- [x] Task 5: Docker Compose (AC: #5, #8)
  - [x] `docker-compose.yml`: `postgres` service on `pgvector/pgvector:pg16`, exposed port, volume for persistence, env-driven credentials matching `.env.example`
  - [x] Verify `uvicorn app.main:app` boots cleanly with no DB calls at startup (Story 1.7 adds schema init) — verified live against a running server; see Completion Notes for the Docker Compose caveat

### Review Findings

- [x] [Review][Patch] CORS origins hardcoded, missing built-SPA origin, no env override, no test guarding non-wildcard [backend/app/main.py:11-13] — fixed: `ALLOWED_ORIGINS` env var (comma-separated) via `settings.allowed_origins_list`, documented placeholder in `.env.example`, `test_cors_origins_are_explicit_not_wildcard` added
- [x] [Review][Patch] No `StarletteHTTPException` handler — HTTPException-raised errors (401/403/404, used from Story 1.3 onward) bypass the centralized error contract [backend/app/core/errors.py] — fixed: handler registered, `test_http_exception_returns_centralized_error_contract` added
- [x] [Review][Patch] Unhandled-exception handler has no server-side logging — real bugs become invisible [backend/app/core/errors.py:23-28] — fixed: `logger.exception(...)` added
- [x] [Review][Patch] Validation error handler leaks raw pydantic internals (`str(exc.errors())`, can include submitted field values) to API clients [backend/app/core/errors.py:16-20] — fixed: full detail now `logger.warning(...)`-logged server-side only, client gets a safe generic message
- [x] [Review][Patch] `Settings()` crashes at import with a raw, unfriendly traceback if `.env`/env vars are missing on a fresh clone [backend/app/core/config.py:12] — fixed: `load_settings()` wraps `Settings()`, raises `SystemExit` with a clear message pointing at `.env.example`; tests added in `test_config.py`
- [x] [Review][Patch] `conftest.py` test `DATABASE_URL` points at a `talentpilot_test` DB that nothing provisions (compose only creates `talentpilot`) — harmless today, guaranteed to break the first DB-backed test [backend/tests/conftest.py:3] — fixed: default now points at the actually-provisioned `talentpilot` DB
- [x] [Review][Defer] JWT `role` claim accepts any string (no enum check); `JWT_EXPIRATION_HOURS` has no bounds check [backend/app/core/security.py] — deferred, Story 1.3 already specs role-enum validation at the dependency layer; not required by this story's AC3
- [x] [Review][Defer] No `import-linter`/lint enforcement of the AD-1 single-owner module boundary — stubs are docstrings only [backend/app/*/repository.py] — deferred, architectural-governance tooling, no AC in this story requests it
- [x] [Review][Defer] No lockfile/hash-pinning beyond top-level `==` pins; transitive deps unconstrained [backend/requirements.txt] — deferred, reasonable for a 5-week internal pilot, revisit if reproducibility becomes an issue
- [x] [Review][Defer] No engine-disposal/lifespan hook to close the async DB engine on shutdown [backend/app/main.py] — deferred, no live-connection bug exists yet since Story 1.7 is the first to exercise a real DB connection

## Dev Notes

- **This is the first story in the project — there is no existing `backend/` code to read or preserve.** Everything here is net-new. Do not look for prior patterns; the module skeleton created here is itself the pattern every later story must match exactly (AC6).
- **Module set is fixed and exhaustive** — `core, auth, assignments, content, progress, dashboard` — per [ARCHITECTURE-SPINE.md](../../planning-artifacts/architecture/architecture-TalentPilot-AI-2026-07-09/ARCHITECTURE-SPINE.md) source tree. Do not add a `models.py` to `dashboard/`: it is explicitly a read-composition module owning no table (AD-8). Do not invent extra modules (e.g. no separate `employees/` or `skills/` module — those tables are seeded by Epic 3 stories but the spine gives them no dedicated module; place their models under the module noted in later stories, don't guess now — leave them out of this story's scope entirely).
- **No Redis.** The epic text says "Redis (if used)" — nothing elsewhere in the PRD, addendum, or architecture spine calls for caching/session-store infrastructure beyond the JWT cookie itself. Do not add a Redis service; it would be unused infrastructure this early (violates YAGNI and there's no AC requiring it).
- **JWT algorithm is locked to HS256** — addendum.md and Story 1.2 both state HS256 for simplicity; do not implement RS256 or make the algorithm configurable/pluggable, that's speculative generality not asked for.
- **`pgvector/pgvector` image, not plain `postgres`.** Epic 2 (Content Catalog) needs the `vector` extension on the same database instance from Story 2.1 onward — provisioning plain Postgres now means re-provisioning later. Use the `pgvector/pgvector:pg16` image (or current pg16+-compatible tag) from the start.
- **Don't wire up login yet.** Story 1.2 (JWT token generation & session model) and Story 1.4 (login endpoint) own the actual login flow and credential validation. This story only creates the reusable JWT *utility functions* and the empty `auth/router.py` stub — no `/login` route body yet.
- **Don't build schema/migrations yet.** Story 1.7 owns table creation (`accounts`, `employees`, `skills`, `content_catalog`, `assignments`, `skill_progress`, `assignment_overrides`) and the fail-fast schema-version-mismatch behavior. This story's `models.py` files can stay empty stubs (or `Base = declarative_base()` only) — do not pre-create SQLAlchemy models for tables whose exact shape is defined in later stories, to avoid rework/drift.

### Project Structure Notes

- Backend source tree (binding, from architecture spine):
  ```text
  backend/app/
    core/          # config, JWT/security, CORS, error handlers — this story
    auth/          # login, session/role gate dependency — stub only this story
    assignments/   # stub only this story
    content/       # stub only this story
    progress/      # stub only this story
    dashboard/     # read-composition, no models.py — stub only this story
    main.py
  ```
- Every module folder gets `router.py`, `service.py`, `repository.py`, `schemas.py`; every module *except* `dashboard/` also gets `models.py`. This exact shape is what every subsequent story (1.2 onward) will extend — deviating here creates rework across the whole Epic 1 sequence.
- Cross-module access is Service-API only (AD-1) — even though everything is a stub right now, don't add direct cross-module imports of `repository.py` or `models.py` as shortcuts in later stories; route through `service.py`.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.1: Project Structure & Core Dependencies] — acceptance criteria origin
- [Source: _bmad-output/planning-artifacts/architecture/architecture-TalentPilot-AI-2026-07-09/ARCHITECTURE-SPINE.md#Source tree] — module list and folder shape (binding)
- [Source: _bmad-output/planning-artifacts/architecture/architecture-TalentPilot-AI-2026-07-09/ARCHITECTURE-SPINE.md#Consistency Conventions] — naming, error contract, auth/CORS conventions
- [Source: _bmad-output/planning-artifacts/architecture/architecture-TalentPilot-AI-2026-07-09/ARCHITECTURE-SPINE.md#Stack] — pinned technology list
- [Source: _bmad-output/planning-artifacts/prds/prd-TalentPilot-AI-2026-07-09/addendum.md#Technical Stack (locked)] — JWT cookie mechanism, HS256, local-only deployment scope
- [Source: _bmad-output/implementation-artifacts/sprint-status.yaml] — story key `1-1-project-structure-and-core-dependencies`, epic 1 backlog → in-progress

## Library/Framework Requirements

Verified current stable versions (web research, 2026-07-09) — pin close to these, adjust only for a documented compatibility reason:

| Package | Version | Note |
| --- | --- | --- |
| `fastapi` | 0.136.x | `fastapi[standard]` extra pulls in uvicorn + other extras |
| `uvicorn[standard]` | 0.34.x | ASGI server |
| `sqlalchemy[asyncio]` | 2.0.36+ | async engine/session support required |
| `asyncpg` | latest compatible with SQLAlchemy 2.0 async | Postgres async driver |
| `pydantic` | 2.10.x | v2 API (`BaseModel`, `model_config`) — do not write v1-style `class Config` |
| `pydantic-settings` | latest | `BaseSettings` moved out of core pydantic in v2 — must be a separate dependency |
| `pyjwt` | latest | HS256 only per addendum.md |
| `python-dotenv` | latest | local `.env` loading in dev |

## Testing Requirements

- Unit tests for `core/security.py` (Task 3): valid round-trip, expired-token rejection, tampered-signature rejection — no network/DB dependency.
- A smoke test (`pytest` + `httpx.AsyncClient` or `TestClient`) hitting a trivial route (or `/`) to confirm the app boots and CORS/error handlers are registered — this is the pattern later stories' endpoint tests will extend.
- Do not write tests for `/login` or any DB-backed behavior yet — those belong to Stories 1.2/1.4/1.7 respectively, which own that functionality.
- Test framework: `pytest` + `httpx` per architecture spine Stack table.

## Dev Agent Record

### Agent Model Used

claude-sonnet-5

### Debug Log References

- `backend/.venv/Scripts/python.exe -m pytest tests/ -v` → 8 passed (final run)
- `docker compose config` → validated `docker-compose.yml` syntax (Docker Desktop daemon unavailable in this sandbox — see Completion Notes)
- Live `uvicorn app.main:app` boot on port 8123, `GET /` → `200 {"status":"ok"}`

### Completion Notes List

- Implemented all 5 tasks test-first: `core/security.py` and the `core/errors.py` handlers each had failing tests written before the implementation existed (`ModuleNotFoundError`/import failure confirmed as the red state), then made green.
- **Version pins deviated from the story's Library/Framework Requirements table for a documented reason**: this sandbox's only available Python is 3.14.0, and `pydantic-core`, `sqlalchemy`, etc. at the exact versions listed (e.g. pydantic 2.10.4) have no prebuilt `cp314` wheel and fail to compile from source here (no working Rust/MSVC toolchain). Installed the newest versions that do ship `cp314` wheels instead: `fastapi==0.139.0`, `uvicorn==0.51.0`, `sqlalchemy==2.0.51`, `asyncpg==0.31.0`, `pydantic==2.13.4`, `pydantic-settings==2.14.2`, `pyjwt==2.13.0`, `python-dotenv==1.2.2`, `pytest==9.1.1`, `pytest-asyncio==1.4.0`, `httpx==0.28.1` — all within the same major/API-compatible lines (Pydantic v2, SQLAlchemy 2.0, FastAPI 0.1xx), just newer patch/minor. `requirements.txt` pins these exact working versions. If the target deploy/dev environment runs Python 3.12/3.13 as the architecture spine specifies, the older pins should also work — reconfirm wheel availability there.
- Used `HTTP_422_UNPROCESSABLE_CONTENT` instead of the deprecated `HTTP_422_UNPROCESSABLE_ENTITY` alias (both map to status 422; avoids a `StarletteDeprecationWarning` surfaced during the first test run).
- **AC8/Task 5 Docker Compose caveat**: `docker-compose.yml` was validated with `docker compose config` (confirms valid syntax, resolves image/env/volumes) but could not be brought up live — the Docker CLI is present in this sandbox but its daemon (`dockerDesktopLinuxEngine`) is not running/reachable, which is an environment constraint, not a code defect. The "app boots" half of AC8 was verified directly instead: `uvicorn app.main:app` starts cleanly and `GET /` returns 200 with **no live Postgres running at all** — this is expected and correct, since SQLAlchemy's `create_async_engine()` is lazy and opens no connection until first query (Story 1.7 is where a live DB connection first gets exercised). Recommend re-running `docker compose up -d postgres` once on a machine with a running Docker daemon to close this verification gap before Story 1.7 depends on it.
- Added a `.env` (git-ignored, not committed) alongside `.env.example` so local `uvicorn`/`pytest` runs have real values for `Settings()` to load — `pydantic-settings` requires `DATABASE_URL`/`JWT_SECRET` to be present at import time since they have no defaults (intentional: a missing secret should fail loudly, not silently default).
- No previous story existed to carry learnings forward (this is Epic 1's first story).

### File List

- `backend/app/main.py` (new)
- `backend/app/core/__init__.py` (new)
- `backend/app/core/config.py` (new)
- `backend/app/core/db.py` (new)
- `backend/app/core/security.py` (new)
- `backend/app/core/errors.py` (new)
- `backend/app/auth/__init__.py`, `router.py`, `service.py`, `repository.py`, `models.py`, `schemas.py` (new)
- `backend/app/assignments/__init__.py`, `router.py`, `service.py`, `repository.py`, `models.py`, `schemas.py` (new)
- `backend/app/content/__init__.py`, `router.py`, `service.py`, `repository.py`, `models.py`, `schemas.py` (new)
- `backend/app/progress/__init__.py`, `router.py`, `service.py`, `repository.py`, `models.py`, `schemas.py` (new)
- `backend/app/dashboard/__init__.py`, `router.py`, `service.py`, `repository.py`, `schemas.py` (new — no `models.py`, per AD-8)
- `backend/tests/conftest.py` (modified — code review patch)
- `backend/tests/test_security.py` (new)
- `backend/tests/test_main.py` (modified — code review patch)
- `backend/tests/test_config.py` (new — code review patch)
- `backend/pytest.ini` (new)
- `backend/requirements.txt` (new)
- `backend/.env.example` (modified — code review patch)
- `backend/.env` (modified, git-ignored — code review patch)
- `backend/.gitignore` (new)
- `docker-compose.yml` (new, repo root)

## Change Log

- 2026-07-09: Initial implementation of Story 1.1 — full module skeleton, async DB engine/config, JWT utilities (TDD), centralized error contract, Docker Compose for Postgres+pgvector. 8/8 tests passing. Status → review.
- 2026-07-09: Code review — 6 patch findings applied (CORS made configurable + built-SPA placeholder, `StarletteHTTPException` handler added, exception logging added, validation-error client message no longer leaks raw pydantic internals, `Settings()` fails fast with a clear message, test `DATABASE_URL` fixed to match the actually-provisioned DB), 4 findings deferred to `deferred-work.md`, 7 dismissed (2 as false positives from reviewer misreads/my own truncated prompt, verified directly). 4 new tests added. 12/12 tests passing. Status → done.
