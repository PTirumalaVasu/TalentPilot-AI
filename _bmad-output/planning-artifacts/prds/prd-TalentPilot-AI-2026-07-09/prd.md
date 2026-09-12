---
title: TalentPilot-AI
status: final
created: 2026-07-09
updated: 2026-09-12
---

# PRD: TalentPilot-AI
*Working title — confirm.*

## 0. Document Purpose

This PRD is for TalentPilot (product owner and sole builder), and for whoever picks up architecture and implementation work against it. It consolidates the discovery already done — Product Brief, Trigger Map, UX Scenarios, working HTML prototypes (`_bmad-output/E-Development/`), and a PRFAQ stress-test — into one authoritative capability spec. It does not duplicate that prior work: UX flow detail lives in `_bmad-output/C-UX-Scenarios/` and the prototypes; visual/interaction spec is theirs to own. This PRD is organized as Glossary-anchored vocabulary, features grouped with globally-numbered Functional Requirements (FR-N) nested underneath, and inline `[ASSUMPTION]` tags indexed in §12. Implementation/technical detail (stack, data models, rejected technical alternatives) lives in `addendum.md`, not here.

## 1. Vision

HR at SAILS Software tracks employee skill development through a shared spreadsheet: HR assigns must-do skills, employees are supposed to self-report progress, and HR periodically eyeballs the grid to judge who's ready for what. The spreadsheet isn't the problem — the self-reporting chore is. It has no payoff for employees, so it gets skipped, and HR ends up chasing people instead of managing skills. By the time HR needs an answer — "who can we staff on this?" — the data can't be trusted, and getting a real answer means asking around anyway.

TalentPilot-AI replaces that self-reporting loop with automatic capture, for the one content type where it's possible: video. HR still assigns the skill; the system still recommends content; but progress is read from actual watch behavior, not typed in by the employee. The same write that tells HR "this person is 73% through" also tells the employee "resume here" — one signal, two payoffs, no separate sync step and no chore.

This is deliberately not a claim that everything on the dashboard becomes trustworthy. Anything that isn't video-shaped (documents, websites, sub-skill status) stays self-reported, and stays visibly labeled as such. The differentiator isn't "the whole dashboard is now verified" — it's that HR can tell, at a glance, which cells to trust and which to still treat as a starting point for more work.

## 2. Target User

### 2.1 Jobs To Be Done

- **HR/L&D Admin ("Rita the Referee") — primary.** Needs to know who's ready for a project without manual check-ins or chasing. Opens the tracking sheet daily to add/update must-do skills and check status; periodically has to make a fast, defensible readiness call under time pressure (a project lead asking "who can we staff?" today, not next week). Is resigned to the current process, not tolerant of it — three years of chasing updates has taught her that nagging doesn't fix a chore nobody wants to do. `[ASSUMPTION]` This "resigned, not tolerant" read is TalentPilot's own inference, not confirmed via interview — see §12.
- **Employee ("Casey the Continuer") — secondary.** Needs to find the right learning content fast and resume exactly where they left off, Netflix/Spotify-style. Currently self-reports progress into the same shared sheet Rita uses — an easy-to-deprioritize chore with zero personal payoff.

### 2.2 Non-Users (v1)

Manager/Team-Lead is explicitly not a role in this product. Only HR Admin and Employee exist. This was left as an open question in an earlier draft brief and is now resolved: no manager-facing view, no manager-initiated assignments, in v1. Revisit only if pilot usage surfaces real demand.

### 2.3 Key User Journeys

These three journeys were already designed as UX scenarios and built as working HTML prototypes (`_bmad-output/C-UX-Scenarios/`, `_bmad-output/E-Development/`) — reproduced here in PRD form so FRs can reference them by ID. Treat the linked scenario docs as the source of visual/interaction truth; this is the capability summary.

- **UJ-1. Rita makes a staffing call in under two minutes, without opening the spreadsheet.**
  - **Persona + context:** Rita, mid-morning, a project lead has just Slacked her: "who can we staff on the Q3 skills initiative?"
  - **Entry state:** Authenticated, on the Skill Assignment Dashboard (§4.10) — the HR Admin landing page as of this update; previously she landed directly on the full row grid described below.
  - **Path:** Glances at the landing page's org-wide stats and employee segmentation (On Track / In Progress / Needs Attention, §4.10/FR-32) for a temperature check, then opens `Skill Assignments` from the left nav (FR-33) to scan 15–20 employee rows. Each row carries a Status badge at a glance (`Not Started`, `In Progress`, `Completed`). One row's percentage looks inconsistent with what she remembers — she clicks it to drill down.
  - **Climax:** Drill-down shows the Provenance Label and raw signal (watch %, timestamp, Verified vs. Self-reported vs. Needs Attention vs. HR Override) backing the Status — she can see *why* it says what it says, not just trust the badge blindly.
  - **Resolution:** She tells the project lead "three are ready, one needs attention" in about 90 seconds, with no spreadsheet cross-reference.
  - **Edge case:** If the label and her own memory disagree, the drill-down — not a re-check against the old sheet — is what resolves it. If she still reaches for the spreadsheet, the product hasn't done its job (see SM-C1, §7).

- **UJ-2. Casey resumes a video with zero manual reporting.**
  - **Persona + context:** Casey gets a notification: a skill has been assigned, with one recommended piece of content attached.
  - **Entry state:** Authenticated, opening the assignment notification.
  - **Path:** Opens Content Discovery, sees a list of assigned Skills grouped In Progress / To Start (no search box, no browsable catalog), picks the new one, plays it, watches to 14:32 of 28:00, closes the tab mid-video. Returns three days later, sees a "Continue Watching" card at 51% with "14 min remaining," clicks, and resumes at exactly 14:32.
  - **Climax:** The resume position is exactly right, on the first try — no re-scrubbing, no lost place.
  - **Resolution:** Casey never typed a status update. The same write that resumed the video already told Rita's dashboard "In Progress" (with Verified · 51% watched, 3 days ago one click away in drill-down).
  - **Edge case:** If Casey watches the same content in two tabs concurrently, the later timestamp wins — progress never regresses. Realizes FR-7.

- **UJ-3. Rita assigns a skill and watches the loop close itself.**
  - **Persona + context:** Rita decides a new must-do skill is needed and opens the assignment flow.
  - **Entry state:** Authenticated, Assignment Dashboard, clicks `[+ New Assignment]`.
  - **Path:** Three-step modal — select employee, select/search skill, review the AI-recommended content that's auto-linked (she isn't hunting for it herself) — then confirms.
  - **Climax:** The new row appears immediately: Status `Not Started`. She's done — total time under two minutes.
  - **Resolution:** Later, with zero further action from Rita, the row updates itself to `In Progress` as Casey watches (Verified · 23% watched, 2 hours ago in drill-down). Assignment → passive signal → verified dashboard → confident next call, with no manual sync step.
  - **Edge case:** If the assignment saves but the dashboard's live refresh fails, the assignment itself must not be lost — the UI shows a refresh error, not silent data loss.

## 3. Glossary

- **HR Admin** — The primary user role (persona: Rita). Assigns skills, makes readiness judgments. Not a people-manager role — assigns and judges org-wide, doesn't manage individual employees directly.
- **Employee** — The secondary user role (persona: Casey). Receives skill assignments, consumes recommended content, generates watch-progress signal passively. `[UPDATED 2026-09-11, corrected post-review]` HR Admin creates, views, edits, and deletes/archives Employee records from the Employees roster (§4.7, FR-24–28) — the Employee entity's system-of-record profile data (contact info, position, manager, department, etc.) and login provisioning both originate here, replacing the earlier hand-seeded demo list **for EMPLOYEE-role accounts**. HR_ADMIN account provisioning is a separate, still-open concern (Open Question 9) — this roster management does not touch it.
- **Session** — The authenticated context established after HR Admin or Employee login, carried via a JWT in an HTTP-only/Secure/SameSite cookie (see `addendum.md`, Technical Stack). Required before any Assignment, Content, or Watch Progress data is reachable (FR-13); scoped to exactly one role and, for Employees, exactly one identity (FR-14).
- **Skill** — A named competency HR can assign to an Employee (e.g., "Data Visualization"). Distinct from a **sub-skill**, a finer-grained status field that remains self-reported (out of MVP auto-capture scope). `[ADDED 2026-09-08]` HR Admin can create, edit, and delete Skills from the Skills tab (§4.6, FR-20/21/22) — but a Skill becomes permanently locked from editing or deletion the first time it's ever assigned to an Employee, protecting the stability of existing Assignment/audit history.
- **Assignment** — A record linking one Employee to one Skill, created by an HR Admin. Carries a Status badge (Not Started → In Progress → Completed) and, one level down via drill-down, a Provenance Label. An HR Admin can remove an Assignment (FR-15, added via `bmad-correct-course`, 2026-07-13); removal is a soft delete — the Assignment disappears from both the Dashboard and the Employee's Content Discovery list, but the underlying record and any watch-progress/override history are retained for audit, never physically deleted.
- **Content** — A video, document, or website recommended for a given Skill. Reaches the catalog via the scheduled batch job (§4.2) or, `[ADDED 2026-09-08]`, via an HR Admin's live lookup-and-attach action (§4.6). Only video content is auto-captured in MVP; document/website content is recommended but not progress-tracked.
- **Content Source API Key/Credential** — `[ADDED 2026-09-08]` What an HR Admin configures so FR-17's live content-link lookup can run: a **personal** per-Admin key for YouTube, or the **organization-wide** Udemy for Business client ID/secret (SAILS already holds this subscription). Distinct from the shared, system-managed key the batch ingestion job already uses.
- **Watch Progress** — The percentage of a video an Employee has watched, captured automatically from actual playback behavior, never typed in.
- **Status** — The primary at-a-glance completion badge shown on every dashboard row: **Not Started**, **In Progress**, or **Completed**, computed from Watch Progress percentage (0% / 1–99% / 100%). Answers "how far along," not "how much do I trust this" — that's the Provenance Label's job, one level down via drill-down (FR-9).
- **Provenance Label** — The trust indicator behind a row's Status, reached via drill-down (FR-9): **Verified** (auto-captured from video), **Self-reported** (employee-entered, non-video), **Needs Attention** (stale or inconsistent signal), or **HR Override** (manually confirmed ready by an HR Admin, independent of Watch Progress). Never color-only — always paired with text or icon (WCAG 2.1 AA).
- **HR Override** — A manual readiness confirmation by an HR Admin, used when Watch Progress or self-reported data doesn't reflect HR's actual confidence. Carries its own Provenance Label; never blended with or displayed as "Verified."
- **Needs Attention** — A dashboard state, not a separate page: a row whose self-reported data has gone stale beyond a defined freshness threshold. Surfaced via drill-down on the row itself, not a standalone filter view.
- **Readiness Dashboard** — The full row-grid view: one row per Employee×Skill assignment, each carrying a Status badge, with its Provenance Label one click away via drill-down. `[UPDATED 2026-09-12]` As of §4.10, this is no longer the HR Admin's first screen — it's reached via its own **Skill Assignments** left-nav entry (§4.8/FR-29) or a per-employee drill-down from the Skill Assignment Dashboard landing page (FR-33).
- **Skill Assignment Dashboard** — `[ADDED 2026-09-12]` The HR Admin's new landing page (§4.10): org-wide stats (Total Employees, Total Skills/Videos Assigned, Total Completed), an Assignment Progress breakdown (Completed / In Progress / Not Started counts + Overall Progress %), and an Employee Segmentation pie chart (On Track / In Progress / Needs Attention). A read-composition view only — it owns no table and introduces no new tracked data, matching the existing Readiness Dashboard's architectural pattern (AD-3/AD-8).
- **Skill Progress (per-Employee drill-down)** — `[ADDED 2026-09-12]` The single-Employee view reached by clicking an employee from the Skill Assignment Dashboard (FR-33): that Employee's own Assignment rows, rendered with the same Status/Provenance model as the Readiness Dashboard (FR-8/9/10), just pre-filtered to one Employee instead of the whole roster.
- **Employee Segmentation (On Track / In Progress / Needs Attention)** — `[ADDED 2026-09-12]` A per-Employee, dashboard-only categorization distinct from a per-Assignment Status or Provenance Label (§4.10/FR-32) — it summarizes an Employee's *entire* Assignment set into one of three buckets for the landing page's pie chart. Not a new tracked field; computed on read from existing Status/Provenance data.
- **Resume Position** — The exact video timestamp an Employee last reached; used to resume playback without re-scrubbing.
- **Coaching-only** — The data-use guarantee: auto-captured Watch Progress is never used as input to performance evaluations. A structural constraint on data access, not a policy statement (see §9 Constraints and Guardrails).

