# Implementation Steps for Story 9-4: Frontend Needs Attention Popover & Drill-Down

**Story Key:** 9-4-frontend-needs-attention-popover-and-drill-down
**Epic:** 9 (Skill Assignment Dashboard) — 4 of 5 stories
**Status:** ✅ DONE (code-reviewed; not yet committed to git)
**Completed Date:** 2026-09-14

---

## Overview

Story 9.4 adds the interactive layer Story 9.3 deliberately left out: clicking the Employee Segmentation pie chart's "Needs Attention" segment (FR-33, UX-DR45/UX-DR46). When the count is greater than zero, it now opens a popover listing every flagged Employee/Skill pair, each a link into that Employee's existing per-assignment Provenance Drill-Down modal (FR-9) — reusing an already-shipped view, not building a new one. When the count is exactly zero, the segment stays genuinely non-interactive, per UX-DR46's explicit requirement.

No story file existed yet for 9.4 (only 9.1–9.3 had been created), so this session ran `bmad-create-story` first, then `bmad-dev-story`, then `bmad-code-review`, all in one continuous pass — the same pattern established for Story 9.3.

This story turned out to be **entirely frontend-only**: `EmployeeSegmentationResponse.needs_attention` (Story 9.2's response shape) already carried everything the popover needed — Story 9.3 had fetched that field but never read it, explicitly flagging the gap in its own code review as "Story 9.4 will use it." Zero backend files were touched.

One real judgment call was found and resolved during story creation:

1. **No existing code let any page open `ProvenanceDrillDownModal` from outside `/hr/dashboard`'s own grid-row click.** Satisfying AC1's "link into that Employee's existing Skill Progress drill-down" without building a second, parallel view (which `epics.md` explicitly forbids — "not a new view built for this story") required adding new `?assignmentId=` deep-link support to `Dashboard.tsx`/`DashboardPage.tsx`. Scoped as wiring the existing FR-9 view, not building a new one.

A second, easy-to-get-wrong distinction was resolved before it could become an implementation bug: `needs_attention_count` (the pie segment's number, distinct-Employee count) and `needs_attention.length` (one row per flagged *Assignment*) are not the same number and must not be conflated or deduplicated.

A real, unanticipated **implementation bug** — not a spec gap — was found and fixed during Task 2: `ProvenanceDrillDownModal` was only ever rendered in `DashboardPage.tsx`'s final "grid loaded" branch, not its Loading/Error/Empty early-return branches. Since every deep-linked open starts in the Loading state, the popover's own links would have silently failed to open the modal on first navigation without a fix.

Code review then caught a **follow-on defect in that very fix**: the shared `drillDownModal` render was hoisted into all four branches, but at *different tree positions* in the Loaded branch versus the other three — causing React to unmount/remount the modal (discarding its fetched data) on the realistic Loading→Loaded transition. Neither original test caught it, since both mocked an empty grid, which happens to keep the modal's position matching across Loading→Empty. This was corrected and locked in with a new regression test before the story was marked `done`.

---

## Agents Invoked

### 1. Blind Hunter (`bmad-review-adversarial-general` skill, background subagent)

**Purpose:** Open-ended adversarial critique of the finished diff — no spec context, no priors.

**When Invoked:** Part of `bmad-code-review`'s 3-parallel-layer step, once the story reached `review` status.

**Key Findings Identified:** The single most consequential finding of the entire review — `drillDownModal` rendered at an inconsistent child position across `DashboardPage.tsx`'s four state branches, causing React's positional reconciliation to unmount/remount `ProvenanceDrillDownModal` on the Loading→Loaded transition, discarding its already-fetched data and re-firing `getDrillDown`. Also flagged: the popover's grammatically loose "1 employees" aria-label copy (verified as exact UX-spec-mandated text, not a bug); the badge count vs. popover row count visibly disagreeing with no on-screen explanation (verified as Story 9.2's own deliberate design); `onInitialAssignmentConsumed` firing on every drill-down close, not just the deep-linked one; the mount-only deep-link effect silently ignoring in-place query-param changes; an unbounded popover with no scroll container; no `aria-controls`/`id` association between the trigger and the popover; no focus-out/Tab-away close handling; plus several observations about the tracking-doc narrative that turned out to be artifacts of this reviewer's own diff-construction (see Skills Invoked, `bmad-code-review`, below).

### 2. Edge Case Hunter (`bmad-review-edge-case-hunter` skill, background subagent)

**Purpose:** Method-driven walk of every branching path and boundary condition — orthogonal to Blind Hunter's attitude-driven pass.

**When Invoked:** Same trigger, launched in parallel with Blind Hunter and the Acceptance Auditor.

**Key Findings Identified:** `handleDeleteClick`/`handleViewDetails` bypassing the new `onInitialAssignmentConsumed` contract by clearing `selectedAssignmentId` directly (verified unreachable — `Dialog.tsx`'s full-screen backdrop blocks all interaction with the underlying grid while any drill-down modal is open); an empty-string `?assignmentId=` edge case (verified unreachable — the only real caller always builds the link from a real UUID); a theoretical `count > 0`-with-empty-`entries` prop desync (verified unreachable given the backend's own derivation, where `needs_attention_count` is defined as the distinct-employee count *within* `needs_attention`); the same unbounded-popover and aria-label-mismatch observations Blind Hunter also raised, independently corroborating them; `assignment_id` interpolated into the query string without `encodeURIComponent`.

### 3. Acceptance Auditor (custom prompt, background subagent)

**Purpose:** Cross-check the diff against the story's own ACs, Scope Notes, and Tasks — and against the UX design spec and `epics.md`'s original AC text.

**When Invoked:** Same trigger, full review mode against the story file as spec, with `epics.md`'s Story 9.4 section and the UX spec file also loaded as additional context.

**Key Findings Identified:** **Zero AC violations found.** Confirmed the implementation matches AC1–AC5 exactly: the literal `aria-label` copy ("Needs Attention, {N} employees, click to see who"), the literal popover row format ("{employee_name} — {skill_name}"), the count-gated zero/non-zero branching (AC2), the On Track/In Progress permanent inertness (AC3), the three-path close behavior with Escape-refocus (AC4), and the nav-shell boundary (AC5, verified by omission — no nav-link code added). Independently confirmed `/hr/dashboard`'s routing wires end-to-end and re-ran the actual test suite (35/35 passing at that point) rather than trusting the story file's own claims.

---

## Skills Invoked

### 1. `bmad-agent-dev` (Amelia persona activation)

**Purpose:** Activate the Senior Software Engineer persona for test-first implementation.

**When Invoked:** `start implementation for both API and UI for the story 9-4-frontend-needs-attention-popover-and-drill-down if required refer the UX desing`. Sprint status showed 9.4 as `backlog` (no story file yet) — dispatched straight to `bmad-create-story` first, matching Story 9.3's own established same-session create-then-dev precedent.

### 2. `bmad-create-story`

**Purpose:** Produce a comprehensive, implementation-ready story file for 9.4, since none existed yet.

**When Invoked:** Immediately on recognizing Story 9.4 had no story file, before any implementation work began.

**Workflow Steps Executed:**
1. Loaded Epic 9's Story 9.4 AC text from `epics.md`, plus Story 9.2's AC text (the origin of the `needs_attention` field this story consumes) and its own explicit forward-reference: "the frontend's popover (Story 9.4) needs this to render without a second round-trip."
2. Located and fully read the UX design spec — `06.1-skill-assignment-dashboard.md` — specifically its popover object IDs (`dashboard-needs-attention-popover`, `-popover-item`, `-hint`), Interactions table, Page States table's popover sub-states, and Accessibility Requirements section's exact `aria-label` copy.
3. Read Story 9.3's shipped page (`SkillAssignmentDashboard.tsx`) and its own Scope Note 12, which explicitly handed off this interactive layer, plus its Review Findings, which had already flagged the unused `needs_attention` field as this story's future payoff.
4. Read the current frontend's real drill-down machinery directly — `DashboardPage.tsx` (confirming `selectedAssignmentId`/`ProvenanceDrillDownModal` is entirely internal state, with no existing deep-link mechanism), `ProvenanceDrillDownModal.tsx` (confirming it fetches by `assignmentId` independent of grid/pagination state), `Dialog.tsx` (the Escape/focus-restore precedent, and confirming its Tab-trap and full-screen positioning don't fit a segment-anchored popover), `HrAppShell.tsx` (the anchored-dropdown positioning precedent, and confirming it has no Escape/outside-click handling of its own — not a full precedent to copy), and `types/dashboard.ts` (the `NeedsAttentionEntry`/`EmployeeSegmentationResponse` shapes already defined by Story 9.2/9.3).
5. Wrote 10 numbered Scope Notes covering: the frontend-only scope confirmation; the one-row-per-flagged-Assignment granularity rule (not deduplicated per Employee); the drill-down destination and the missing deep-link mechanism that had to be built; the exact `?assignmentId=` wiring plan for `Dashboard.tsx`/`DashboardPage.tsx`; the decision to build the popover locally in `SkillAssignmentDashboard.tsx` rather than as a new shared `components/ui/` primitive; the count-gated interactivity split; the three required close paths; the `useSearchParams` hook being new to this codebase but not a new dependency; the unchanged nav-shell scope boundary; and reusing `CHART_COLORS.needsAttention`.
6. Set Status to `ready-for-dev`; `sprint-status.yaml`'s `9-4-...` entry updated `backlog` → `ready-for-dev`.

