---
title: TalentPilot-AI
status: final
created: 2026-07-09
updated: 2026-07-09
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
  - **Entry state:** Authenticated, on the Assignment Dashboard.
  - **Path:** Scans 15–20 employee rows. Each row carries a Status badge at a glance (`Not Started`, `In Progress`, `Completed`). One row's percentage looks inconsistent with what she remembers — she clicks it to drill down.
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
- **Employee** — The secondary user role (persona: Casey). Receives skill assignments, consumes recommended content, generates watch-progress signal passively.
- **Skill** — A named competency HR can assign to an Employee (e.g., "Data Visualization"). Distinct from a **sub-skill**, a finer-grained status field that remains self-reported (out of MVP auto-capture scope).
- **Assignment** — A record linking one Employee to one Skill, created by an HR Admin. Carries a Status badge (Not Started → In Progress → Completed) and, one level down via drill-down, a Provenance Label.
- **Content** — A video, document, or website recommended for a given Skill. Only video content is auto-captured in MVP; document/website content is recommended but not progress-tracked.
- **Watch Progress** — The percentage of a video an Employee has watched, captured automatically from actual playback behavior, never typed in.
- **Status** — The primary at-a-glance completion badge shown on every dashboard row: **Not Started**, **In Progress**, or **Completed**, computed from Watch Progress percentage (0% / 1–99% / 100%). Answers "how far along," not "how much do I trust this" — that's the Provenance Label's job, one level down via drill-down (FR-9).
- **Provenance Label** — The trust indicator behind a row's Status, reached via drill-down (FR-9): **Verified** (auto-captured from video), **Self-reported** (employee-entered, non-video), **Needs Attention** (stale or inconsistent signal), or **HR Override** (manually confirmed ready by an HR Admin, independent of Watch Progress). Never color-only — always paired with text or icon (WCAG 2.1 AA).
- **HR Override** — A manual readiness confirmation by an HR Admin, used when Watch Progress or self-reported data doesn't reflect HR's actual confidence. Carries its own Provenance Label; never blended with or displayed as "Verified."
- **Needs Attention** — A dashboard state, not a separate page: a row whose self-reported data has gone stale beyond a defined freshness threshold. Surfaced via drill-down on the row itself, not a standalone filter view.
- **Readiness Dashboard** — The HR Admin's primary surface: one row per Employee×Skill assignment, each carrying a Status badge, with its Provenance Label one click away via drill-down.
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

#### FR-2: HR Admin sees AI-recommended Content during assignment

During the assignment flow, the system surfaces its matched Content recommendation for the selected Skill so the HR Admin can see what the Employee will be pointed to. Realizes UJ-3.

**Consequences (testable):**
- If no matching Content exists for a Skill, the flow allows the HR Admin to assign the Skill without Content, rather than blocking the assignment ("No approved content found yet for this skill. [Choose Different Content] or assign without content.").

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

- HR Skill Assignment Flow (FR-1, FR-2)
- AI-Assisted Content Discovery, video/doc/website recommendations (FR-3, FR-4)
- Automatic Video Progress Capture & Resume, bundled as one mechanic (FR-5, FR-6, FR-7)
- Readiness Dashboard — Status badges at a glance, Provenance Label + Needs Attention on drill-down, HR manual override (FR-8, FR-9, FR-10, FR-11, FR-12)

### 6.2 Out of Scope for MVP

- **Automated skill-gap-to-project matching** — HR makes this judgment manually via the dashboard; an earlier "coach" concept that infers gaps was explicitly shelved.
- **Progress tracking for documents/websites** — recommended, not verified. `[NOTE FOR PM]` This is the dashboard's known residual trust gap even post-launch — sub-skills and non-video status stay self-report-dependent. Candidate v2: Proxy-Signal Tracking. (The related manual-override safety net shipped in MVP as FR-12, not deferred — see §4.4.)
- **Post-completion content recommendations.**
- **"Your Week in Learning" recap, streaks/badges** — no confirmed pain point behind these; deferred to Phase 3/4 if ever.
- **Employee Profile View** — deferred out of pilot scope during prototype validation.
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