## 4. Features

### 4.1 Skill Assignment Flow

**Description:** HR Admin assigns a must-do Skill to an Employee. As part of the same flow, the system's AI-recommended Content for that Skill is shown so the HR Admin can see what the Employee will be pointed to — this is visibility, not a separate approval gate `[ASSUMPTION: no content-approval step in MVP — confirmed this session; content reaches the Employee automatically once matched, without a human QA checkpoint]`. Realizes UJ-3.

**Functional Requirements:**

#### FR-1: HR Admin assigns a Skill to an Employee

HR Admin can create an Assignment linking one Employee to one Skill. Realizes UJ-3.

**Consequences (testable):**
- Assignment flow (employee select → skill select → content review → confirm) completes in under 2 minutes for a single assignment.
- On confirm, the new Assignment appears on the Readiness Dashboard immediately, Status `Not Started`, with a success toast ("✓ Skill assigned to {Employee first name} — {Skill name}") and the new row visually highlighted for several seconds so HR Admin can locate it without searching.
- If the Assignment saves successfully but the dashboard's live view fails to refresh, the Assignment is not lost — the UI surfaces a refresh error, distinct from a save error.
- Canceling the assignment flow at any step before confirm leaves no orphaned Assignment record — a cancel is a true no-op, not a partial save.
- If the selected Skill is already assigned to the selected Employee, the flow surfaces the existing Assignment rather than silently creating a duplicate — HR Admin can update it or explicitly confirm a second, intentional Assignment.
- `[ADDED 2026-09-11, post-review]` The target Employee's active/non-archived status (§4.7/FR-27) is re-validated server-side at confirm time, not only when the employee picker was loaded — an Employee archived after the picker loaded but before confirm cannot have a new Assignment created against them; the HR Admin sees a clear error and must re-pick from the current roster.

#### FR-2: HR Admin sees AI-recommended Content during assignment

During the assignment flow, the system surfaces its matched Content recommendation for the selected Skill so the HR Admin can see what the Employee will be pointed to. Realizes UJ-3.

**Consequences (testable):**
- If no matching Content exists for a Skill, the flow allows the HR Admin to assign the Skill without Content, rather than blocking the assignment ("No approved content found yet for this skill. [Choose Different Content] or assign without content.").

#### FR-15: HR Admin removes an Assignment from the Dashboard

`[ADDED 2026-07-13 via bmad-correct-course — not in original PRD scope; surfaced from live dashboard use, not an original UJ.]` HR Admin can remove an Assignment from the Readiness Dashboard via a delete control on the row, after confirming the action.

**Consequences (testable):**
- Deletion is soft: the Assignment row is hidden from the Dashboard and from the Employee's Content Discovery list; the underlying `assignments`, `skill_progress`, and `assignment_overrides` records are retained for audit, never physically removed.
- A confirmation step is always required before delete executes; canceling leaves the Assignment untouched.
- If the Assignment has recorded watch progress, the confirmation copy explicitly names the recorded percentage before HR confirms; a Not Started Assignment gets plain confirmation copy.
- Any Assignment is deletable regardless of Status (Not Started / In Progress / Completed) or whether it carries an active HR Override.
- No restore/undo path exists in the product UI for this capability; recovery, if ever needed, is a database-level operation outside product scope.

### 4.2 AI-Assisted Content Discovery

**Description:** For each assigned Skill, the system recommends one relevant piece of Content (video, document, or website) — loose/approximate topical matches are acceptable; exact tag matching is not required `[ASSUMPTION: confirmed decision from prior research — semantic matching, not exact-tag filtering]`. The Employee sees these recommendations as a list across all their assigned Skills (FR-4), not a searchable catalog. This is discovery only: the system does not infer unmet skills or auto-assign anything — HR retains that judgment entirely. Realizes UJ-2, UJ-3.

**Functional Requirements:**

#### FR-3: System matches Content to an assigned Skill

The system surfaces Content relevant to a given Skill using semantic matching, not requiring exact vocabulary overlap between the Skill name and the Content's tags/description. Realizes UJ-2, UJ-3.

