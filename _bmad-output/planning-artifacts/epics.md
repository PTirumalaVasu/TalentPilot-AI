---
stepsCompleted: ['step-01-validate-prerequisites', 'step-02-design-epics', 'step-03-create-stories', 'step-04-final-validation', 'advanced-elicitation', 'blocker-resolution']
blockersResolved: ['OQ9-LOCAL-provisioning', 'E1.S3-auth-edge-cases', 'E5.S2-privacy-enforcement', 'E1.S7-database-migration-added', 'E2.S2-error-handling']
readinessStatus: 'READY FOR DEVELOPMENT'
inputDocuments:
  - '_bmad-output/planning-artifacts/prds/prd-TalentPilot-AI-2026-07-09/prd.md'
  - '_bmad-output/planning-artifacts/architecture/architecture-TalentPilot-AI-2026-07-09/ARCHITECTURE-SPINE.md'
  - '_bmad-output/C-UX-Scenarios/00-ux-scenarios.md'
  - '_bmad-output/C-UX-Scenarios/01-ritas-trust-call/01-ritas-trust-call.md'
  - '_bmad-output/C-UX-Scenarios/02-caseys-resume-and-watch/02-caseys-resume-and-watch.md'
  - '_bmad-output/C-UX-Scenarios/03-ritas-assignment-and-track/03-ritas-assignment-and-track.md'
projectName: 'TalentPilot-AI'
extractedAt: '2026-07-09'
---

# TalentPilot-AI - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for TalentPilot-AI, decomposing the requirements from the PRD, Architecture Spine, and UX Scenarios into implementable stories organized by the Architecture Spine's build order and feature-domain modules.

**Extracted from:**
- PRD: 14 Functional Requirements (FRs)
- Architecture: 9 Architectural Decisions (ADs) governing 21 architectural requirements
- UX Scenarios: 3 scenarios, 6 core pages, 24 UX design requirements
- **Total Requirements: 75**

---

## Requirements Inventory

### Functional Requirements (14 total)

**Feature 4.1: Skill Assignment Flow**
- FR-1: HR Admin assigns a Skill to an Employee
- FR-2: HR Admin sees AI-recommended Content during assignment

**Feature 4.2: AI-Assisted Content Discovery**
- FR-3: System matches Content to an assigned Skill (semantic matching)
- FR-4: Employee views all their assigned Content in one list, without searching

**Feature 4.3: Automatic Video Progress Capture & Resume**
- FR-5: System captures video watch position automatically
- FR-6: Employee resumes a video at the exact last-watched position
- FR-7: Watch-progress writes are ordered by event time, not by position

**Feature 4.4: Readiness Dashboard — Status at a Glance, Provenance on Drill-Down**
- FR-8: HR Admin views per-Assignment rows with a Status badge (Not Started / In Progress / Completed)
- FR-9: HR Admin drills down into the Provenance Label and raw signal behind a Status badge
- FR-10: Dashboard flags stale self-reported data as "Needs Attention" (7-day threshold)
- FR-11: Dashboard rows update automatically as Watch Progress arrives (≤30 seconds)
- FR-12: HR Admin manually overrides an assignment's readiness status

**Feature 4.5: Authentication & Session Gate**
- FR-13: System requires a valid authenticated session before any Assignment, Content, or Watch Progress data is served
- FR-14: A session is scoped to exactly one role and, for Employees, exactly one identity

---

### Non-Functional Requirements (16 total)

**Latency:**
- NFR-L1: Readiness Dashboard loads in under 2 seconds
- NFR-L2: Content/video player loads in under 3 seconds
- NFR-L3: New Assignment appears on dashboard within 1 second of confirm
- NFR-L4: Video resume starts within 1 second of clicking Continue Watching
- NFR-L5: Dashboard rows reflect a new watch-position update within 30 seconds without manual refresh

**Data Integrity:**
- NFR-DI1: Watch-progress writes are ordered by event timestamp, never by position value (FR-7 binding)
- NFR-DI2: Assignment creation must not be lost by a failed dashboard refresh
- NFR-DI3: Canceled assignment flow leaves no orphaned record

**Write Integrity (Anti-spoofing):**
- NFR-WI1: Watch Progress updates are validated server-side before persisted
- NFR-WI2: Position must advance at a rate consistent with real playback (not instantaneous jumps)
- NFR-WI3: Updates require a valid authenticated session tied to the actual Assignment

**Coaching-only Enforcement:**
- NFR-C1: Raw Watch Progress and drill-down history are not exposed through any interface, export, or report shaped for performance review
- NFR-C2: Access is scoped to Readiness Dashboard's stated coaching use, enforced at the data-access layer

**Reliability of Capture:**
- NFR-R1: Watch position flushes on tab close / visibility change via `sendBeacon`

**Accessibility:**
- NFR-A1: WCAG 2.1 AA compliance
- NFR-A2: Status badges and Provenance Labels are never color-only
- NFR-A3: Assignment and dashboard drill-down flows are keyboard-operable end-to-end
- NFR-A4: Dynamic updates (success toast, live row updates) are announced to screen readers

**Platform:**
- NFR-P1: Responsive web, desktop-first
- NFR-P2: No offline mode, no native app, no PWA in v1

**Feature-Specific (FR-4):**
- NFR-F1: Content ingestion runs as a scheduled batch job, not live per-request search

---

### Architectural Requirements (21 total)

**Architectural Invariants (binding all FRs):**
- AR-1: Single-owner data modules — each table has exactly one owning module; all other features access via Service API (AD-1)
- AR-2: Coaching-only is a read boundary — `skill_progress` reachable only through `progress/` coaching-shaped read methods (AD-2)
- AR-3: Single derivation authority for (Status, Provenance) — computed in exactly one place (`progress/`) from {watch signal, self-report staleness (7 days), active HR override} (AD-3)
- AR-4: HR Override is a separate, coexisting record — never a field-overwrite on `skill_progress` (AD-4)
- AR-5: Watch-progress write path — conditional write ordered by client event-timestamp; requires server-side anti-spoofing (AD-5)
- AR-6: Server-side session/role/identity gate on every request (AD-6)
- AR-7: Content ingestion is batch-only; matching is filter-then-rank with a threshold (AD-7)
- AR-8: Module dependency direction — dependencies point one way; `dashboard` depends on `assignments` and `progress` but never the reverse (AD-8)
- AR-9: Video capture behind a player Adapter — YouTube-specific details encapsulated, future-proof for Vimeo swap (AD-9)

**Data Model Consistency:**
- AR-10: Entity IDs are opaque UUIDs; all timestamps ISO-8601 UTC
- AR-11: API schemas (Pydantic) kept separate from SQLAlchemy ORM models
- AR-12: One centralized JSON error contract (`status`, `code`, `message`, `timestamp`)
- AR-13: Failed dashboard refresh after successful save is a distinct **refresh error**, never a lost Assignment
- AR-14: Empty vs error are distinct states (FR-4)