**Output File:** `_bmad-output/implementation-artifacts/9-4-frontend-needs-attention-popover-and-drill-down.md`
**Sprint Status:** `9-4-...`: `backlog` → `ready-for-dev`

---

### 3. `bmad-dev-story` (implementation, Amelia persona)

**Purpose:** Execute the story's 4 tasks in sequence: popover component, deep-link support, tests, regression.

**When Invoked:** Immediately after the story file was created and marked `ready-for-dev`.

**Workflow Steps Executed:**
1. **Task 1 — Popover component:** New local `NeedsAttentionControl` in `SkillAssignmentDashboard.tsx`, replacing the always-plain Needs Attention row Story 9.3 shipped. `count === 0` keeps the identical plain `LegendRow`; `count > 0` renders a real `<button>` (`aria-haspopup`, `aria-expanded`, the exact spec-mandated `aria-label`) plus a `"Click to see who"` hint and an absolutely-positioned popover panel, one `<Link>` per `needs_attention` entry. Escape-to-close-and-refocus and click-outside-to-close implemented via a `useEffect` scoped to the open state, mirroring `Dialog.tsx`'s effect-lifecycle shape without its Tab-trap.
2. **Task 2 — Deep-link support:** `Dashboard.tsx` reads `assignmentId` via `useSearchParams()` (new to this codebase, not a new dependency) and passes it to `DashboardPage` as `initialAssignmentId`, with an `onInitialAssignmentConsumed` callback that strips the param on close. `DashboardPage.tsx` added the two new props, a mount-only effect that opens the existing `selectedAssignmentId` state/modal, and wired `handleCloseDrillDown()` to also call the new callback. **Real bug found and fixed here:** `ProvenanceDrillDownModal` was only rendered in the final "grid loaded" branch — hoisted a shared `drillDownModal` const, rendered in all four state branches, so a deep-linked open works regardless of the grid's own load state.
3. **Task 3 — Tests:** Extended `SkillAssignmentDashboard.test.tsx` (6 new/modified tests: button+aria-label+hint rendering, popover opening with one row per flagged Assignment — not deduplicated, Escape-close-and-refocus, click-outside-close, item-click-closes-and-links-correctly, On Track/In Progress staying inert) and `DashboardPage.test.tsx` (2 new tests: `initialAssignmentId` opens the modal on mount without a row click; closing it fires `onInitialAssignmentConsumed`).
4. **Task 4 — Regression:** `vitest run` → 420/420 (412 baseline + 8 new); `tsc --noEmit` → 31 pre-existing errors, confirmed as the exact baseline before starting (not assumed), unchanged after; `vite build` → clean, 537 modules (same count as Story 9.3's baseline — no new files created).
5. **Live verification:** Docker's `talentpilot-ui` was found 23h stale/unhealthy at session start (matching Story 9.3's own documented trap) — rebuilt and restarted. Seeded one temporary self-reported `skill_progress` row backdated 10 days on an existing assignment with no prior progress, to produce a real Needs Attention flag without waiting out the 7-day staleness threshold. Playwright (Chromium, installed ad hoc, removed after use) walked the full flow as HR Admin: click the segment → popover opens with the correct `aria-label` and one listed entry → Escape closes it and refocuses the button → reopen and click the employee link → lands on `/hr/dashboard?assignmentId=...` with the drill-down modal already open, visible over the grid's own Loading skeleton (proving the Task 2 bug fix) → close → URL cleaned back to `/hr/dashboard`. Screenshots captured; seeded row deleted immediately after and confirmed reverted via `curl`.
6. Story's Dev Agent Record, Completion Notes, and File List filled in; Status → `review`.

