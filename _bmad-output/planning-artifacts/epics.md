---
stepsCompleted: ['step-01-validate-prerequisites', 'step-02-design-epics', 'step-03-create-stories', 'step-04-final-validation', 'advanced-elicitation', 'blocker-resolution', 'critical-issue-resolution-round-1', 'tier-2-ux-alignment-round-2']
blockersResolved: ['OQ9-LOCAL-provisioning', 'E1.S3-auth-edge-cases', 'E5.S2-privacy-enforcement', 'E1.S7-database-migration-added', 'E2.S2-error-handling', 'E5.S2-drill-down-regression-fixed', 'E1.S3-identity-hard-scoping-added', 'E4.S5-atomic-write-specified', 'E2.S5-content-discovery-aligned', 'E3.S4-assignment-flow-aligned', 'E5.S2-needs-attention-specified', 'E5.S5b-override-reversal-added']
readinessStatus: 'TIER-1-AND-TIER-2-READY'
lastUpdated: '2026-07-09-round-2-tier-2-complete'
criticalFixesApplied: 
  - 'TIER 1: E5.S2, E1.S3, E4.S5 — Launch blockers fixed'
  - 'TIER 2: E2.S5, E3.S4, E5.S2, E5.S5b — All aligned to UX specs (no UX changes)'
highPriorityFixesApplied:
  - 'E2.S5: Rewritten as single-card Content Discovery (per UX spec 02.1)'
  - 'E3.S4: Enhanced HR Assignment Flow with exact UX spec 03.1 copy/layout'
  - 'E5.S2: Needs Attention rendering now concrete (⚠️ icon, red-600, WCAG compliant)'
  - 'E5.S5b: NEW story created for HR Override Reversal with complete flow'
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
I want to enforce role and identity scoping at the FastAPI dependency layer and repository layer,
So that every protected request is validated server-side before data access, and EMPLOYEE sessions are hard-scoped to prevent cross-employee data access (FR-14).

**Acceptance Criteria:**

#### **JWT Token Validation (FastAPI Dependency Layer)**

**Given** a request to a protected endpoint with a valid JWT  
**When** the request includes role and user_id claims  
**Then** a FastAPI dependency extracts both claims and validates:
- Role ∈ {HR_ADMIN, EMPLOYEE}
- User identity (user_id) is present and non-null

**And** the dependency passes the validated (role, user_id) to the request context (e.g., `request.state.current_user`)

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
**Then** request proceeds (passes validation); user is authenticated as Employee with identity context ready for hard-scoping

---

#### **CRITICAL: Employee Hard-Scoping at Repository Layer (FR-14 Enforcement)**

**GIVEN** an authenticated EMPLOYEE session for user_id=casey@example.com  
**WHEN** that session calls `GET /api/assignments` (listing assignments)  
**THEN** the repository layer **hard-scopes the query** by employee_id, returning **only** assignments where `assignment.employee_id == casey`

**AND** this hard-scoping happens at the **repository layer**, not at the service or controller layer — the query itself contains the WHERE clause, making it impossible for an overlooked permission check to leak data

---

**GIVEN** an EMPLOYEE session for user_id=casey  
**WHEN** that session calls `GET /api/assignments?employee_id=morgan` (attempting to override the scoping)  
**THEN** the repository layer **ignores the request parameter** `?employee_id=morgan` and still applies the hard-scoped filter `WHERE employee_id = casey`

**AND** the response returns only casey's assignments (not morgan's), regardless of what `?employee_id` was requested

**AND** no error message is returned (silent filtering, not "invalid parameter" — to avoid leaking the scoping mechanism)

---

**GIVEN** an EMPLOYEE session for user_id=casey  
**WHEN** that session calls `GET /api/content` (listing content)  
**THEN** the repository layer **joins through assignments** and returns only content matched to casey's assignments

**AND** if casey attempts SQL injection like `?employee_id=morgan UNION SELECT ...`, the query still returns only casey's data (parameterized query + hard-scoped WHERE prevent injection)

---

