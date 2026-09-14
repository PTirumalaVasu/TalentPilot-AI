# Implementation Steps for Story 9-5: Frontend Nav Shell — Add "Skill Assignments" Entry

**Story Key:** 9-5-frontend-nav-shell-add-skill-assignments-entry
**Epic:** 9 (Skill Assignment Dashboard) — 5 of 5 stories, **epic complete**
**Status:** ✅ DONE (code-reviewed; not yet committed to git)
**Completed Date:** 2026-09-14

---

## Overview

Story 9.5 is the final story in Epic 9 and the last piece needed to make the Skill Assignment Dashboard (Story 9.3) actually reachable from normal navigation. Stories 9.3/9.4 deliberately left `HrAppShell.tsx`'s left-pane nav untouched — the "Dashboard" link kept pointing at the pre-existing full grid (`/hr/dashboard`) the whole time, with both stories' own code comments explicitly deferring the repoint to 9.5. This story does exactly that: it relabels/repoints the nav so **"Dashboard"** now opens the new landing page (`/dashboard`) and a new **"Skill Assignments"** entry opens the full grid — four nav entries in total, matching FR-29's amendment and UX-DR47/UX-DR48.

No story file existed yet for 9.5, so this session ran `bmad-create-story` first, then `bmad-dev-story`, then `bmad-code-review`, all in one continuous pass — the same pattern established for Stories 9.3 and 9.4.

This story is **entirely frontend-only** per `epics.md`'s own explicit framing ("this story is frontend-only (`HrAppShell.tsx` per Story 7.7's precedent) — no backend/API change"). Both routes (`/dashboard`, `/hr/dashboard`) and their `<RequireAuth>` wrapping already existed in `App.tsx` — this story never touched routing, either page component, or any backend file. It is the smallest story in the epic: two one-line production changes plus their tests.

One real judgment call was found and resolved during story creation, going beyond `epics.md`'s literal AC text:

1. **`Login.tsx`'s post-login `HR_ADMIN` redirect still hardcoded `/hr/dashboard`.** The PRD's own UJ-1 user journey and §4.10 glossary entry (both `[UPDATED 2026-09-12]`) already say the HR Admin's entry state is now the Skill Assignment Dashboard, not the full grid — but no story anywhere in Epic 9 mentioned updating `Login.tsx`. Since this is the epic's last story, the redirect was fixed here (Task 2/AC5) rather than leaving Epic 9 "complete" while still contradicting its own PRD.

Code review's Blind Hunter layer flagged this exact judgment call as **undisclosed scope expansion** — the earlier `AskUserQuestion` scope confirmation the user answered had only described `HrAppShell.tsx` nav changes, never `Login.tsx`. The independent Acceptance Auditor pass separately confirmed the change itself was well-justified and not backend/API scope creep. Presented back to the user as a decision-needed item; **resolved: keep the change as shipped, explicitly flagged in the permanent record**, with a process lesson captured for future stories (raise a fresh `AskUserQuestion` before folding a judgment call into a new file/behavior category, even after an earlier "proceed frontend-only" answer).

Code review's most consequential finding was a **documentation-accuracy defect, not a code bug**: this story's own References section (and `project-context.md`/`sprint-status.yaml`) claimed both nav routes were "already role-gated." Direct inspection of `RequireAuth.tsx` showed it checks authentication only, with zero role branching — there is no frontend role-based route gate anywhere in this app. This is a real, pre-existing, app-wide gap (established at least since Story 9.3), not introduced by this diff, so no code fix was made to `RequireAuth.tsx` itself — but the inaccurate wording was corrected everywhere it appeared, and the underlying gap was logged in `deferred-work.md`.

---

## Agents Invoked

### 1. Blind Hunter (`bmad-review-adversarial-general` skill, background subagent)

**Purpose:** Open-ended adversarial critique of the finished diff — no spec context, no priors.

**When Invoked:** Part of `bmad-code-review`'s 3-parallel-layer step, once the story reached `review` status.