**Deployment & Stack:**
- AR-15: Local working copy only; no production deployment (out of scope)
- AR-16: Docker Compose local environment (Postgres+pgvector + uvicorn + Vite)
- AR-17: Python 3.12+, FastAPI, SQLAlchemy 2.0 async + asyncpg, PostgreSQL 16+
- AR-18: React+TS+Vite, shadcn/ui+Tailwind, React Hook Form+Zod
- AR-19: Embedding model: local `sentence-transformers` (e.g., `all-MiniLM-L6-v2`, 384-dim)
- AR-20: YouTube IFrame API (polling-based `getCurrentTime()`/`onStateChange` behind Adapter)
- AR-21: Client polling for live dashboard updates (≤30s), no WebSocket/SSE

---

### UX Design Requirements (24 total)

**Scenario-Driven Interaction Contracts:**
- UX-DR1: Assignment Dashboard grid displays one row per Employee×Skill assignment with Status badge (Not Started / In Progress / Completed) as primary at-a-glance signal
- UX-DR2: Provenance Drill-Down modal reachable from every dashboard row in one click, showing Provenance Label and raw data (watch %, last-updated timestamp, attribution)
- UX-DR3: Content Discovery shows list of all Employee's assigned Skills/Content grouped by status (In Progress / To Start) with summary counts (Total / In Progress / To Start)
- UX-DR4: Resume/Continue Watching card shows progress bar, "X min remaining" text, large play button, resumes at exact position on first use
- UX-DR5: Skill Assignment Flow is a multi-step modal (select employee → select skill → review AI-recommended content → confirm) completing in under 2 minutes
- UX-DR6: Assignment Confirmation shows new row on dashboard immediately with Status `Not Started`, success toast notification, and row highlighted for several seconds

**State & Feedback Patterns:**
- UX-DR7: Empty state for no Content matched yet ("No recommended content yet for this skill. [Contact Rita]")
- UX-DR8: Empty state for nothing in progress ("Nothing in progress right now. [View your assignments]")
- UX-DR9: Error state for video load failure ("This video couldn't be loaded. [Try again]"), not silent blank player
- UX-DR10: Refresh error distinct from save error when dashboard refresh fails after successful Assignment save
- UX-DR11: Continue-Watching shows explicit empty state before any video watched, not blank space
- UX-DR12: Success toast on Assignment creation ("✓ Skill assigned to {Employee first name} — {Skill name}")

**Accessibility & Visual Consistency:**
- UX-DR13: Status badges never color-only; always paired with text or icon (WCAG 2.1 AA)
- UX-DR14: Provenance Labels never paired text or icon (WCAG 2.1 AA)
- UX-DR15: Freshness stated in plain language in drill-down ("Not updated in 14 days"), not ambiguous status word
- UX-DR16: HR Admin can defend any readiness call, not only flagged ones — drill-down reachable from every row
- UX-DR17: Canceled assignment flow at any step before confirm leaves no orphaned Assignment record

**Content & Assignment Interaction:**
- UX-DR18: If Skill already assigned to Employee, flow surfaces existing Assignment rather than silently creating duplicate
- UX-DR19: If no matching Content exists for a Skill, flow allows assignment without Content ("No approved content found yet. [Choose Different Content] or [Assign without content]")
- UX-DR20: If Content fails to load, Employee sees explicit error state, not silent blank player
- UX-DR21: No search box in Content Discovery — strictly assignments-scoped list, never browsable catalog

**Real-Time & Behavioral:**
- UX-DR22: Dashboard row Status updates automatically as Watch Progress data arrives (Not Started → In Progress → Completed)
- UX-DR23: HR Override can be reversed by HR Admin; if fresher Watch Progress arrives, both are visible in drill-down and override stands until explicitly changed
- UX-DR24: All dynamic updates announced to screen readers (success toast, live row updates), not just visually rendered

---

### FR Coverage Map

| FR | Module | Epic | Realized By Stories | Status |
|----|----|----|----|---|
| FR-1 | `assignments/` | Epic 3 | E3.S1, E3.S2, E3.S3 | Pending |
| FR-2 | `assignments/`, `content/` | Epic 3 | E3.S2, E3.S3 | Pending |
| FR-3 | `content/` | Epic 2 | E2.S2, E2.S3 | Pending |
| FR-4 | `content/`, frontend | Epic 2 | E2.S4 | Pending |
| FR-5 | `progress/` + YouTube Adapter | Epic 4 | E4.S1, E4.S2 | Pending |
| FR-6 | `progress/` + YouTube Adapter | Epic 4 | E4.S3 | Pending |
| FR-7 | `progress/` | Epic 4 | E4.S2 | Pending |
| FR-8 | `dashboard` ← `progress/` | Epic 5 | E5.S1 | Pending |
| FR-9 | `dashboard` ← `progress/` | Epic 5 | E5.S2 | Pending |
| FR-10 | `progress/` derivation | Epic 5 | E5.S3 | Pending |
| FR-11 | `dashboard` ← `progress/` | Epic 5 | E5.S4 | Pending |
| FR-12 | `progress/` | Epic 5 | E5.S5 | Pending |
| FR-13 | `auth/` + `core/` | Epic 1 | E1.S1, E1.S2 | Pending |
| FR-14 | `auth/` + `core/` | Epic 1 | E1.S3, E1.S4 | Pending |

---

## Recommended Epic Sequence (Architecture Spine Build Order)

Based on the Architecture Spine's module dependency order (AD-8) and the build-time constraints:

1. **Epic 1: Authentication & Session Gate** — Foundation for all protected endpoints (FR-13, FR-14)
2. **Epic 2: Content Catalog & Matching** — Dependency for assignments and discovery (FR-3, FR-4); requires batch ingestion job
3. **Epic 3: Skill Assignment Flow** — HR's entry point to the system (FR-1, FR-2)
4. **Epic 4: Video Progress Capture & Resume** — Automatic signal generation (FR-5, FR-6, FR-7); YouTube Adapter dependency
5. **Epic 5: Readiness Dashboard** — Composition of assignments + progress (FR-8 through FR-12); depends on all prior epics

---

## Epic List

- **Epic 1:** Authentication & Session Gate (FR-13, FR-14; AR-6)
- **Epic 2:** Content Catalog, Semantic Matching & Discovery (FR-3, FR-4; AR-7)
- **Epic 3:** Skill Assignment Flow & Content Review (FR-1, FR-2)
- **Epic 4:** Video Progress Capture, Resume & Event-Time Ordering (FR-5, FR-6, FR-7; AR-5, AR-9)
- **Epic 5:** Readiness Dashboard — Status, Provenance, Auto-Update & Override (FR-8 through FR-12; AR-2, AR-3, AR-4)

---

## EPIC 1: Authentication & Session Gate

**Epic Goal:** Establish a secure, role-scoped session mechanism that gates all protected endpoints (Assignment, Content, Watch Progress data) and enforces coaching-only privacy boundaries.

**Owned by:** `auth/` module, `core/` security layer (AD-6)

**Binds:** FR-13, FR-14, AR-6, NFR-A3, NFR-C1, NFR-C2

---

### Story 1.1: Project Structure & Core Dependencies

As a **developer**,
I want to initialize the FastAPI project structure with core dependencies (uvicorn, SQLAlchemy, asyncpg, Pydantic, JWT libraries),
So that I have a foundation for building the modular monolith.

**Acceptance Criteria:**

