---
title: Architecture Spine Review — Good-Spine Rubric Walker
reviewer: Claude (Rubric Walker)
review_date: 2026-07-09
spine_version: draft (2026-07-09)
---

# Architecture Spine Review: Good-Spine Checklist

## Executive Summary

**Verdict: PARTIAL PASS**

This spine demonstrates strong architectural rigor in most dimensions but has three critical gaps that prevent a clean pass:

1. **Dimensional gap: Deployment/operations remain unresolved** — AD-15 identifies single-server deployment as "ASSUMPTION" and flags Open Question 7 as blocking the 2026-07-13 launch, but the Deferred section lists deployment target as explicitly not decided. This is a contradiction: the spine makes deployment decisions (single-server, colocated services) while simultaneously claiming not to. Either promote AD-15 to a decided constraint or defer all deployment topology choices.

2. **Silent deferral: Several integration/operational concerns lack explicit treatment** — Error-handling strategy (AD-14), SSE connection lifecycle (AD-6), and batch ingestion failure modes (AD-17) make implementation choices without corresponding ADs for observability, logging, or incident response patterns. These aren't "deferred" in the Deferred section but also aren't architecturally bound.

3. **Enforceable rule ambiguity: AD-10 anti-spoofing threshold** — The "≤ 1.2x real-time" advance rate is flagged as arbitrary in Open Question 8 but appears as a concrete Rule in AD-10. How would a reviewer verify compliance when the threshold itself is provisional?

The spine excels at: preventing data ownership conflicts (AD-2, AD-3), architectural clarity on write integrity (AD-4, AD-10), comprehensive schema documentation (AD-11), and explicit coverage of all 14 functional requirements from the PRD.

---

## Checklist Results

### 1. Fixes Real Divergence Points

**Result: PASS**

Every AD prevents two units one level down from building incompatibly.

**Evidence:**
- **AD-1** (Three-Tier CQRS-lite) prevents: mixing read-optimization with write-integrity constraints → binds client/API/DB separation
- **AD-2** (Domain-Driven Module Boundaries) prevents: tangled dependencies across `auth`, `assignments`, `content_discovery`, `watch_progress`, `dashboard` → five modules can't share mutable state
- **AD-3** (Data Ownership per Module) prevents: conflicting writes to `assignments`, `skill_progress`, `content_catalog`, `users` tables → each module owns its tables exclusively
- **AD-4** (Event-Timestamp Conditional Writes) prevents: out-of-order writes from regressing progress or blocking legitimate rewinds → implements FR-7
- **AD-5** (Coaching-Only Enforcement) prevents: performance-review misuse → no export endpoints shaped for evaluation
- **AD-6** (SSE for Real-Time Dashboard) prevents: polling overhead, WebSocket bidirectional complexity → unidirectional push pattern
- **AD-7** (YouTube Adapter Pattern) prevents: YouTube-specific logic leaking into `watch_progress` → future Vimeo swap is drop-in
- **AD-8** (pgvector In-Database) prevents: dedicated vector DB overhead at pilot scale → filter-then-rank within PostgreSQL
- **AD-9** (JWT in HTTP-only Cookie) prevents: XSS token theft, CSRF via URL parameters → cookie-based transport only
- **AD-10** (Server-Side Anti-Spoofing) prevents: client-spoofed completion, "Verified" misuse → three validation rules enforced server-side
- **AD-11** (Core Database Schema) prevents: schema drift, ambiguous relationships → six tables with explicit ownership
- **AD-12** (RESTful + Pragmatic RPC) prevents: endpoint proliferation, unclear semantics → five route namespaces with CRUD vs. RPC clarity
- **AD-13** (React Context + TanStack Query) prevents: prop-drilling, stale cache, race conditions → session in Context, server state in query cache
- **AD-14** (Explicit Error States) prevents: silent failures, ambiguous states → every async operation has distinct error feedback
- **AD-15** (Single-Server Deployment) prevents: multi-tier coordination overhead → colocated frontend/API/DB
- **AD-16** (Server-Side Status Computation) prevents: client-side trust logic, inconsistent badge rendering → Status/Provenance computed once, server-side
- **AD-17** (Batch Content Ingestion) prevents: YouTube API quota exhaustion → scheduled job, not on-demand
- **AD-18** (Multi-Layer Testing) prevents: untested edge cases, accessibility gaps → unit/integration/E2E/a11y coverage defined