**Key Findings Identified:** The single most consequential finding of the entire review — the "already role-gated" claim in the story's own documentation is demonstrably false, since `RequireAuth.tsx` has zero role branching (confirmed by direct code read, not taken on faith). Also flagged: the undisclosed `Login.tsx` scope expansion (see Overview); a stale comment in `SkillAssignmentDashboard.tsx` still describing the nav repoint as a future Story 9.5 event; no regression test asserting the new `/dashboard` active-state (AC2's own specific claim); AC1's literal nav order having no automated assertion; `HrAppShell.tsx`'s new doc comment overclaiming "not one page linking to the other" when Story 9.4's popover already deep-links into the grid at the content level; plus several observations about the rename being "confusing" for muscle memory, unreproducible ad hoc Playwright verification, self-attested status transitions, and narrative prose in `sprint-status.yaml` comments — all investigated and dismissed as either spec-conformant or matching this project's own established conventions (see Skills Invoked, `bmad-code-review`, below).

### 2. Edge Case Hunter (`bmad-review-edge-case-hunter` skill, background subagent)

**Purpose:** Method-driven walk of every branching path and boundary condition — orthogonal to Blind Hunter's attitude-driven pass.

**When Invoked:** Same trigger, launched in parallel with Blind Hunter and the Acceptance Auditor.

**Key Findings Identified:** A missing test asserting Skill Assignments does *not* become active on `/dashboard` (merged into the same AC2 test-coverage gap Blind Hunter and the Acceptance Auditor both independently flagged); `Login.tsx`'s non-`HR_ADMIN` ternary fallback silently routing to `/employee/content` for any unrecognized role value (verified unreachable — this ternary structure is completely unchanged pre-existing logic, and `role` is a validated backend enum with no reachable third value); two low-confidence "deletion risk" findings speculating that some other file might assume the old Dashboard→`/hr/dashboard` mapping or the old post-login redirect target (both explicitly flagged low-confidence by the reviewer itself, and both verified unfounded via direct `grep` across `frontend/src` — no other file makes either assumption).

### 3. Acceptance Auditor (custom prompt, background subagent)

**Purpose:** Cross-check the diff against the story's own ACs, Scope Notes, and Tasks — and independently against `epics.md`'s original Story 9.5 AC text and the PRD's UJ-1/FR-29 sections.

**When Invoked:** Same trigger, full review mode against the story file as spec, with `epics.md` and `prd.md` also read directly as additional context.

**Key Findings Identified:** **No AC violations found in the core nav change (AC1–AC4).** Independently traced `epics.md`'s Story 9.5 section (confirmed only 4 ACs exist, `Login.tsx` never mentioned) against the PRD's UJ-1 and §4.10 (both carrying `[UPDATED 2026-09-12]` tags) and against the *original* Epic 1 login story's own AC text (found it generic and unpinned to a specific route — the same class of stale/ambiguous epics text this repo has already flagged and corrected elsewhere) — concluded the `Login.tsx` fix was a genuine, real drift between a stale epics AC and an already-updated PRD, defensible rather than an overreach. Flagged one real test-coverage gap: no test asserts AC2's own specific claim ("Dashboard... is marked active there") at the new `/dashboard` route, since the previous suite's default render path used to cover Dashboard for free before the repoint and now covers a different entry instead.

---

## Skills Invoked

### 1. `bmad-agent-dev` (Amelia persona activation)

**Purpose:** Activate the Senior Software Engineer persona for test-first implementation.

**When Invoked:** `start implementation for both API and UI for the story 9-5-frontend-skill-assignment-dashboard-landing-pag if required refer the UX desing`. Checked `epics.md` before dispatching and found a scope mismatch: Story 9.5 is frontend-only nav-shell work per its own AC text, with no API component at all — surfaced this to the user via `AskUserQuestion` before proceeding (matching the same class of check already applied for Story 9.2). User confirmed proceeding frontend-only per `epics.md`.

