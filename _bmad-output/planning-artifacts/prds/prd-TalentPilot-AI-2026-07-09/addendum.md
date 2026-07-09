# Addendum: TalentPilot-AI

Implementation how-to, rejected-alternative rationale, and depth material that informed the PRD but doesn't belong in its main narrative. Read alongside `prd.md`.

## Technical Stack (locked)

- **Backend:** Python 3.12+ / FastAPI, domain-module structure, async SQLAlchemy 2.0 + asyncpg.
- **Frontend:** React + TypeScript + Vite SPA (not Next.js — no SEO need, internal authenticated tool only). shadcn/ui + Tailwind. React Hook Form + Zod on the client, Pydantic on the server.
- **Database:** PostgreSQL + pgvector, in-process (not a dedicated vector DB). Embedding model: `text-embedding-3-small`. Query pattern: filter-then-rank (metadata pre-filter on skill tag, vector similarity ranks within that set).
- **Auth:** JWT in an HTTP-only/Secure/SameSite cookie, not localStorage.
- **Video provider:** YouTube IFrame API, polling-based (`getCurrentTime()` / `onStateChange`).
  - Wrapped in an Adapter pattern so a future Vimeo swap (event-driven `timeupdate`) doesn't require rewriting the capture pipeline.
  - YouTube branding cannot be removed (ToS) — this is why Vimeo was the fallback candidate if native branding ever becomes a requirement.
  - On tab close or visibility change, the last known position flushes via the browser `sendBeacon` API — chosen specifically because it delivers the request without blocking page unload, unlike a normal fetch/XHR call.