**Given** a fresh project directory  
**When** I run the project initialization script  
**Then** I have:
- FastAPI application entry point (`main.py`) with CORS, error handlers, and middleware
- SQLAlchemy 2.0 async engine with asyncpg driver configured for PostgreSQL
- JWT security utilities for token generation/validation
- Centralized error contract JSON handler (status, code, message, timestamp)
- Docker Compose configuration for local Postgres+pgvector+Redis (if used)

**And** the project structure follows `backend/app/{module}/` with `router.py`, `service.py`, `repository.py`, `models.py`, `schemas.py` per module

**And** environment variables are externalized (`.env` template with DATABASE_URL, JWT_SECRET, etc.)

---

### Story 1.2: JWT Token Generation & Session Model

As a **developer**,
I want to implement JWT token generation and validation within the auth module,
So that sessions can be created and verified securely.

**Acceptance Criteria:**

**Given** an HR Admin or Employee attempting login  
**When** credentials are validated  
**Then** a JWT token is generated containing:
- User identity (user_id, role)
- Expiration time (default: 24 hours, configurable)
- Signature using HS256 or RS256 (locked in addendum as HS256 for simplicity)

**And** the token is stored in an HttpOnly/Secure/SameSite cookie (not in localStorage or URL params)

**And** token validation on every protected request:
- Extracts JWT from cookie
- Verifies signature and expiration
- Rejects expired tokens with 401 Unauthorized
- Rejects invalid signatures with 401 Unauthorized

---

### Story 1.3: Role & Identity Scoping on Every Request

As a **developer**,
I want to enforce role and identity scoping at the FastAPI dependency layer,
So that every protected request is validated server-side before data access.

**Acceptance Criteria:**

**Given** a request to a protected endpoint with a valid JWT  
**When** the request includes role and user_id claims  
**Then** a FastAPI dependency extracts both claims and validates:
- Role ∈ {HR_ADMIN, EMPLOYEE}
- User identity (user_id) is present and non-null

**And** for EMPLOYEE sessions, the identity is hard-scoped — the same user_id is used to filter all queries, making cross-employee data retrieval impossible regardless of request parameters

**And** for HR_ADMIN sessions, role is verified but data access filters are applied by the downstream service layer (not here)

**EDGE CASE: Missing Role Claim**  
**Given** JWT token with no "role" key present  
**When** the dependency validates the JWT  
**Then** the request returns **401 Unauthorized** (not 403, distinguishing missing from invalid) with error message: "JWT missing required 'role' claim"

**EDGE CASE: Invalid Role Value**  
**Given** JWT with role="UNKNOWN" or role="admin" (typo, not matching enum)  
**When** the dependency validates the JWT  
**Then** the request returns **403 Forbidden** with error code 'INVALID_ROLE' and message: "Role 'UNKNOWN' not recognized. Expected: HR_ADMIN or EMPLOYEE"

**EDGE CASE: EMPLOYEE Session Missing user_id**  
**Given** JWT with role="EMPLOYEE" but user_id is missing or null  
**When** the dependency validates the JWT  
**Then** the request returns **400 Bad Request** with error message: "EMPLOYEE role requires user_id claim; token rejected"

**EDGE CASE: Valid HR_ADMIN Role**  
**Given** JWT with role="HR_ADMIN" and valid user_id  
**When** the dependency validates the JWT  
**Then** request proceeds (passes validation); user is authenticated as HR Admin

**EDGE CASE: Valid EMPLOYEE Role**  
**Given** JWT with role="EMPLOYEE" and valid user_id  
**When** the dependency validates the JWT  
**Then** request proceeds (passes validation); user is authenticated as Employee with identity scoped to their user_id

---

### Story 1.4: Login Endpoint & Credential Store (Mock for MVP)

As an **HR Admin or Employee**,
I want to log in with my credentials,
So that I can access Assignment, Content, and Watch Progress data.

**Acceptance Criteria:**

**Given** I navigate to `/login`  
**When** I submit my email and password  
**Then** the backend validates against a **mock credential store** (hardcoded for MVP, not a real LDAP/SSO — see Open Question 9):
- HR Admins: `rita@sails.example.com` / `demo123` → role: HR_ADMIN
- Employees: `casey@sails.example.com`, `morgan@sails.example.com`, etc. / `demo123` → role: EMPLOYEE, scoped to their own identity

**And** on successful validation, a JWT is generated and stored in an HttpOnly/Secure/SameSite cookie

**And** user is redirected to the role-appropriate entry point (Assignment Dashboard for HR, Content Discovery for Employee)

**And** on failed validation, an error message is shown ("Email or password incorrect") without revealing which field failed

---

### Story 1.5: Sign Out & Session Invalidation

As an **HR Admin or Employee**,
I want to sign out,
So that my session is terminated and no one else can use my session token.

**Acceptance Criteria:**

**Given** I am logged in and click Sign Out  
**When** Sign Out is triggered  
**Then** the session cookie is cleared (deleted, not just expired)

**And** any subsequent request with that JWT is rejected with 401 Unauthorized, even if the token itself hasn't expired yet

**And** I am redirected to the login page

**And** if I use the browser back button, I cannot access a previously-open protected page without re-authenticating

---

### Story 1.6: Protected Endpoint Gate — No Flash of Protected Content

As a **developer**,
I want protected endpoints to reject unauthenticated requests before rendering any data,
So that no confidential Assignment/Content/Watch Progress data leaks before a redirect.

**Acceptance Criteria:**

**Given** a request to a protected endpoint (e.g., `/api/assignments`, `/api/content`, `/api/dashboard`) with no session or an expired session  
**When** the FastAPI dependency validates the JWT  
**Then** the request is rejected with 401 Unauthorized before the route handler executes

**And** the frontend receives 401 and redirects to login, not a 200 response with no data

**And** no partial data, data structure, or timing information is returned that could leak the existence of endpoints or data

---

### Story 1.7: Database Schema Initialization & Migration

As a **developer**,
I want the application to initialize or migrate the database schema on startup,
So that first-time deployments succeed and schema drift is caught early.

**Acceptance Criteria:**

**GIVEN** a fresh PostgreSQL instance with no tables  
**WHEN** the FastAPI application starts  
**THEN** all required tables are created in the correct order:
- `accounts` (for local auth credentials, locked by OQ9 decision: LOCAL)
- `employees` (HR and Employee roster)
- `skills` (skill master data)
- `content_catalog` (video/doc/website catalog with pgvector embeddings)
- `assignments` (Employee × Skill links)
- `skill_progress` (watch position + event time for videos)
- `assignment_overrides` (HR manual override records)

**AND** all foreign keys, indexes, and constraints are created correctly (no referential integrity errors on first data insert)

**GIVEN** an existing database with an outdated schema  
**WHEN** the application starts  
**THEN** schema migration logic runs automatically:
- Compares current schema version to expected version
- Applies pending migrations (if using Alembic or similar)
- Database schema is updated to current version
- Application startup succeeds (idempotent, no duplicate-key or constraint errors)

**GIVEN** an application restart against the current schema version  
**WHEN** the application starts  
**THEN** startup succeeds without re-running migrations (idempotent, no errors)