**GIVEN** an EMPLOYEE session for user_id=casey  
**WHEN** that session calls `GET /api/assignments/{assignment_id}/progress/drill-down` for an assignment NOT owned by casey (e.g., assignment belongs to morgan)  
**THEN** endpoint returns **403 Forbidden** with error: "You do not have access to this assignment" (session identity check at controller layer before repository call)

**AND** no data structure or timing information is leaked that could reveal whether the assignment exists

---

#### **HR_ADMIN Sessions (Role-Based Access Control)**

**AND** for HR_ADMIN sessions, role is verified at the dependency layer, but **data access filters are applied by the downstream service layer** (not hard-scoped by user_id):
- HR_ADMIN can list all assignments, all employees, all content (org-wide scope)
- No hard-scoping by HR_ADMIN identity — HR Admins have full read access to all assignments and coaching data

---

#### **Session Propagation Through Stack**

**AND** the validated (role, user_id) is passed through the entire stack:
- FastAPI dependency → request context
- Route handler → service layer
- Service layer → repository layer
- Repository layer → SQL query builder (WHERE clauses enforce hard-scoping)

**AND** if any layer attempts to override or bypass the scoping (e.g., a service layer method calls `query.filter(employee_id=different_id)`), the hard-scoped WHERE clause at the repository layer still applies (defense in depth)

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

### Story 2.5: Content Discovery — Single Assignment Card View

As an **Employee**,
I want to see my assigned Skill with the AI-recommended Content prominently displayed and ready to watch,
So that I can start learning immediately with minimal friction.

**Acceptance Criteria:**

#### **Page Entry & Context**

**Given** I am authenticated as an Employee  
**When** I navigate to Content Discovery or click a skill assignment link  
**Then** I see:
- Page URL: `/assignments/:id/content` (parameterized by assignment ID)
- Page loads the specific **Assignment Card** (one Skill + one recommended Content item)
- Header shows: Logo, navigation (Assignments, Continue Watching), user menu

---

#### **Assignment Card Display (UX Spec 02.1-content-discovery.md)**

**Given** the Content Discovery page loads  
**When** the assignment data has been fetched  
**Then** I see an **Assignment Card** containing:

**Card Header:**
- Skill name + Status badge
- Text: "[Skill Name] - Assigned today by Rita"
- Status: "Assigned · Awaiting first watch"

**Recommended Content Section:**
- Label: "Recommended Content"
- Content Thumbnail (image from video)
- Content Title: "[Video Title]"
- Source Badge: "YouTube"
- Approval Provenance: "✓ Approved" (per UX spec line 84, 110)
- Duration: "[X] minutes"
- Brief Description: Learning outcome description (plain text, not transcript)

**Actions:**
- Primary button: [▶ Play] — launches video player at 0:00
- Secondary link: "View alternatives" — hidden by default, available for edge cases
- Thumbnail itself is also clickable and launches player

---

#### **Page States (Per UX Spec)**

**Loaded State (Happy Path):**
- Full card with thumbnail, title, approval badge, play button
- Actions: Play, View alternatives

**Loading State:**
- Skeleton card placeholder in place of content
- Header remains interactive
- Wait for data

**Empty State (No Matching Content):**
- Card displays: "No recommended content yet for this skill. [Contact Rita]"
- No thumbnail, no play button
- Contact link triggers: "Questions about this skill? Contact Rita"

**Error State:**
- Player area shows: "This video couldn't be loaded. [Try again] · [View alternatives]"
- [Try again] retries video load
- [View alternatives] shows other options

---

#### **Interactions (Per UX Spec 02.1)**

**Click Play Button or Thumbnail:**
- Player launches immediately
- Video starts at 0:00 (or resume position if previously watched)
- Exit to video player page (handled by Story 4.0 YouTube Adapter)

**Hover "✓ Approved" Badge:**
- Tooltip appears: "This content was reviewed and approved by Rita before being recommended to you"
- Reinforces trust in the recommendation

**Click "View Alternatives":**
- Secondary content search/browse interface appears (out of scope for this story; can be fast-follow)
- Employee can choose different content or return to recommended default