**Output Files:**
- `frontend/src/features/dashboard/DashboardPage.tsx`, `frontend/src/pages/hr/Dashboard.tsx`, `frontend/src/pages/hr/SkillAssignmentDashboard.tsx` (modified)
- `frontend/src/features/dashboard/DashboardPage.test.tsx`, `frontend/src/tests/SkillAssignmentDashboard.test.tsx` (modified)
- `_bmad-output/implementation-artifacts/9-4-frontend-needs-attention-popover-and-drill-down.md`

**Sprint Status:** `9-4-...`: `ready-for-dev` → `in-progress` → `review`

---

### 4. `bmad-code-review` (3-layer adversarial review + patch application)

**Purpose:** Independent adversarial verification of the finished implementation, followed by resolving every finding.

**When Invoked:** User explicitly asked to run code review immediately after implementation completed.

**Workflow Steps Executed:**
- Constructed the diff against uncommitted working-tree changes (`git diff HEAD`, 7 files changed, 380 insertions / 24 deletions, 583 diff lines), confirmed scope with the user (uncommitted changes, spec-backed against the story file).
- Launched Blind Hunter, Edge Case Hunter, and the Acceptance Auditor in parallel as background subagents, the Acceptance Auditor also given `epics.md`'s Story 9.4 section and the UX spec as additional loaded context.
- Normalized and deduplicated the three layers' raw findings, then **read the actual code before rating each one** — including reading `components/ui/dialog.tsx` directly to confirm its full-screen backdrop makes several "handler bypass while a modal is open" scenarios unreachable, and reading the real `sprint-status.yaml`/`project-context.md` files directly to disprove two Blind Hunter findings that turned out to be artifacts of this reviewer's own diff-trimming (long narrative comment lines had been shortened to placeholder text when building the subagent prompt, to keep it under length — the real files were always fully detailed) rather than real defects in the tracked content.
- Triaged into: **0 decision-needed, 4 patch, 2 defer, 13 dismiss.**
- **All 4 patches applied** (unambiguous, low-risk, applied proactively during investigation with a regression test added to prove the fix):
  1. **The most consequential fix:** `drillDownModal` was rendered at a different child index in the Loaded branch than in Loading/Error/Empty — moved it to the same position (right after `toastElement`) in all four branches, removing the stale duplicate reference near `<DeleteAssignmentModal>`. A new regression test in `DashboardPage.test.tsx` resolves the grid's fetch with real non-empty rows mid-test and asserts `getDrillDown` is called exactly once across the transition — this test would have caught the bug had it existed at implementation time.
  2. **Popover overflow fixed:** added `max-h-80 overflow-y-auto` to the popover panel, previously unbounded.
  3. **Accessibility association fixed:** added a `useId()`-derived id on the popover panel, referenced via `aria-controls` on the trigger button (only while open) — `aria-haspopup`/`aria-expanded` previously had nothing pointing at what they controlled.
  4. **URL hardening:** wrapped the popover link's `assignment_id` in `encodeURIComponent()` — defensive, low-risk since it's a UUID that never contains characters requiring escaping in practice.