- **Latency:** Readiness Dashboard loads in under 2 seconds; content/video player loads in under 3 seconds; a new Assignment appears on the dashboard within 1 second of confirm; video resume starts within 1 second of clicking Continue Watching; dashboard rows reflect a new watch-position update within 30 seconds without manual refresh (FR-11).
- **Data integrity:** watch-progress writes are ordered by event timestamp, never by position value, so a stale out-of-order write can't overwrite a newer one while a legitimate rewind still applies correctly (FR-7). Assignment creation must not be lost by a failed dashboard refresh (FR-1), and a canceled assignment flow leaves no orphaned record (FR-1).
- **Write integrity (anti-spoofing):** Watch Progress updates are validated server-side before being persisted or reflected as Verified — position must advance at a rate consistent with real playback (not instantaneous jumps to 100%), and updates require a valid authenticated session tied to the actual Assignment. The Verified label is only as trustworthy as this validation; it is the product's core differentiator versus self-reported data, so it can't rest on client-reported values alone.
- **Coaching-only enforcement:** raw Watch Progress and its drill-down history (FR-9) are not exposed through any interface, export, or report shaped for performance review — access is scoped to the Readiness Dashboard's stated coaching use, enforced at the data-access layer per §9.
- **Reliability of capture:** watch position flushes on tab close / visibility change via `sendBeacon`, not solely on the next poll interval (FR-5).
- **Accessibility:** WCAG 2.1 AA. Status badges and Provenance Labels are never color-only (FR-8, FR-9). The full assignment and dashboard drill-down flows are keyboard-operable end to end, and dynamic updates (the FR-1 success toast, live row updates) are announced to screen readers, not just visually rendered.
- **Platform:** responsive web, desktop-first. No offline mode, no native app, no PWA in v1.

## 9. Constraints and Guardrails

- **Privacy (coaching-only boundary):** Auto-captured Watch Progress must never be usable as input to performance evaluations. This must be enforced structurally at the data-access/service layer — not merely a UI-copy or documentation commitment. This was flagged as a launch-blocking requirement during PRFAQ stress-testing and is treated as such here.
- **Cost:** Zero budget. No new paid infrastructure, no paid video-hosting tier.
- **Content ingestion quota:** The video-source API's daily search quota caps content-catalog ingestion to a scheduled batch job — see FR-3/FR-4 feature-specific NFR. This is a hard external constraint, not a design choice.
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
9. **Authentication and employee-roster provisioning has no FR in this PRD.** Every User Journey assumes an "Authenticated" entry state, but how HR Admins and Employees get accounts, and where the Employee roster/identity data comes from, is undefined anywhere in the source material. Reviewer-surfaced gap — needs an answer before FR-1 (which depends on selecting a known Employee) can be built.
10. **No fallback is defined for Content that becomes unavailable after assignment.** Recommended videos/documents/websites are externally hosted and can be taken down or moved at any time after an Assignment already points to them (FR-2, FR-4). Reviewer-surfaced gap, not addressed in any source artifact.
11. **The Status/Provenance split (FR-8, FR-9, FR-10) may reintroduce the trust-ambiguity problem this product exists to solve.** A Status badge computed purely from Watch Progress percentage doesn't distinguish Verified from Self-reported data at the row level — that distinction now lives one click away in the drill-down. This works only if HR Admins reliably use the drill-down before trusting a badge at face value, which is unproven (compounds with Open Question 8's untested label comprehension) and structurally undercuts the original design target of spotting flagged rows without clicking into each one (Business Goals Objective 3). Needs a real decision: accept the risk as-is, add a secondary at-a-glance cue for Needs Attention/stale rows specifically, or reconsider the pivot.
12. **The Content Discovery data model already supports one Employee viewing another Employee's assignments** (`getEmployees`/`setSelectedEmployee` in the prototype's API layer, built for cross-scenario data reuse) — no UI currently exposes this, but wiring it up would take minimal effort. This is a latent privacy/scope risk, not a built feature; treated as a hard Non-Goal (§5) going forward, but worth naming here so it isn't accidentally exposed in a future iteration.

## 12. Assumptions Index

- §2.1 — "Resigned, not tolerant" characterization of HR's relationship to the current spreadsheet process is TalentPilot's own inference; no HR interviews were conducted. See Open Question 6.
- §4.1 — No content-approval step exists in MVP; confirmed twice this session — once against the prototype's "✓ Approved" badge (placeholder, not a spec), and again against the PRFAQ, which had committed to an approval checkpoint as a "required MVP feature." That PRFAQ commitment is knowingly superseded by this decision.
- §4.2 — Semantic/approximate matching (not exact-tag filtering) is required for Content Discovery to be useful — confirmed decision, not yet validated against real catalog content.
- §4.2/FR-4 — Content Discovery pivoted from a single-recommendation model to a multi-assignment list (Total/In Progress/To Start), confirmed this session after the prototype was found to have already made this change unrecorded. Not yet validated with a real Employee.
- §4.4/FR-8 — The dashboard's primary at-a-glance signal pivoted from Provenance Label to a completion-Status badge, with Provenance moved to drill-down, confirmed this session after the prototype was found to have already made this change unrecorded. Carries a real, unresolved coherence risk — see Open Question 11.