**Click Navigation:**
- Logo → `/dashboard` (or `/assignments` depending on role)
- "Assignments" nav → `/assignments` (list all assignments for this Employee)
- "Continue Watching" nav → `/continue-watching` (list videos in progress)

**Click Sign Out:**
- Session cleared, redirect to `/login`

---

#### **Watch-Position Capture (Technical Detail)**

**Given** I start watching the video  
**When** the video player is actively playing  
**Then** in the background:
- Player adapter samples position every 5–10 seconds
- Samples are batched and POSTed to `POST /api/assignments/{assignment_id}/progress`
- Request includes: `{ watch_position, event_time, video_url }`

**And** when I close the tab or browser:
- `sendBeacon` API flushes the last known position to the backend
- Rita's dashboard updates within 30 seconds (FR-11)

**And** next time I return to this assignment:
- Video resumes at exact last-watched position (FR-6, E4.S6)

---

#### **Content Rules (Per UX Spec 02.1)**

- ✅ Always show exactly one curated recommendation per assignment (never search results)
- ✅ Always label as "Recommended Content," not "Search Results"
- ✅ Always include approval provenance ("✓ Approved")
- ✅ Brief description is learning-outcome focused, not transcript snippet
- ✅ No search box on this page (Casey should never search)
- ✅ Never show raw YouTube search results

---

#### **Performance & Accessibility**

- Page + video player loads in under 3 seconds (NFR-L2)
- Responsive: desktop-primary; video player scales to viewport width
- Thumbnail has alt text: "[Video title] - [Duration]"
- All buttons/links have descriptive labels
- Approval badge tooltip is keyboard-accessible
- User menu dropdown is keyboard-navigable
- Video player supports keyboard controls (Space, arrow keys, etc.)

---

#### **Test Cases**

- ✅ Page loads with assignment ID; displays correct Skill + Content
- ✅ Play button launches player at 0:00
- ✅ Thumbnail click also launches player
- ✅ "View alternatives" link available but hidden (for future use)
- ✅ Approval badge shows tooltip on hover + keyboard focus
- ✅ Page load time < 3 seconds
- ✅ Empty state renders when no content matched
- ✅ Error state renders on video load failure
- ✅ Watch capture begins automatically during playback
- ✅ sendBeacon fires on tab close
- ✅ Resume position fetched on next visit

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
So that I can create new assignments quickly with auto-linked AI-recommended content.

**Acceptance Criteria:**

#### **Modal Entry (UX Spec 03.1-skill-assignment-flow.md)**

**Given** I am authenticated as an HR Admin on the Assignment Dashboard  
**When** I click `[+ New Assignment]`  
**Then** a modal opens with:
- Title: "Assign a New Skill"
- Progress indicator: "Step 1 of 3"
- Close button [X]

---

#### **Step 1: Select Employee (Per UX Spec 03.1)**

**When** the modal shows Step 1  
**Then** I see:
- Section title: "Who should learn this?"
- Dropdown/searchable input: "Select employee or search..."
- Actions: [Continue to Skill Selection] button, [Cancel] button

**Given** I interact with the employee dropdown  
**When** I type or click  
**Then**:
- Dropdown shows searchable list of all Employees
- Results auto-filter as I type (search by name or email)
- Each result shows: Employee name + role (optional)
- Example: "Casey the Continuer · Individual Contributor"

**Given** I select an employee and click [Continue to Skill Selection]  
**When** validation passes  
**Then**:
- Employee is selected (highlight/confirm)
- Modal advances to Step 2
- Progress indicator updates: "Step 2 of 3"

---

#### **Step 2: Select Skill (Per UX Spec 03.1)**

**When** Step 2 displays  
**Then** I see:
- Section title: "What skill?"
- Dropdown/searchable input: "Search for a skill or select from recommended..."
- Actions: [Review Content] button, [Cancel] button

**Given** I interact with the skill dropdown  
**When** I type or click  
**Then**:
- Dropdown shows list of recommended skills (pre-populated)
- Results auto-filter as I type (search by name or description)
- Examples shown: "Data Visualization Fundamentals," "Python Basics," "Advanced SQL"