**GIVEN** a schema version mismatch is detected (e.g., expected v5, found v3)  
**WHEN** the application attempts to start  
**THEN** startup fails fast with a clear error message (NOT a cryptic database error later):
```
ERROR: Database schema version mismatch
Current schema version: 3
Expected schema version: 5
This application requires database schema version 5.

To migrate, run: alembic upgrade head
(or equivalent migration command for chosen tool)

See migration logs in: _logs/migration.log
```

**AND** this error is logged with full stack trace for debugging

**AND** no application code executes past this check (fail-fast principle, not silent schema-drift)

---

## EPIC 2: Content Catalog, Semantic Matching & Discovery

**Epic Goal:** Build the content catalog foundation with semantic embedding-based matching, batch ingestion from YouTube, and the Employee-scoped discovery list view.

**Owned by:** `content/` module (AD-7)

**Binds:** FR-3, FR-4, AR-7, NFR-F1, UX-DR3, UX-DR7, UX-DR8, UX-DR21

**Dependencies:** Epic 1 (authentication)

---

### Story 2.1: Content Catalog Data Model & Schema

As a **developer**,
I want to define the Content Catalog data model and API schemas,
So that content records can be stored and matched to Skills.

**Acceptance Criteria:**

**Given** the architecture requirement for semantic matching  
**When** I define the `content_catalog` table  
**Then** it includes:
- `id` (UUID primary key)
- `skill_id` (UUID, foreign key to skills table — see dependencies)
- `title` (string, content name)
- `description` (text, content metadata)
- `type` (enum: VIDEO, DOCUMENT, WEBSITE)
- `url` (string, external URL)
- `embedding` (pgvector 384-dim, from `sentence-transformers` model)
- `source` (enum: YOUTUBE, MANUAL, etc.)
- `ingested_at` (timestamp)
- `metadata` (JSONB for source-specific fields: YouTube video ID, duration, etc.)

**And** a Pydantic schema for Content responses (without the raw embedding vector, unless explicitly requested for admin/debug purposes)

**And** a separate internal schema for embedding computation (text input → vector output)

---

### Story 2.2: Embedding Model Integration (Sentence-Transformers)

As a **developer**,
I want to integrate a local embedding model (sentence-transformers),
So that Skill names and Content descriptions can be vectorized for semantic matching.

**Acceptance Criteria:**

**Given** the architecture locked a local free embedding model  
**When** the app starts  
**Then** it loads a pre-trained `sentence-transformers` model (e.g., `all-MiniLM-L6-v2`, 384-dim):
- Downloads/caches it locally (no API calls, no quota concerns)
- Loads into memory once per app startup

**And** a utility function `embed_text(text: str) -> ndarray[384]` is available to compute embeddings on demand

**And** the embedding is deterministic (same input always produces the same vector)

**And** the model is never called per-request; embeddings are pre-computed during ingestion and stored in pgvector

**ERROR HANDLING & DIAGNOSTICS:**

**GIVEN** app startup WHEN sentence-transformers model download fails (network error, DNS failure, repository unavailable, invalid PyPI version)  
**THEN** app fails fast with a clear, actionable error message:
```
ERROR: Embedding model download failed
Model: all-MiniLM-L6-v2 (sentence-transformers)
Reason: Network error - connection timeout

Diagnostics:
- Check network connectivity: can reach huggingface.co?
- Check disk space: at least 100MB free?
- Check PyPI access: `pip install sentence-transformers==<version>` manually?

The application cannot start without the embedding model.
See logs: _logs/embedding_model_error.log
```
(NOT a hung process, NOT silent failure)

**GIVEN** app startup WHEN model file is corrupted or checksum mismatch  
**THEN** app fails with error: "Model file corrupted or checksum mismatch. Delete cache: ~/.cache/huggingface/models/ and retry."

**GIVEN** app startup WHEN model output shape is wrong (e.g., 768-dim instead of 384-dim)  
**THEN** app fails with error: "Unexpected embedding shape: model produced 768-dim vector, expected 384-dim. Check model name and version match configuration."

**GIVEN** app successfully loads model WHEN `embed_text('sample')` is called  
**THEN** inference completes in under 100ms (measured for batch ingestion latency requirement)

**GIVEN** app startup with model loaded WHEN checking memory footprint  
**THEN** memory usage for loaded model is logged: "Embedding model loaded (~100MB memory)" (so operator can monitor)

**GIVEN** a crash or OOM during model load  
**THEN** error is caught, logged with stack trace, and app exits with status code 1 and clear message (not a zombie process)

---

### Story 2.3: Batch Content Ingestion Job (YouTube Search)

As a **developer**,
I want to build a scheduled batch job that discovers and ingests video content from YouTube,
So that the `content_catalog` is populated without exhausting YouTube's daily API quota.

**Acceptance Criteria:**

**Given** a list of Skills to ingest content for  
**When** the batch job runs (e.g., once per day via cron/APScheduler)  
**Then** for each Skill:
- The Skill name is used to search YouTube's `search.list` API (respecting ~100 calls/day quota)
- Top N results are retrieved (e.g., top 3 videos per Skill)
- For each video, metadata is fetched (title, description, duration, thumbnail URL)
- A `sentence-transformers` embedding is computed from the title + description

**And** the embedding and metadata are stored in `content_catalog` with `source: YOUTUBE`

**And** if a video is already in the catalog (de-duped by YouTube video ID), it is skipped

**And** the job logs success/failure per Skill; on quota exhaustion, it stops gracefully and logs the next run date

**And** manual seeding is supported: a CLI command or admin endpoint allows inserting content directly without triggering a YouTube search

---

### Story 2.4: Semantic Content Matching (Filter-then-Rank)

As a **developer**,
I want to implement semantic content matching using pgvector cosine similarity,
So that relevant (but not exact-tag-matched) content is surfaced for a Skill.

**Acceptance Criteria:**

**Given** a Skill with an assignment  
**When** the system needs to recommend Content  
**Then** matching logic applies:
- **Pre-filter:** retrieve all Content rows for the same Skill ID (metadata filter)
- **Rank:** compute cosine similarity between Skill embedding and each Content embedding using pgvector
- **Threshold:** filter to Content above a relevance threshold (e.g., cosine similarity > 0.7)
- **Sort:** rank by similarity descending; return top 1 (for FR-3/FR-4)

**And** if no Content clears the threshold, return `null` (no recommendation) rather than a low-quality match

**And** the matching is deterministic and repeatable (same Skill, same ranked result each time, unless ingestion adds new content)

---

### Story 2.5: Content Discovery List — Employee View (Assigned Skills, Grouped by Status)

As an **Employee**,
I want to see all my assigned Skills with their recommended Content, grouped by watch status,
So that I know what I need to learn and what I've already started.

**Acceptance Criteria:**

**Given** I am authenticated as an Employee and have multiple assigned Skills  
**When** I navigate to Content Discovery  
**Then** I see:
- A list of my assigned Skills (scoped to my identity via session)
- Each Skill has its recommended Content and status (In Progress / To Start)
- Summary counts at the top: "Total: 5 | In Progress: 2 | To Start: 3"
- Grouped sections: **In Progress** (with Continue Watching card if applicable) and **To Start**

**And** there is NO search box, filter control, or ability to browse other Content — strictly my assignments