- **Deferred 2 low-severity findings** to `deferred-work.md`: `onInitialAssignmentConsumed` firing on every drill-down close, not just the deep-linked one (harmless today, safely guarded by the caller); the mount-only deep-link effect silently ignoring an in-place `?assignmentId=` change without a full remount (already a documented, deliberate trade-off).
- **Dismissed 13 findings after verification**, each checked rather than waved off: the "grammatically broken" aria-label is the UX spec's own exact mandated copy; the badge-count-vs-popover-row-count mismatch is Story 9.2's own explicit design (re-confirmed by the Acceptance Auditor); popover-doesn't-close-on-Tab-away is not one of AC4's three required close paths; the handler-bypass scenarios are unreachable given `Dialog.tsx`'s full-screen backdrop (verified by direct read); the empty-string-assignmentId and prop-desync edge cases are unreachable given real callers/backend construction; the URL-building-style inconsistency matches this codebase's existing convention; the missing 404-deep-link test targets `ProvenanceDrillDownModal`'s own pre-existing, independently-tested error handling; and the two "unfilled placeholder"/"out of order" changelog findings were verified false against the real tracked files.
- Re-ran the full frontend suite — **421 passed** (412 baseline + 9, up from 8 after the new regression test), zero regressions. `tsc --noEmit` unchanged at 31 pre-existing errors. `vite build` clean.
- Story Status → `done`; `sprint-status.yaml` synced; `project-context.md` updated per this project's own established rule that no story reaches `done` without a matching entry there.