**Given** I select a skill and click [Review Content]  
**When** validation passes and content recommendation is fetched  
**Then**:
- Skill is selected (highlight/confirm)
- Backend queries content matching for this skill
- Modal advances to Step 3
- Progress indicator updates: "Step 3 of 3"

---

#### **Step 3: Review AI-Recommended Content (Per UX Spec 03.1)**

**When** Step 3 displays  
**Then** I see:
- Section title: "Recommended Learning Content"
- Label: "We've found the best match for this skill:"

**Content Display (Auto-Populated, Per UX Spec):**
- Thumbnail image (from video/content)
- Content Title: "[Video Title]"
- Source Badge: "YouTube"
- Duration: "[X] minutes"
- Approval Provenance: **"✓ Approved"** (per UX spec lines 90, 121, 249)
- Brief Description: Learning outcome description (plain text)

**Content Actions:**
- [View on YouTube] link (opens content in new tab for preview)
- [Choose Different Content] link (shows alternatives — optional, out of scope for MVP)

**Assignment Summary (Read-Only):**
- "Employee: {Employee name}"
- "Skill: {Skill name}"
- "Content: {Content title} (Approved)"
- "Assignment Date: Today"
- "Status: Will be 'Assigned · Awaiting first watch'"

**Primary Action:**
- [Assign] button — completes the assignment
- [Cancel] button — discards assignment, returns to dashboard

---

#### **Edge Cases**

**If (Employee, Skill) pair already assigned:**
- Modal displays: "This skill is already assigned to {Employee}. [View] or [Assign Again]"
- [View] navigates to that Assignment's dashboard row
- [Assign Again] allows creating second intentional assignment (per FR-1)

**If no Content matches the Skill:**
- Step 3 shows: "No approved content found yet for this skill."
- Offer two options: [Choose Different Content] or [Assign without content]
- [Assign] button is still enabled (Assignment can proceed without pre-matched content)

**If Content lookup fails:**
- Inline error message under content section: "Couldn't load content recommendation. [Retry]"
- [Retry] re-fetches content

---

#### **Page States (Per UX Spec 03.1)**

| State | When | Display | Actions |
|-------|------|---------|---------|
| **Step 1: Employee selection** | Modal just opened | Employee dropdown active; Step 2/3 disabled | Select, Cancel |
| **Step 2: Skill selection** | Employee selected | Skill dropdown active; Step 3 disabled | Select, Cancel |
| **Step 3: Content review** | Skill selected, content auto-linked | Recommended content + summary shown; [Assign] enabled | Assign, choose content, Cancel |
| **Loading** | Employee list, skill list, or content recommendation being fetched | Placeholder/skeleton in affected field; Cancel available | Wait, Cancel |
| **Empty — No content match** | Skill selected but no approved content found | Step 3 shows "No approved content found yet" message | Assign without content, choose different, Cancel |
| **Error** | Dropdown/content lookup fails | Inline error: "Couldn't load [employees/skills/content]. [Retry]" | Retry, Cancel |

---

#### **Form Validation & Buttons**

- Employee: **required** — Step 1 [Continue] disabled until selected
- Skill: **required** — Step 2 [Review Content] disabled until selected
- Content: **auto-selected** — not user-modifiable in primary flow (pre-matched by backend)
- All steps remain **cancelable** via [Cancel] button or modal close [X]

---

#### **Approval Provenance (Per UX Spec & PRD)**

**Important:** The "✓ Approved" badge shown in Step 3 represents:
- Per PRD §5 Non-Goals: "Not a content-approval workflow in MVP"
- Per UX spec line 316: "Always pair content with approval provenance ('✓ Approved')"
- **Interpretation:** Content is AI-recommended (not filtered by human approval gate in MVP). Badge indicates: "This content was auto-matched by the system for relevance to the skill."
- **Future:** If post-pilot feedback surfaces quality issues, implement approval QA gate (E2.S7 fast-follow)

---

#### **Interactions (Per UX Spec 03.1)**