**And** for each Content item:
- Title, type (Video / Document / Website), source
- For videos: duration and current watch position (if any)
- A play/open button to start or resume

**And** if a Skill has no matched Content yet, the row shows "No recommended content yet for this skill. [Contact Rita]"

**And** if I have no assignments, the view shows "Nothing in progress right now. [View your assignments]"

---

### Story 2.6: Empty & Error States for Content Discovery

As a **developer**,
I want to handle edge cases in Content Discovery,
So that the UI is always in a defined state.

**Acceptance Criteria:**

**Given** various content states  
**When** rendering Content Discovery  
**Then** I handle:
- **No assignments:** "Nothing in progress right now. [View your assignments]"
- **Assignments but no matched Content:** "No recommended content yet for this skill. [Contact Rita]"
- **Video load failure:** "This video couldn't be loaded. [Try again]" (not a silent blank player)
- **Continue Watching with no video watched:** explicit empty state, not blank space
- **API error fetching content list:** distinct error message, not a blank grid

**And** each state is visually distinct (colors, text, icons) — never relying on color alone (WCAG 2.1 AA, NFR-A2)

---

## EPIC 3: Skill Assignment Flow & Content Review

**Epic Goal:** Enable HR Admins to assign Skills to Employees and review AI-recommended Content as part of the assignment workflow.

**Owned by:** `assignments/` module, `content/` for content lookup (AD-1)

**Binds:** FR-1, FR-2, UX-DR5, UX-DR6, UX-DR12, UX-DR17, UX-DR18, UX-DR19, NFR-L3, NFR-DI2, NFR-DI3

**Dependencies:** Epic 1 (authentication), Epic 2 (content catalog)

---

### Story 3.1: Assignments Data Model & HR Admin Scope

As a **developer**,
I want to define the Assignments data model,
So that HR Admins can create and manage Skill-to-Employee links.

**Acceptance Criteria:**

**Given** the architecture's single-owner pattern  
**When** I define the `assignments` table  
**Then** it includes:
- `id` (UUID primary key)
- `employee_id` (UUID, foreign key to employees)
- `skill_id` (UUID, foreign key to skills)
- `content_id` (UUID, nullable, foreign key to content_catalog — the AI-recommended match)
- `assigned_at` (timestamp, when HR created this assignment)
- `assigned_by` (UUID, HR Admin who created it)

**And** a constraint: (employee_id, skill_id) may have multiple rows (same skill can be intentionally re-assigned), but each row is a distinct Assignment

**And** Pydantic schemas for:
- CreateAssignmentRequest (employee_id, skill_id)
- AssignmentResponse (full assignment with Status, Provenance computed server-side)

**And** all mutations restricted to HR Admin sessions via the `auth/` dependency (role check)

---

### Story 3.2: Skill Master Data & Seed

As a **developer**,
I want to seed the Skills master table,
So that HR Admins can assign from a defined list.

**Acceptance Criteria:**

**Given** the TalentPilot MVP scope  
**When** the app starts for the first time  
**Then** a seed script populates the `skills` table with:
- Core skills from the Product Brief / design-thinking discovery (e.g., "Data Visualization", "Salesforce Admin", etc.)
- At least 5-10 starter skills to demo the system

**And** each Skill has:
- `id` (UUID)
- `name` (string, unique)
- `description` (optional text)
- `embedding` (pgvector 384-dim, computed from skill name for semantic matching against Content)

**And** the seed is idempotent (can run multiple times without duplication)

---

### Story 3.3: Employee Master Data & Seed

As a **developer**,
I want to seed the Employees master table,
So that HR Admins can assign Skills to known Employees.

**Acceptance Criteria:**

**Given** the MVP's local-only mock credential store  
**When** the app starts for the first time  
**Then** a seed script populates the `employees` table with:
- Employee records matching the mock credentials (Rita, Casey, Morgan, Jordan, Sam)
- Each with: `id` (UUID), `name`, `email`, `role` (EMPLOYEE or HR_ADMIN)

**And** HR Admins are seeded as Employees with role HR_ADMIN (so they can be assigned content for their own learning too, if needed)

**And** the seed is idempotent

**And** Open Question 9 is noted: this local seed will be replaced with an actual HRIS/SSO roster in production

---

### Story 3.4: HR Assignment Flow — Multi-Step Modal (Employee + Skill Selection)

As an **HR Admin**,
I want to open an assignment modal, select an Employee and Skill, and confirm,
So that I can create new assignments quickly.

**Acceptance Criteria:**

**Given** I am authenticated as an HR Admin on the Assignment Dashboard  
**When** I click `[+ New Assignment]`  
**Then** a modal opens with:

**Step 1 — Employee Select:**
- Dropdown/searchable list of all Employees
- Search by name or email
- Single selection

**And Step 2 — Skill Select:**
- Dropdown/searchable list of all Skills
- Search by name or description
- Single selection

**And** if the selected (Employee, Skill) pair is already assigned, the modal displays:
- "This skill is already assigned to {Employee}. [View] or [Assign Again]"
- Choosing [View] goes to that Assignment's row on the dashboard
- Choosing [Assign Again] creates a second intentional assignment (allowed per FR-1)

**And Step 3 — Content Review:**
- Display the AI-recommended Content for the selected Skill (if any exists)
- Show: Content title, type, description, duration (for video)
- Text: "The system has recommended this content for {Skill name}. You can review it below."
- "Proceed with this content" or "[Choose Different Content]" or "[Assign without content]"

**And** if no Content matches, skip to confirmation with text: "No approved content found yet for this skill. [Proceed] or [Assign without content]"

**And Step 4 — Confirmation:**
- Summary: "{Employee name} will be assigned {Skill name}"
- If content: "+ Recommended content: {Content title}"
- [Confirm] or [Cancel]

**And** the entire flow completes in under 2 minutes for a typical assignment (NFR-L3 feedback target)

---

### Story 3.5: Assignment Creation & Immediate Dashboard Appearance

As an **HR Admin**,
I want to confirm an assignment and see it appear on the dashboard immediately,
So that I know it was saved and can track progress without manual refresh.

**Acceptance Criteria:**

**Given** I confirm an assignment in the modal  
**When** the POST `/api/assignments` request succeeds  
**Then**:
- The new Assignment row appears on the Readiness Dashboard within 1 second (NFR-L3)
- Status badge shows `Not Started` (FR-8)
- Provenance shows `Assigned · Awaiting first watch` (derived from having no Watch Progress yet)
- A success toast appears: "✓ Skill assigned to {Employee first name} — {Skill name}"
- The new row is visually highlighted (e.g., background color or border) for 3–5 seconds so HR can locate it

**And** if the Assignment is created but the dashboard fails to refresh (e.g., websocket/polling error), the UI shows a distinct refresh error (AR-13, NFR-DI2):
- "Assignment saved, but dashboard didn't update. [Retry]"
- The Assignment itself is not lost; retrying the fetch succeeds

**And** if the POST itself fails (validation, DB error), the modal stays open with an error message and [Cancel] to close

---

### Story 3.6: Cancel Assignment Flow Leaves No Orphaned Record

As an **HR Admin**,
I want to cancel the assignment flow at any step,
So that I can start over or abandon the action without polluting the database.

**Acceptance Criteria:**

