---
name: 'TalentPilot-AI'
type: architecture-spine
purpose: build-substrate
altitude: initiative
paradigm: 'Modular monolith — feature-domain modules, each internally layered Router→Service→Repository, with single-owner data ownership per module'
scope: 'Full MVP: 4 features / 14 FRs — Skill Assignment, AI Content Discovery, Auto Video Progress Capture & Resume, Readiness Dashboard, Auth & Session Gate. Local working copy only; no production deployment.'
status: final
created: '2026-07-09'
updated: '2026-07-09'
binds: [FR-1, FR-2, FR-3, FR-4, FR-5, FR-6, FR-7, FR-8, FR-9, FR-10, FR-11, FR-12, FR-13, FR-14]
sources:
  - '_bmad-output/planning-artifacts/prds/prd-TalentPilot-AI-2026-07-09/prd.md'
  - '_bmad-output/planning-artifacts/prds/prd-TalentPilot-AI-2026-07-09/addendum.md'
  - '_bmad-output/planning-artifacts/research/technical-overall-stack-architecture-for-talentpilot-ai-research-2026-07-08.md'
  - '_bmad-output/deliveries/DD-001-poc-hypothesis-flows.yaml'
companions: []
---

# Architecture Spine — TalentPilot-AI

## Design Paradigm

**Modular monolith.** One FastAPI application, one Postgres+pgvector instance, one React SPA — deliberately not microservices (over-engineering for an internal single-environment pilot). The app is divided into **feature-domain modules**, each internally layered **Router → Service → Repository** (+ `models.py` SQLAlchemy, `schemas.py` Pydantic). A feature is understood by opening one folder, not by walking layers across the tree.

| Module | Owns (sole read+write) | Realizes |
| --- | --- | --- |
| `auth/` | accounts, session/role gate | FR-13, FR-14 |
| `assignments/` | `assignments` | FR-1, FR-2 |
| `content/` | `content_catalog` (+ embeddings), ingestion job | FR-3, FR-4 |
| `progress/` | `skill_progress`, `assignment_overrides`, readiness derivation | FR-5..FR-12 |
| `dashboard` (read-composition, owns no table) | — | FR-8..FR-11 (HR read surface) |
| `core/` | config, JWT/security, CORS, error contract | cross-cutting |

Frontend mirrors these as feature folders (`src/features/{dashboard,content-discovery,video-progress,assignment,auth}`), shared presentational components + per-resource API clients at top level.

## Invariants & Rules

The durable heart — the calls a future builder cannot read off compliant code. IDs are stable; `[ADOPTED]` marks calls already settled by a source input or an explicit decision this session.

### AD-1 — Single-owner data modules

- **Binds:** `assignments`, `content_catalog`, `skill_progress`, `assignment_overrides`; all modules
- **Prevents:** two features writing or reading one entity in incompatible ways; scattered table access that would make coaching-only and derivation-coherence unenforceable
- **Rule:** each table has exactly one owning module (per the paradigm table). Only that module's Repository touches the table; every other feature goes through the owning module's Service API. No module imports, queries, or writes another module's tables directly. `[ADOPTED — user, this session]`

### AD-2 — Coaching-only is a read boundary [ADOPTED]

- **Binds:** `skill_progress`, `progress/`; FR-9, §9, NFR "Coaching-only enforcement"
- **Prevents:** auto-captured Watch Progress leaking into any performance-evaluation-shaped interface, export, or report
- **Rule:** `skill_progress` is reachable only through `progress/`'s coaching-shaped read methods — single-assignment status, and single-row drill-down. No bulk, cross-employee, raw-history, or export read method exists to call. Enforced at the service/repository layer, not by UI convention. This is launch-blocking (PRD §9).

### AD-3 — Single derivation authority for (Status, Provenance)