All 18 ADs fix real divergence points at the appropriate level (system-wide communication, module boundaries, data ownership, write integrity, API structure, frontend state, deployment topology).

---

### 2. Enforceable Rules

**Result: PARTIAL**

Most ADs have concrete, verifiable rules. Two have ambiguity that would complicate compliance verification.

**Passing ADs:**
- **AD-1**: "Client (React SPA) → API (FastAPI) → Database (PostgreSQL)" — verifiable via codebase structure inspection
- **AD-2**: "Five domain modules... each owns database tables, service logic, API routes. Cross-module communication only via service interfaces, never direct table access." — verifiable via import graph analysis
- **AD-3**: "No module may mutate another module's tables." — verifiable via SQL query pattern inspection
- **AD-4**: "Accept watch-progress update only if `incoming_event_timestamp > stored_event_timestamp`" — verifiable via conditional write query inspection
- **AD-5**: "No export endpoints, no drill-down history API shaped for performance evaluation." — verifiable via API route audit
- **AD-6**: "SSE (one-directional server→client push)... No WebSocket" — verifiable via network protocol inspection
- **AD-7**: "`VideoPlayerAdapter` interface wraps YouTube IFrame API" — verifiable via interface/implementation inspection
- **AD-8**: "pgvector extension in PostgreSQL, not Pinecone/Weaviate" — verifiable via dependency manifest
- **AD-9**: "JWT in HTTP-only/Secure/SameSite cookie, not localStorage" — verifiable via auth implementation inspection
- **AD-11**: Six tables with explicit schema — verifiable via migration files
- **AD-12**: Five route namespaces — verifiable via API route registration
- **AD-13**: "React Context for session... TanStack Query for server state... No global assignment/progress state" — verifiable via state management pattern inspection
- **AD-14**: "Every async operation has distinct error state" — verifiable via error-handling code inspection
- **AD-15**: "Frontend static build served from FastAPI `/static`... colocated on one VM/container" — verifiable via deployment manifest
- **AD-16**: "Status computed from `position_seconds / duration_seconds`... Provenance determined by: [4 rules]" — verifiable via computation logic inspection
- **AD-17**: "Scheduled batch job (cron/background worker), not on-demand search" — verifiable via job scheduler configuration
- **AD-18**: Four test layers (unit/integration/E2E/a11y) — verifiable via test suite structure

**Failing ADs:**
- **AD-10**: "Position advance rate ≤ 1.2x real-time" is called out in Open Question 8 as arbitrary/provisional, requiring tuning based on pilot usage. How does a reviewer verify compliance when the threshold is provisional? The rule is concrete but its correctness is uncertain. **Recommendation:** Either (1) promote 1.2x to a decided constraint with a rationale (e.g., "allows 1.2x playback speed + minor clock skew, disallows instant completion") and defer tuning to post-pilot iteration, OR (2) add to Deferred section: "Anti-spoofing advance-rate threshold (1.2x is placeholder, may need adjustment based on real usage patterns — false positive rate monitored in pilot)."

- **AD-15**: Marked as `[ASSUMPTION]` with Open Question 7 flagged as "blocks 2026-07-13 launch date," yet makes concrete deployment decisions (single-server, colocated services, FastAPI serving static build). This is a contradiction: the AD is simultaneously decided (for implementation purposes) and undecided (for deployment target selection). **Recommendation:** Either (1) promote single-server deployment to a decided constraint if stakeholders have committed to it, OR (2) move all deployment topology choices to Deferred and remove concrete decisions from AD-15, leaving only the pattern (colocated services for MVP) without binding to a specific target.

---

### 3. Nothing Silent Under Deferred

**Result: PARTIAL**

The Deferred section explicitly calls out 10 items as not-decided, which is good. However, several implementation choices in the ADs make decisions without corresponding architectural binding in other dimensions.