**Given** I am in the assignment modal at any step (Employee select, Skill select, Content review, or Confirmation)  
**When** I click [Cancel] or close the modal  
**Then**:
- No Assignment record is created
- No partial data persists in the backend
- The modal closes cleanly
- I return to the Assignment Dashboard as if I never opened the modal

**And** this holds even if I cancel on the final Confirmation step

---

## EPIC 4: Video Progress Capture, Resume & Event-Time Ordering

**Epic Goal:** Automatically capture Employee video watch positions, enable exact-position resume, and order writes by event timestamp to prevent stale writes from regressing progress.

**Owned by:** `progress/` module, YouTube Adapter pattern (AD-9)

**Binds:** FR-5, FR-6, FR-7, AR-5, AR-9, NFR-DI1, NFR-WI1, NFR-WI2, NFR-WI3, NFR-R1, NFR-L4, UX-DR4

**Dependencies:** Epic 1 (authentication), Epic 3 (assignments), Epic 4.0 (YouTube IFrame Adapter)

---

### Story 4.0: YouTube IFrame Adapter — Abstraction Layer for Player Events

As a **developer**,
I want to build an Adapter abstraction over YouTube's player API,
So that the capture pipeline is decoupled from YouTube-specific details.

**Acceptance Criteria:**

**Given** the architecture's design (AD-9) to future-proof for Vimeo  
**When** I implement a player adapter  
**Then** it provides a normalized interface:

```typescript
interface PlayerAdapter {
  position(): number                    // current playback position in seconds
  duration(): number                    // total video duration
  on(event: 'play' | 'pause' | 'ended' | 'timeupdate', handler: () => void): void
  sendBeacon(position: number, eventTime: string): Promise<void>
}
```

**And** the YouTube adapter implementation:
- Uses YouTube IFrame API's polling-based `getCurrentTime()` (not event-driven like Vimeo)
- Polls every 5–10 seconds during playback to capture position
- Listens to `onStateChange` events (PLAYING, PAUSED, ENDED)
- On tab close / visibility change, calls `sendBeacon()` to flush the last position

**And** the adapter is instantiated per video playback session (one per `<iframe>` element)

**And** a future Vimeo adapter would implement the same interface but use event-driven `timeupdate` instead of polling

---

### Story 4.1: Skill Progress Data Model & Watch-Position Storage

As a **developer**,
I want to define the Skill Progress data model,
So that watch positions can be stored and retrieved efficiently.

**Acceptance Criteria:**

**Given** the architecture's data model (AD-3, AD-5)  
**When** I define the `skill_progress` table  
**Then** it includes:
- `id` (UUID primary key, internal)
- `assignment_id` (UUID, unique, foreign key to assignments — keyed by Assignment, not (Employee, Skill) pair, to allow duplicate assignments)
- `watch_position` (integer, seconds, 0–max_duration)
- `event_time` (timestamp UTC, when the client observed this position)
- `verified` (boolean, true if passed server-side anti-spoofing checks)
- `updated_at` (timestamp UTC, server time when record was persisted)

**And** Pydantic schemas for:
- RecordWatchProgressRequest (assignment_id, watch_position, event_time, video_url_for_context)
- SkillProgressResponse (position, event_time, verified flag, Attribution)

**And** no progress row exists until the first watch-position is recorded (lazy initialization)

---

### Story 4.2: Watch-Position Capture & Periodic Posting from Client

As a **developer**,
I want to collect watch-position samples from the player adapter and post them to the backend,
So that the system has a record of Employee watch behavior.

**Acceptance Criteria:**

**Given** an Employee is watching a video  
**When** the page is actively displayed  
**Then** on the client side:
- The player adapter samples position every 5–10 seconds
- Each sample is queued locally (not posted immediately)
- A client-side capture service batches samples and posts them via `POST /api/assignments/{assignment_id}/progress`
- Post frequency: every 10–15 seconds (or when queue has 3+ samples)
- Request body includes:
  - `assignment_id` (UUID)
  - `watch_position` (seconds)
  - `event_time` (ISO-8601 client timestamp of when the position was observed)
  - `video_url` (for server-side anti-spoofing validation)

**And** on successful POST (201 Created), the backend returns the persisted record with `verified: true/false`

**And** client-side error handling: if POST fails (network error), samples are queued locally and re-tried on the next interval (do not spam the server)

---

### Story 4.3: Tab-Close Flush via sendBeacon (Reliability)

As a **developer**,
I want to ensure the last watch position is flushed when the tab is closed or hidden,
So that no progress is lost if the Employee closes mid-watch.

**Acceptance Criteria:**

**Given** an Employee is watching a video  
**When** the tab is closed, hidden (browser tab switch), or the page unloads  
**Then** the client-side capture service:
- Listens to `visibilitychange` and `beforeunload` events
- Calls the player adapter's `sendBeacon(position, eventTime)` method
- `sendBeacon` uses the browser's `navigator.sendBeacon()` API to send a POST (not guaranteed delivery, but best-effort even during unload)
- Request includes the last known position and its event timestamp

**And** if `sendBeacon` fails or is not supported, it logs a warning but does not error (best-effort, not blocking)

**And** this behavior is tested against multiple tab-close scenarios (direct close, alt-tab switch, browser tab switch)

---

### Story 4.4: Server-Side Anti-Spoofing: Validate Position Advances

As a **developer**,
I want to validate watch-position updates on the server,
So that a spoofed or forged position (e.g., jumping to 100% instantly) is rejected and not marked as Verified.

**Acceptance Criteria:**

**Given** a POST `/api/assignments/{assignment_id}/progress` request  
**When** the backend receives a watch-position update  
**Then** the `progress/` service validates:
- **Session tie:** The request's authenticated session identity matches the Assignment's Employee ID (prevents cross-employee spoofing via Open Question 12 latent endpoint)
- **Position bounds:** `0 <= watch_position <= video_duration` (from metadata)
- **Rate check:** Position advances by ≤ (video_duration / 10) per second of elapsed time (rejects instantaneous jumps toward 100%, allows 1x-to-slightly-faster playback, allows rewinds)
- **Event time coherence:** `event_time` is recent (within the last 5 minutes, tolerating client-clock skew)

**And** if all checks pass, `verified: true` and the write proceeds (AD-5)

**And** if any check fails:
- `verified: false` is set
- The write still persists (for debugging) but is not marked as Verified
- No error response to the client (silent rejection, to avoid client-side logic learning the validation details)

**And** all validations are deterministic (same input always produces the same result)

---

### Story 4.5: Event-Time Ordering: Conditional Write (Skip Stale Writes)

As a **developer**,
I want to order watch-progress writes by event timestamp, not by position value,
So that a stale out-of-order write doesn't regress progress while a real rewind still applies.

**Acceptance Criteria:**

**Given** a watch-progress write for an Assignment  
**When** the `progress.record_watch_progress()` method is called  
**Then** it applies this logic:
- **Read current:** Fetch the stored `skill_progress` row (if any)
- **Compare timestamps:** If stored `event_time` >= incoming `event_time`, skip the write and return success silently (AR-5 conditional write rule)
- **Accept newer:** If incoming `event_time` > stored `event_time`, persist the new position, marking it as the new canonical position

