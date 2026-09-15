# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

TalentPilot-AI: an internal HR tool for assigning employees AI-matched learning content (YouTube/Udemy videos) against Skills, auto-capturing watch progress, and giving HR a readiness dashboard. Local-only pilot (no production deployment) — one FastAPI backend, one Postgres+pgvector instance, one React SPA.

## Commands

### Backend (`backend/`, Python 3.12+, venv at `backend/.venv`)

```
# Postgres (pgvector) via Docker — required before running the backend
docker-compose up -d postgres          # from repo root; exposes localhost:5433

# Setup
cd backend
.venv\Scripts\activate                 # Windows; or source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env                 # then fill DATABASE_URL / JWT_SECRET / ADMIN_KEY_ENCRYPTION_SECRET

# Run
uvicorn app.main:app --reload --port 8000

# Migrations (Alembic)
alembic upgrade head
alembic revision --autogenerate -m "description"

# Tests (pytest, async mode auto via pytest.ini)
pytest                                            # full suite
pytest tests/test_assignments_service.py          # one file
pytest tests/test_assignments_service.py::test_name   # one test
pytest --cov                                      # coverage (see .coveragerc)

# Manual content ingestion CLI (never exposed as an HTTP route — see AD-7)
python -m app.content.cli ingest [--skill-id UUID ...]
python -m app.content.cli seed --skill-id UUID --title ... --url ... --type {VIDEO,DOCUMENT,WEBSITE}
```

### Frontend (`frontend/`, React + TypeScript + Vite)

```
cd frontend
npm install
npm run dev              # Vite dev server on :5173, proxies /api -> localhost:8000
npm run build             # tsc && vite build
npm run test              # vitest
npm run test -- path/to/File.test.tsx -t "test name"   # single test
npm run test:coverage
```

### Full stack via Docker Compose (repo root)

```
docker-compose up -d      # postgres (5433) + backend (8000) + frontend (5173, served via nginx)
```

## Architecture

**Modular monolith** — one FastAPI app divided into feature-domain modules, each internally layered `router.py` → `service.py` → `repository.py`, plus `models.py` (SQLAlchemy) and `schemas.py` (Pydantic). A feature is understood by opening one folder, not by walking layers across the tree. Full rationale lives in `_bmad-output/planning-artifacts/architecture/architecture-TalentPilot-AI-2026-07-09/ARCHITECTURE-SPINE.md` — read it before making cross-module or schema changes.

### Modules and single-owner tables

| Module | Owns (sole read+write) |
| --- | --- |
| `auth/` | accounts, session/role gate |
| `assignments/` | `assignments` |
| `skills/` | `skills` (+ embeddings), `ever_assigned` lock |
| `content/` | `content_catalog` (+ embeddings), `admin_api_keys`, `org_api_credentials`, batch ingestion, admin live-lookup (YouTube + Udemy) |
| `progress/` | `skill_progress`, `assignment_overrides`, readiness derivation |
| `dashboard/` | read-composition over `assignments` + `progress`; owns no table |
| `core/` | config, JWT/security, CORS, error contract, `secrets.py` (Fernet encrypt/decrypt) |

**Only a table's owning module's `repository.py` touches that table.** Every other module goes through the owner's Service API — no cross-module ORM imports or direct queries. Dependency direction is one-way: `dashboard` → `assignments`/`progress`; `assignments` → `content`/`skills`; `content` → `skills`; nothing depends back. `core`/`auth` is used by everything and depends on nothing feature-specific.

Frontend mirrors backend modules as feature folders: `src/features/{admin,assignments,dashboard}`, shared presentational components in `src/components/`, per-resource API clients in `src/lib/api/`, TS types in `src/types/` mirroring Pydantic schemas, path alias `@` → `src/`.

### Invariants that matter when writing code