### 2. `bmad-create-story`

**Purpose:** Produce a comprehensive, implementation-ready story file for 9.5, since none existed yet.

**When Invoked:** Immediately after the scope confirmation, before any implementation work began.

**Workflow Steps Executed:**
1. Loaded Epic 9's Story 9.5 AC text from `epics.md` (4 ACs: nav order, Dashboard repoint, Skill Assignments addition, frontend-only framing), plus its "Recommended build order" note confirming 9.5 is last, dependent on 9.3's `/dashboard` route already existing.
2. Read `prd.md`'s FR-29 section (§4.8) and its own `[NOTE FOR PM]` confirming no dedicated UX scenario/prototype exists for this nav layout — the complete spec is `epics.md`'s AC text plus UX-DR47/UX-DR48 (both defined inline in `epics.md`'s own Design Decisions register, not a separate UX file).
3. Read `prd.md`'s UJ-1 user journey and §4.10 glossary entry directly, both `[UPDATED 2026-09-12]` — found the real, undocumented PRD/epics drift around `Login.tsx`'s post-login redirect (see Overview) before it could become a silent epic-completion gap.
4. Read the current frontend's real nav/routing machinery directly — `HrAppShell.tsx` (confirming `NAV_LINKS` is a pure `.map()`-driven array with no logic changes needed for a 4th entry), `App.tsx` (confirming both `/dashboard` and `/hr/dashboard` already exist and are wrapped in `<RequireAuth>`), `Login.tsx` (the exact ternary line to change), `HrAppShell.test.tsx`/`Login.test.tsx` (the existing test conventions to extend), and Story 9.3's own file header comment (which explicitly deferred the nav repoint to this story) and Story 7.7's original 3-entry nav story (the active-state/keyboard/aria pattern being extended, not reinvented).
5. Wrote 6 numbered Scope Notes covering: the frontend-only scope confirmation; the exact `NAV_LINKS` data change with before/after arrays; the `testId` reuse rule (don't rename `app-nav-link-dashboard`); the `Login.tsx` redirect fix and its justification; the absence of a dedicated UX spec; and an explicit "do not touch" list (routes, both page components, backend).
6. Set Status to `ready-for-dev`; `sprint-status.yaml`'s `9-5-...` entry updated `backlog` → `ready-for-dev`.

**Output File:** `_bmad-output/implementation-artifacts/9-5-frontend-nav-shell-add-skill-assignments-entry.md`
**Sprint Status:** `9-5-...`: `backlog` → `ready-for-dev`

---

### 3. `bmad-dev-story` (implementation, Amelia persona)

**Purpose:** Execute the story's 4 tasks in sequence: nav repoint, redirect fix, tests, regression.

**When Invoked:** Immediately after the story file was created and marked `ready-for-dev`.

**Workflow Steps Executed:**
1. Confirmed the pre-story baseline directly rather than assuming Story 9.4's own record still held: `vitest run` → 421/421; `tsc --noEmit` → 31 pre-existing errors.
2. **Task 1 — Repoint and extend the nav:** `HrAppShell.tsx`'s `NAV_LINKS` array changed from 3 to 4 entries — `Dashboard` repointed from `/hr/dashboard` to `/dashboard`, keeping its existing `testId`; new `Skill Assignments` entry added (`to: '/hr/dashboard'`, `testId: 'app-nav-link-skill-assignments'`); `Skills`/`Employees` unchanged. File header doc comment updated to describe the 4-entry nav. No other logic touched — the render loop's active-state/keyboard/mobile-collapse behavior generalizes to 4 entries with zero code changes.
3. **Task 2 — Fix post-login landing redirect:** `Login.tsx`'s one ternary branch changed from `/hr/dashboard` to `/dashboard` for the `HR_ADMIN` case.
4. **Task 3 — Tests, true TDD:** `HrAppShell.test.tsx`/`Login.test.tsx` updated first and confirmed **RED** (3 failing tests) against the unmodified source, before any production code change — then confirmed **GREEN** after. Updated the 3-destination test to assert 4; added a new active-state test for the Skill Assignments entry at `/hr/dashboard`; renamed and re-targeted the Login redirect test.
5. **Task 4 — Regression:** `vitest run` → 422/422 (421 baseline + 1 net new); `tsc --noEmit` → 31 pre-existing errors, unchanged; `vite build` → clean, 537 modules (same as Story 9.4's baseline — no new files created).
6. **Live verification:** Docker's `talentpilot-ui` was found unhealthy/stale at session start (matching the same trap Stories 9.3/9.4 had already documented) — rebuilt and restarted. Playwright (Chromium, installed ad hoc, removed after use) walked the full flow as HR Admin: login lands on `/dashboard` (AC5) → all 4 nav entries render in order → "Dashboard" points at/marks-active `/dashboard` → "Skill Assignments" opens/marks-active the full grid at `/hr/dashboard`, rendering unfiltered with both seeded Employees visible → Skills/Employees unaffected → clicking "Dashboard" again from elsewhere returns to the landing page, not the full grid → a 375px mobile viewport's hamburger overlay shows all 4 entries and closes on link click. Two bugs found and fixed mid-verification were in the *verification script itself*, not the app — an active-state assertion needed a short settle delay after router navigation, and a "grid renders rows" assertion wrongly assumed a `<table>` structure instead of the grid's real accordion-by-Employee layout — both confirmed via direct DOM inspection (`outerHTML`/`innerText` dumps) before correcting the assertions, rather than accepting the failures as real defects.
7. Story's Dev Agent Record, Completion Notes, and File List filled in; Status → `review`.

**Output Files:**
- `frontend/src/components/layout/HrAppShell.tsx`, `frontend/src/pages/Login.tsx` (modified)
- `frontend/src/tests/HrAppShell.test.tsx`, `frontend/src/tests/Login.test.tsx` (modified)
- `_bmad-output/implementation-artifacts/9-5-frontend-nav-shell-add-skill-assignments-entry.md`

**Sprint Status:** `9-5-...`: `ready-for-dev` → `in-progress` → `review`

---

### 4. `bmad-code-review` (3-layer adversarial review + decision resolution + patch application)

**Purpose:** Independent adversarial verification of the finished implementation, followed by resolving every finding.

**When Invoked:** User explicitly asked to run code review immediately after implementation completed.

**Workflow Steps Executed:**
- Constructed the diff against uncommitted working-tree changes (`git diff HEAD`, 6 files changed, 39 insertions / 13 deletions, 145 diff lines), confirmed scope with the user (uncommitted changes, spec-backed against the story file).
- Launched Blind Hunter, Edge Case Hunter, and the Acceptance Auditor in parallel as background subagents, the Acceptance Auditor also given `epics.md` and `prd.md` as additional loaded context.
- Normalized and deduplicated the three layers' raw findings, then **read the actual code before rating each one** — including reading `RequireAuth.tsx` directly to confirm the "role-gated" claim was false, and running a live `grep` across `frontend/src` to confirm the two low-confidence "deletion risk" findings were genuinely unfounded rather than dismissing them on the reviewer's own stated low confidence alone.
- Triaged into: **1 decision-needed, 5 patch, 2 defer, 7 dismiss.**
- **Decision-needed item resolved by the user:** the `Login.tsx` redirect change (an auth-flow file) had exceeded the literal scope of the earlier `AskUserQuestion` confirmation. Presented three options (keep as shipped / revert / keep as shipped but explicitly flag); **user chose to keep it as shipped, explicitly flagged** — resolved with no code change, but the story file's Review Findings and Dev Notes now record the process gap and a lesson for future stories.
- **All 5 patches applied** (unambiguous, low-risk, no per-finding confirmation needed since the user chose "apply every patch"):
  1. **The most consequential fix:** corrected the inaccurate "already role-gated" claim wherever it appeared (this story's own Scope Notes/References, `project-context.md`, `sprint-status.yaml`) to accurately describe `<RequireAuth>` as authentication-only gating, with a pointer to the newly-logged deferred item.
  2. **Missing AC2 test coverage fixed:** added a new active-state test asserting `app-nav-link-dashboard` gets `aria-current="page"`/`font-medium` at `/dashboard`, and that `app-nav-link-skill-assignments` does not.
  3. **Missing AC1 order coverage fixed:** the renamed "renders all four nav destinations, in order" test now asserts the sidebar's nav links' `textContent` in exact DOM order. **Verified the assertion actually catches a real regression**, not just trusting its shape: temporarily swapped the first two `NAV_LINKS` entries, confirmed the new test failed, then restored the correct order and confirmed green again — a repeatable verification habit applied during the review itself, not assumed.
  4. **Stale cross-story comment fixed:** `SkillAssignmentDashboard.tsx`'s doc comment, which still described this story's own nav repoint as a future event ("until Story 9.5 repoints it"), corrected to past tense.
  5. **Overclaiming doc comment reworded:** `HrAppShell.tsx`'s new file header comment ("two distinct destinations, not one page linking to the other") was scoped explicitly to nav entries, with an added sentence acknowledging the landing page's own Story 9.4 content-level deep links into the grid.
- **Deferred 2 items** to `deferred-work.md`, both pre-existing and out of this story's scope: the app-wide missing frontend role-gate itself (item #1 above's underlying cause); `Login.tsx`'s redirect tested only via a mocked `navigateMock` assertion, not an integration-level route-rendering check — matches this test file's pre-existing pattern since Story 1.x.
- **Dismissed 7 findings after verification**, each checked rather than waved off: the rename being "confusing" for muscle memory is the literal, explicitly-specified epics/PRD behavior change (UX-DR47), not a defect; the ad hoc Playwright install/verify/remove pattern matches this project's own established convention across every Epic 8/9 story; "self-attested status transition with no reviewer" is exactly what this code-review pass is; narrative prose in `sprint-status.yaml` comments is a pre-existing project-wide convention already kept in Story 9.4's own review; `Login.tsx`'s non-`HR_ADMIN` ternary fallback is completely unchanged pre-existing logic against a validated backend role enum; both Edge Case Hunter "deletion risk" findings were verified unfounded via direct `grep`.
- Re-ran the full frontend suite — **423 passed** (421 baseline + 2 net new), zero regressions. `tsc --noEmit` unchanged at 31 pre-existing errors. `vite build` clean.
- Story Status → `done`; `sprint-status.yaml` synced; **`epic-9` flipped `in-progress` → `done`** — all 5 stories now complete; `project-context.md` updated per this project's own established rule that no story reaches `done` without a matching entry there.

**Output:** Story file's "### Review Findings" subsection (1 checked-off decision with resolution note, 5 checked-off patches with inline "Fixed:" notes, 2 checked-off deferred items, 7 dismissed noted in prose); `deferred-work.md` gained a new "Deferred from: code review of 9-5-..." section.

**Documentation Generated:**
- The story file's Review Findings section, Change Log, and Status field
- `deferred-work.md`'s new Story 9.5 section
- Sprint status synced (`9-5-...`: `backlog` → `ready-for-dev` → `in-progress` → `review` → `done`; `epic-9`: `in-progress` → `done`)
- Two `project-context.md` entries (implementation completion, then code-review completion)
- A new persistent-memory feedback entry recording the "raise a fresh `AskUserQuestion` before expanding scope into an unannounced file category" process lesson

---

## Files Created/Updated

### Frontend — Modified Files

| File | Purpose |
|------|---------|
| `frontend/src/components/layout/HrAppShell.tsx` | `NAV_LINKS`: 3 → 4 entries; `Dashboard` repointed to `/dashboard`; new `Skill Assignments` entry (`/hr/dashboard`); file header doc comment updated, then reworded again during code review to scope its "two distinct destinations" claim to nav entries specifically |
| `frontend/src/pages/Login.tsx` | Post-login `HR_ADMIN` redirect target changed from `/hr/dashboard` to `/dashboard` |
| `frontend/src/pages/hr/SkillAssignmentDashboard.tsx` | Code-review patch only: fixed a stale doc comment still describing this story's own nav repoint as a future event |
| `frontend/src/tests/HrAppShell.test.tsx` | Updated the 3-destination test to 4 (later extended with a DOM-order assertion); added active-state tests for both the "Skill Assignments" entry and (code-review patch) the "Dashboard" entry at its new `/dashboard` target |
| `frontend/src/tests/Login.test.tsx` | Renamed and updated the HR_ADMIN redirect test's asserted target |

### Planning/Tracking — Modified Files

| File | Purpose |
|------|---------|
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | `9-5-...` progressed `backlog` → `ready-for-dev` → `in-progress` → `review` → `done`; `epic-9` progressed `in-progress` → `done`; code-review patch corrected an inaccurate "role-gated" claim |
| `_bmad-output/implementation-artifacts/deferred-work.md` | New "Deferred from: code review of 9-5-..." section, 2 entries |
| `_bmad-output/project-context.md` | Two entries appended (implementation completion, then code-review completion); code-review patch applied the same "role-gated" wording correction |

### Documentation Files

| File | Purpose |
|------|---------|
| `_bmad-output/implementation-artifacts/9-5-frontend-nav-shell-add-skill-assignments-entry.md` | Story file — 5 ACs, 6 Scope Notes, Dev Notes, Dev Agent Record, Review Findings section |
| `documentation/ImplementationStepsForStory9-5.md` | This file |

### Not Changed (by design)

- Any backend file (`backend/`) — this story is entirely frontend
- `frontend/src/App.tsx` — both routes (`/dashboard`, `/hr/dashboard`) and their `<RequireAuth>` wrapping already existed
- `frontend/src/pages/hr/Dashboard.tsx`, `frontend/src/features/dashboard/DashboardPage.tsx` — neither page references the nav or a "Dashboard" label; their own internal links already hardcode the correct route paths
- `frontend/src/lib/auth/RequireAuth.tsx` — read as evidence for a code-review finding, not modified; the app-wide missing role-gate it exposes is logged as a deferred item, out of this story's scope

---

## Implementation Workflow Summary

### Phase 1: Story Creation
**Skill:** `bmad-create-story`
- Read `epics.md`'s Story 9.5 AC text (4 ACs, frontend-only), `prd.md`'s FR-29/UJ-1/§4.10 sections, and the current frontend's real nav/routing machinery directly
- Resolved a real PRD/epics drift before it could become a silent epic-completion gap: `Login.tsx`'s post-login redirect still targeted the old full-grid route, contradicting the PRD's own already-updated entry-state journey
- 6 numbered Scope Notes written, including the exact before/after `NAV_LINKS` arrays and an explicit "do not touch" list
- Status → `ready-for-dev`

### Phase 2: Implementation
**Execution:** Amelia persona, frontend-only (confirmed via `AskUserQuestion` before starting)
- 4 tasks executed in sequence: nav repoint → redirect fix → tests → full regression
- True TDD: tests updated and confirmed RED (3 failing) before any production code change
- Full regression: 422 passed (421 baseline + 1 new), zero regressions; live-verified end-to-end via Playwright against a rebuilt Docker container
- Story marked `review`

### Phase 3: Code Review + Decision + Patches
**Skill:** `bmad-code-review`
- 3 parallel adversarial layers (Blind Hunter, Edge Case Hunter, Acceptance Auditor — the auditor also given `epics.md` and `prd.md`) against the uncommitted diff
- 15 unique findings after triage: 1 decision-needed (resolved by the user), 5 patched, 2 deferred, 7 dismissed after direct verification
- The most consequential finding was a documentation-accuracy defect, not a code bug: this story's own record inaccurately claimed frontend role-gating existed, disproven by reading `RequireAuth.tsx` directly
- Full regression re-verified after patches: 423 passed (421 baseline + 2, up from 1), zero regressions
- Story marked `done`; **Epic 9 flipped to `done`** — all 5 stories complete

---

## Test Coverage

### New/Extended Test Files

- `HrAppShell.test.tsx` — 7 total tests (5 pre-existing + 2 net new for this story):
  - `renders all four nav destinations, in order, and the page content` (renamed/extended from Story 7.7's original 3-destination test; code-review patch added the DOM-order assertion)
  - `marks Dashboard active with the same treatment when on the landing page route` (code-review patch — the AC2 coverage gap)
  - `marks Skill Assignments active with the same treatment when on the full grid route` (implementation-phase new test)
- `Login.test.tsx` — 7 total tests (6 pre-existing + 0 net new, 1 renamed/re-targeted for this story):
  - `redirects an HR_ADMIN to the Skill Assignment Dashboard on successful login` (renamed from "...to the HR dashboard...", asserted target changed to `/dashboard`)

### Regression Verification

- Frontend: 421 → 422 (implementation) → 423 (code review patches) passed, 0 failed throughout
- `tsc --noEmit`: 31 pre-existing errors at every checkpoint (confirmed as the exact baseline before starting, not assumed), none in this story's files
- `vite build`: clean at every checkpoint, 537 modules throughout (no new files created)
- Live verification (Playwright, installed ad hoc, removed after use, against a rebuilt Docker `talentpilot-ui` container): full login → nav-order → both-destination-active-state → mobile-hamburger flow walked with real data; two script-level (not application-level) bugs caught and fixed mid-verification by inspecting the real rendered DOM directly

---

## Architecture Decisions Implemented

| Decision | Implementation | Files Affected |
|----------|---|---|
| **Frontend-only scope** | Verified both `/dashboard` and `/hr/dashboard` already existed and were already wrapped in `<RequireAuth>` in `App.tsx`, directly against the live route table before any implementation began; zero backend files touched | (verification only, no backend files) |
| **AC1: 4-entry nav, exact order** | `NAV_LINKS` array is a pure data change consumed by an already-correct `.map()` render loop; no new JSX/state/CSS | `frontend/src/components/layout/HrAppShell.tsx` |
| **AC2/UX-DR47: Dashboard repoint** | `Dashboard`'s `to` changed to `/dashboard`, `testId` reused unchanged | `frontend/src/components/layout/HrAppShell.tsx` |
| **AC3/UX-DR48: new Skill Assignments entry** | New `NAV_LINKS` entry, `to: '/hr/dashboard'`, new `testId: 'app-nav-link-skill-assignments'` | `frontend/src/components/layout/HrAppShell.tsx` |
| **AC5 (added this story): PRD UJ-1 post-login entry state** | `Login.tsx`'s HR_ADMIN ternary branch repointed to `/dashboard` | `frontend/src/pages/Login.tsx` |
| **Documentation must not overstate security posture** (code review) | Corrected "role-gated" → "wrapped in `<RequireAuth>`" (authentication-only) everywhere the inaccurate claim appeared; underlying gap logged as deferred, not silently left inaccurate | `_bmad-output/implementation-artifacts/9-5-...md`, `_bmad-output/project-context.md`, `_bmad-output/implementation-artifacts/sprint-status.yaml` |

---

## Key Technical Achievements

✅ **Ran the full create → implement → review → decide → patch pipeline in one continuous session**, correctly identifying the story as entirely frontend-only from the outset via a proactive `AskUserQuestion` scope check
✅ **Resolved a real PRD/epics drift before it caused a silent epic-completion gap** — `Login.tsx`'s post-login redirect still targeted the old full-grid route, found and fixed as this story's own Task 2/AC5
✅ **Verified a new test assertion actually catches a real regression, not just trusting its shape** — temporarily swapped two `NAV_LINKS` entries during code review, confirmed the new order test failed, then restored and confirmed green again
✅ **Code review caught a genuine documentation-accuracy defect, not a code bug** — this story's own record inaccurately claimed frontend role-gating existed; disproven by reading `RequireAuth.tsx` directly rather than repeating an unverified claim into the permanent project history
✅ **A genuine scope-boundary question was surfaced to the user rather than silently resolved either way** — the `Login.tsx` change exceeded the literal `AskUserQuestion` scope confirmation; presented as a decision-needed item, resolved explicitly, and captured as a process lesson for future stories
✅ **Two reviewer "deletion risk" findings verified unfounded via direct `grep`, not accepted on the reviewer's own stated low confidence alone**
✅ **Zero regressions across every regression run in the session** — 421 → 422 → 423, with the same 31 pre-existing `tsc` errors at every checkpoint
✅ **Epic 9 (Skill Assignment Dashboard) fully complete** — all 5 stories (org-wide stats, employee segmentation, landing page, Needs Attention popover/drill-down, and now the nav shell repoint) done

---

## Deferred Items (Not Story 9-5 Scope)

From this story's own code review, logged in `deferred-work.md`:
- **No frontend role-based route gate exists on any HR page** (`/dashboard`, `/hr/dashboard`, `/skills`, `/employees`) — `RequireAuth.tsx` checks authentication only; access control relies entirely on backend 403 responses plus each page's own Error-state UI. Real, pre-existing, app-wide gap, established at least since Story 9.3, not introduced or worsened by this story. Revisit as its own scoped decision (defense-in-depth, or to avoid a visible Error-state flash for the wrong role) rather than folding into a nav-relabeling story.
- **`Login.tsx`'s redirect change is verified only via a mocked `navigateMock` assertion**, not an integration-level check that `/dashboard` actually renders the right component — matches this test file's pre-existing pattern since Story 1.x. Revisit only if a route-table typo in `App.tsx` is ever a real concern.

Carried forward from earlier epics, unaffected by this story:
- `EmployeeSegmentationResponse.needs_attention`'s unbounded list growth (Story 9.2's own already-logged deferral) — irrelevant to this story's scope.
- `auth/repository.py::authenticate()` still does not read `Account` (Epic 7's own flagged gap) — irrelevant to this story's scope.

---

## Conclusion

Story 9-5 is **✅ DONE** after a full create-then-implement-then-review-decide-and-patch cycle, run start to finish in one session:

- All 5 acceptance criteria satisfied — the left-pane nav shows exactly four entries in the correct order, "Dashboard" opens the new landing page, "Skill Assignments" opens the existing unfiltered full grid, no backend/API code was touched, and the post-login HR Admin redirect now matches the PRD's own updated entry-state journey — verified by 2 net-new dedicated frontend tests plus a full 423-test regression pass, both before and after the code-review patches, and live-verified end-to-end against a rebuilt Docker container
- Code review surfaced 15 findings: 1 requiring a human decision (resolved, with a process lesson recorded), 5 patched (the most consequential being a documentation-accuracy defect this story's own record had introduced, corrected everywhere it appeared), 2 correctly deferred as real-but-pre-existing app-wide gaps, and 7 dismissed after direct verification
- Zero regressions across every regression run in the session (421 → 422 → 423 passed)
- **Not yet committed to git** — working tree still uncommitted as of this document, on top of `HEAD` at `89008eb1` ("Story 9.4: Frontend Needs Attention Popover & Drill-Down (FR-33/UX-DR45/46)")

**Epic 9 status:** ✅ **`done`** — all 5 stories (9.1 backend stats, 9.2 backend segmentation, 9.3 landing page, 9.4 popover/drill-down, 9.5 nav shell) are complete. `epic-9-retrospective` remains `optional`, now unblocked.