**And** this behavior correctly handles:
- **Out-of-order arrival:** Two-tab scenario where tab 1 watches to 50% at T=10s, tab 2 sends a 40% update at T=8s — the 40% is dropped (stale), 50% at T=10s stands
- **Legitimate rewind:** Employee scrubs back to 20% within the same session (new event_time T=11s > stored T=10s) — the rewind is accepted and stored as the new position
- **Concurrent writes:** Multiple rapid requests come in; only the newest event_time wins; no race condition where a faster-arriving older write overwrites a slower-arriving newer one

**And** the write is atomic (single UPDATE statement with WHERE clause on event_time comparison)

---

### Story 4.6: Resume Position Retrieval & Exact-Point Playback

As an **Employee**,
I want to resume a video from exactly where I left off,
So that I don't have to re-scrub or lose my place.

**Acceptance Criteria:**

**Given** I previously watched a video to position 14:32 (seconds: 872) and closed the tab  
**When** I return 3 days later and click "Continue Watching"  
**Then**:
- The frontend calls `GET /api/assignments/{assignment_id}/progress`
- The backend returns `{ watch_position: 872, event_time: "2026-07-06T14:32:00Z", verified: true }`
- The YouTube IFrame is initialized with `startSeconds=872`
- Playback starts at 14:32 exactly (within ±1 second tolerance due to video encoding)

**And** on first use (the very first resume), the position is exact — a wrong resume point on first encounter is a launch-blocking defect (NFR-L4 feedback target)

**And** if the stored position is out of bounds (corrupted data), return an error and fall back to starting from 0 (start-over fallback, UX-DR4)

**And** if no position is stored yet (first view), return `{ watch_position: 0 }` and start from the beginning

---

### Story 4.7: Continue Watching Card — Empty & Loaded States

As a **developer**,
I want to render the Continue Watching UI with proper state handling,
So that the Employee knows whether they have a saved position or not.

**Acceptance Criteria:**

**Given** an Employee on the Content Discovery page  
**When** rendering the Continue Watching card for a video  
**Then** I handle states:

**Empty State (no video watched):**
- Text: "Start watching" or "No videos in progress"
- No progress bar, no resume button
- Clicking the card starts from position 0

**Loaded State (position saved):**
- Progress bar showing current position as a percentage of duration
- Text: "Resume at {current_time} | {time_remaining} min remaining"
- Large play button
- Clicking resumes at the saved position

**Loading State:**
- Spinner or skeleton loader
- Text: "Loading..."

**Error State:**
- Text: "Couldn't load your progress. [Try again]"
- [Try again] retries the GET request

**And** none of these states rely on color alone for distinction (WCAG 2.1 AA, NFR-A2)

---

## EPIC 5: Readiness Dashboard — Status, Provenance, Auto-Update & Override

**Epic Goal:** Build the HR Admin's primary dashboard showing Assignment Status at a glance, Provenance details on drill-down, auto-updating rows as Watch Progress arrives, and manual override capability.

**Owned by:** `dashboard` (read-composition, owns no table), `progress/` (derivation authority, AR-3)

**Binds:** FR-8, FR-9, FR-10, FR-11, FR-12, AR-2, AR-3, AR-4, NFR-L1, NFR-L5, NFR-A1, NFR-A2, NFR-A3, NFR-A4, NFR-C1, NFR-C2, UX-DR1, UX-DR2, UX-DR6, UX-DR13, UX-DR14, UX-DR15, UX-DR16, UX-DR22, UX-DR23, UX-DR24

**Dependencies:** Epic 1 (authentication), Epic 3 (assignments), Epic 4 (watch progress)

---

### Story 5.1: Assignment Dashboard Grid — Status Badge Display

As an **HR Admin**,
I want to see all my assigned Skills on a grid dashboard with Status badges,
So that I can assess readiness at a glance without drilling into each row.

**Acceptance Criteria:**

**Given** I am authenticated as an HR Admin on the Assignment Dashboard  
**When** the page loads  
**Then** I see:
- A table/grid with one row per Assignment (Employee × Skill pair)
- Columns: Employee Name, Skill Name, Status Badge, Last Updated (timestamp), Actions

**Status Badge Column (FR-8):**
- Displays one of: **Not Started**, **In Progress**, **Completed**
- Badge is styled with:
  - **Not Started:** gray/neutral color + text "Not Started"
  - **In Progress:** blue/progress color + text "In Progress" + watch percentage (e.g., "In Progress (45%)")
  - **Completed:** green/success color + text "Completed"
- **NEVER color-only** — text label is always present (WCAG 2.1 AA, NFR-A2)

**Last Updated Column:**
- Plain text timestamp: "2 hours ago", "3 days ago", etc. (human-readable relative time, not ISO-8601)
- For Self-reported data over 7 days stale: this column is red/highlighted to hint at Needs Attention (secondary visual cue for OQ11)

**Actions Column:**
- "[View Details]" button → opens Provenance Drill-Down (Story 5.2)

**And** the grid displays up to 50 rows per page; older Assignments are paginated or scrollable

**And** load time is under 2 seconds (NFR-L1) for a typical HR Admin with 20–50 assignments

---

### Story 5.2: Provenance Drill-Down Modal — Trust Detail & Raw Data

As an **HR Admin**,
I want to drill down into any dashboard row and see the Provenance Label and raw data,
So that I can verify the signal and trust (or question) the Status badge.

**Acceptance Criteria:**

**Given** I click "[View Details]" on a dashboard row  
**When** the modal opens  
**Then** I see:

**Assignment Header:**
- Employee name
- Skill name
- Status badge (same as grid, for context)

**Provenance Section (FR-9):**
- Label: one of **Verified**, **Self-reported**, **Needs Attention**, **HR Override**
- **Never color-only** — always paired with text or icon (WCAG 2.1 AA, NFR-A2)

**Raw Signal (varies by Provenance):**

If **Verified** (auto-captured from video):
- "Watch Progress: 73% (completion)"
- "Last Updated: 2 hours ago"
- "Verified via video playback" (text confirmation)

If **Self-reported** (non-video):
- "Status: In Progress"
- "Last Updated: 5 days ago"
- "Self-reported by {Employee name} on {date}"
- If over 7 days stale, add: "⚠ This status is stale (not updated in 14 days). Consider reaching out to {Employee}."

If **Needs Attention** (stale self-reported, >7 days):
- Same as Self-reported, but with red/warning styling
- Text: "This status hasn't been updated in 14 days. Flagged for follow-up."

If **HR Override** (manually confirmed by HR):
- "Override Status: Completed"
- "Overridden by: {HR Admin name}"
- "Override Reason: {optional text, if provided}"
- "Overridden at: {timestamp}"
- "Underlying Signal: {watch % or self-report status}" (to show the override did not erase the original signal)

**Data Confidence Statement (all):**
- Freshness stated in plain language: "Not updated in 14 days" (not "stale since 2026-06-25")

**Actions:**
- If Self-reported and over 7 days: "[Send Reminder Email]" button (tentative; can be a fast-follow)
- If HR_ADMIN and row is not already overridden: "[Mark as Ready]" button → Story 5.5 (HR Override)
- "[Close]" button