- **Data models (named):** `assignments`, `skill_progress` (conditional-write semantics — skip write if incoming timestamp isn't newer), `content_catalog` (+ embeddings column).
- **Deployment/hosting:** explicitly out of scope / deferred in the technical research.

## Rejected Technical Alternatives

- **Full-stack TypeScript** (Node backend) — rejected for Python's stronger AI/ML ecosystem fit (`sentence-transformers`, `openai`, `pgvector` client libs are Python-first).
- **Next.js** — unnecessary SSR complexity for an internal, authenticated-only tool with no SEO surface.
- **SQLModel uniformly** — kept SQLAlchemy models and Pydantic schemas separate since the video-progress and pgvector table shapes diverge meaningfully from the API contract shapes.
- **Neon / PlanetScale (serverless Postgres)** — ruled out entirely; neither supports pgvector.
- **MUI** — heavier component library, better suited to very data-dense apps; not this one.
- **Dedicated vector DB (Pinecone / Weaviate)** — no bottleneck at pilot catalog scale (low hundreds/thousands of content rows) justifies the operational overhead; pgvector inside the existing Postgres instance is sufficient.
- **Plain metadata/tag filtering without embeddings** — considered and rejected once TalentPilot confirmed loose/approximate skill-to-content matches were acceptable (e.g., "Data Visualization" should match a video tagged "Charting in Excel") — exact-tag filtering can't surface that.

## Prototype Implementation Notes

- All three UX scenarios (`_bmad-output/E-Development/`) were built as static HTML prototypes, 6 pages total, each covering Loading/Empty/Error/Loaded states, backed by per-screen dev-ready specs under each scenario's `stories/` folder and `work/*.yaml` + `work/Logical-View-Map.md`.
- A `fetch()`-on-local-JSON bug was hit early (blocked under `file://` protocol in the prototype environment) — worked around via `<script>`-tag global-variable data loading. Not relevant to the real (server-backed) build, but documented in case the pattern resurfaces in any static-preview tooling.
- Scenario 03 (Rita's Assignment & Track) intentionally duplicates Scenario 01's dashboard markup as its starting point rather than sharing a component — a deliberate prototyping trade-off, not an oversight; the real build should componentize this properly.
- Concrete UI copy already drafted in the prototypes (useful as a first-pass source for real copy, not a locked spec):
  - Empty state: "No assignments yet — click + New Assignment to get started."
  - Save error: "Couldn't load assignments. [Retry]"
  - Refresh-only error: "Skill assigned, but the dashboard couldn't refresh. [Refresh]" — the assignment itself must persist regardless.
  - No-content-match state: "No approved content found yet for this skill. [Choose Different Content] or assign without content."
  - Assignment success toast: "✓ Skill assigned to {FirstName} — {SkillName}" — auto-dismisses after 4 seconds; the new row's highlight fades after 6 seconds.
  - Content Discovery empty states (two distinct conditions, not one generic empty view): "No recommended content yet for this skill. [Contact Rita]" (no match found) vs. "Nothing in progress right now. [View your assignments]" (nothing started).
  - Content Discovery error states: "This video couldn't be loaded. [Try again] · [View alternatives]" (load failure) vs. "Couldn't resume this video. [Try again] · [Start over]" (resume failure).
  - Approval badge tooltip (hardcoded in the prototype, not data-driven — matches the PRD's own noted assumption that no real approval gate exists): "Reviewed and approved by Rita."
  - Tone acceptance criteria from the stories (sharpens PRD §9's tone split into testable terms): Employee-facing cards should not "feel like a compliance checklist" and copy should read as "encouraging, not evaluative/surveillance-toned."

### Known prototype regressions (fix in real build, do not carry forward)

A 2026-07-09 UI-cleanup commit (`0493247`, "Add Status Badges") introduced two regressions against the prototype's own already-approved specs, discovered during PRD reconciliation:
- **Drill-down is unreachable from the dashboard grid.** The row-level button that opened the Provenance drill-down (FR-9) was deleted as part of removing a table column; `openDrillDown()` now only fires via a `?demo_state=` debug URL parameter. The real build must restore a real, always-visible entry point per row — FR-9's "one click/tap" consequence is not optional.
- **Content Discovery (02.1) lost its loading/empty/error states**, previously built and signed off in story `02.1.3`. Only a bare "no assigned skills" empty state remains; there's no error state for a failed content load. Restore full state coverage in the real build per FR-4/FR-5's testable consequences.

Separately, the same commit and a same-day data/API update (`f541924`) introduced two **intentional** scope changes, now reflected in `prd.md`: the dashboard's primary row indicator became a completion-Status badge instead of the Provenance Label (§4.4, Open Question 11), and Content Discovery became a multi-assignment list instead of a single recommendation (FR-4). Both are real product decisions, not regressions — don't revert them when fixing the two bugs above.

## Hypothesis / Test Flows (DD-001 / TS-001)

24 tests were defined against the prototypes and hypothesis flows: 3 happy-path, 6 error-state, 5 edge-case (including EC-004: concurrent watch in two tabs → conditional writes must prevent progress regression, now FR-7), 3 accessibility, 2 usability (observational — watch for Rita reverting to the spreadsheet habit, i.e., SM-C1; watch for Casey resuming unprompted), 5 performance. Full detail in `_bmad-output/deliveries/DD-001-poc-hypothesis-flows.yaml` and `TS-001-poc-hypothesis-flows.yaml`.

## Rejected Product Alternatives (from brainstorming)

- **Automated skill-gap-to-project matcher** — an earlier "coach" concept that would infer unmet skills and suggest project fits automatically. Shelved for MVP specifically to keep AI judgment out of staffing decisions — HR retains that call entirely.
- **Blocker column on the dashboard** — proposed, then removed from scope.
- **Checkpoint quizzes as a trust signal for document/website content** — considered as a way to close the non-video trust gap; rejected as scope expansion beyond MVP.
- **Manager/Team-Lead role** — considered during Morphological Analysis; rejected to keep the product to two roles (HR Admin, Employee).
- **Reversed flow** ("employee self-triggers a readiness certificate" instead of HR assigning) — ideated, not selected.
- **"Your Week in Learning" recap, streaks/badges** — motivational extras ideated alongside the core auto-capture/resume mechanic; none made MVP scope, no confirmed pain point behind them.
- **Merging the Readiness Dashboard and Assignment Flow into a single view** (SCAMPER idea #19) — considered, not adopted. Kept as two distinct surfaces because Rita's two interaction modes are genuinely different: frequent, low-stakes assignment entry versus occasional, high-stakes readiness judgment. Collapsing them risked muddying both.
- **Enforcing stricter compliance on the existing spreadsheet** (reminders, mandatory fields, escalation) — rejected as a non-starter. The root-cause problem is that manual self-reporting itself is the failure mode; adding process rigor on top of a chore nobody wants to do doesn't remove the chore; it just adds friction to it.
- **Buying an existing enterprise LMS/talent-intelligence suite instead of building** — evaluated and rejected. None of the reviewed vendors (Cornerstone, Degreed, Eightfold, Gloat, etc.) use granular auto-polled watch-% as their core trust signal, and heavyweight implementation costs run 20–50% of license cost again on top — disproportionate for a 5-week internal pilot.

## Market Landscape Detail

- **Market sizing:** Corporate LMS market ~$15–18.5B (2025–26), CAGR 8.4–22.9% through 2030. Adjacent Talent Marketplace Platform market: $8.2B (2024) → $15.1B by 2032.
- **Competitor tiers:**
  - Enterprise talent-intelligence: Eightfold, Gloat, Reejig, 365Talents, Fuel50, Skillpanel.
  - LMS/LXP incumbents: Cornerstone (owns EdCast, 50,000-skill ontology), Degreed, LinkedIn Learning, Docebo, Litmos, D2L Brightspace, Pluralsight.
  - AI skills-gap point tools: Valamis, Paradiso Solutions, TechClass, Disco, **iMocha** (domain research names this as the closest existing competitor on the "readiness dashboard" concept specifically — worth watching, not just listing).
- **Named competitive threat:** Gloat's embedding into Microsoft 365 Copilot/Teams is flagged in the market report's risk assessment as a distribution threat — it could out-distribute a standalone tool like this one on convenience grounds alone, independent of feature parity.
- **Buying process:** 4–6-month enterprise cycle, ~13 internal / 9 external stakeholders typical, 81% decide before talking to sales, POC beats demo. (Not directly relevant to this internal pilot, which has no external sales motion — retained for context if this ever becomes a shopped product.)
- **Key stats:**
  - 88% of HR spreadsheets contain errors (Hackett Group).
  - Only 20% of HR leaders trust their own skills data (Gartner).
  - 87% cite skills-visibility gaps as a top growth barrier.
  - Employees waste ~35% of time searching for content (industry research).
  - 70–80% of LMS implementations are reported as failing.

## Innovation Strategy Notes

Recommended strategic posture: "Focused Wedge" (narrow scope, workflow lock-in before incumbents reach feature parity in 12–24 months) over broader alternatives (adjacent expansion into performance correlation, or a distributed/PLG-first motion). Business model is explicitly undefined/hypothetical (per-employee SaaS assumed if this ever commercializes) — not validated, and out of scope for this internal-pilot PRD. Four "undefended positioning gaps" identified: assignment-first workflow, fully-automatic capture, consumer-grade resume UX, narrow/fast-deploy scope.

Privacy/consent risk was flagged in the innovation-strategy document (GDPR/CCPA consent implications of video watch-tracking, recommending a default data-retention limit, e.g., deleting progress after 90 days of inactivity) but never adopted as a product decision — this is the source of PRD Open Question 1.