**Explicit Deferrals (Good):**
1. Employee roster source (Open Question 9)
2. Session TTL policy (AD-9 assumption)
3. Deployment target (Open Question 7)
4. Content unavailability fallback (Open Question 10)
5. Data retention period (Open Question 1)
6. Self-reported status entry mechanism (PRD §5 Non-Goals)
7. Manager/Team-Lead role (out of MVP scope)
8. Video-specific staleness threshold (FR-10 note)
9. Scaling beyond single-server (not needed at pilot scale)
10. Non-YouTube video providers (Vimeo Adapter exists as pattern, not implemented)

**Silent Gaps (Items that make implementation choices but lack corresponding architectural decisions):**

1. **Observability/Logging Strategy**: AD-14 specifies explicit error states and structured JSON errors (`{error, code, retryable}`), AD-17 mentions "failed ingestion logs error," and the Open Questions reference "pilot telemetry (SM-C1)" — but no AD binds logging/monitoring/alerting patterns. Where are logs centralized? What's the incident-detection mechanism? How does HR Admin know if the SSE stream has failed for all users vs. one? This is an operational dimension that's neither decided nor deferred.

2. **Backup/Recovery Strategy**: AD-15 specifies single-server PostgreSQL but doesn't address backup cadence, recovery procedures, or data loss tolerance. Given the coaching-only constraint (AD-5) and internal-only scope, this may be acceptable risk for MVP, but it should be explicitly deferred rather than silent.

3. **API Rate Limiting/Abuse Prevention**: AD-10 validates server-side, but no AD addresses rate limiting on write endpoints (`/api/progress/update` could be spammed). Is this out of scope for internal-only pilot, or is it a silent gap?

4. **Session Invalidation Mechanism**: AD-9 mentions "token blacklist or short TTL" as alternatives but doesn't decide which. This affects sign-out reliability (blacklist requires stateful storage, short TTL may force frequent re-login). Should be explicitly deferred if undecided.

**Recommendation:** Add to Deferred section:
- "Observability/logging strategy — centralized logging, incident detection, metrics collection (pilot will determine operational needs)"
- "Backup/recovery strategy — backup cadence, point-in-time recovery requirements (internal-only pilot may tolerate data loss risk)"
- "API rate limiting — abuse prevention for write endpoints (internal-only scope may not require)"
- "Session invalidation mechanism — token blacklist vs. short TTL (affects sign-out reliability and re-login frequency)"

---

### 4. Named Tech is Current

**Result: PASS**

All named technologies are current and exist as specified.

**Verified:**
- **Python 3.12+**: Current stable version (as of 2026-07-09, Python 3.12 is current)
- **FastAPI**: Current async Python web framework
- **SQLAlchemy 2.0 + asyncpg**: Current ORM with async support
- **React + TypeScript + Vite**: Current frontend stack
- **shadcn/ui + Tailwind**: Current React component library (shadcn) + CSS framework
- **React Hook Form + Zod**: Current form handling + validation libraries
- **PostgreSQL + pgvector**: Current database with vector extension (`vector(1536)` matches `text-embedding-3-small` dimension)
- **JWT**: Standard session token format
- **YouTube IFrame API**: Current video embed API
- **OpenAI `text-embedding-3-small`**: Current embedding model (1536 dimensions)
- **TanStack Query (`react-query`)**: Current server-state caching library
- **Playwright**: Current E2E testing framework
- **axe-core**: Current accessibility testing library

No outdated or non-existent technologies named.

---

### 5. Covers Spec Capabilities

**Result: PASS**

All 14 functional requirements from the PRD have explicit architectural support.

**Mapping:**