- **Binds:** FR-8, FR-10, FR-12; every surface that shows a Status badge or Provenance Label
- **Prevents:** the same assignment rendering an inconsistent Status or trust signal across surfaces (the divergence half of PRD Open Question 11)
- **Rule:** effective `(Status, Provenance)` is derived in exactly one place — `progress/` — from `{watch signal, self-report staleness (7 days), active HR override}`. No other module (dashboard, assignment flow, frontend) computes Status or Provenance from raw columns. Consumers ask `progress/` for the already-reconciled pair. **Status** ∈ {Not Started, In Progress, Completed} (from Watch % 0 / 1–99 / 100) and **Provenance** ∈ {Verified, Self-reported, Needs Attention, HR Override} are **orthogonal axes** — Needs Attention is a Provenance value, never a Status (correcting the prototype's conflation). An Assignment with no recorded watch signal derives as **Not Started** — no `skill_progress` row need pre-exist, so `assignments/` never has to write into `progress/`'s domain to create one. Whether the pair is computed on read or cached on the row is `progress/`'s private choice (see Deferred).

### AD-4 — HR Override is a separate, coexisting record

- **Binds:** FR-12; `assignment_overrides`, `progress/`
- **Prevents:** an override overwriting/erasing the watch signal it should coexist with; a manual override masquerading as auto-verified data
- **Rule:** an HR Override is stored as its own record — attributed to the HR Admin, timestamped, reversible — never a field-overwrite on `skill_progress`. Derivation: an active override wins the effective Status; its Provenance is **HR Override** and is never merged into or displayed as **Verified**. Fresh Watch Progress arriving on an overridden row does not replace the override; both remain visible in drill-down until an HR Admin explicitly changes it. Set/reverse flows through a `progress/` write method (a second validated write path alongside AD-5).

### AD-5 — Watch-progress write path [ADOPTED]

- **Binds:** FR-5, FR-7, §8 (Data integrity, Write integrity); `skill_progress`
- **Prevents:** stale out-of-order writes regressing progress; a legitimate rewind being wrongly dropped; client-forged progress being trusted as Verified
- **Rule:** `skill_progress` mutates only via `progress.record_watch_progress()`, which (1) takes the Employee identity from the authenticated session, never the request body; (2) is a **conditional write ordered by client event-timestamp** — skip if the incoming event-time is not newer than what is stored — ordered by time, **never by position magnitude**, so a lower position with a newer timestamp (a real rewind) is accepted while an older-timestamp write is dropped; (3) applies **server-side anti-spoofing** — reject position advances inconsistent with real playback (e.g. an instantaneous jump toward 100%) and require the write be tied to the caller's own real Assignment. Only writes passing all three persist and are eligible to derive as Verified.

### AD-6 — Server-side session/role/identity gate on every request [ADOPTED]

- **Binds:** FR-13, FR-14, Open Question 12; all protected endpoints
- **Prevents:** unauthenticated data exposure; an Employee reaching another Employee's data; enforcement that lives only at login/routing or only client-side
- **Rule:** every protected request passes a `core`/`auth` FastAPI dependency that (a) requires a valid JWT from the HttpOnly/Secure/SameSite cookie before any Assignment/Content/Watch-Progress data is served — no flash of protected content before redirect; (b) resolves role + identity from the verified token, never from request params; (c) scopes every query by role — an **Employee** session is hard-scoped to its own identity and can only ever reach its own Assignments/Content/Progress regardless of how the request is formed, while an **HR Admin** session may read org-wide but only through the coaching-shaped read methods of AD-2, never a raw/export path; (d) refuses a valid session presented against a role it lacks with an explicit access-denied, not an empty result. The prototype's latent employee-switch (`getEmployees`/`setSelectedEmployee`) is a hard non-goal — no endpoint exposes it.

### AD-7 — Content ingestion is batch-only; matching is filter-then-rank with a threshold [ADOPTED]

- **Binds:** FR-3, FR-4; `content/`, `content_catalog`
- **Prevents:** exhausting YouTube's ~100 search.list calls/day on live per-request search; surfacing a misleading low-relevance match
- **Rule:** `content_catalog` is populated only by a scheduled batch ingestion job — never a live per-request YouTube search. Recommendations (FR-3) are **filter-then-rank** over already-ingested rows: metadata pre-filter on skill tag, then pgvector cosine ranking within that set, with a relevance threshold below which **no** recommendation is returned (an honest blank beats a wrong match). The skill-matching feature has no real data until ingestion has run at least once (build-order dependency).

### AD-8 — Module dependency direction

- **Binds:** all modules
- **Prevents:** dependency cycles and back-references that let the dashboard's read shape leak into the write-owning modules
- **Rule:** dependencies point one way — the `dashboard` read-composition depends on `assignments` and `progress` read APIs; those modules never depend on the dashboard. `auth`/`core` is a cross-cutting dependency every protected module uses; it depends on none of them. Cross-module calls are Service-API only (AD-1). See diagram.

```mermaid
graph TD
    Core["core/ + auth/ (session gate, config, error contract)"]
    Assign["assignments/"]
    Content["content/"]
    Progress["progress/"]
    Dash["dashboard (read-composition, no table)"]

    Dash --> Assign
    Dash --> Progress
    Assign -. depends on .-> Core
    Content -. depends on .-> Core
    Progress -. depends on .-> Core
    Dash -. depends on .-> Core
```

### AD-9 — Video capture behind a player Adapter [ADOPTED]

- **Binds:** FR-5, FR-6; `progress/` capture pipeline
- **Prevents:** YouTube-specific API details leaking into the capture/progress pipeline, blocking the locked future-Vimeo swap
- **Rule:** the capture pipeline depends on an abstract **player-adapter interface** (normalized `position` + `event-time` + play/pause/ended events), never on YouTube's API surface directly. YouTube's polling `getCurrentTime()`/`onStateChange` lives only behind the adapter; a Vimeo (event-driven `timeupdate`) implementation must be swappable without touching `progress/`. The client-side flush on tab-close/visibilitychange via `sendBeacon` (FR-5, §8 reliability) is part of this boundary.

## Consistency Conventions

| Concern | Convention |
| --- | --- |
| Backend modules | `app/{module}/` each with `router.py`, `service.py`, `repository.py`, `models.py` (SQLAlchemy), `schemas.py` (Pydantic). Cross-module access via Service API only. |
| Naming | Tables snake_case plural (`assignments`, `skill_progress`, `content_catalog`, `assignment_overrides`). REST resources plural-noun, ≤2 levels deep (`/api/assignments`, `/api/skills/{id}/content`, `/api/assignments/{id}/progress`). Frontend feature folders mirror backend module names. |
| IDs & time | Entity IDs opaque UUIDs; storage keys never leaked as API contract. All timestamps ISO-8601 UTC. Watch-progress writes carry an explicit client **event-time** field (AD-5 orders on it). |
| API schemas | Pydantic request/response schemas kept separate from SQLAlchemy ORM models (storage shape must not leak into the contract). Client mirrors them as TS types in `src/types`. |
| Errors | One JSON error contract (`status`, `code`, `message`, `timestamp`) via centralized FastAPI exception handlers; 422 on validation. A failed dashboard refresh after a successful save is a distinct **refresh error**, never a lost Assignment (FR-1). Empty vs error are distinct states, per condition (FR-4). |
| Auth & CORS | JWT in HttpOnly/Secure/SameSite cookie, verified server-side per request (AD-6). `CORSMiddleware` with explicit allowed origins (local dev + built SPA origin), never `*` with credentials. |
| Accessibility | Status badges and Provenance Labels never color-only — always paired with text/icon (WCAG 2.1 AA); live updates announced to screen readers. |
| Validation | Client: React Hook Form + Zod (UX only). Server: Pydantic is the real guard. |
| Real-time | Live dashboard row updates (FR-11, ≤30s) via **client polling** of the dashboard read endpoint — no WebSocket/SSE (research: no server-push requirement). Capture posts periodically (every 5–10s) plus a `sendBeacon` flush on tab-close. |

## Stack

Seed — verified current for 2026 in the overall-stack research (2026-07-08); the code owns exact versions once it exists.

| Name | Version |
| --- | --- |
| Python | 3.12+ |
| FastAPI + uvicorn | current |
| SQLAlchemy (async) + asyncpg | 2.0 |
| PostgreSQL + pgvector | 16+ / current |
| Embedding model | local `sentence-transformers` (e.g. `all-MiniLM-L6-v2`, 384-dim) — free/offline, no API key (supersedes the addendum's `text-embedding-3-small` under zero-budget/local-only) |
| React + TypeScript + Vite | current |
| shadcn/ui + Tailwind CSS | current |
| React Hook Form + Zod | current |
| YouTube IFrame API | polling (`getCurrentTime()`/`onStateChange`), behind an Adapter |
| Docker Compose (local only) | current |
| pytest + httpx / Vitest + RTL | current |

## Structural Seed

### Runtime topology (local only — no production deployment)

```mermaid
graph LR
    Browser["Browser — React SPA (Vite)"]
    API["FastAPI modular monolith (uvicorn)"]
    DB[("PostgreSQL + pgvector")]
    Cron["Scheduled ingestion job"]
    YT["YouTube IFrame Player"]
    YTAPI["YouTube Data API (search.list)"]

    Browser -->|REST/JSON, HttpOnly cookie| API
    Browser <-->|IFrame, client-side capture| YT
    API --> DB
    Cron --> DB
    Cron -->|<= ~100 calls/day| YTAPI

    subgraph Local["Docker Compose — single local environment"]
        API
        DB
        Cron
    end
```

### Core entities

```mermaid
erDiagram
    employees ||--o{ assignments : "assigned"
    skills ||--o{ assignments : "as skill"
    content_catalog ||--o{ assignments : "recommended"
    skills ||--o{ content_catalog : "matched via embedding"
    assignments ||--|| skill_progress : "watch signal"
    assignments ||--o{ assignment_overrides : "HR override"

    assignments {
        uuid id
        uuid employee_id
        uuid skill_id
        uuid content_id
    }
    skill_progress {
        uuid assignment_id
        int watch_position
        timestamptz event_time
    }
    assignment_overrides {
        uuid assignment_id
        uuid set_by
        timestamptz set_at
        boolean active
    }
    content_catalog {
        uuid id
        uuid skill_id
        vector embedding
    }
```

Note: `skill_progress` is keyed by `assignment_id` (not `user_id`+`skill_id` as DD-001 sketched) because FR-1 permits a second intentional Assignment of the same skill to the same Employee — the watch signal belongs to the Assignment, not the (employee, skill) pair.

### Source tree

```text
backend/app/
  core/          # config, JWT/security, CORS, error handlers
  auth/          # login, session/role gate dependency (FR-13/14)
  assignments/   # assignments table + FR-1/FR-2 flow
  content/       # content_catalog + embeddings; matching (FR-3), discovery list (FR-4); ingestion job
  progress/      # skill_progress + assignment_overrides; capture (FR-5/6/7), readiness derivation (FR-8..12)
  dashboard/     # read-composition over assignments + progress (owns no table)
  main.py
frontend/src/
  api/           # per-resource clients
  components/    # shared presentational (Badge, Modal, ...)
  features/      # dashboard, content-discovery, video-progress, assignment, auth
  types/         # TS mirrors of Pydantic schemas
```

## Capability → Architecture Map

| FR | Lives in | Governed by |
| --- | --- | --- |
| FR-1, FR-2 (assign + content review) | `assignments/`, reads `content/` | AD-1, AD-8; error conventions |
| FR-3 (semantic match) | `content/` | AD-7 |
| FR-4 (discovery list) | `content/` + frontend | AD-1, AD-6 (own-data scope) |
| FR-5 (capture) | `progress/` + YouTube Adapter | AD-5, AD-9 |
| FR-6 (resume) | `progress/` + YouTube Adapter | AD-5 (reads last position), AD-9 |
| FR-7 (event-time ordering) | `progress/` | AD-5 |
| FR-8 (Status badge) | `dashboard` ← `progress/` | AD-3 |
| FR-9 (provenance drill-down) | `dashboard` ← `progress/` | AD-2, AD-3 |
| FR-10 (Needs Attention staleness) | `progress/` derivation | AD-3 |
| FR-11 (auto row update) | `dashboard` ← `progress/` | AD-3, AD-5 |
| FR-12 (HR override) | `progress/` | AD-4 |
| FR-13, FR-14 (session/role gate) | `auth/` + `core/` | AD-6 |

## Deferred

- **Production deployment / hosting** — out of scope this build (OQ7 resolved: local working copy only). Revisit only if the pilot moves beyond local. No Kubernetes / serverless-FaaS split / multi-region under any later choice (research constraint).
- **SSO + HRIS roster sourcing** (OQ9 hosted half) — local build seeds accounts/roster; company SSO and roster integration deferred to any hosted version.
- **Compute-on-read vs cached (Status, Provenance) column** — mechanism owned privately by `progress/` (AD-3); not a spine invariant.
- **Proactive dead-content detection / auto-re-matching** (OQ10) — MVP surfaces unavailable content through the existing FR-4/FR-5 video error states only; the Assignment is never lost. Proactive handling deferred.
- **Video-specific staleness for Verified rows** (FR-10 open) — only Self-reported staleness (7d) is defined; whether an abandoned-mid-video Verified row should flag Needs Attention has no source threshold.
- **Self-reported non-video status entry** — no FR provides an in-product entry mechanism; non-video cells stay blank/Unknown or come from outside the product.
- **Data retention period for Watch Progress** (OQ1) — no default locked; does not block MVP.
- **Status/Provenance UI coherence** (OQ11 UX half) — AD-3 closes the structural divergence; whether a badge alone reads clearly, and whether stale rows need a secondary at-a-glance cue, is a UX decision, not an architecture one. Pairs with the untested label-comprehension check (OQ8).