**Output:** Story file's "### Review Findings" subsection (4 checked-off patches with inline "Fixed:" notes, 2 checked-off deferred items, 13 dismissed noted in prose); `deferred-work.md` gained a new "Deferred from: code review of 9-4-..." section.

**Documentation Generated:**
- The story file's Review Findings section, Change Log, and Status field
- `deferred-work.md`'s new Story 9.4 section
- Sprint status synced (`9-4-...`: `backlog` → `ready-for-dev` → `in-progress` → `review` → `done`; `epic-9` remains `in-progress`, since Story 9.5 is still `backlog`)
- Two `project-context.md` entries (implementation completion, then code-review completion)

---

## Files Created/Updated

### Frontend — Modified Files

| File | Purpose |
|------|---------|
| `frontend/src/pages/hr/SkillAssignmentDashboard.tsx` | New `NeedsAttentionControl` component (button + anchored popover for count > 0, unchanged plain row for count === 0); replaced the old always-plain Needs Attention row usage; popover panel hardened with `max-h-80 overflow-y-auto`, `id`/`aria-controls`, and `encodeURIComponent` (code review patches) |
| `frontend/src/pages/hr/Dashboard.tsx` | Added `useSearchParams`-based `?assignmentId=` deep-link read/strip, passed to `DashboardPage` |
| `frontend/src/features/dashboard/DashboardPage.tsx` | Added `initialAssignmentId`/`onInitialAssignmentConsumed` props; mount-only effect opens the drill-down modal from the deep-link; `drillDownModal` hoisted and rendered at the same tree position in all four state branches (implementation bug fix, then code-review position-parity fix) |
| `frontend/src/tests/SkillAssignmentDashboard.test.tsx` | Re-scoped Story 9.3's old always-non-interactive test to the `count === 0` case; added 6 new tests covering the button/popover/Escape/outside-click/item-click/On-Track-In-Progress-inert behavior |
| `frontend/src/features/dashboard/DashboardPage.test.tsx` | Added a `describe` block with 2 tests covering `initialAssignmentId`-driven modal open and `onInitialAssignmentConsumed` on close, plus a 3rd regression test (code review) proving the modal survives the Loading→Loaded transition without remounting |