**And** this modal is reachable from every row, no exceptions (UX-DR16, fixing the prototype regression noted in Story 3.5)

**ACCESS CONTROL TESTS (AD-2 Coaching-Only Boundary):**

**GIVEN** an EMPLOYEE session (not HR_ADMIN)  
**WHEN** attempting to call `GET /api/assignments/{assignment_id}/progress/drill-down`  
**THEN** endpoint returns **403 Forbidden** with error: "Employee role cannot access drill-down data" (not 200 OK, never 404)

**GIVEN** an HR_ADMIN session  
**WHEN** calling `GET /api/assignments/{assignment_id}/progress/drill-down` for an assignment they manage  
**THEN** endpoint returns 200 OK with drill-down data (Provenance Label + raw signal)

**GIVEN** any authenticated session (EMPLOYEE or HR_ADMIN)  
**WHEN** searching for alternative endpoints: `/api/progress/export`, `/api/progress/history`, `/api/progress/bulk-read`  
**THEN** all return **405 Method Not Allowed** or **404 Not Found** — no bulk/export/history path exists (only single-row drill-down)

**AND** this AC is passed only if no alternative data-access paths have been added. Only the single-row drill-down `GET /api/assignments/{assignment_id}/progress/drill-down` exists (AD-2 enforces read boundary).

---

### Story 5.3: Needs Attention Flagging — 7-Day Staleness Threshold

As the **system**,
I want to flag self-reported data that hasn't been updated in 7 days,
So that HR Admins can spot rows needing follow-up without manually checking every timestamp.

**Acceptance Criteria:**

**Given** a Skill Assignment with self-reported (non-video) progress  
**When** the `progress/` module derives the Provenance Label (AR-3)  
**Then** it checks:
- If (now - last_update) > 7 days: set Provenance = **Needs Attention**
- Otherwise: Provenance = **Self-reported** (if there's a stored self-report record) or **Not Started** (if no signal at all)

**And** the Needs Attention check is only for **Self-reported** data, not Verified (video) data:
- A Verified row with abandoned video (no new watch-position for 30+ days) is not flagged as Needs Attention in MVP (Open Question 10 deferred)
- Only Self-reported staleness triggers Needs Attention

**And** the 7-day threshold is a config constant, not hardcoded (for easy adjustment post-pilot)

**And** this derivation happens on every `GET /api/dashboard` request (compute-on-read, not pre-cached) — the architecture leaves caching as a private `progress/` optimization (AR-3 deferred)

---

### Story 5.4: Dashboard Auto-Update — Live Row Refresh on Watch Progress

As an **HR Admin**,
I want the dashboard to automatically update as Employees watch content,
So that I see current readiness without manual refresh.

**Acceptance Criteria:**

**Given** I have the Assignment Dashboard open in my browser  
**When** an Employee watches a video and posts a watch-progress update  
**Then** the frontend:
- Polls `GET /api/dashboard` every 10–15 seconds (or on a configurable interval)
- Compares the response to the current local state
- If any Assignment's Status or Provenance has changed, updates the row (no full-page refresh)
- Updates the "Last Updated" timestamp

**And** the polling is client-driven (no WebSocket/SSE; research confirmed no real-time requirement, AR-21)

**And** new rows (newly created Assignments) also appear on subsequent polls

**And** a dashboard row reflects a new watch-position update within 30 seconds (NFR-L5)

**And** the poll stops if the tab is hidden (browser `visibilitychange` event) and resumes when tab is visible again (to save bandwidth)

**And** if polling fails (network error), a warning is logged but polling continues on the next interval (non-blocking)

---

### Story 5.5: HR Override — Manual Readiness Confirmation

As an **HR Admin**,
I want to manually mark an Assignment as Ready (e.g., because I verified competency in a conversation),
So that I can use the dashboard even when auto-captured data doesn't reflect my assessment.

**Acceptance Criteria:**

**Given** I have an Assignment row with incomplete or stale data  
**When** I drill down and click "[Mark as Ready]"  
**Then**:
- A confirmation modal opens: "Mark {Employee} as Ready for {Skill}?"
- Optional text field: "Reason" (e.g., "Verified in conversation on 2026-07-09")
- [Confirm] and [Cancel] buttons

**And** on Confirm:
- `POST /api/assignments/{assignment_id}/override` with `{ action: 'set', reason?: string }`
- Backend creates a record in `assignment_overrides` table:
  - `assignment_id`, `set_by` (HR Admin ID), `set_at` (timestamp), `reason` (optional), `active` (true)
  - No entry in `skill_progress` is modified (AR-4 — separate record, not a field-overwrite)

**And** immediately:
- The Assignment's Status badge on the dashboard becomes **Completed** (or the override status set by HR)
- The Provenance Label changes to **HR Override** (never **Verified**)
- The drill-down now shows both the override and the underlying signal (watch % or self-report)

**And** if a fresh watch-position update arrives for this Assignment after the override:
- The underlying `skill_progress` updates normally
- The drill-down shows both: override + fresh signal (AR-4)
- The override status is not replaced by the fresh signal; HR must explicitly reverse it

**And** an HR Admin can reverse an override by:
- Opening the drill-down again, seeing "[Reverse Override]" button (Story 5.5b)
- Clicking it → `POST /api/assignments/{assignment_id}/override` with `{ action: 'unset' }`
- `assignment_overrides.active` is set to false
- Status reverts to being derived from the underlying signal (watch % or self-report staleness)

---

### Story 5.6: Accessibility & Real-Time Announcements

As a **developer**,
I want to ensure the dashboard is fully keyboard-operable and announces dynamic updates,
So that HR Admins using assistive technology have full access.

**Acceptance Criteria:**

**Given** the dashboard is open in a screen reader  
**When** I interact with it  
**Then**:
- **Keyboard navigation:** All buttons, rows, and controls are reachable via Tab key; Enter/Space activates buttons
- **Status badge focus:** When focus lands on a Status badge, the screen reader announces: "{Employee} {Skill}: {Status} {watch percentage if applicable}"
- **Drill-down modal:** Opens with focus moved to the modal title; can be closed via Escape key
- **Dynamic updates:** When a row's Status changes due to polling, an `aria-live` region announces: "{Employee} {Skill} status updated to {Status}"
- **Success toast (FR-1):** Announced as: "Skill assigned to {Employee} — {Skill name}"
- **Errors:** Error messages are announced immediately

**And** color is never the only way to convey information (NFR-A2):
- Status badges have text labels
- Provenance labels have text labels
- Stale rows have text ("Not updated in X days") in addition to any color highlighting

---

---

## Next Steps

**This completes Step 01 (Requirements Extraction).** 

The epics.md file has been saved with all 75 requirements extracted and organized. The epic sequence follows the Architecture Spine's build order (AD-8):

1. **Epic 1:** Authentication & Session Gate
2. **Epic 2:** Content Catalog & Semantic Matching
3. **Epic 3:** Skill Assignment Flow
4. **Epic 4:** Video Progress Capture & Resume
5. **Epic 5:** Readiness Dashboard & Override

Each epic contains 5–7 detailed stories with complete acceptance criteria ready for the development team.

**[C] Continue to Step 02 (Epic Design) for detailed story refinement and dependencies mapping:**