1. **Interaction 1: Open Assignment Form**
   - Rita clicks [+ New Assignment] on dashboard
   - Modal opens showing Step 1: Select Employee
   - **UX moment:** Linear, simple flow with clear next step

2. **Interaction 2: Select Employee**
   - Rita clicks employee dropdown, types "Casey", selects from list
   - Rita clicks [Continue to Skill Selection]
   - Form advances to Step 2

3. **Interaction 3: Select Skill**
   - Rita sees skill search field with recommended skills
   - Rita types "Python" or selects "Python Basics"
   - Rita clicks [Review Content]
   - Form advances to Step 3, content auto-fetched

4. **Interaction 4: Review AI-Recommended Content**
   - Rita sees: Thumbnail, title, "✓ Approved" badge, duration, description
   - System auto-matched content (Rita didn't manually search)
   - **UX moment:** Reduces assignment time to < 2 minutes; all content already linked

5. **Interaction 5: Confirm Assignment**
   - Rita reviews summary: Employee, Skill, Content (Approved)
   - Rita clicks [Assign]
   - Assignment created, modal closes, returns to dashboard
   - Exit: Navigate to 03.2 Assignment Confirmation & Auto-Update

---

#### **Performance & Accessibility (Per UX Spec)**

- Form completes in under 2 minutes (NFR-L3 feedback target)
- Form is keyboard navigable (Tab through fields/buttons)
- Dropdowns support keyboard selection (arrow keys, Enter)
- Progress indicator clearly shows current step
- Error messages announced to screen readers
- Close button [X] is large and accessible

---

#### **Test Cases**

- ✅ Modal opens with Step 1: Employee Select
- ✅ Employee dropdown filters by name/email
- ✅ Skill dropdown filters by name/description  
- ✅ Content auto-fetches when skill selected
- ✅ Content shows: thumbnail, title, "✓ Approved" badge, duration, description
- ✅ [Assign] creates assignment within 2 minutes
- ✅ Cancel at any step leaves no orphaned record
- ✅ Already-assigned skill shows "duplicate" prompt
- ✅ No content match shows "No approved content" message
- ✅ Error states show retry option
- ✅ Keyboard navigation works end-to-end

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
I want to order watch-progress writes by event timestamp, not by position value, using atomic database operations,
So that a stale out-of-order write doesn't regress progress while a real rewind still applies — even under concurrent write scenarios (FR-7, NFR-DI1).

**Acceptance Criteria:**

#### **Conditional Write Logic (Timestamp-Based Ordering)**

**GIVEN** a watch-progress POST request for an assignment  
**WHEN** the `progress/` service calls `record_watch_progress(assignment_id, watch_position, event_time, ...)`  
**THEN** it applies this logic:
- **Read current:** Fetch the stored `skill_progress` row for this assignment_id (if it exists)
- **Compare timestamps:** Compare incoming `event_time` to stored `event_time`
  - If incoming `event_time` <= stored `event_time`: skip write, return success silently (stale write, don't persist)
  - If incoming `event_time` > stored `event_time`: proceed to atomic write (new event is newer, accept it)

**AND** this comparison **happens at the SQL layer**, not in Python, to ensure atomicity under concurrent requests

---

#### **Atomic SQL Implementation (CRITICAL)**

**GIVEN** incoming watch-progress data (assignment_id, watch_position, event_time)  
**WHEN** the repository layer executes the write  
**THEN** it uses an atomic **SQL UPDATE with a WHERE clause on event_time**, not a separate Python read-compare-write sequence:

```sql
UPDATE skill_progress 
SET watch_position = %s,
    event_time = %s,
    updated_at = NOW(),
    verified = %s
WHERE assignment_id = %s 
  AND (event_time IS NULL OR event_time < %s)
RETURNING watch_position, event_time, verified;
```

**AND** the query binds parameters safely (no string interpolation)

**AND** the driver returns the number of rows affected:
- 0 rows updated = stale write (stored event_time >= incoming), return silent success
- 1 row updated = newer write accepted, return success with new values

**AND** this is a **single round-trip to the database**, not a separate SELECT followed by INSERT/UPDATE (defense against race conditions)

---

#### **Behavior Under Scenarios**

**SCENARIO 1: Out-of-Order Arrival (Two Tabs)**

**GIVEN** Tab 1 watches to 50% and sends event_time=2026-07-09T14:10:00Z at real time 14:10  
**GIVEN** Tab 2 watches to 40% and sends event_time=2026-07-09T14:08:00Z at real time 14:12 (delayed network)  
**WHEN** both requests arrive at the database  
**THEN**:
- First request (50%, T=14:10:00) executes: WHERE (event_time IS NULL OR event_time < 14:10:00) → matches, updates row, returns 1 row affected
- Second request (40%, T=14:08:00) executes: WHERE (event_time IS NULL OR event_time < 14:08:00) → does NOT match (14:10:00 is newer), 0 rows affected, returns silent success
- Stored value remains 50% (correct, stale write rejected)

---

**SCENARIO 2: Legitimate Rewind**

**GIVEN** Employee watches to 50% at event_time=2026-07-09T14:10:00Z  
**GIVEN** Employee scrubs back to 20% within the same session at event_time=2026-07-09T14:11:00Z (newer timestamp)  
**WHEN** the rewind update is sent  
**THEN**:
- UPDATE executes: WHERE (event_time < 14:11:00) → matches (14:10:00 < 14:11:00), updates row to watch_position=20%, event_time=14:11:00, returns 1 row affected
- Stored value is now 20% (correct, rewind accepted because timestamp is newer)

---

**SCENARIO 3: Concurrent Rapid Writes (Race Condition Prevention)**

**GIVEN** Three concurrent requests all arrive at the database within 100ms:
- Request A: position=60%, event_time=14:10:00 (arrives T=0ms)
- Request B: position=50%, event_time=14:09:00 (arrives T=50ms, older than A)
- Request C: position=65%, event_time=14:10:30 (arrives T=100ms, newest)  
**WHEN** all three UPDATE statements execute concurrently  
**THEN**:
- First to lock: Request A updates row (event_time was NULL), WHERE succeeds, returns 1
- Next: Request B checks WHERE (event_time < 14:09:00) → fails (14:10:00 is stored now), returns 0, no update
- Last: Request C checks WHERE (event_time < 14:10:30) → succeeds (14:10:00 < 14:10:30), updates row, returns 1
- Final stored value: position=65%, event_time=14:10:30 (correct, newest wins)

**AND** no race window where an older write could overwrite a newer one (atomic WHERE clause prevents it)

---

#### **Error Handling & Observability**

**AND** the repository method logs:
- On stale write (0 rows): `{ assignment_id, incoming_event_time, stored_event_time, status: 'skipped_stale' }`
- On newer write (1 row): `{ assignment_id, event_time, watch_position, verified, status: 'updated' }`
- On unexpected result (0 or >1 rows in error): `{ error: 'unexpected_row_count', actual, expected: 1 }`

**AND** the service layer treats both success and stale-skip uniformly: return 201 Created with the current state (no error response for stale writes — silent skipping per AR-5)

---

#### **Testing Requirements**

**AND** this story is not considered done until these test cases pass:
- ✅ Out-of-order writes (older event_time after newer): stale write rejected
- ✅ Rewind within session (newer event_time, lower position): accepted
- ✅ Concurrent rapid writes: only newest event_time persists
- ✅ No race condition from separate SELECT + UPDATE: atomic WHERE clause only
- ✅ Silent stale-write success (no 409 Conflict, no error): return 201 with current state

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

#### **CRITICAL FIX: Row-Level Entry Point (Fixing Prototype Regression)**

**Given** I am viewing the Assignment Dashboard with one or more assignments  
**When** I look at any row  
**Then** I see a "[View Details]" button in the Actions column (or a drill-down icon, never a debug URL parameter)

**And** when I click "[View Details]"  
**Then** the Provenance Drill-Down modal opens immediately

**And** this entry point is **always visible and functional on every row**, not conditionally hidden or only accessible via debug query parameters (fixing the known prototype regression where this button was deleted)

---

#### **Modal Content & Display**

**Given** the drill-down modal opens  
**When** it loads  
**Then** I see:

**Assignment Header (always visible):**
- Employee name
- Skill name
- Status badge (same styling as grid row, for context)

**Provenance Section (FR-9) — Always Present:**
- **Provenance Label:** one of **Verified**, **Self-reported**, **Needs Attention**, **HR Override**
- **Label Display:** Text label + visual indicator (icon or badge), never color-only (WCAG 2.1 AA, NFR-A2)

**Raw Signal Display (varies by Provenance):**

**IF Provenance = Verified (auto-captured from video):**
- "✓ Verified via video playback"
- "Watch Progress: 73% (completion)"
- "Last Updated: 2 hours ago"

**IF Provenance = Self-reported (non-video, ≤7 days old):**
- "📝 Self-reported"
- "Status: In Progress"
- "Last Updated: 5 days ago"
- "Self-reported by {Employee name} on {date}"

**IF Provenance = Needs Attention (stale self-reported, >7 days old):**
- "⚠️ Needs Attention" (warning icon + text label, not color-only)
- "Status: In Progress"
- "Last Updated: 14 days ago"
- **Plain-language freshness:** "This status hasn't been updated in 14 days. Consider reaching out to {Employee} to confirm."
- "Self-reported by {Employee name} on {date}"

**IF Provenance = HR Override (manually confirmed by HR):**
- "🔒 HR Override"
- "Override Status: Completed"
- "Overridden by: {HR Admin name}"
- "Overridden at: {timestamp}"
- "Reason: {optional text, if provided}" (or "No reason provided" if empty)
- **Underlying Signal (always shown, never erased):** "Original signal: Watch Progress 45% (Verified)" OR "Original signal: Self-reported · Not Started"

**Data Confidence Statement (all Provenance types):**
- Freshness always stated in **plain language**, never as a date string
  - ❌ Bad: "stale_since: 2026-06-25"
  - ✅ Good: "Not updated in 14 days"

**Actions:**
- If Provenance = Self-reported AND over 7 days old: "[Send Reminder Email]" button (future; can be post-MVP)
- If Provenance ≠ HR Override: "[Mark as Ready]" button → triggers Story 5.5 (HR Override creation)
- If Provenance = HR Override: "[Reverse Override]" button → triggers Story 5.5b (HR Override reversal)
- "[Close]" button (or Escape key)

---

#### **ACCESS CONTROL TESTS (AD-2 Coaching-Only Boundary)**

**GIVEN** an EMPLOYEE session (not HR_ADMIN)  
**WHEN** attempting to call `GET /api/assignments/{assignment_id}/progress/drill-down`  
**THEN** endpoint returns **403 Forbidden** with error: "Employee role cannot access drill-down data" (never 200 OK, never 404)

**GIVEN** an HR_ADMIN session  
**WHEN** calling `GET /api/assignments/{assignment_id}/progress/drill-down` for an assignment they manage  
**THEN** endpoint returns 200 OK with drill-down data (full Provenance Label + raw signal)

**GIVEN** any authenticated session (EMPLOYEE or HR_ADMIN)  
**WHEN** searching for alternative data-access endpoints: `/api/progress/export`, `/api/progress/history`, `/api/progress/bulk-read`, `/api/progress/raw`  
**THEN** all return **405 Method Not Allowed** or **404 Not Found** — no bulk/export/history access (only single-row drill-down via `/api/assignments/{assignment_id}/progress/drill-down`)

**AND** no undocumented endpoints exist for exporting, filtering, or bulk-reading watch-progress data (AD-2 enforces read boundary at service layer)

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

### Story 5.5b: HR Override Reversal — Undo Manual Confirmation

As an **HR Admin**,
I want to reverse/remove an HR Override I previously set,
So that an Assignment returns to being based on its underlying signal (video progress or self-reported status).

**Acceptance Criteria:**

#### **Reversal Button Visibility (In Drill-Down Modal)**

**Given** I have an assignment with an **active HR Override**  
**When** I click "[View Details]" to open the Provenance Drill-Down (E5.S2)  
**Then** I see:
- Current Provenance Label: "🔒 HR Override"
- Current override details: "Status: Completed" (or whatever override status is set)
- "Overridden by: {HR Admin name}"
- "Overridden at: {timestamp}"
- "[Reverse Override]" button (red/warning styling, prominently displayed)

**And** if the assignment has **NO active override**:
- "[Reverse Override]" button is hidden
- "[Mark as Ready]" button is visible instead (E5.S5)

---

#### **Reversal Confirmation Flow**

**Given** I click [Reverse Override]  
**When** confirmation modal appears  
**Then** I see:
- Confirmation question: "Remove this HR Override?"
- Current override summary: "Status: Completed (set by Rita on 2026-07-09)"
- Underlying signal that will take effect: "In Progress · Video progress: 65%" (or "Not Started · No signal" if no underlying data)
- Buttons: [Remove Override] (red/confirm) and [Cancel]

**Given** I click [Cancel]  
**When** the confirmation modal closes  
**Then**:
- No changes made
- Return to Provenance Drill-Down modal
- Override remains active

**Given** I click [Remove Override]  
**When** the backend processes the request  
**Then**:
- `POST /api/assignments/{assignment_id}/override { action: 'unset' }`
- Backend sets `assignment_overrides.active = false`
- Drill-down modal updates immediately to show underlying signal
- Success toast appears: "Override removed. Status now based on video progress."
- Modal closes or refreshes to show new state

---

#### **Post-Reversal Display (Drill-Down Updated)**

**Given** override has been removed  
**When** I re-open the Provenance Drill-Down  
**Then** the modal displays:
- **New Provenance Label:** Based on underlying signal
  - If video progress exists: "✓ Verified" + "Watch Progress: 65%"
  - If only self-report: "📝 Self-reported" + self-report status
  - If no signal at all: "Not Started" + no Provenance label
- "[Mark as Ready]" button is NOW visible (can set override again if needed)
- "[Reverse Override]" button is HIDDEN (no active override)
- Dashboard row Status updates to reflect new underlying signal
- Last Updated timestamp is current (shows reversal just happened)

---

#### **State Management During Reversal**

**Given** reversal is in progress  
**When** a new Watch Progress update arrives simultaneously (race condition)  
**Then**:
- Reversal still completes (override is removed)
- Fresh Watch Progress persists to `skill_progress` table
- Drill-down shows newest Watch Progress (override no longer shadowing it)
- No data loss, no inconsistent state
- Status reflects both: "In Progress · Verified" (from fresh watch data)

---

#### **Access Control**

**Given** an EMPLOYEE session (not HR_ADMIN)  
**WHEN** attempting to call `POST /api/assignments/{id}/override { action: 'unset' }`  
**THEN** endpoint returns **403 Forbidden** with error: "Only HR Admins can manage overrides"

**AND** Employees cannot see override details in the drill-down (if they had access)

---

#### **Dashboard Integration**

**Given** an override is reversed  
**WHEN** the dashboard refreshes (polling interval)  
**THEN**:
- Row Status badge updates to new underlying signal
- Example: "Completed" (override) → "In Progress (65%)" (underlying Verified)
- Row Provenance hint updates (if visible; per OQ11 may be drill-down only)
- "Last Updated" timestamp reflects the reversal

---

#### **Test Cases**

- ✅ Active override shows [Reverse Override] button in drill-down
- ✅ No override hides [Reverse Override] button (shows [Mark as Ready] instead)
- ✅ Click [Reverse Override] → confirmation modal appears
- ✅ Confirmation modal shows current override + underlying signal
- ✅ Click [Cancel] → no changes, drill-down remains open
- ✅ Click [Remove Override] → POST request sent, override removed
- ✅ After reversal → drill-down shows underlying signal (Verified or Self-reported)
- ✅ Dashboard row updates within 30 seconds (NFR-L5)
- ✅ Concurrent Watch Progress during reversal → no data loss
- ✅ EMPLOYEE cannot call reversal endpoint → 403 Forbidden
- ✅ Success toast displayed after reversal

---

## Story 5.6: Accessibility & Real-Time Announcements

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