### Planning/Tracking — Modified Files

| File | Purpose |
|------|---------|
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | `9-4-...` progressed `backlog` → `ready-for-dev` → `in-progress` → `review` → `done` |
| `_bmad-output/implementation-artifacts/deferred-work.md` | New "Deferred from: code review of 9-4-..." section, 2 entries |
| `_bmad-output/project-context.md` | Two entries appended (implementation completion, then code-review completion), per this project's own established "no story reaches `done` without a matching entry here" rule |

### Documentation Files

| File | Purpose |
|------|---------|
| `_bmad-output/implementation-artifacts/9-4-frontend-needs-attention-popover-and-drill-down.md` | Story file — 5 ACs, 10 Scope Notes, Dev Notes, Dev Agent Record, Review Findings section |
| `documentation/ImplementationStepsForStory9-4.md` | This file |

### Not Changed (by design)

- Any backend file (`backend/`) — this story is entirely frontend, consuming a field Story 9.2 already shipped
- `frontend/src/features/dashboard/ProvenanceDrillDownModal.tsx` — reused unmodified, per its own Scope Note
- `frontend/src/components/layout/HrAppShell.tsx` — nav wiring is Story 9.5's explicitly-claimed scope, deliberately untouched here
- `frontend/src/components/ui/dialog.tsx` — read as a close-behavior precedent only, not modified or reused directly (this popover is non-modal, built locally instead)

---

## Implementation Workflow Summary

### Phase 1: Story Creation
**Skill:** `bmad-create-story`
- Read `epics.md`'s Story 9.2/9.4 AC text, the UX design spec's popover object IDs/interactions/accessibility copy, Story 9.3's shipped page and its own hand-off note, and the current frontend's real drill-down/dialog/nav-dropdown machinery directly
- Resolved a real scope gap before it could become a mid-implementation surprise: no existing code let any page open `ProvenanceDrillDownModal` outside the grid's own row click
- Resolved the `needs_attention_count`-vs-`needs_attention.length` granularity distinction before it could become an implementation bug
- 10 numbered Scope Notes written, including the deep-link wiring plan and the local-popover-not-a-shared-primitive decision
- Status → `ready-for-dev`

### Phase 2: Implementation
**Execution:** Amelia persona, frontend-only (confirmed the one consumed field already shipped)
- 4 tasks executed in sequence: popover component → deep-link support → tests → full regression
- A real, unanticipated bug found and fixed mid-implementation: `ProvenanceDrillDownModal` wasn't rendered in 3 of `DashboardPage`'s 4 state branches
- Full regression: 420 passed (412 baseline + 8 new), zero regressions; live-verified end-to-end via Playwright against seeded real data, then reverted
- Story marked `review`

### Phase 3: Code Review + Patches
**Skill:** `bmad-code-review`
- 3 parallel adversarial layers (Blind Hunter, Edge Case Hunter, Acceptance Auditor — the auditor also given `epics.md` and the UX spec) against the uncommitted diff
- 19 unique findings after triage: 0 decision-needed, 4 patched, 2 deferred, 13 dismissed after direct verification
- The most consequential finding was a follow-on defect in the implementation phase's own bug fix — the position-inconsistent `drillDownModal` render, caught only because Blind Hunter reasoned about React's reconciliation behavior rather than just reading the diff at face value; confirmed and locked in with a new regression test
- Full regression re-verified after patches: 421 passed (412 baseline + 9, up from 8), zero regressions
- Story marked `done`

---

## Test Coverage

### New/Extended Test Files