- **Coaching-only boundary (AD-2):** `skill_progress` is reachable only through `progress/`'s coaching-shaped read methods (single-assignment status, single-row drill-down). Never add a bulk/cross-employee/export read of watch data — this is launch-blocking, not a style preference.
- **Single derivation authority (AD-3):** effective `(Status, Provenance)` is computed in exactly one place, `progress/`, from `{watch signal, 7-day self-report staleness, active HR override}`. No other module or the frontend re-derives it. Status ∈ {Not Started, In Progress, Completed}; Provenance ∈ {Verified, Self-reported, Needs Attention, HR Override} — these are orthogonal axes, never conflated.
- **HR Override is a separate record (AD-4):** stored as its own attributed/timestamped/reversible record in `assignment_overrides`, never a field-overwrite on `skill_progress`. New watch progress arriving on an overridden row does not erase the override.
- **Watch-progress write path (AD-5):** all writes go through `progress.record_watch_progress()`, which takes identity from the session (never the request body), does a conditional write ordered by client **event-time** (never by position magnitude, so genuine rewinds aren't dropped), and applies server-side anti-spoofing before a row can be eligible for "Verified".
- **Server-side session/role gate on every request (AD-6):** JWT from an HttpOnly/Secure/SameSite cookie, verified per request; Employee sessions are hard-scoped to their own identity regardless of request params; HR Admin org-wide reads must go through `progress/`'s coaching-shaped methods (AD-2), never a raw/export path.
- **Content ingestion is batch-only on the shared key, with a narrow admin-lookup exception (AD-7):** `run_ingestion_job` and `settings.YOUTUBE_API_KEY` must never be referenced from any `router.py`/`main.py` — enforced by a regression-guard test (`test_content_ad7_regression_guard.py`). An authenticated HR_ADMIN may trigger a *live* lookup, but only with their own per-admin key (YouTube, `admin_api_keys`) or the org-wide credential (Udemy, `org_api_credentials`) — never the shared batch key. Live-lookup results are written to `content_catalog` only on an explicit attach action, never automatically from the search call.
- **Credentials are encrypted and module-owned (AD-10):** `admin_api_keys` (per-admin, YouTube) and `org_api_credentials` (org-wide, Udemy) are both Fernet-encrypted via `core/secrets.py`, keyed by `ADMIN_KEY_ENCRYPTION_SECRET` — deliberately a different secret from `JWT_SECRET`. Decrypt/encrypt only happens in `content/repository.py`; no endpoint ever returns plaintext, only a boolean "configured" flag.
- **Player capture behind an Adapter (AD-9):** the watch-progress capture pipeline depends only on the `PlayerAdapter` interface (`frontend/src/lib/adapters/`, documented in `frontend/docs/ADAPTERS.md`) — normalized `position`/`event-time`/play-pause-ended events. YouTube-specific polling details must stay behind `youtubeAdapter.ts`, never leak into `CaptureService` or `progress/`.
- **`skills/` owns the `ever_assigned` lock (AD-11):** a one-way boolean, never reset to `false`, that gates edit/delete of a Skill (FR-21/FR-22). `assignments/` sets it via `skills.service.mark_ever_assigned()` on successful Assignment creation — it never writes the `skills` table directly. Content-sourcing endpoints (FR-17/18/19/23) are deliberately *not* gated by this flag.

### Conventions

- REST resources: plural-noun, ≤2 levels deep (`/api/assignments`, `/api/skills/{id}/content`). Admin-only routes prefixed `/api/admin/...`, HR_ADMIN-gated.
- IDs are opaque UUIDs; all timestamps ISO-8601 UTC.
- Pydantic schemas are kept separate from SQLAlchemy ORM models — storage shape must never leak into the API contract.
- One JSON error contract (`status`, `code`, `message`, `timestamp`) via centralized exception handlers in `core/errors.py`; 422 on validation.
- Client validation is UX-only (React Hook Form + Zod); Pydantic on the server is the real guard.
- Live dashboard updates are client polling (≤30s) of the dashboard read endpoint — no WebSocket/SSE. Capture posts periodically (5–10s) plus a `sendBeacon` flush on tab-close.
- `get_db()` (`app/core/db.py`) commits on successful route completion and rolls back on exception — repository/service functions should `flush`, not `commit`, and rely on this.

## Documentation map

- `_bmad-output/planning-artifacts/architecture/architecture-TalentPilot-AI-2026-07-09/ARCHITECTURE-SPINE.md` — canonical architecture decisions (AD-1..AD-11), full ER diagram, capability-to-architecture map.
- `_bmad-output/planning-artifacts/prds/` — product requirements (FRs referenced throughout the codebase and tests).
- `documentation/ImplementationStepsForStory*.md` — per-story implementation logs (one per Story, e.g. Story 9.5).
- `frontend/docs/ADAPTERS.md` — Player Adapter pattern (AD-9) with YouTube implementation and a worked Vimeo-swap example.
- Root-level `*_SUMMARY.md`, `*_GUIDE.md`, `FEATURE_COMPLETE.txt`, etc. describe an earlier static-HTML prototype phase (`_bmad-output/E-Development/`), not the current FastAPI/React implementation — treat them as historical, not authoritative.

## Current status (as of 2026-09-15)

Epics 1–9 (FR-1–FR-33) are fully implemented and `done` (`_bmad-output/implementation-artifacts/sprint-status.yaml`). **Epic 10 ("Post-MVP Admin & Roster Refinements," FR-34–FR-43, 16 stories) is planned but not yet implemented** — approved via `_bmad-output/planning-artifacts/sprint-change-proposal-2026-09-15.md` and specified in the PRD (§4.11) and `epics.md`, but no story has started. If you see FR-34–FR-43 referenced in the PRD/architecture docs with no corresponding code, that's expected — check `sprint-status.yaml` for each story's real status (`10-1-...` through `10-16-...`) before assuming something is missing or broken. Stories 10.11–10.16 were added after the original 10-story Sprint Change Proposal, directly against `_bmad-output/E-Development/01-Ritas-Trust-Call-Prototype/`'s static HTML mockups (not real app code) — those mockups are ahead of, and visually diverge from, the real `frontend/src/pages/hr/*` components; treat them as a design reference for future stories, not as a description of current app behavior.