| FR | Requirement | Architectural Support |
|----|-------------|----------------------|
| FR-1 | HR Admin assigns Skill to Employee | AD-2 (`assignments` module), AD-3 (`assignments` table ownership), AD-11 (schema), AD-12 (`/api/assignments/*` routes) |
| FR-2 | HR Admin sees AI-recommended Content during assignment | AD-2 (`content_discovery` module), AD-8 (pgvector matching), AD-12 (`/api/content/*` routes) |
| FR-3 | System matches Content to assigned Skill | AD-8 (pgvector filter-then-rank, `text-embedding-3-small`), AD-17 (batch ingestion) |
| FR-4 | Employee views assigned Content in one list | AD-2 (`content_discovery` module), AD-12 (`/api/content/discovery` route), AD-13 (TanStack Query for caching) |
| FR-5 | System captures video watch position automatically | AD-7 (YouTube Adapter polling + `sendBeacon` flush), AD-2 (`watch_progress` module), AD-3 (`skill_progress` table ownership), AD-11 (schema) |
| FR-6 | Employee resumes video at exact last position | AD-7 (Adapter `getCurrentTime()`), AD-12 (`/api/progress/*` routes), AD-11 (`skill_progress.position_seconds`) |
| FR-7 | Watch-progress writes ordered by event time, not position | AD-4 (event-timestamp conditional writes: `incoming_event_timestamp > stored_event_timestamp`) |
| FR-8 | HR Admin views per-Assignment rows with Status badge | AD-2 (`dashboard` module), AD-16 (server-side Status computation: 0%/1-99%/100%), AD-12 (`/api/assignments/*`) |
| FR-9 | HR Admin drills down into Provenance Label and raw signal | AD-16 (server-side Provenance computation: Verified/Self-reported/Needs Attention/HR Override), AD-5 (coaching-only enforcement: no export endpoints) |
| FR-10 | Dashboard flags stale self-reported data as "Needs Attention" | AD-16 (Provenance rule: `provenance='self_reported'` + `updated_at` > 7 days → Needs Attention) |
| FR-11 | Dashboard rows update automatically as Watch Progress arrives | AD-6 (SSE `/api/dashboard/stream` for real-time push), AD-14 (SSE connection drop shows explicit refresh prompt) |
| FR-12 | HR Admin manually overrides assignment readiness status | AD-11 (`assignment_history` audit log table), AD-16 (`hr_override` flag → HR Override provenance), AD-12 (`/api/assignments/*` override route) |
| FR-13 | System requires valid authenticated session | AD-9 (JWT validation on every protected request), AD-12 (all routes validate session) |
| FR-14 | Session scoped to exactly one role and identity | AD-9 (JWT payload: `{role, employee_id, exp}`), AD-13 (session in React Context, role-specific route guards) |

All 14 FRs have explicit architectural decisions covering them. No orphaned requirements.

---

### 6. No Dimensional Gaps

**Result: PARTIAL**

Most structural dimensions are decided. Two have gaps or contradictions.

**Covered Dimensions:**

| Dimension | Decisions | ADs |
|-----------|-----------|-----|
| **Data** | Module ownership, schema, conditional writes, anti-spoofing | AD-3, AD-4, AD-10, AD-11 |
| **Boundaries** | Three-tier, five domain modules, service interfaces only | AD-1, AD-2, AD-12 |
| **Deployment** | Single-server MVP (colocated frontend/API/DB) | AD-15 |
| **Operations** | Batch ingestion, explicit error states, multi-layer testing | AD-14, AD-17, AD-18 |
| **Integration** | YouTube Adapter, OpenAI embeddings, JWT validation, SSE stream | AD-7, AD-8, AD-9, AD-6 |
| **State Mutation** | Conditional writes, server-side computation, cross-module communication rules | AD-3, AD-4, AD-10, AD-16 |

**Gaps:**

1. **Deployment dimension is contradictory**: AD-15 makes concrete deployment decisions (single-server, colocated, FastAPI serving static build) but simultaneously flags deployment target as `[ASSUMPTION]` and Open Question 7 as "blocks 2026-07-13 launch." The Deferred section lists "Deployment target — VM provider, container orchestration, hosting environment (Open Question 7, blocks launch)" as explicitly not decided. This is a dimensional gap: deployment topology is both decided (for architecture purposes) and undecided (for operational purposes). Either promote the decision or defer the architecture.