**Consequences (testable):**
- If no Content clears the relevance threshold for a Skill, the system surfaces no recommendation rather than a low-relevance guess — a blank result is preferred to a misleading one (the same design principle FR-8's Provenance Labels follow: an honest "nothing here" beats a confident wrong answer).

**Out of Scope:**
- Automatic detection of skill gaps or unmet-skill inference. HR assigns; the system never decides what should be assigned.

#### FR-4: Employee views all their assigned Content in one list, without searching

Employee sees a list of all Content recommended across their assigned Skills, grouped by status (In Progress / To Start), with summary counts (Total / In Progress / To Start). `[ASSUMPTION: confirmed pivot this session — the original model was a single recommendation per Skill with no list view; this list model is now the intended scope]`. Each Skill still surfaces exactly one recommended piece of Content — the list is Content-per-assigned-Skill, not a searchable catalog or multiple candidates per Skill. Realizes UJ-2.

**Consequences (testable):**
- The list is scoped strictly to the Employee's own assigned Skills — never a browsable catalog, and never another Employee's assignments (see Non-Goals, §5).
- Distinct empty states for distinct conditions: no Content matched for a given Skill yet ("No recommended content yet for this skill. [Contact Rita]") versus nothing currently in progress ("Nothing in progress right now. [View your assignments]") are different states, not one generic empty view.
- If a video fails to load, the Employee sees an explicit error state ("This video couldn't be loaded. [Try again]"), not a silent blank player — this must hold in the real build regardless of what the current prototype shows (see addendum, prototype regressions).

**Feature-specific NFRs:**
- Content ingestion (for video sources) runs as a scheduled batch job, not live per-request search — the underlying video-source API has a hard daily quota that cannot support on-demand querying at pilot scale. `[NOTE FOR PM]` This caps how quickly the Content catalog can grow or refresh; if pilot feedback demands broader/fresher catalog coverage, the ingestion cadence is the first constraint to revisit.

### 4.3 Automatic Video Progress Capture & Resume

**Description:** The system captures an Employee's video watch position automatically during playback and lets them resume at the exact last position later. These two behaviors are architecturally one feature, not two separable ones — a single data write updates both the Employee's resume point and the HR Admin's dashboard signal. Realizes UJ-2.

**Functional Requirements:**

#### FR-5: System captures video watch position automatically

The system records an Employee's playback position during video viewing without any manual entry. Realizes UJ-2.

**Consequences (testable):**
- Watch position is sampled during active playback (target cadence: every 5–10 seconds).
- On tab close or visibility change, the last known position is flushed reliably via the browser's `sendBeacon` mechanism (not dependent on the next poll interval landing first).
- No Employee-facing input field exists for reporting video progress manually.
- If the video fails to load, the Employee sees a clear error state, not a silent blank player.

#### FR-6: Employee resumes a video at the exact last-watched position

Employee can return to an assigned video and resume playback from their last captured position, without manually seeking. Realizes UJ-2.

**Consequences (testable):**
- Resume position matches the last captured watch position exactly on first use — a wrong resume point on an Employee's first encounter with the feature is treated as a launch-blocking defect, not a minor bug.
- If a stored resume position fails to load correctly, the Employee gets an explicit "Start over" fallback rather than a broken or stuck player.
- Before any video has been watched, the Continue-Watching surface shows an explicit empty state, not a blank space.

#### FR-7: Watch-progress writes are ordered by event time, not by position

If watch-position updates arrive out of order (e.g., the same video open in two tabs), the system applies only the update whose *event timestamp* (when the client observed that position) is newer than what's stored — ordering is by time, not by position value. Realizes UJ-2.

**Consequences (testable):**
- Two-tab concurrent-watch scenario: opening the same video in two tabs and generating out-of-order updates does not regress the stored progress — a write with an older event timestamp arriving after a newer one is dropped, regardless of its position.
- `[NOTE FOR PM]` This must NOT be implemented as "reject any update with a lower position than what's stored" — that would incorrectly block a legitimate rewind (an Employee intentionally scrubbing backward mid-session produces a lower position with a *newer* timestamp, and must be accepted). Ordering by event time, never by position magnitude, is what distinguishes a real rewind from a stale out-of-order write.

### 4.4 Readiness Dashboard — Status at a Glance, Provenance on Drill-Down

**Description:** HR Admin's primary surface: one row per Employee×Skill Assignment. Each row leads with a **Status** badge (Not Started / In Progress / Completed) as the at-a-glance signal, with the **Provenance Label** (the trust detail — Verified / Self-reported / Needs Attention / HR Override) one click away via drill-down rather than on the row itself. `[ASSUMPTION: confirmed pivot this session — the row previously led with Provenance directly; Status-as-primary is now the model]`. Includes a "Needs Attention" state for stale self-reported data, surfaced via drill-down rather than a separate page. Realizes UJ-1, UJ-3.

**Functional Requirements:**

#### FR-8: HR Admin views per-Assignment rows with a Status badge

Each Assignment row displays its Skill, progress, and a Status badge: **Not Started**, **In Progress**, or **Completed**, computed from Watch Progress percentage. Realizes UJ-1.

**Consequences (testable):**
- The badge is never conveyed by color alone — always paired with text or an icon (WCAG 2.1 AA).
- `[NOTE FOR PM]` **Unresolved coherence risk, not silently smoothed over:** Status is computed purely from Watch Progress percentage, with no distinction between a Verified percentage and a Self-reported (unverified) one at the row level. A Self-reported "40% — In Progress" and a Verified "40% — In Progress" render identically on the grid. This risks reintroducing the exact trust-ambiguity problem this product exists to solve, unless the one-click drill-down (FR-9) is genuinely always available and HR Admins actually use it before trusting a Status badge at face value (see SM-C1, and the untested label-comprehension risk at Open Question 8). Logged as Open Question 11, not resolved here.

**Notes:** Earlier spreadsheet-era columns (start date, estimated end date, actual end date) are superseded by this Status + drill-down model, not silently dropped — the badge and its drill-down carry the readiness signal those columns used to.

#### FR-9: HR Admin drills down into the Provenance Label and raw signal behind a Status badge

From any dashboard row, HR Admin can open a drill-down showing the Provenance Label (Verified / Self-reported / Needs Attention / HR Override) and the underlying data (watch %, last-updated timestamp) that produced the row's Status. Realizes UJ-1.

**Consequences (testable):**
- Drill-down is reachable from every row in one click/tap, not just flagged ones — Rita must be able to defend any readiness call, not only the ones the system already flagged. `[NOTE FOR PM]` **This regressed in the current prototype** (the row-level entry point was removed in a UI-cleanup pass, leaving the drill-down reachable only via a demo/debug URL parameter) — flagging explicitly so the real build doesn't repeat it. This consequence must hold in the shipped product regardless of what the current prototype shows.
- Freshness is stated in plain language ("Not updated in 14 days") within the drill-down, not an ambiguous status word.

#### FR-10: Dashboard flags stale self-reported data as "Needs Attention"

Rows whose self-reported (non-video) data has gone stale beyond a defined threshold carry a **Needs Attention** Provenance Label, reachable via drill-down (FR-9). Realizes UJ-1.

**Consequences (testable):**
- Staleness threshold is **7 days** without a data update, matching the original success-metric proposal from design-thinking discovery (self-reported status stale beyond 7 days). UJ-1's "14 days" example is illustrative of a row well past that threshold, not the threshold itself.
- `[NOTE FOR PM]` **Same coherence risk as FR-8's note, sharpened here:** if "Needs Attention" only exists inside the drill-down and the row-level Status badge (Not Started/In Progress/Completed) doesn't distinguish a healthy Verified row from a stale Self-reported one, HR loses the ability to visually scan for problem rows at all — directly undercutting the original design target of replacing full-grid scanning with spotting flagged rows at a glance (Business Goals Objective 3). Whether the Status badge needs a secondary visual cue for Needs Attention/stale rows specifically (separate from the general Status/Provenance split in FR-8) is unresolved — see Open Question 11.
- This FR only defines staleness for **Self-reported** rows. Whether a **Verified** row whose Watch Progress has stopped advancing (an Employee started a video, then abandoned it) should also eventually flag as Needs Attention is unresolved — no source material specifies a video-specific staleness threshold.

**Out of Scope:**
- A separate "Needs Attention" filter page. This is a row-level state surfaced via drill-down, deliberately not a standalone view (design decision already made during prototyping).

#### FR-11: Dashboard rows update automatically as Watch Progress arrives

Once an Assignment exists, its row's Status badge updates itself (`Not Started` → `In Progress` → `Completed`, per FR-8) as Watch Progress data arrives, with zero manual action from the HR Admin. Realizes UJ-3.

**Consequences (testable):**
- A dashboard row reflects a new watch-position update within 30 seconds, without requiring a manual page refresh.

#### FR-12: HR Admin manually overrides an assignment's readiness status

HR Admin can mark an Assignment as ready independent of its Watch Progress or self-reported status, for cases where HR has other grounds for confidence (e.g., a conversation, a completed offline assessment). This promotes what earlier scoring called the "Assessed Live" audit-flag concept from a v2 candidate into MVP, per PRFAQ commitment reconciliation.

**Consequences (testable):**
- An overridden row's Status badge reflects the override (e.g., `Completed`), but its Provenance Label — reachable via drill-down — is its own distinct state, **HR Override**, never silently merged into or displayed as "Verified." Provenance now carries four states, not three (§3 Glossary): Verified, Self-reported, Needs Attention, HR Override.
- The override is timestamped and attributed to the HR Admin who made it; visible in the row's drill-down (FR-9) alongside any other signal history for that row.
- An HR Override can be reversed by an HR Admin. If fresher Watch Progress or self-reported data arrives on an overridden row, it does not silently replace the override — both are visible in the drill-down, and the override stands until an HR Admin explicitly changes it.

**Notes:** `[NOTE FOR PM]` No existing UX scenario or prototype covers this interaction (it wasn't in the original three scenarios built and tested). Downstream UX work needs to design the override entry point and confirmation flow, not just implement it from this FR description alone.

### 4.5 Authentication & Session Gate

**Description:** Every User Journey in this PRD assumes an "Authenticated" entry state (UJ-1, UJ-2, UJ-3) — until this update, no Functional Requirement defined what that meant. This feature closes the authentication half of what was Open Question 9: no Assignment, Content, or Watch Progress data is reachable without a valid session, and a session is scoped to exactly one role (HR Admin, or exactly one Employee identity). The session-carrying mechanism itself (JWT in an HTTP-only/Secure/SameSite cookie) was already locked during technical research (`addendum.md`, Technical Stack); this feature turns that locked mechanism into testable product behavior. `[ASSUMPTION: the login → role-routing → own-data-only UX pattern below was validated end-to-end against a prototype-level mock gate via the wds-8-product-evolution pipeline (2026-07-09) — see _bmad-output/evolution/. The mock gate's client-side, hardcoded-credential implementation is explicitly not the production mechanism; see Open Question 9.]`

**Functional Requirements:**

#### FR-13: System requires a valid authenticated session before any Assignment, Content, or Watch Progress data is served

No dashboard, content-discovery list, video, or API response containing Assignment/Content/Watch-Progress data is reachable without a valid session. Realizes UJ-1, UJ-2, UJ-3.

**Consequences (testable):**
- Requesting any protected page or endpoint with no session, or an expired session, redirects to login before any protected content renders — never a flash of protected content followed by a redirect.
- Session is carried via a JWT in an HTTP-only/Secure/SameSite cookie (locked stack decision, `addendum.md`), not `localStorage` or a URL parameter — not inspectable or forgeable from client-side script.
- Signing out invalidates the session immediately; re-requesting a previously-open protected page afterward redirects to login again, never a cached view.
- `[NOTE FOR PM]` Where account credentials originate (HR- and Employee-provisioned local accounts vs. company SSO) and where the Employee roster comes from are still undecided — see Open Question 9. This FR defines session/access-gate behavior, not the identity-provisioning source.

#### FR-14: A session is scoped to exactly one role and, for Employees, exactly one identity

An HR Admin session can reach the Readiness Dashboard and Skill Assignment Flow; an Employee session can reach only Content Discovery and Continue-Watching, scoped to that Employee's own Assignments — never another Employee's. Realizes UJ-1, UJ-2, UJ-3.

**Consequences (testable):**
- An Employee session can never retrieve or display another Employee's Assignment, Content, or Watch Progress data, regardless of how the request is formed — this is the hard Non-Goal already stated in §5 ("An Employee can never view another Employee's assignments"), now backed by an access-control FR rather than only a UI-level assumption.
- A valid session presented against a role it doesn't hold (e.g., an Employee session requesting an HR-only endpoint) is refused with an explicit access-denied response, not a silent empty result or a broken redirect.
- `[NOTE FOR PM]` The prototype validated the *shape* of this (role-based login routing, a wrong-role notice instead of a broken redirect) using a mock, single-device credential store — the real build must enforce this scoping server-side, on every request, not just at the login/routing step client-side.

### 4.6 Admin-Assisted Content Sourcing (Live Skill-Link Lookup & Curation)

`[ADDED 2026-09-08 via bmad-prd update — new enhancement request, not in original PRD scope]`

**Description:** From the Skills tab of the Admin dashboard — which opens on a list of every Skill in the system — HR Admin either picks an existing Skill or creates a new one (FR-20), edits or deletes it while it's still unassigned (FR-21, FR-22), then either (a) triggers a live search for candidate learning-content links on YouTube and/or Udemy, or (b) pastes a content link in directly (FR-17a), reviews the candidate(s) — including whatever is currently approved, with the option to reject it outright (FR-23) — sees an estimated days-to-complete for each (FR-19), and attaches one or more approved links as Content for that Skill. This supplements — it does not replace — the existing scheduled batch-ingestion pipeline that auto-matches Content to Skills for Employees (§4.2, FR-3/FR-4): batch ingestion keeps populating the catalog in the background; this feature lets an HR Admin fill a specific gap immediately, on their own initiative. `[UPDATED 2026-09-08]` Udemy was briefly dropped from v1 (2026-09-08 architecture research: no free, self-serve public search API exists — Udemy's Affiliate API was discontinued 2025-01-01, and the remaining APIs require a paid Udemy for Business subscription). **Restored the same day**: SAILS already holds a Udemy for Business subscription, so the zero-budget objection doesn't apply — see Open Question 14. `[NOTE FOR PM]` Udemy's credential model is not the same shape as YouTube's, though — see FR-16.

`[RESOLVED 2026-09-08, architecture spine update]` **This is a live, per-request lookup — architecturally distinct in kind from the existing batch job, not a variation of it.** The architecture doc amended AD-7 with a narrow, explicit carve-out: an HR Admin's live lookup is permitted specifically because it runs against that Admin's own, individually-provisioned API key (FR-16), never the shared batch key — the batch job's quota-protection rule is otherwise unchanged. Per-admin key storage is encrypted at rest (new AD-10). See Open Question 13 (now resolved) for the full reasoning.

**Functional Requirements:**

#### FR-16: HR Admin manages content-source API credentials for lookups

Before FR-17's lookup works for a given source, a credential must be configured for it. `[UPDATED 2026-09-08]` The two sources have **different credential shapes**, confirmed via architecture research, not assumed identical:
- **YouTube:** a **personal, per-Admin** API key — free, self-serve, one per individual Google/developer account. Each Admin adds their own; `[ASSUMPTION]` not shared with or visible to other Admins, matching the original request's framing ("his api keys").
- **Udemy:** a **single, organization-wide** client ID/secret pair issued by Udemy for Business per UFB account, not per individual — SAILS already holds this subscription (confirmed 2026-09-08). `[ASSUMPTION]` Any HR Admin can view (as "configured," never the raw secret) and update this one shared org credential — it is inherently not personal the way the YouTube key is, so "connected by {Admin name}" is the right framing, not "each Admin's own." Revisit if a narrower "only the Admin who configured it can change it" model is preferred.

**Consequences (testable):**
- An Admin can add, replace, and remove the YouTube key (personal) and the Udemy credential (org-wide, if not already configured by another Admin) from an account/settings surface reachable from the Skills tab.
- Once saved, neither credential is ever redisplayed in plaintext — the UI shows only that each source is configured (e.g., "YouTube: connected," "Udemy: connected by {Admin name}, {date}"), consistent with standard secret-handling practice.
- If a given source has no credential configured, the lookup entry point (FR-17) shows a clear prompt to add one first for that source, rather than attempting a lookup and failing opaquely — the other source, if configured, still works (partial availability, not an all-or-nothing gate).
- An invalid or revoked credential produces a clear, source-specific error at the point of lookup (FR-17), not a silent empty result.

#### FR-17: HR Admin performs a live content-link lookup for a Skill

From the Skills tab, HR Admin enters or selects a Skill and triggers a live search against whichever source(s) have a configured credential (FR-16), returning candidate content links (title, source, link, and available metadata such as duration/thumbnail).

**Consequences (testable):**
- Results are clearly labeled as unreviewed candidates ("Search Results"), never as "Recommended" — that label is reserved for the existing AI-matched Content shown to Employees (§4.2), so the two flows are never visually conflated.
- Results are grouped or labeled by source (YouTube / Udemy) so the Admin knows where each link came from.
- `[NOTE FOR PM]` Udemy results are scoped to whatever SAILS's Udemy for Business subscription actually licenses (its own catalog), **not the full public Udemy marketplace** — a real, testable behavior difference from YouTube's open search. Worth confirming this narrower scope is acceptable before build, since "look up a course on Udemy" may read to a first-time user as "search all of Udemy."
- If a source's search returns nothing, that source's section shows an explicit empty state ("No results from {source} for this skill"), not a blank area indistinguishable from a loading state.
- If a source's search fails (invalid/missing credential, source API error, rate limit), that source shows a distinct, source-specific error state; a failure in one source does not block results from the other.
- This lookup is a distinct, deliberately-triggered admin action — it never runs automatically or silently in the background (unlike the batch job), consistent with the "never live per-request search" language in FR-3/FR-4's NFR being reserved for *unattended* system-triggered search.
- `[UPDATED 2026-09-08, REVISED again 2026-09-08]` For a Skill that has never been assigned, the Edit entry point (FR-21) is the single way to reach this lookup. **A standalone "Find Content" button was tried as the equivalent entry point for assigned Skills, then removed from every card, assigned or not, per direct feedback the same day — see Open Question 17.** As of this revision, an assigned Skill has **no UI entry point into FR-17/18/23 from the Skills tab at all**, even though FR-23's own wording still states content rejection/replacement "works regardless of Skill assignment/lock status." That capability is real but currently unreachable in the UI for an assigned Skill — flagged, not silently resolved.

#### FR-17a: HR Admin manually enters a content link, as an alternative to search

`[ADDED 2026-09-08, from UX design session]` Instead of searching (FR-17), HR Admin can paste a content URL directly into the Skills tab for the same review-and-approve treatment (FR-18). Reuses this product's existing "manually seed content, bypassing any source API" pattern already established for the batch pipeline's operator-facing CLI (`source: MANUAL`) — this FR is that same capability, exposed through the Admin UI instead of a terminal command.

**Consequences (testable):**
- A manually-entered link goes through the identical review/approve step as a searched result (FR-18) — it is never attached automatically just because it was typed in directly.
- No source-specific metadata (duration, thumbnail) is fetched for a manually-entered link unless the Admin also supplies it — an estimated completion time (FR-19) is simply omitted for a manual entry with no duration, consistent with "no data beats a guessed one" (FR-3's principle).
- A manually-entered link is not validated against YouTube/Udemy or any other source — HR Admin is responsible for the link being correct and appropriate; no automated content-quality check exists (consistent with §5's "not a content-approval workflow" Non-Goal for AI-surfaced content, extended here to manually-entered content too).

#### FR-18: HR Admin reviews and attaches a looked-up link as approved Content for a Skill

From the lookup results (FR-17), HR Admin selects one or more links and attaches them as Content for the Skill being curated.

**Consequences (testable):**
- An attached link becomes visible to Employees the same way existing batch-matched Content is (§4.2) — same Content surface, not a separate list.
- Each attached Content item records which HR Admin attached it and when, for audit — same audit expectation this PRD already holds for HR Overrides (FR-12).
- Attaching a link is additive: it does not remove or replace any existing batch-matched Content already recommended for that Skill on its own — an explicit removal action now exists for the admin-approved link specifically (FR-23), resolving what was previously an open assumption here.
- `[ADDED 2026-09-08, from UX design session]` The Skills tab's per-Skill summary card (see UX spec 04.1) always shows exactly one approved link per Skill — the most recently approved — never a list, even if more than one item has been approved for that Skill over time. This mirrors the Employee-facing "always exactly one recommendation per Skill" rule already locked for Content Discovery (§4.2/FR-4); it constrains what the summary card *displays*, not what FR-18 permits *attaching*. Clicking it opens the same in-app watch popup described below, not a new-tab redirect.
- `[ADDED 2026-09-08, from UX design session]` Before approving, HR Admin can open any candidate to watch/preview it — an in-app watch popup with a close control, not a bare new-tab redirect, so review doesn't mean leaving the product. `[UPDATED 2026-09-08]` Embeds the actual video when the source supports it (YouTube); for a source that can't be embedded (Udemy, most manually-pasted links), the popup shows a clear "preview not available" state with an explicit "Open in new tab" fallback, rather than silently failing. On Approve, the Content Lookup panel closes immediately — no intermediate "approved, panel stays open" state — returning HR Admin directly to the Skills tab, where that Skill's card now shows the newly approved link, confirmed by a toast.
- This action is HR Admin-only, gated the same way every other write in this PRD is (FR-14's role scoping) — an Employee session can never reach this surface or its underlying endpoints.

**Out of Scope:**
- This does not turn Content Discovery into a searchable catalog for Employees (§5 Non-Goals still holds) — the lookup/search surface is Admin-only; Employees still only ever see the curated, attached result.
- No automatic re-validation of previously-attached links (e.g., checking a video was taken down or a Udemy course was removed from the org's licensed catalog) — same accepted risk already logged for batch-matched Content (Open Question 10).

#### FR-19: System estimates days-to-complete for a candidate or attached Content item

`[ADDED 2026-09-08, from UX design session]` During review (FR-18), HR Admin sees an estimated number of days to complete each candidate — and later, the attached — Content item, computed from its duration at a fixed pace of **5 hours per day**.

**Consequences (testable):**
- Estimate = `ceil(duration_hours / 5)`, shown as e.g. "≈ 2 days to complete (at 5 hrs/day)" alongside the link during review (FR-18) and wherever the attached Content is later surfaced to the Employee (§4.2).
- The 5-hours/day pace is a single, fixed, system-wide constant in v1 — `[ASSUMPTION]` not configurable per Skill, per Employee, or per Admin; revisit if a real pilot user asks for it to vary.
- If a candidate has no duration available — a manually-entered link with none supplied (FR-17a), or a source that didn't return one — the estimate is omitted entirely, never guessed. Consistent with FR-3's "no match beats a bad match" principle, applied here to "no estimate beats a wrong one."
- This estimate is informational only; it does not gate, block, or influence the approve/attach action (FR-18) in any way.

#### FR-20: HR Admin creates a new Skill, flowing directly into content-sourcing

`[ADDED 2026-09-08, from UX design session]` Every Skill in this PRD up to now originates from a fixed, pre-seeded catalog (Story 3.2's seed script) — no FR has ever let an HR Admin add one. This closes that gap: from the Skills tab, HR Admin creates a new Skill (name required), and the flow lands directly in the FR-17/FR-17a content-sourcing experience for that Skill, pre-populated with the name just entered — closing the "brand-new Skill, zero content" gap at the moment of creation rather than leaving Rita to remember to come back.

**Consequences (testable):**
- "+ New Skill" opens a lightweight entry: Skill name (required), description (optional).
- On submit, the Skill is created and immediately appears in the Skills tab's card grid (§4.6 UX spec 04.1); the Content Lookup panel (FR-17) opens automatically for it, with the search term pre-filled from the entered name — HR Admin can search YouTube/Udemy right away, paste a link directly (FR-17a), or close the panel and source content later. Content-sourcing is not force-coupled to creation: closing without approving anything still leaves the new Skill created, with "None yet" shown on its card (mirrors FR-2's existing "assign without content" allowance).
- If the entered name matches an existing Skill (case-insensitive), the flow surfaces the existing Skill instead of creating a duplicate — same anti-duplicate principle as FR-1's existing-Assignment surfacing.
- A newly-created Skill is immediately selectable everywhere Skills are chosen elsewhere in the product (e.g., the Skill Assignment Flow's skill selector, FR-1) — no separate publish/activation step.
- `[NOTE FOR PM]` A newly-created Skill's eligibility for the *batch* AI-matching pipeline (§4.2/FR-3) depends on that Skill having an embedding computed and at least one ingestion run — this FR only guarantees the *admin-sourced* path (FR-17/18) works immediately; the batch path catches up on its normal schedule. Not a conflict, just two different timelines for two different sourcing paths on the same Skill.

**Out of Scope:**
- Any bulk-import mechanism (CSV, etc.) — one Skill at a time via this flow.

#### FR-21: HR Admin edits an unassigned Skill's name or description

`[ADDED 2026-09-08, from UX design session]` `[UPDATED 2026-09-08]` Reverses this FR's original "editing is out of scope" note, now that full Skill lifecycle management (create/edit/delete) is requested. HR Admin can edit a Skill's name and/or description from the Skills tab — but **only until that Skill has been assigned to an Employee for the first time**; once assigned, it is permanently locked from editing.

**Consequences (testable):**
- Edit is available from each Skill's card, but only while the Skill has zero Assignments referencing it — the moment the first Assignment is created for a Skill (FR-1), that Skill's edit control disables permanently. This is not reversible even if every Assignment referencing it is later removed (FR-15's soft-delete) — historical Assignment/audit records must always resolve to a stable Skill identity, so "has ever been assigned" is a one-way gate, not a live count.
- A locked (ever-assigned) Skill's card shows why editing isn't available (e.g., "Locked — assigned to an Employee") rather than silently hiding the control with no explanation.
- Renaming a Skill re-triggers the embedding computation the batch matching pipeline (§4.2/FR-3) depends on — same "new Skill, batch catches up on its normal schedule" timing note as FR-20.
- Duplicate-name protection applies here too: renaming to a name that collides with another existing Skill (case-insensitive) is rejected with the same notice pattern as FR-20.
- `[UPDATED 2026-09-08]` Editing a Skill opens the same experience as FR-17/FR-18's content lookup — showing whatever is currently approved for it, if anything, alongside the ability to search for or paste a replacement — rather than a bare name-only form disconnected from content. Renaming and content-sourcing happen in one place, not two separate flows.

#### FR-22: HR Admin deletes an unassigned Skill

`[ADDED 2026-09-08, from UX design session]` Same lock as FR-21: HR Admin can delete a Skill only while it has never been assigned to an Employee. This closes the loop on a genuine "I created this by mistake" case (wrong name, duplicate, or a Skill nobody ended up needing) without threatening any Assignment/audit history, which by construction can never exist yet for a deletable Skill.

**Consequences (testable):**
- Delete requires a confirmation step, same pattern as FR-15's Assignment removal — canceling leaves the Skill untouched.
- `[ASSUMPTION]` Because a deletable Skill has zero Assignments by definition, deletion is a **hard delete** (the row and its content_catalog links are actually removed), not a soft delete like FR-15 — there is no audit trail to preserve for a Skill nothing has ever referenced. Any Content links approved for it via FR-18 are removed along with it (nothing else could reference them, since no Assignment exists). Revisit only if a future requirement needs to recover an accidentally-deleted unassigned Skill.
- Once locked (ever-assigned), a Skill can never be deleted — same permanent, one-way gate as FR-21, for the same reason (audit-record stability).
- A locked Skill's card shows the same "Locked — assigned to an Employee" explanation as FR-21 in place of a Delete control.

**Out of Scope:**
- Deleting or editing a Skill that has ever been assigned, under any circumstance — no override, no admin-only bypass. If a mistake reaches an Employee's assignment, the correction path is a new Skill, not editing the old one out from under existing history.

#### FR-23: HR Admin rejects the currently approved Content link for a Skill

`[ADDED 2026-09-08, from UX design session]` `[UPDATED 2026-09-08]` Reverses this section's prior framing (FR-18's original consequence treated removal as only implicit, via approving a replacement, with an open `[ASSUMPTION]` about the mechanism) — HR Admin can now explicitly reject/remove the currently approved link for a Skill on its own, independent of approving a new one. Shown alongside the review experience (FR-17/FR-18), not as a separate flow.

**Consequences (testable):**
- A "Reject" action sits next to the currently-approved link wherever it's shown during review (the same surface FR-18's review happens on) — HR Admin can reject it without having anything lined up to replace it with.
- Rejecting clears the Skill back to "no approved Content" (the same state as a Skill that was never sourced) — it does not require or trigger approving a replacement in the same action; the Admin can search afterward, or leave the Skill without approved Content for now.
- Unlike FR-21/FR-22's Skill-identity lock, rejecting a Content link is **not** gated by whether the Skill has ever been assigned — a Skill actively assigned to an Employee is exactly the case where swapping out a bad or outdated link matters most, so this rule holds regardless of the Skill's assignment/lock status (FR-21/FR-22's lock is about the Skill's own identity — name/description/existence — not its Content). `[NOTE FOR PM, ADDED 2026-09-08]` This rule is currently **not reachable from the UI** for an assigned Skill — see Open Question 17. Stated here as the intended product rule regardless of today's UI gap.
- This is a hard removal (the previously-approved Content row and its attribution are gone), not a soft-delete/audit-preserving one — `[ASSUMPTION]` consistent with FR-22's reasoning that admin-sourced Content carries lighter audit weight than Assignment/watch-progress history; revisit if a real pilot use case needs to know what was previously approved for a Skill.
- No confirmation step required (unlike FR-22's Skill deletion) — rejecting a Content link is lower-stakes and reversible in spirit (the Admin can immediately search and approve something else); `[ASSUMPTION]` revisit if this proves too easy to trigger by accident in practice.

### 4.7 Employee Roster Management

`[ADDED 2026-09-11 via bmad-prd update — new capability, not in original PRD scope]`

**Description:** HR Admin manages the canonical Employee roster directly in-product — creating, viewing, editing, and deleting/archiving Employee records — replacing the previous hand-seeded/demo employee list as the system's source of truth for Employee profile data and, for **EMPLOYEE-role accounts specifically**, login provisioning. `[CORRECTED 2026-09-11, post-review]` This does not touch how HR_ADMIN accounts are provisioned or authenticated — that remains on the existing mock credential store (`auth/repository.py`) untouched by this feature; see Open Question 9. This is an HR Admin-only capability; there is no Employee-facing self-service profile view (Employee Profile View remains deferred per §6.2 — that item refers to an Employee viewing/editing their *own* profile, a different concern from HR managing the roster here). Creating an Employee record here also provisions that Employee's login: Email is the login identity, and the system auto-generates an initial password shown once to the HR Admin to share out-of-band, since no email-sending infrastructure exists in this zero-budget-constrained stack (§9).

**Functional Requirements:**

#### FR-24: HR Admin creates a new Employee record

HR Admin creates a new Employee-role record with: Employee ID/Code (HR-assigned, distinct from the system's internal identifier), Name, Email, Phone Number, Experience, Technologies, Position/Job Title, Project, Manager Name, Location, and Department. `[NOTE FOR PM]` This FR provisions EMPLOYEE-role accounts only; creating additional HR_ADMIN accounts is not covered here and remains an open gap — see Open Question 9.

**Consequences (testable):**
- Email must be unique across the roster (matches the existing `employees.email` unique constraint), checked case-insensitively (same duplicate-detection rule already used for Skill names, §4.6/FR-20) — attempting to create a second Employee with an already-used email is rejected with a clear message, not a silent overwrite or duplicate row.
- On successful creation, the system auto-generates an initial password and displays it once, in the creation-confirmation UI, to the HR Admin — never emailed, never re-displayable after the confirmation view is dismissed (same "write-only after initial display" pattern already established for API keys, §4.6/FR-16). `[NOTE FOR PM, ADDED 2026-09-11]` This "never re-displayable" guarantee is only a real security guarantee if enforced server-side (a one-time-reveal flag consumed on first view) — client-side UI discipline alone (e.g. just not showing a "view password" button again) does not actually prevent re-access. The architecture pass must pick the server-side approach for this consequence to hold in practice (see addendum).
- The new Employee immediately appears in the roster (FR-25) and is immediately selectable in the Skill Assignment Flow's employee picker (§4.1/FR-1) — no separate publish/activation step (mirrors FR-20's "immediately selectable" pattern for new Skills), **provided** the Employee is not archived (§4.1/FR-1 gains a matching consequence).
- Employee ID/Code must be unique; a duplicate is rejected with a clear message. `[ASSUMPTION, ADDED 2026-09-11]` A hard-deleted Employee's ID/Code and Email become available for reuse by a future hire; an archived (soft-deleted) Employee's do not, since the record still exists — revisit if HR wants stricter reuse prevention regardless of delete type.
- Name, Email, and Employee ID/Code are required; Phone, Experience, Technologies, Position/Job Title, Project, Manager Name, Location, and Department are optional at creation. `[ASSUMPTION]` Not every field is realistically known at hire time — revisit if HR needs any of these enforced as required.

**Notes:** `[NOTE FOR PM]` No existing UX scenario or prototype covers this interaction (it wasn't part of the original three UJs). Downstream UX work needs to design the creation form, the one-time password-reveal screen, and its confirmation copy.

#### FR-25: HR Admin views the Employee roster

HR Admin sees a list of all Employee records with their profile fields, serving as the system's source of truth for the roster.

**Consequences (testable):**
- The roster is searchable/filterable by at least Name, Department, and Position/Job Title — the same "find who you need fast, don't just browse" principle already applied to Content Discovery (§4.2/FR-4), applied here to roster size instead of content volume. `[NOTE FOR PM, ADDED 2026-09-11]` Department filtering depends on the addendum's still-open schema decision (whether Department reuses the existing `group` column or is a distinct new column) — this consequence holds structurally regardless of which is chosen, but isn't buildable until that call is made.
- A blank/optional field (Department, Position/Job Title, etc. — FR-24) is excluded from a filter on that field rather than silently matching everything or nothing; an Employee with an unfilled field never becomes permanently unfindable — they remain reachable via Name search regardless of which optional fields are blank.
- A soft-deleted/archived Employee (FR-27) does not appear in the default roster view or in any Employee picker elsewhere in the product (e.g. the Skill Assignment Flow), but remains visible via an explicit "show archived" toggle for audit purposes — mirrors FR-15's Assignment soft-delete visibility pattern.

#### FR-26: HR Admin edits an Employee record

HR Admin edits any Employee's profile fields (all fields from FR-24 except Employee ID/Code, which is immutable once set).

**Consequences (testable):**
- Edit is always available regardless of the Employee's Assignment/watch-progress history — unlike a Skill's identity-lock (§4.6/FR-21/22), an Employee's profile fields (phone, manager, location, project, department) are expected to change over time (promotions, transfers), and locking them would block routine HR maintenance.
- Editing Email re-validates the uniqueness constraint (FR-24) and, since Email is the login identity, updates the Employee's login going forward. `[ASSUMPTION]` An existing session is not silently invalidated by an Email edit — revisit if this proves confusing in practice.
- Employee ID/Code cannot be changed after creation.
- Concurrent edits to the same Employee record by two HR Admins use last-write-wins, with no optimistic-lock/conflict detection in v1. `[ASSUMPTION, ADDED 2026-09-11]` Revisit if concurrent HR Admin edits prove to cause real data loss in practice — no other write path in this PRD has conflict detection either.
- `[DECISION, ADDED 2026-09-11, post-review]` Renaming an Employee's Name re-renders that new name on every historical Assignment/Watch-Progress/HR-Override record referencing them — Employee identity is resolved live at read time (`assignment.employee.name`), not snapshotted at the time each historical record was created. This is accepted as intended behavior for this update, not a defect; it does mean a drill-down (FR-9) or Override history (FR-12) reflects the Employee's *current* name, not their name *at the time* of that historical event. Revisit with a name-snapshot mechanism only if a real audit/compliance need for point-in-time identity surfaces.
- Manager Name is a free-text field, not a reference to another Employee record. `[ASSUMPTION, ADDED 2026-09-11]` It is an unmaintained snapshot — if the named manager is later renamed, archived, or deleted, this field does not update and carries no staleness indicator. Revisit if HR needs it to stay live-linked.

#### FR-27: HR Admin deletes or archives an Employee record

If an Employee has never had an Assignment created for them, HR Admin can hard-delete the record. Once an Employee has any Assignment history (active or soft-deleted, per §4.1/FR-15) — the moment they've ever been assigned any Skill — HR Admin can only soft-delete/archive them: the record and its full Assignment/Watch-Progress/Override history are retained, but the Employee drops off the active roster and every Employee picker (FR-25).

**Consequences (testable):**
- Delete requires a confirmation step; canceling leaves the record untouched (same pattern as FR-15/FR-22).
- The confirmation copy states which behavior will occur (hard delete vs. archive) before the HR Admin confirms, based on whether Assignment history exists — this is not a silent, uncommunicated branch.
- The zero-Assignment-history check and the delete/archive action execute as a single atomic operation, not a check-then-act sequence — a concurrent Assignment creation for the same Employee (§4.1/FR-1) cannot race past this check and leave an Assignment pointing at a hard-deleted Employee (mirrors FR-7's existing "correctness under concurrency is a stated requirement" discipline).
- An archived Employee's login is deactivated immediately, enforced **server-side on every subsequent protected request, not only at new-login time** — `[DECISION, ADDED 2026-09-11, post-review]` an already-issued, unexpired session for that Employee also loses access immediately once archived, not just future login attempts. This requires the session-validation path (§4.5/FR-13) to check the identity's active/archived status per request, not signature validity alone — the same principle FR-13 already states for "no data reachable without a valid session," extended here to "an archived identity's session stops being valid."
- No restore path exists in the product UI for a hard delete. `[ASSUMPTION]` An archived record can be un-archived by an HR Admin — revisit if un-archive proves unnecessary in practice. `[NOTE FOR PM, ADDED 2026-09-11]` Un-archiving does not by itself restore a usable login — see FR-28.

#### FR-28: HR Admin regenerates an Employee's password

`[ADDED 2026-09-11, post-review — closes a critical gap found by the PRD Reviewer Gate: no password recovery/change path existed anywhere in §4.7]` HR Admin can generate a new password for an existing, active (non-archived) Employee at any time — covering a lost/forgotten password, a suspected compromise, an HR Admin who failed to record the one-time password shown at creation (FR-24), or reactivating a previously-archived Employee (FR-27) whose old password may no longer be known to anyone.

**Consequences (testable):**
- Regenerating immediately invalidates the previous password — the old password no longer authenticates once a new one is generated.
- The new password is shown once, in the same write-once/server-side one-time-reveal pattern as FR-24, and shared out-of-band by the HR Admin (same no-email-infrastructure constraint, §9).
- Available for any active (non-archived) Employee regardless of Assignment history — this is a credential operation, not a profile edit, and is not subject to FR-26's field-edit scope (Employee ID/Code and password are both excluded from "all fields from FR-24" in FR-26).
- `[NOTE FOR PM]` This FR does not add a self-service "forgot password" flow reachable by the Employee directly — regeneration is always HR Admin-initiated. No forced password-change-on-first-login exists either; an HR Admin retains knowledge of whatever password they most recently generated/shared, unless the Employee has some other way to change it themselves (no such FR exists in v1). Flagged as an accepted trust tradeoff, not silently ignored — this sits in tension with SM-C2's anti-surveillance intent and is worth revisiting if pilot feedback surfaces real concern.

### 4.8 HR Admin Navigation Shell

`[ADDED 2026-09-11 via bmad-prd update — new capability, not in original PRD scope]`

**Description:** The HR Admin application's primary navigation (currently a horizontal bar in the page header, linking Dashboard and Skills) moves to a persistent left-side vertical pane, gaining a new Employees entry for the roster (§4.7). Scoped to the HR Admin shell only — the Employee-facing Content Discovery experience is unchanged. `[UPDATED 2026-09-12 via bmad-prd update]` A fourth entry, **Skill Assignments**, is added by §4.10: `Dashboard` now opens the new Skill Assignment Dashboard landing page (§4.10/FR-31/32) instead of the full row grid directly; the grid itself (§4.4/FR-8-12, previously reached directly from `Dashboard`) becomes its own permanent nav destination, **Skill Assignments**, rather than a link/button surfaced only from within the landing page.

**Functional Requirements:**

#### FR-29: HR Admin's primary navigation is presented in a left-side pane

The HR Admin shell presents Dashboard, Skill Assignments, Skills, and Employees as a vertical navigation list in a left-side pane, persistent across all HR Admin pages, instead of the current top-header horizontal links. `[UPDATED 2026-09-12]` Four entries, not three — see description above.

**Consequences (testable):**
- The left pane is present and shows the same four entries on every HR Admin page (Dashboard, Skill Assignments, Skills, Employees) — never a page-specific subset.
- The current page is visually indicated in the pane (matches the existing top-nav's active-link treatment, relocated rather than redesigned).
- All four destinations remain reachable in one click from any HR Admin page, same as today's top nav — this is a layout change, not a reduction in what's reachable.
- The existing user-menu (avatar + Sign Out, currently top-right of the header) keeps its current position and behavior — only the Dashboard/Skills/Skill Assignments/Employees navigation links relocate, not the whole header.
- `[ADDED 2026-09-12]` `Dashboard` and `Skill Assignments` are two distinct, separately-reachable nav destinations, not one page with an internal link to the other (superseding FR-33's originally-drafted `[+ View All Assignments]` in-page control, now handled via nav instead — see §4.10/FR-33).
- `[ADDED 2026-09-11, post-review]` The relocation preserves every entry point currently reachable from the top header — including the Skills tab's API-key/credential settings surface (§4.6/FR-16) — with no functionality silently dropped during the header-to-left-pane refactor. `[NOTE FOR PM]` Whether `SkillsPage.tsx` currently duplicates `Dashboard.tsx`'s top-nav (and therefore needs the identical treatment for this consequence to hold everywhere) is unconfirmed — verify before build.

**Notes:** `[NOTE FOR PM]` No UX scenario or prototype covers this layout; downstream UX work needs to spec the pane's width, responsive/collapsed behavior on narrow viewports, and icon treatment (if any) before build. `[ADDED 2026-09-11]` Keyboard/ARIA behavior for the pane is expected to fall under the existing blanket WCAG 2.1 AA commitment (§8) rather than needing a separate accessibility statement here.

### 4.9 Application Theming (Light/Dark Mode)

`[ADDED 2026-09-11 via bmad-prd update — new capability, not in original PRD scope]`

**Description:** The application supports both a light and a dark visual theme, switchable by the user, across both the HR Admin and Employee-facing shells (a general appearance preference, not role-specific). `[ASSUMPTION]` Scope inferred as app-wide rather than HR-only, since a theme preference is a personal display choice with no HR-vs-Employee product-logic distinction, unlike §4.8's nav change (which is genuinely HR-shell-specific). Revisit if only one shell was actually intended.

**Functional Requirements:**

#### FR-30: User switches between Light and Dark theme

Either role (HR Admin or Employee) can switch the application's visual theme between Light and Dark via a persistent, easy-to-find control.

**Consequences (testable):**
- On first visit, the theme defaults to the user's OS/browser-level preference (`prefers-color-scheme`) if available; otherwise Light. `[ASSUMPTION]` Not a product requirement sourced from any prior UJ/research — a reasonable default, revisit if a fixed default is preferred instead.
- Once a user manually picks a theme, that choice persists across sessions on that browser (stored client-side, e.g. `localStorage`) and overrides the OS-preference default until changed again. `[ASSUMPTION]` Persistence is per-browser/per-device, not synced server-side to the account — no backend change required, consistent with the zero-budget/local-only constraint (§9). Revisit if HR/Employees need their theme choice to follow them across devices.
- Every screen in both shells (Dashboard, Skills, Employees, Content Discovery, login) renders correctly in both themes — this is a full-application commitment, not a partial/best-effort skin on select pages.
- Status badges and Provenance Labels (§4.4, FR-8/FR-9) remain WCAG 2.1 AA-compliant (non-color-only, sufficient contrast) in both themes — the existing accessibility NFR (§8) applies identically regardless of theme.
- Switching theme takes effect immediately, with no page reload required.

**Notes:** `[NOTE FOR PM]` No UX scenario, prototype, or prior design work covers this — downstream UX work needs to design both palettes (not just invert one) and confirm the toggle's placement (likely alongside the user-menu, §4.8) before build. No Success Metric applies — this is a UI preference, not an outcome-bearing capability, consistent with §4.7/§4.8 also carrying no new SM.

### 4.10 Skill Assignment Dashboard — HR Landing Page

`[ADDED 2026-09-12 via bmad-prd update — new capability, not in original PRD scope]`

**Description:** The HR Admin's `Dashboard` nav entry (§4.8/FR-29) now opens on a new org-wide aggregate view — the Skill Assignment Dashboard — instead of opening directly on the full Readiness Dashboard row grid (§4.4). This is additive, not a replacement: `[UPDATED 2026-09-12, post-clarification]` the full grid (FR-8/9/10) still exists in full and gains its own permanent left-nav entry, **Skill Assignments** (§4.8/FR-29), reachable in one click same as `Dashboard` — not a link nested inside the new landing page — preserving UJ-1 exactly as already validated. The new landing page answers "how's the org doing overall, and who needs my attention" at a glance, before Rita drops into row-level detail via the `Skill Assignments` nav entry. `[DECISION, 2026-09-12]` Confirmed with the user: this is a new, separate view sitting alongside the existing per-Assignment grid (not a redesign of it); it is HR Admin-only, consistent with this product's existing role scoping (FR-14); and it introduces no new tracked data — every number on it is derived from Assignment/Skill/Watch-Progress data FR-1 through FR-12 already define. Realizes an extension of UJ-1 (a faster, org-wide first read before Rita's existing staffing-call flow).

**Functional Requirements:**

#### FR-31: HR Admin views org-wide assignment stats on the landing page

The Skill Assignment Dashboard shows, above the fold: Total Employees (active/non-archived roster count, §4.7/FR-25), Total Skills/Videos Assigned (count of active, non-soft-deleted Assignments, §4.1/FR-1, §4.1/FR-15), and Total Completed (count of those Assignments currently at Status `Completed`, §4.4/FR-8).

**Consequences (testable):**
- All three counts exclude archived Employees (§4.7/FR-27) and soft-deleted Assignments (§4.1/FR-15) — this mirrors the existing "archived/soft-deleted records drop out of active views" rule already established for the Employee roster (FR-25) and Content Discovery (FR-4), applied here for the first time at an org-wide aggregate level.
- `[ASSUMPTION, 2026-09-12]` "Total Skills/Videos Assigned" counts every active Assignment regardless of whether it has attached Content (§4.1/FR-2 already allows assigning without Content) — it is an Assignment count, not a strictly video-content count. Revisit if HR wants this scoped only to Assignments with video Content attached.
- These counts refresh whenever the landing page loads; no specific real-time-update NFR is claimed here (unlike FR-11's 30-second row-update guarantee) — `[NOTE FOR PM]` revisit if HR needs this page to auto-refresh while left open, the way individual dashboard rows already do.

#### FR-32: HR Admin views an Assignment Progress breakdown and Employee Segmentation pie chart

Below the stats (FR-31), the landing page shows two more views: (a) an Assignment Progress breakdown — Completed / In Progress / Not Started counts (per-Assignment Status, §4.4/FR-8) plus an Overall Progress % shown as a completion ring; and (b) a pie chart segmenting every active Employee with at least one active Assignment into exactly three buckets: **On Track**, **In Progress**, **Needs Attention**.

**Consequences (testable):**
- Overall Progress % = `Total Completed (FR-31) / Total Skills/Videos Assigned (FR-31) × 100`, rounded to the nearest whole percent.
- Employee Segmentation, computed per Employee across all their active Assignments, in this priority order — `[ASSUMPTION, 2026-09-12, needs validation — see Open Question 20]`:
  1. **Needs Attention** — the Employee has at least one Assignment whose Provenance Label is currently `Needs Attention` (§4.4/FR-10's existing 7-day staleness rule). Takes priority over the other two buckets regardless of overall completion.
  2. **On Track** — no `Needs Attention` Assignments, and the Employee's own completion rate (their Completed Assignments ÷ their total active Assignments) is at or above **80%** `[ASSUMPTION — exact threshold not yet confirmed by the user, see Open Question 20]`.
  3. **In Progress** — everything else: no `Needs Attention` flags, but completion rate below the On-Track threshold. `[NOTE FOR PM]` This bucket is a catch-all by construction — it also holds Employees who haven't started anything yet (0% complete, all Assignments `Not Started`), since the pie chart's spec names only these three buckets, with no separate "Not Started" segment. Confirm this reads correctly to HR before build, or consider a 4th segment.
- An Employee with zero active Assignments is excluded from the pie chart entirely (nothing to segment) — does not silently count toward any of the three buckets.
- Same non-color-only accessibility rule as every other Status/Provenance surface in this PRD (§8): each pie segment and the progress ring are labeled with text/count, not color alone.
- Clicking a pie segment shows the list of Employees in that bucket (each one a click-through into their own Skill Progress drill-down, FR-33) — `[NOTE FOR PM]` exact interaction (inline expand vs. a filtered list view) is a UX-design decision, not specified here.

**Out of Scope:**
- Any drill-down "why" explanation beyond what FR-9's existing per-Assignment drill-down already provides — Employee Segmentation is a landing-page summary, not a new audit surface.

#### FR-33: HR Admin reaches the full grid via its own nav entry, or a single Employee's Skill Progress via drill-down from the landing page

`[UPDATED 2026-09-12, post-clarification]` The full Readiness Dashboard row grid is reachable two ways: (a) directly, via the left-pane's own **Skill Assignments** nav entry (§4.8/FR-29) — not an in-page link on the landing page — or (b) scoped to a single Employee, by clicking that Employee from a Skill Assignment Dashboard pie-chart segment (FR-32).

**Consequences (testable):**
- Path (a) renders exactly the existing FR-8/9/10/11/12 experience, unfiltered, as its own persistent nav destination — this consequence exists specifically so UJ-1's already-validated "scan 15-20 rows" flow keeps working unchanged, just relocated to its own nav entry instead of being the `Dashboard` entry's direct target.
- Path (b) renders the same FR-8/9/10 row/badge/drill-down model, pre-filtered to the selected Employee's Assignments only — not a different visual model, just a different scope, and reached from the landing page rather than the nav.
- Both paths remain gated by the existing HR-Admin-only role scoping (§4.5/FR-14) — no new access-control surface is introduced.

**Notes:** `[NOTE FOR PM]` No UX scenario or prototype covers this landing page's layout, chart treatment, or the pie-segment click-through interaction — downstream UX work needs to design all of §4.10 from scratch, consistent with this PRD's existing pattern for other request-driven additions (FR-12, FR-20, FR-24).

## 5. Non-Goals (Explicit)

- **Not an LMS or LXP.** No course catalog browsing, no learning paths, no certifications. It is an assignment-and-tracking dashboard, deliberately narrow.
- **Not a skill-gap inference engine.** The system never decides what an Employee should learn — HR assigns explicitly, always.
- **Not a performance-evaluation input.** Auto-captured Watch Progress is coaching-only by design (see §9 Constraints and Guardrails) — this is a hard boundary, not a phase-1 simplification to relax later without a deliberate policy change.
- **Not tracking non-video content progress.** Documents and websites are recommended but not progress-verified in v1 — they remain self-reported, and visibly labeled as such rather than silently blended with verified data. `[NOTE FOR PM]` No FR in this PRD provides an in-product entry mechanism for that self-reported status — it either continues via whatever process (e.g., the legacy spreadsheet) HR already uses outside this product, or the cell shows blank/"Unknown" rather than a guess. A blank cell is the intended behavior for an untracked signal, not a bug (same principle as FR-3's "no match beats a bad match").
- **Not a manager-facing tool.** No manager/team-lead role or view (§2.2).
- **Not a content-approval workflow.** AI-recommended content reaches Employees without a human QA gate in v1 — an accepted risk, not an oversight (§9).
- **Not a commercial product.** Internal pilot for SAILS Software's own HR function; no unit economics, no external customer, no pricing model.
- **An Employee can never view another Employee's assignments or Content Discovery list.** The underlying data model has latent support for employee-switching (built for cross-scenario prototype/demo reuse, not an end-user feature) — no UI may ever expose it (see Open Question 12).

## 6. MVP Scope

### 6.1 In Scope

- HR Skill Assignment Flow (FR-1, FR-2, FR-15)
- AI-Assisted Content Discovery, video/doc/website recommendations (FR-3, FR-4)
- Automatic Video Progress Capture & Resume, bundled as one mechanic (FR-5, FR-6, FR-7)
- Readiness Dashboard — Status badges at a glance, Provenance Label + Needs Attention on drill-down, HR manual override (FR-8, FR-9, FR-10, FR-11, FR-12)
- Authentication & Session Gate — login required for all Assignment/Content/Watch Progress access, role-scoped sessions (FR-13, FR-14)
- Admin-Assisted Content Sourcing — API key/credential management, Skill create/edit/delete (locked once assigned) flowing directly into content-sourcing, live YouTube/Udemy skill-link lookup or manual entry, review-and-attach to a Skill, reject the currently approved link, estimated days-to-complete (FR-16, FR-17, FR-17a, FR-18, FR-19, FR-20, FR-21, FR-22, FR-23)
- Employee Roster Management — HR Admin CRUD on Employee records (create/view/edit/delete-or-archive/regenerate-password), roster becomes the Employee login-provisioning source (FR-24, FR-25, FR-26, FR-27, FR-28)
- HR Admin Navigation Shell — primary navigation relocated to a left-side pane, four entries (Dashboard, Skill Assignments, Skills, Employees) (FR-29)
- Application Theming — Light/Dark mode, app-wide (FR-30)
- Skill Assignment Dashboard — HR Admin landing page: org-wide stats, Assignment Progress ring, Employee Segmentation pie chart, drill-down into the full grid or a single Employee (FR-31, FR-32, FR-33)

### 6.2 Out of Scope for MVP

- **Automated skill-gap-to-project matching** — HR makes this judgment manually via the dashboard; an earlier "coach" concept that infers gaps was explicitly shelved.
- **Progress tracking for documents/websites** — recommended, not verified. `[NOTE FOR PM]` This is the dashboard's known residual trust gap even post-launch — sub-skills and non-video status stay self-report-dependent. Candidate v2: Proxy-Signal Tracking. (The related manual-override safety net shipped in MVP as FR-12, not deferred — see §4.4.)
- **Post-completion content recommendations.**
- **"Your Week in Learning" recap, streaks/badges** — no confirmed pain point behind these; deferred to Phase 3/4 if ever.
- **Employee Profile View** — deferred out of pilot scope during prototype validation. `[NOTE FOR PM, ADDED 2026-09-11]` Distinct from §4.7's Employee Roster Management: this item refers to an Employee viewing/editing their *own* profile (still deferred); §4.7 is HR Admin managing the roster on Employees' behalf, and is in MVP scope.
- **Content-approval/QA gate** — accepted risk for v1 (§5, §8).
- **Manager/Team-Lead role and view.**
- **Dedicated "Needs Attention" filter control** — considered (named in early feature scoring as a target replacement for full-grid scanning) and explicitly not added; FR-9's per-row drill-down plus FR-10's visual flagging is the MVP interaction model instead.
- **Fast-follow, not MVP:** proactive resume nudges ("you paused 3 days ago, 8 min left") and transcript-level semantic search (jump to timestamp via natural-language query). Named as "Should"-priority in early scoping — real candidates for the first post-launch iteration, not this build.
- **"View alternatives"** — a link surfaced in the prototype's video-error state, implying an ability to browse alternative Content for a Skill instead of the one auto-recommended. Not built, not specified — a hinted future FR, not an MVP commitment.

## 7. Success Metrics

**Primary**
- **SM-1**: Self-reported-status staleness rate for video Assignments drops below **5%** within 60 days of launch (by **2026-09-11**). Validates FR-5, FR-11.

**Secondary**
- **SM-2**: HR Admin uses the dashboard as their primary reference for readiness decisions — not the prior spreadsheet — by the 60-day checkpoint. Measured via usage analytics and direct stakeholder feedback, not self-report. Validates FR-8, FR-9.
- **SM-3**: 100% of video Assignments show auto-captured Watch Progress at launch (zero manual employee entry required). Validates FR-5.
- **SM-4**: Skill Assignment Flow completes in under 2 minutes, HR Admin's own workflow. Validates FR-1.
- **SM-5**: Employee video completion rate and Continue-Watching (resume) feature usage — adoption signals that content discovery is surfacing relevant material and resume genuinely reduces friction. Directional, not numerically targeted — this is a greenfield product with no pre-launch baseline to set a target against; establish one from the first 30 days of real usage. Validates FR-3, FR-4, FR-6.

**Counter-metrics (do not optimize)**
- **SM-C1**: HR Admin continuing to privately cross-reference the old spreadsheet or personal memory after go-live is a red flag even if SM-1's backend number looks good — the hypothesis is proven by observed behavior change, not by the metric alone. Counterbalances SM-1, SM-2.
- **SM-C2**: Employee sentiment around being "watched" should not rise. The coaching-only guarantee (§ Constraints and Guardrails) must hold in practice, not just numerically — a technically-accurate dashboard that makes Employees feel surveilled is a failure mode, not a success. Counterbalances SM-3.

## 8. Cross-Cutting NFRs

- **Latency:** Readiness Dashboard loads in under 2 seconds; content/video player loads in under 3 seconds; a new Assignment appears on the dashboard within 1 second of confirm; video resume starts within 1 second of clicking Continue Watching; dashboard rows reflect a new watch-position update within 30 seconds without manual refresh (FR-11). `[ADDED 2026-09-12]` The Skill Assignment Dashboard landing page (§4.10, FR-31/32) targets the same under-2-second load budget as the Readiness Dashboard.
- **Data integrity:** watch-progress writes are ordered by event timestamp, never by position value, so a stale out-of-order write can't overwrite a newer one while a legitimate rewind still applies correctly (FR-7). Assignment creation must not be lost by a failed dashboard refresh (FR-1), and a canceled assignment flow leaves no orphaned record (FR-1).
- **Write integrity (anti-spoofing):** Watch Progress updates are validated server-side before being persisted or reflected as Verified — position must advance at a rate consistent with real playback (not instantaneous jumps to 100%), and updates require a valid authenticated session tied to the actual Assignment. The Verified label is only as trustworthy as this validation; it is the product's core differentiator versus self-reported data, so it can't rest on client-reported values alone.
- **Coaching-only enforcement:** raw Watch Progress and its drill-down history (FR-9) are not exposed through any interface, export, or report shaped for performance review — access is scoped to the Readiness Dashboard's stated coaching use, enforced at the data-access layer per §9.
- **Reliability of capture:** watch position flushes on tab close / visibility change via `sendBeacon`, not solely on the next poll interval (FR-5).
- **Accessibility:** WCAG 2.1 AA. Status badges and Provenance Labels are never color-only (FR-8, FR-9). The full assignment and dashboard drill-down flows are keyboard-operable end to end, and dynamic updates (the FR-1 success toast, live row updates) are announced to screen readers, not just visually rendered.
- **Platform:** responsive web, desktop-first. No offline mode, no native app, no PWA in v1.
- **Secret storage:** `[ADDED 2026-09-08]` Per-Admin content-source API keys (FR-16) are encrypted at rest, never logged, and never returned to any client in plaintext after initial submission — write-only via the UI, matching the JWT/cookie session's existing "not inspectable from client-side script" bar (§4.5, FR-13).
- **Employee credential provisioning:** `[ADDED 2026-09-11]` No email-sending infrastructure exists in this zero-budget stack — a new Employee's initial password is system-generated and shown once to the HR Admin in-product for out-of-band sharing (§4.7, FR-24), the same constraint-driven, no-new-infra pattern already accepted for the Udemy/YouTube credential handling above.
- **Live-lookup resilience:** `[ADDED 2026-09-08]` A single source's failure (invalid key, source API error, rate limit) during a live lookup (FR-17) never blocks results from another configured source, and is surfaced as a distinct, source-specific error rather than a generic failure (mirrors the existing per-card/per-source empty-and-error-state pattern in FR-4).

## 9. Constraints and Guardrails

- **Privacy (coaching-only boundary):** Auto-captured Watch Progress must never be usable as input to performance evaluations. This must be enforced structurally at the data-access/service layer — not merely a UI-copy or documentation commitment. This was flagged as a launch-blocking requirement during PRFAQ stress-testing and is treated as such here.
- **Cost:** Zero budget. No new paid infrastructure, no paid video-hosting tier.
- **Content ingestion quota:** The video-source API's daily search quota caps content-catalog ingestion to a scheduled batch job — see FR-3/FR-4 feature-specific NFR. This is a hard external constraint, not a design choice. `[RESOLVED 2026-09-08, architecture spine update]` FR-16–FR-18's live, per-request lookup is scoped around this constraint via an explicit AD-7 carve-out — it runs against each Admin's own key, never the shared batch key — see Open Question 13.
- **Udemy — in scope via an existing subscription:** `[ADDED 2026-09-08]` Udemy's free self-serve Affiliate API was discontinued 2025-01-01; the remaining Udemy APIs require a paid Udemy for Business subscription. SAILS already holds this subscription (confirmed by TalentPilot, 2026-09-08) — an **existing** cost, not new paid infrastructure, so this constraint's "no new paid infra" framing isn't violated. The credential is organization-wide (one client ID/secret for the whole account), unlike YouTube's free per-Admin personal key — see FR-16, Open Question 14.
- **Content quality:** No human-approval gate exists for AI-surfaced content in v1 (§5). Externally-sourced video content carries no inherent quality guarantee. Accepted risk, revisit if pilot feedback surfaces real quality problems.
- **No data migration.** The dashboard launches clean on 2026-07-13. Historical spreadsheet data does not import.
- **Tone of voice:** HR-facing surfaces (dashboard, drill-down) stay factual and calm — no encouragement copy, no color-only signaling (FR-8). Employee-facing surfaces (content discovery, resume) carry warmth and encouragement. This split is deliberate and locked; full tone framework and copy examples live in the Product Brief (`A-Product-Brief/project-brief.md`), not duplicated here.

## 10. Why Now

The corporate skills-tracking / LMS-LXP category has been consolidating since 2022 — LMS vendors adding discovery features, LXP vendors adding compliance features — meaning the boundary between "assignment-driven tracking" and "broad learning platform" is closing, not fixed. No reviewed competitor (heavyweight talent-intelligence suites, LMS/LXP incumbents, or newer AI gap-analysis tools) combines this product's specific wedge: HR-assignment-first workflow, fully automatic video-progress capture, and a consumer-grade resume experience, in one narrow, fast-to-deploy tool. That positioning gap is real today and time-limited. Independent research reinforces the timing: 87% of CHROs expect greater AI adoption in HR through 2026, and the World Economic Forum projects 6 in 10 employees will need upskilling by 2027 — the demand curve is already rising, not speculative. Full competitive detail lives in `addendum.md` and the underlying market research report.

## 11. Open Questions

1. **Data retention period for auto-captured Watch Progress is not defined.** No default was ever locked (a 90-day inactivity default was floated in early strategy work but never adopted). Deferred — does not block MVP build; revisit before any scope expansion beyond internal pilot.
2. **Legal/compliance review of employee video-watch tracking has not happened**, and was consciously declined as unnecessary for the current internal-pilot, coaching-only scope. Revisit if scope expands (more departments, external customers, or if the coaching-only data policy ever changes).
3. **No named post-pilot owner or committed team/timeline exists.** Three viable post-pilot paths are already named (stay standalone / feed a future LMS / get adopted into a commercial platform) — the open part isn't *whether* a path exists, it's that nobody has committed to *which one*, or to an owner and timeline for ongoing maintenance, content-quality judgment calls, or metric monitoring after launch. Must be resolved before the Pilot & Validation phase begins — not before the 2026-07-13 build/launch date.
4. **The non-video trust gap is a known, accepted residual risk**, not a solved problem: sub-skills and non-video status fields remain self-reported indefinitely post-launch. Proxy-Signal Tracking and an "Assessed Live" manual-override audit flag are v2 candidates, not commitments.
5. **HRIS integration (e.g., Workday, BambooHR) appears in early strategic framing but nowhere in the product-definition or prototype artifacts.** Unresolved scope gap between the strategic document and everything downstream of it — treat as not-in-MVP unless explicitly revisited.
6. **The root-cause hypothesis itself is unvalidated.** Whether HR's relationship to the old spreadsheet was genuinely "resigned" (fixable) versus "tolerant" (a deeper behavioral pattern the product won't change) has never been tested with a real HR Admin. Validation is deferred to post-launch telemetry (SM-1, SM-2) rather than pre-launch research — a deliberate choice, not an oversight.
7. **Deployment/hosting target is undecided.** The technical research explicitly deferred this. Given the hard 2026-07-13 launch date, this is a real risk to the date holding, not just a remaining implementation nicety — flagging it here so it doesn't fall through as "someone else's problem." Compounds with #9 below: two of this PRD's newest FRs (FR-12 and the overall timeline) have no implementation head start.
8. **Provenance-label comprehension has not been usability-tested.** The PRFAQ named this as one of the two structural cracks in an otherwise-forged concept: whether HR Admins actually read and correctly interpret the Verified / Self-reported / Needs Attention / HR Override distinction (rather than skimming past it) is untested. Recommend a lightweight comprehension check before or immediately after launch, not deferred indefinitely.
9. **Authentication is now scoped (FR-13, FR-14, added 2026-07-09) — but two sub-questions remain genuinely open.** The access-gate and session-scoping behavior is defined and was validated end-to-end at the prototype level (`wds-8-product-evolution`, see `_bmad-output/evolution/`), which confirmed the login → role-routing → own-data-only UX pattern works. Still undefined, and not answered by the prototype's mock credential store: (a) where HR Admin and Employee accounts come from in production — locally provisioned by HR, or company SSO — and (b) where the Employee roster/identity data originates. Needs an answer before FR-1 (which depends on selecting a known Employee) can be built against a real roster rather than a hand-seeded demo list. `[UPDATED 2026-09-11 via bmad-prd update]` Sub-question (b) is now **RESOLVED**: the Employee roster/identity data originates from HR Admin's own Employee CRUD (§4.7, FR-24–27), replacing the hand-seeded demo list. Sub-question (a) is **partially resolved for Employee accounts specifically**: they are locally provisioned by HR Admin (FR-24), with a system-generated initial password shared out-of-band — not SSO. Still open: how HR_ADMIN accounts themselves get provisioned (§4.7's FR-24 explicitly creates EMPLOYEE-role accounts only, not additional HR_ADMIN accounts). `[STRENGTHENED 2026-09-11, post-review]` This is not a someday-if-needed concern — a working HR_ADMIN account is required from day one for §4.7 itself to be usable, and it currently still runs on the pre-existing mock credential store (`auth/repository.py`, plaintext dict), completely untouched by this feature. That store is also a single point of failure with no stated rotation/recovery path of its own. Revisit before launch, not just if a second HR Admin is ever needed, or if company SSO is later adopted for either role.
10. **No fallback is defined for Content that becomes unavailable after assignment.** Recommended videos/documents/websites are externally hosted and can be taken down or moved at any time after an Assignment already points to them (FR-2, FR-4). Reviewer-surfaced gap, not addressed in any source artifact.
11. **The Status/Provenance split (FR-8, FR-9, FR-10) may reintroduce the trust-ambiguity problem this product exists to solve.** A Status badge computed purely from Watch Progress percentage doesn't distinguish Verified from Self-reported data at the row level — that distinction now lives one click away in the drill-down. This works only if HR Admins reliably use the drill-down before trusting a badge at face value, which is unproven (compounds with Open Question 8's untested label comprehension) and structurally undercuts the original design target of spotting flagged rows without clicking into each one (Business Goals Objective 3). Needs a real decision: accept the risk as-is, add a secondary at-a-glance cue for Needs Attention/stale rows specifically, or reconsider the pivot.
12. **The Content Discovery data model already supports one Employee viewing another Employee's assignments** (`getEmployees`/`setSelectedEmployee` in the prototype's API layer, built for cross-scenario data reuse) — no UI currently exposes this, but wiring it up would take minimal effort. This is a latent privacy/scope risk, not a built feature; treated as a hard Non-Goal (§5) going forward, but worth naming here so it isn't accidentally exposed in a future iteration.
13. **`[ADDED 2026-09-08, RESOLVED 2026-09-08 via architecture spine update]` FR-16–FR-18's live, per-request content lookup vs. the locked batch-only architecture.** AD-7 (architecture spine) and this PRD's own FR-3/FR-4 feature-specific NFR state content ingestion is batch-only, never live per-request search — a rule specific enough to be enforced by a regression test on the existing YouTube batch job (Story 2.3, done). **Resolution:** AD-7 was amended (not replaced) with a narrow carve-out — a live per-request call is permitted only when triggered by an authenticated HR Admin, using that Admin's own individually-stored key (never the shared system key), writing to the catalog only on explicit review/attach. The regression test's intent was re-scoped to guard the shared key's usage specifically, rather than forbidding the search function outright. Full detail: `ARCHITECTURE-SPINE.md` AD-7 (amended) and AD-10 (new).
14. **`[ADDED 2026-09-08 — dropped, reopened, and fully RESOLVED, all the same day]` Udemy as a content source.** Architecture-stage web research found Udemy's free Affiliate API discontinued 2025-01-01, requiring a paid Udemy for Business subscription instead — briefly dropped from v1 for that reason, then restored once SAILS confirmed it already holds that subscription (existing cost, not new spend). A second research pass then found Udemy for Business issues credentials **per organization** (one client ID/secret for the whole account), unlike YouTube's per-individual key — a real difference from the per-Admin model FR-16 was first written around. **Resolution (architecture spine, same day):** AD-7 extended with a third branch symmetric to the YouTube one — a live, HR_ADMIN-gated Udemy lookup is permitted using the org-wide credential, rate-limit failures surfaced via the source's own signal (no local counter, same principle as the YouTube batch job). AD-10 extended with a second table, `org_api_credentials` (one row per org-wide source, attributed to whoever last configured it — "connected by {Admin name}," not personal ownership), kept separate from `admin_api_keys` rather than overloading one table's uniqueness constraint with two ownership models. Full detail: `ARCHITECTURE-SPINE.md` AD-7 (branch 3) and AD-10.
15. **`[ADDED 2026-09-08, RESOLVED 2026-09-08 via architecture spine update]` API key at-rest storage mechanism.** **Resolution:** Fernet symmetric encryption (`cryptography` library), keyed by a new secret dedicated to this purpose (separate from the JWT signing secret) — zero new paid infrastructure, consistent with this PRD's zero-budget constraint. A KMS/envelope-encryption alternative was considered and rejected as disproportionate for a local-only pilot. Full detail: `ARCHITECTURE-SPINE.md` AD-10.
16. **`[ADDED 2026-09-08, RESOLVED 2026-09-08 via architecture spine update]` Skills has never had a proper owning module — FR-20/21/22 make that a real gap, not a theoretical one.** **Resolution:** new `skills/` module (architecture spine AD-11) becomes the sole owner of the `skills` table; the permanent edit/delete lock is a local `ever_assigned` boolean, set by `assignments/` the same way it already depends on `content/` for content lookup. Full detail: `ARCHITECTURE-SPINE.md` AD-11.
17. **`[ADDED 2026-09-11, via PRD Reviewer Gate]` The 5 already-shipped hardcoded demo employees (with live Assignment/Watch-Progress/Override history) have no defined migration path into §4.7's new Employee-CRUD-backed model.** §4.7 introduces a real schema (new columns, hashed passwords) as the roster's source of truth going forward, but doesn't say whether the existing demo employees (Rita, Casey, Morgan, Jordan, Sam) are migrated into the new shape (and with what password, since they never went through FR-24's generation flow), left running unmigrated alongside newly-created real employees, or something else. This collides with §9's "No data migration. The dashboard launches clean on 2026-07-13" constraint, which predates this update and was written for the original launch, not this one. Must be resolved before §4.7 is built.
18. **`[ADDED 2026-09-11, via PRD Reviewer Gate]` The existing `Account` model (`backend/app/auth/models.py`, table `accounts`, columns `id, email, password_hash, role, created_at`) is already seeded (`backend/app/core/seeds.py::create_default_accounts`) but not yet wired into `authenticate()`, which still reads the plaintext `_MOCK_ACCOUNTS` dict in `auth/repository.py`.** This looks like a half-finished migration path already sitting in the repo — directly relevant to how §4.7/FR-24's login provisioning (and the real password-hashing it requires) should be built: extend/adopt this existing `Account` model, or build something new. The architecture pass for §4.7 should reconcile with this existing scaffold rather than treating Employee credential storage as a green field. See `addendum.md`'s Employee Roster Management handoff notes.
19. **`[ADDED 2026-09-08]` An assigned Skill has no UI entry point into content-sourcing (FR-17/18/19/23) on the Skills tab, even though the FRs themselves state that capability is not gated by assignment status.** History: a "Find Content" button was added specifically to give assigned/locked Skills (which have no Edit control, FR-21/22's lock) a way to reach the lookup panel; removed the same day, from every card, per direct feedback, without a replacement named. `[UPDATED 2026-09-08]` **Confirmed at the architecture level (AD-11 point 5) that this is a UX gap, not a backend one** — the backend/API is deliberately built assignment-status-agnostic, so option (a) below would mean changing product intent, not just documenting an existing restriction. **Two ways to resolve, not decided here:** (a) narrow FR-17/18/19/23's stated scope to unassigned Skills only, formally matching what the UI now actually allows — the simpler, more consistent option, but changes the FRs' own wording (and would leave AD-11's assignment-agnostic backend over-built for what's actually needed); or (b) design a different entry point for assigned Skills (e.g., reachable from the Provenance Drill-Down modal, 01.2, alongside other per-Assignment detail, rather than the Skills tab's card grid). Revisit before FR-17/18/19/23 are built for the assigned-Skill case — not a launch-blocker for the unassigned-Skill path, which is unaffected.
20. **`[ADDED 2026-09-12]` The Employee Segmentation "On Track" completion-rate threshold (§4.10/FR-32) is a PM-drafted default (80%), not a value confirmed by the user or sourced from any prior research/design-thinking artifact** — unlike FR-10's 7-day staleness threshold, which traces back to an original design-thinking success-metric proposal. Revisit with the user (or a lightweight HR check-in) before this ships as a hard-coded constant; also unresolved: whether "In Progress" should stay a catch-all bucket that includes not-yet-started Employees, or whether the pie chart needs a 4th "Not Started" segment instead.

## 12. Assumptions Index

- §2.1 — "Resigned, not tolerant" characterization of HR's relationship to the current spreadsheet process is TalentPilot's own inference; no HR interviews were conducted. See Open Question 6.
- §4.1 — No content-approval step exists in MVP; confirmed twice this session — once against the prototype's "✓ Approved" badge (placeholder, not a spec), and again against the PRFAQ, which had committed to an approval checkpoint as a "required MVP feature." That PRFAQ commitment is knowingly superseded by this decision.
- §4.2 — Semantic/approximate matching (not exact-tag filtering) is required for Content Discovery to be useful — confirmed decision, not yet validated against real catalog content.
- §4.2/FR-4 — Content Discovery pivoted from a single-recommendation model to a multi-assignment list (Total/In Progress/To Start), confirmed this session after the prototype was found to have already made this change unrecorded. Not yet validated with a real Employee.
- §4.4/FR-8 — The dashboard's primary at-a-glance signal pivoted from Provenance Label to a completion-Status badge, with Provenance moved to drill-down, confirmed this session after the prototype was found to have already made this change unrecorded. Carries a real, unresolved coherence risk — see Open Question 11.
- §4.5/FR-13/FR-14 — Authentication's login → role-routing → own-data-only UX pattern was validated against a prototype-level mock gate (client-side, hardcoded demo accounts, no backend) via `wds-8-product-evolution` (2026-07-09, see `_bmad-output/evolution/`), then generalized into production FRs using the session mechanism (JWT / HTTP-only cookie) already locked in `addendum.md`. The mock credential store itself is not a production decision — see Open Question 9.
- §4.6/FR-16 — Each Admin's content-source API key(s) are personal to their own account, not shared/visible across Admins — inferred from the request's own "his api keys" framing, not independently confirmed. See Open Question 13 for the related, larger architecture question this feature raises.
- §4.6/FR-16 — Partial-source lookup (running FR-17 against whichever sources the Admin has a key for, rather than blocking until all are configured) is assumed as the more Admin-friendly default; not confirmed against a real workflow.
- §4.6/FR-18 — Content removal for an admin-attached link is assumed to follow the existing Assignment soft-delete pattern (FR-15) applied to Content rather than Assignments; not an independently confirmed decision.
- §4.6/FR-16 — Any HR Admin can view/update the single shared Udemy for Business credential (framed as "connected by {Admin name}," not personal like the YouTube key) — inferred from Udemy for Business issuing credentials per-organization, not per-user; not independently confirmed against a real multi-Admin workflow. See Open Question 14.
- §4.6/FR-22 — An unassigned Skill's deletion is a hard delete (row + its Content links actually removed), not a soft delete like FR-15's Assignment removal — reasoned from "zero Assignments exist by definition for a deletable Skill, so there's nothing to preserve," not independently confirmed.
- §4.7/FR-24 — Only Name, Email, and Employee ID/Code are required at Employee creation; the remaining profile fields (Phone, Experience, Technologies, Position, Project, Manager Name, Location, Department) are optional, on the assumption not all are realistically known at hire time. Not independently confirmed against a real HR workflow.
- §4.7/FR-26 — Editing an Employee's Email does not silently invalidate their existing session, even though Email is the login identity. Not independently confirmed; revisit if this proves confusing in practice.
- §4.7/FR-27 — A hard-deleted Employee record has no restore path, but an archived (soft-deleted) one can be un-archived by an HR Admin. Not independently confirmed against a real HR workflow.
- §4.7/FR-24 — A hard-deleted Employee's ID/Code and Email become reusable by a future hire; an archived Employee's do not, since the record still exists. Not independently confirmed against a real HR workflow.
- §4.7/FR-26 — Concurrent edits to the same Employee record use last-write-wins with no conflict detection, matching the lack of optimistic locking elsewhere in this PRD. Not independently confirmed to be acceptable at real pilot usage levels.
- §4.7/FR-26 — Manager Name is treated as an unmaintained free-text snapshot, not a live reference to the named manager's own Employee record. Reasoned from FR-24's field list (no Manager-ID/FK), not independently confirmed.
- §4.9/FR-30 — Theme scope is assumed app-wide (both HR Admin and Employee shells) and per-browser/per-device persistence (not synced to the account), since a display preference has no role-specific product logic and no backend change was requested. Not independently confirmed against a real workflow.
- §4.10/FR-31 — "Total Skills/Videos Assigned" counts every active Assignment regardless of attached-Content type, not strictly video-content Assignments. Not independently confirmed against what the user meant by "Skill Videos."
- §4.10/FR-32 — Employee Segmentation's "On Track" threshold (80% completion rate, no Needs Attention flags) is a PM-drafted default, not user-confirmed. See Open Question 20.
- §4.10/FR-32 — "In Progress" is a catch-all bucket also covering Employees who haven't started anything yet, since the user's spec named only 3 pie segments. See Open Question 20.
- §4.10/FR-32 — An Employee with zero active Assignments is excluded from the pie chart's denominator entirely, rather than being force-fit into one of the three buckets. Not independently confirmed against a real HR workflow.
