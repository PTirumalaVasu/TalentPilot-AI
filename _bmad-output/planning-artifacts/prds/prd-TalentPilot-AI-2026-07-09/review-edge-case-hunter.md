# Edge Case Hunter Review — TalentPilot-AI PRD

**Reviewed:** `prd.md` (full document), with `addendum.md` as supporting context.
**Method:** Exhaustive path enumeration per `bmad-review-edge-case-hunter` — every branching path and boundary condition implied by the 12 FRs, the Glossary's enumerated states, and the data-write semantics described in the addendum. Only unhandled paths are reported; paths the PRD already resolves (explicit Consequences, Out of Scope lines, Open Questions, `[NOTE FOR PM]` tags) are treated as handled/acknowledged and excluded, even where the resolution is "deferred."

## Findings (JSON)

```json
[
  {
    "location": "prd.md:85-93 (FR-1)",
    "trigger_condition": "HR Admin assigns a Skill already assigned to the same Employee",
    "guard_snippet": "Check for existing Assignment(employee, skill) before create; define block/merge/duplicate-allowed behavior",
    "potential_consequence": "Duplicate or conflicting rows for one employee+skill pair confuse the readiness dashboard"
  },
  {
    "location": "prd.md:85-93 (FR-1)",
    "trigger_condition": "Employee is deactivated/offboarded while holding open Assignments",
    "guard_snippet": "Define assignment lifecycle on employee deactivation (archive/hide rows, freeze capture)",
    "potential_consequence": "Dashboard keeps showing live, updating rows for people no longer employed"
  },
  {
    "location": "prd.md:95-101 (FR-2); prd.md:115-120 (FR-4)",
    "trigger_condition": "Recommended Content (esp. externally-hosted video) is deleted or made unavailable after an Assignment already references it",
    "guard_snippet": "Detect broken content reference at watch-time; surface explicit error + re-match path, not FR-5's 'video fails to load' generic case",
    "potential_consequence": "Employee opens an assignment to a dead link/removed video with no recommended recovery, HR sees a row stuck mid-signal"
  },
  {
    "location": "prd.md:115-120 (FR-4)",
    "trigger_condition": "A Skill has multiple equally-relevant Content items (video + doc + website) but FR-4 specifies a single recommended piece",
    "guard_snippet": "Define selection/priority rule for top-match ties (e.g., prefer video for auto-capture over doc/website)",
    "potential_consequence": "Which content the Employee sees becomes non-deterministic or implementation-defined"
  },
  {
    "location": "prd.md:147-152 (FR-7); addendum.md:12",
    "trigger_condition": "Employee intentionally rewinds and re-watches earlier video content, producing a lower position with a later wall-clock write",
    "guard_snippet": "Disambiguate legitimate rewind from stale out-of-order update (e.g., compare monotonic session/event sequence, not raw position vs timestamp alone)",
    "potential_consequence": "Legitimate rewind is either silently dropped or misreported as regression on the dashboard/resume point"
  },
  {
    "location": "prd.md:147-152 (FR-7)",
    "trigger_condition": "Client-supplied timestamp used for the conditional-write comparison is skewed or manipulated",
    "guard_snippet": "Use server-assigned timestamp for the newer-wins comparison, not a client-supplied value",
    "potential_consequence": "A clock-skewed or malicious client can freeze or falsify stored progress indefinitely"
  },
  {
    "location": "prd.md:138-145 (FR-6)",
    "trigger_condition": "Stored resume position is at or effectively at 100% of video duration",
    "guard_snippet": "Define a completed-state distinct from mid-watch resume (e.g., 'Watch again' instead of resuming at the final second)",
    "potential_consequence": "Employee resuming a finished video lands at the very end with nothing left, reading as broken"
  },
  {
    "location": "prd.md:138-145 (FR-6)",
    "trigger_condition": "Underlying video is replaced or shortened after a resume position was captured, so the stored position now exceeds the new duration",
    "guard_snippet": "Clamp resume position to current video duration, or fall back to the existing 'Start over' path when position > duration",
    "potential_consequence": "Seek-to-invalid-position error or stuck player on resume"
  },
  {
    "location": "prd.md:160-168 (FR-8); prd.md:184-189 (FR-11)",
    "trigger_condition": "A row is `Assigned · Awaiting first watch`, or assigned with no Content (FR-2's no-match path) — neither maps onto the four defined Provenance Labels (Verified/Self-reported/Needs Attention/HR Override)",
    "guard_snippet": "Explicitly classify pre-watch/no-content rows under one of the four labels, or define a fifth labeled state",
    "potential_consequence": "Newly-created rows have ambiguous or inconsistent labeling until the first signal arrives"
  },
  {
    "location": "prd.md:177-182 (FR-10)",
    "trigger_condition": "A Verified (video-based) row stops receiving new Watch Progress for an extended period (abandoned mid-watch)",
    "guard_snippet": "Extend the staleness check to Verified rows with no recent activity, not only self-reported rows",
    "potential_consequence": "A stalled video assignment never surfaces as Needs Attention and looks permanently healthy"
  },
  {
    "location": "prd.md:177-182 (FR-10)",
    "trigger_condition": "FR-10 requires flagging data stale 'beyond a defined threshold', but no concrete threshold value appears anywhere in prd.md or addendum.md",
    "guard_snippet": "State the concrete freshness threshold (e.g., N days) that FR-10 depends on",
    "potential_consequence": "Threshold is left to implementer guess, producing inconsistent Needs-Attention behavior across builds"
  },
  {
    "location": "prd.md:184-189 (FR-11)",
    "trigger_condition": "A watch-position update fails to propagate to the dashboard within the 30-second target (processing backlog or outage)",
    "guard_snippet": "Define degraded-mode/stale-indicator behavior for when the 30s SLA is missed",
    "potential_consequence": "HR Admin sees an out-of-date row with no signal it's behind, undermining trust in the 'Verified' label"
  },
  {
    "location": "prd.md:191-199 (FR-12)",
    "trigger_condition": "HR Admin wants to reverse or edit a previously-applied HR Override",
    "guard_snippet": "Add an explicit override-removal/edit path; FR-12 only specifies override creation",
    "potential_consequence": "An incorrect or outdated override can never be undone through the product"
  },
  {
    "location": "prd.md:191-199 (FR-12); prd.md:170-175 (FR-9)",
    "trigger_condition": "A row carries an active HR Override while newer, contradicting Watch Progress or self-reported data arrives",
    "guard_snippet": "Define precedence: does the override always win, or can fresh Verified data supersede/flag it automatically",
    "potential_consequence": "Dashboard can show a stale HR Override as 'ready' while current signal disagrees, with no resolution rule"
  },
  {
    "location": "prd.md:191-199 (FR-12)",
    "trigger_condition": "The HR Admin who created an override is later deactivated or removed as a user",
    "guard_snippet": "Preserve override attribution as an immutable historical record independent of live user-account state",
    "potential_consequence": "Drill-down attribution becomes a dangling/broken reference"
  },
  {
    "location": "prd.md:108-113 (FR-3)",
    "trigger_condition": "Best-available semantic match score for a Skill is very low (catalog has nothing genuinely close)",
    "guard_snippet": "Define a minimum similarity threshold below which the system treats it as FR-2's 'no matching content' path",
    "potential_consequence": "Employee/HR shown an irrelevant recommendation presented as if it were a good match"
  },
  {
    "location": "prd.md:115-120 (FR-4)",
    "trigger_condition": "Employee has zero assigned Skills (no Assignment exists yet)",
    "guard_snippet": "Define employee-facing empty state for 'nothing assigned yet', distinct from FR-6's Continue-Watching empty state",
    "potential_consequence": "Employee's landing view is undefined/blank on first login before any assignment exists"
  },
  {
    "location": "prd.md:170-175 (FR-9)",
    "trigger_condition": "Drill-down is opened on a row still in `Assigned · Awaiting first watch` with no signal history yet",
    "guard_snippet": "Define drill-down empty state distinct from the populated-history state",
    "potential_consequence": "Drill-down panel has nothing to render for newly-created assignments, reading as broken rather than empty"
  }
]
```

## Notes on scope

- Items already explicitly acknowledged by the PRD as deferred/accepted risk — data-retention period (Open Question 1), legal/compliance review (Open Question 2), non-video trust gap (Open Question 4), provenance-label comprehension being untested (Open Question 8), no content-approval gate (§5/§8) — are **not** repeated here; the PRD already handles them by explicit acknowledgment, even though resolution is deferred.
- No diff was reviewed, so the Step 4 deletion check does not apply.