2. **Operations dimension is incomplete**: While AD-14 (explicit error states), AD-17 (batch ingestion failure logging), and AD-18 (testing strategy) address some operational concerns, there's no decision on:
   - Centralized logging/monitoring/alerting (mentioned in Open Questions as "pilot telemetry" but not architecturally bound)
   - Backup/recovery strategy (PostgreSQL is single-instance per AD-15, but no backup cadence or recovery procedure specified)
   - Incident response patterns (how does HR Admin know if SSE stream is down system-wide vs. per-user?)
   
   These may be acceptable to defer for MVP/pilot, but they should be explicitly listed in Deferred rather than silent.

**Recommendation:**
- Resolve AD-15 deployment contradiction (see Checklist Item 2 above)
- Add to Deferred: "Observability/incident-response strategy (centralized logging, alerting, metrics — pilot will determine operational needs)" and "Backup/recovery strategy (backup cadence, point-in-time recovery — internal-only pilot may tolerate data loss risk)"

---

### 7. Parent Spine Compliance

**Result: N/A**

This is the root spine for TalentPilot-AI. No parent spine exists to check compliance against.

---

## Detailed Findings by Section

### Paradigm

**Assessment: PASS**

Clear, concise paradigm statement: "Three-Tier Web Application with CQRS-lite separation." The elaboration correctly identifies the architectural driver: read-path optimization (dashboard aggregation) separated from write-path integrity (conditional updates, anti-spoofing).

### Architecture Decisions (AD-1 through AD-18)

**Assessment: STRONG, with three items flagged above**

The 18 ADs are well-structured, each with:
- **Binds**: Clear scope of what's locked
- **Prevents**: Specific divergence point addressed
- **Rule**: Concrete, mostly enforceable guidance

**Highlights:**
- **AD-4** (Event-Timestamp Conditional Writes) is architecturally elegant: ordering by time rather than position magnitude prevents both out-of-order regression and blocking legitimate rewinds. This directly implements FR-7 and is testable via sequence diagram (lines 244-270).
- **AD-5** (Coaching-Only Enforcement) correctly translates a business constraint ("coaching only") into architectural structure ("no export endpoints, no drill-down history API shaped for performance evaluation"). This is how a constraint should work: structural enforcement, not policy statement.
- **AD-16** (Server-Side Status & Provenance Computation) prevents client-side trust logic divergence and ensures single source of truth for badge rendering. The four Provenance rules are concrete and verifiable.

**Flagged Items:**
- **AD-10**: Advance rate threshold (1.2x) flagged as arbitrary in Open Question 8 but appears as concrete rule — see Checklist Item 2 above.
- **AD-15**: Deployment topology contradiction — see Checklist Item 2 and 6 above.
- **AD-9**: Session invalidation mechanism ("token blacklist or short TTL") is undecided but not explicitly deferred — see Checklist Item 3 above.

### System Structure (Diagrams)

**Assessment: PASS**

Three clear Mermaid diagrams:
1. **Module Boundaries & Data Flow**: Shows client views, API modules, database tables, with ownership relationships visible
2. **Deployment View (MVP Single-Server)**: Shows colocated services, external integrations (YouTube, OpenAI)
3. **Conditional Write Flow**: Sequence diagram for AD-4 + AD-10, showing timestamp comparison and anti-spoofing checks

All three diagrams match the AD decisions. No contradictions found.

### Seed (Current State)

**Assessment: PASS**

**Technology Stack** section locks all core dependencies and correctly flags deployment as `[UNDECIDED—blocking Open Question 7]`.

**Database Schema (Detailed)** provides full SQL DDL for all six tables from AD-11, with:
- Explicit constraints (`CHECK`, `UNIQUE`, `REFERENCES`)
- Index definitions (`idx_assignments_employee`, `idx_content_embedding` with HNSW for vector search)
- pgvector extension setup (`CREATE EXTENSION IF NOT EXISTS vector`)

Schema is complete, matches AD-11, and is implementation-ready.

**Integration Points** lists four external integrations (YouTube, OpenAI, JWT, SSE) with clear protocol/API references. All match corresponding ADs.

### Deferred

**Assessment: PARTIAL**

10 items explicitly listed as not-decided, which is good. However, several implementation choices in the ADs (observability, backup, rate limiting, session invalidation) are neither decided nor explicitly deferred — see Checklist Item 3 above.