- `SkillAssignmentDashboard.test.tsx` — 14 total tests (8 pre-existing + 6 new/modified for this story):
  - `renders Needs Attention as plain, non-interactive text when the count is exactly zero (AC2, UX-DR46)` (re-scoped from Story 9.3's original always-non-interactive test)
  - `on-click, On Track / In Progress segments remain inert regardless of count (AC3, deliberate asymmetry)`
  - `renders a real button with the exact aria-label and hint text, popover closed by default`
  - `opens on click, listing one row per flagged Assignment -- not deduplicated per Employee`
  - `Escape closes the popover and returns focus to the trigger button (AC4)`
  - `clicking outside the popover closes it (AC4)`
  - `clicking a popover employee link closes the popover and links into the drill-down (AC1, AC4)`
- `DashboardPage.test.tsx` — 22 total tests (19 pre-existing + 3 new for this story):
  - `opens the Provenance Drill-Down modal on mount when initialAssignmentId is set, without a grid row click`
  - `calls onInitialAssignmentConsumed when the deep-linked modal is closed via Escape`
  - `preserves the deep-linked modal's fetched state across the Loading -> Loaded transition (no remount/double-fetch)` (code review regression test)

### Regression Verification

- Frontend: 412 → 420 (implementation) → 421 (code review patch) passed, 0 failed throughout
- `tsc --noEmit`: 31 pre-existing errors at every checkpoint (confirmed as the exact baseline before starting, not assumed), none in this story's files
- `vite build`: clean at every checkpoint, 537 modules throughout (no new files created)
- Live verification (Playwright, installed ad hoc, removed after use, against a rebuilt Docker `talentpilot-ui` container): full popover-open → Escape-close-and-refocus → outside-click-close → item-click → deep-link → drill-down-modal-open-over-the-Loading-skeleton → close-and-URL-cleanup flow walked with real seeded data, reverted afterward

---

## Architecture Decisions Implemented

| Decision | Implementation | Files Affected |
|----------|---|---|
| **Frontend-only scope** | `EmployeeSegmentationResponse.needs_attention` (Story 9.2) verified to already carry everything needed, directly against the live backend schema before any implementation began; zero backend files touched | (verification only, no backend files) |
| **Reuse FR-9's drill-down, don't build a new view** | `?assignmentId=` deep-link added to `/hr/dashboard`, opening the existing `ProvenanceDrillDownModal` unmodified | `frontend/src/pages/hr/Dashboard.tsx`, `frontend/src/features/dashboard/DashboardPage.tsx` |
| **One popover row per flagged Assignment, not per Employee** | `entries.map(...)` iterates `segmentation.needs_attention` directly, no dedup logic | `frontend/src/pages/hr/SkillAssignmentDashboard.tsx` |
| **AC2/UX-DR46: hard zero/non-zero split** | Two structurally different renders (`count === 0` → identical plain `LegendRow`; `count > 0` → real button + popover), not one render with a disabled state | `frontend/src/pages/hr/SkillAssignmentDashboard.tsx` |
| **AC3: deliberate asymmetry** | On Track / In Progress rows never made interactive, regardless of count | `frontend/src/pages/hr/SkillAssignmentDashboard.tsx` |
| **AC4: three close paths + Escape-refocus** | Local `useEffect` (Escape + outside-click), no Tab-trap (non-modal, unlike `Dialog.tsx`) | `frontend/src/pages/hr/SkillAssignmentDashboard.tsx` |
| **Deep-link modal must render independent of grid state** | `drillDownModal` hoisted as a shared const, rendered at the *same tree position* in all four `DashboardPage` state branches (implementation fix, then code-review position-parity fix) | `frontend/src/features/dashboard/DashboardPage.tsx` |

---

## Key Technical Achievements

✅ **Ran the full create → implement → review → patch pipeline in one continuous session**, correctly identifying the story as entirely frontend-only from the outset
✅ **Resolved a real missing-capability gap before it caused rework** — no code existed to deep-link into the existing drill-down modal, satisfied by wiring the existing FR-9 view rather than building a parallel one
✅ **Found and fixed a real implementation bug mid-story** — the drill-down modal wasn't rendered in 3 of 4 `DashboardPage` state branches, discovered by reasoning through the deep-link's actual mount-time state rather than assuming the "renders everywhere" comment was already true
✅ **Live-verified end-to-end against real seeded data**, not just mocks — including deliberately reverting the seed afterward to leave the shared dev DB unchanged
✅ **Code review caught a genuine follow-on defect in the implementation phase's own fix** — the position-inconsistent `drillDownModal` render, undetectable by the original tests since both happened to mock an empty grid; confirmed via React reconciliation reasoning and locked in with a new regression test, not just patched blind
✅ **Two reviewer findings verified false against ground truth, not accepted at face value** — the "unfilled placeholder" and "out of order" changelog claims were traced back to the reviewer's own diff-trimming artifact, not the real tracked files
✅ **Several other findings verified unreachable by reading the actual code**, not dismissed on assumption — `Dialog.tsx`'s full-screen backdrop, the backend's `needs_attention_count` construction, the only real caller of the popover link
✅ **Zero regressions across every regression run in the session** — 412 → 420 → 421, with the same 31 pre-existing `tsc` errors at every checkpoint

---

## Deferred Items (Not Story 9-4 Scope)

From this story's own code review, logged in `deferred-work.md`:
- **`onInitialAssignmentConsumed` fires unconditionally on every drill-down close, not just the deep-linked one** — harmless today only because the caller (`Dashboard.tsx`) re-guards before stripping the URL param. Revisit if this callback ever needs to distinguish "the deep-linked modal specifically closed" from "any drill-down modal closed."
- **The `initialAssignmentId` effect is intentionally mount-only** — an in-place `?assignmentId=` change without a full remount (e.g. same-tab browser back/forward) is silently ignored. Already a documented, deliberate trade-off; revisit only if that navigation pattern becomes a real reported need.

Carried forward from earlier epics, unaffected by this story:
- `EmployeeSegmentationResponse.needs_attention`'s unbounded list growth (Story 9.2's own already-logged deferral, extended by Story 9.3) — this story is the field's first real consumer, but the underlying pagination/capping question is still a backend call better made with real roster-size data.
- `auth/repository.py::authenticate()` still does not read `Account` (Epic 7's own flagged gap) — irrelevant to this story's scope.

---

## Conclusion

Story 9-4 is **✅ DONE** after a full create-then-implement-then-review-and-patch cycle, run start to finish in one session:

- All 5 acceptance criteria satisfied — the popover opens exactly for flagged Employees with a count > 0, lists one row per flagged Assignment with the exact spec-mandated copy and `aria-label`, stays genuinely non-interactive at count zero, closes via all three required paths with correct focus return, and adds no nav-shell code — verified by 9 dedicated frontend tests plus a full 421-test regression pass, both before and after the code-review patches, and live-verified end-to-end against rebuilt Docker containers with real seeded data
- Code review surfaced 19 findings: 0 requiring a human decision, 4 patched (the most consequential being a genuine follow-on defect in the implementation phase's own bug fix, caught and regression-tested), 2 correctly deferred as low-severity accepted trade-offs, and 13 dismissed after direct verification (including two settled by reading the actual tracked files rather than the reviewer's own trimmed diff excerpt)
- Zero regressions across every regression run in the session (412 → 420 → 421 passed)
- **Not yet committed to git** — working tree still uncommitted as of this document, on top of `HEAD` at `c89bab2f` ("Story 9.3: Frontend Skill Assignment Dashboard Landing Page (FR-31/32)")

**Epic 9 status:** `in-progress`. Stories 9.1, 9.2, 9.3, and 9.4 are `done`; Story 9.5 (Frontend: Nav Shell — Add "Skill Assignments" Entry) remains `backlog`.