### Open Questions

**Assessment: PASS**

8 open questions listed, all of which correctly identify risks or unvalidated assumptions:
1. Deployment target must be decided (blocks launch)
2. Employee roster source undecided (affects auth module)
3. Session TTL policy unspecified (affects user interruption frequency)
4. Status/Provenance split may reintroduce trust ambiguity (requires pilot validation)
5. Content ingestion seed size undefined (affects launch readiness)
6. HR Override UX not designed (FR-12 exists but no prototype)
7. Provenance label comprehension untested (core trust differentiator is unvalidated)
8. Anti-spoofing advance-rate threshold is arbitrary (may need tuning)

All 8 questions correctly identify gaps that could block implementation or undermine the product's core value proposition (trust signal differentiation). Open Question 4 in particular ("Status/Provenance split may reintroduce trust ambiguity") is insightful: it identifies the risk that separating Status (at-a-glance) from Provenance (drill-down) may fail if HR Admins don't reliably drill down before trusting badges.

---

## Summary of Recommendations

### Critical (Must Address Before Implementation)

1. **Resolve AD-15 deployment contradiction**: Either promote single-server deployment to a decided constraint (if stakeholders have committed) or move all deployment topology choices to Deferred (if hosting target is truly undecided). The current state — AD-15 makes concrete decisions while Open Question 7 flags deployment as blocking — creates ambiguity for implementers.

2. **Clarify AD-10 anti-spoofing threshold enforceability**: Either promote 1.2x to a decided constraint with rationale ("allows 1.2x playback speed + clock skew, disallows instant completion") and defer tuning to post-pilot, OR add to Deferred: "Anti-spoofing advance-rate threshold (1.2x is placeholder, may need adjustment based on pilot false-positive rate)."

### Important (Should Address to Improve Spine Quality)

3. **Make silent deferrals explicit**: Add to Deferred section:
   - "Observability/logging strategy — centralized logging, incident detection, metrics collection (pilot will determine operational needs)"
   - "Backup/recovery strategy — backup cadence, point-in-time recovery requirements (internal-only pilot may tolerate data loss risk)"
   - "API rate limiting — abuse prevention for write endpoints (internal-only scope may not require)"
   - "Session invalidation mechanism — token blacklist vs. short TTL (affects sign-out reliability and re-login frequency)"

### Advisory (Consider for Future Iterations)

4. **Open Question 4 (Status/Provenance trust ambiguity) is well-identified**: Consider adding a lightweight validation test to the pilot plan: do HR Admins reliably drill down into Provenance before making staffing calls, or do they skim Status badges and skip drill-down? If the latter, the core trust differentiator (Verified vs. Self-reported) may be invisible in practice. This is a product risk, not an architecture defect, but the spine correctly surfaces it.

---

## Conclusion

This is a high-quality architecture spine with strong coverage of data ownership, write integrity, and functional requirements. The three critical gaps (deployment contradiction, anti-spoofing threshold enforceability, silent deferrals in operations dimension) prevent a clean PASS, but all are addressable without major restructuring.

**Final Verdict: PARTIAL PASS**

The spine is implementation-ready for most modules (`auth`, `assignments`, `content_discovery`, `watch_progress`, `dashboard`) but requires resolution of deployment topology and operational concerns (observability, backup, rate limiting, session invalidation) before full implementation can proceed.

**Top 3 Findings:**
1. **AD-15 deployment contradiction**: Concrete single-server decisions coexist with "undecided" Open Question 7 — resolve before build starts
2. **Dimensional gap in operations**: Observability, backup/recovery, rate limiting, session invalidation are neither decided nor explicitly deferred
3. **AD-10 anti-spoofing threshold**: Rule enforceability unclear when threshold itself is provisional (flagged in Open Question 8)

---

**Review Completed:** 2026-07-09  
**Reviewer:** Claude (Rubric Walker Agent)  
**Spine Status:** draft (2026-07-09)  
**Recommended Next Action:** Address Critical items 1-2 above, then promote spine status to `ready-for-implementation` once deployment target and anti-spoofing threshold are resolved.
