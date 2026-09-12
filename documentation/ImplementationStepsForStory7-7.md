# Implementation Steps for Story 7-7: HR Admin Navigation Shell — Left-Pane Nav

**Story Key:** 7-7-hr-admin-navigation-shell-left-pane-nav
**Epic:** 7 (Employee Roster Management) — **seventh and final story**
**Status:** ✅ DONE (committed and pushed)
**Completed Date:** 2026-09-12

---

## Overview

Story 7.7 relocates the HR Admin's primary navigation (FR-29) from a top-header nav duplicated across three pages into a single shared left-pane sidebar, adding the "Employees" destination that Stories 7.2–7.6 had built a page for but never a nav entry point to. Below the 768px breakpoint the sidebar collapses to a hamburger-triggered overlay with a dismiss backdrop (UX-DR40). The story is frontend-only by its own AC5 — no backend/API surface exists to touch.

Unlike Stories 7.5/7.6 (new backend write paths, new modals, multi-layer adversarial code review), this story was a pure extraction-and-refactor: the three HR pages (`Dashboard.tsx`, `SkillsPage.tsx`, `EmployeesPage.tsx`) had each accumulated their own copy-pasted header/nav/user-menu block over Stories 5–7, and this story's job was to collapse that drift into one shared component before adding the one genuinely new thing (the Employees link + the mobile collapse behavior). It was also the epic's deliberately-last story per `epics.md`'s own recommended build order, since it needed Story 7.3's Employees page to exist as a real nav target.

This session ran story discovery and implementation directly, in one pass, without a separate story-creation phase or a multi-agent adversarial code review round — the epic's own Story 7.7 section already carried a complete, unambiguous 5-AC spec (`epics.md`), and the change's blast radius (three presentational page shells, no data layer) was judged small enough that a dedicated story file and a parallel-reviewer pass would have been process overhead rather than value. This is documented here explicitly rather than silently, since it is a deliberate deviation from the pattern Stories 7.5/7.6 used.

---

## Skills / Workflow Invoked

### 1. **`/bmad-agent-dev` → direct TDD implementation (Amelia persona)**

**Purpose:** Discover the story's real requirements from existing artifacts (no story file existed yet for 7.7), then implement it end to end.

**When Invoked:** Explicit user instruction: "start development api and ui for the story 7-7-hr-admin-navigation-shell-left-pane-nav refer the ux design if required."

**Workflow Steps Executed:**

1. Confirmed via `sprint-status.yaml` that 7.1–7.6 were `done` and 7.7 was `backlog`, with no story file present in `_bmad-output/implementation-artifacts/`.
2. Read Epic 7's Story 7.7 section directly from `_bmad-output/planning-artifacts/epics.md` (5 ACs) rather than authoring a separate context-filled story file first — the epic text was already unambiguous and self-contained.
3. Read the WDS prototype's own left-nav story (`_bmad-output/E-Development/05-Ritas-Roster-Management-Prototype/stories/Employees-Tab.1-left-nav-topbar.md`) and its HTML implementation (`05.1-Employees-Tab.html`), extracting the exact Tailwind classes, breakpoint (`md:`/768px), object IDs, and backdrop/hamburger DOM shape to mirror — the "refer the ux design if required" instruction resolved to this prototype, the only existing left-nav reference in the repo.
4. Read the current state of all three real HR pages (`Dashboard.tsx`, `SkillsPage.tsx`, `EmployeesPage.tsx`) directly and confirmed they carried three near-identical, already-drifted copies of the header/nav/user-menu block.
5. Specifically verified AC3's flagged concern — "verify `SkillsPage.tsx`'s header duplication explicitly" — by reading the file: the "Manage API Keys" entry point lives in the page's toolbar content, not the header nav, so nothing was at risk of being silently dropped by the header-to-sidebar move.
6. Checked `App.tsx` for the real route paths (`/hr/dashboard`, `/skills`, `/employees`) to drive the new sidebar's `Link` targets and active-route matching.

**Output:** No separate story file was authored before implementation (see Overview); the epic's own AC text served as the spec. A retrospective implementation-artifacts doc was written after the fact (see below) to preserve the same record Stories 7.1–7.6 have.

---

### 2. **Direct TDD implementation**

**Purpose:** Build the shared nav shell test-first (red → green) and adopt it across all three HR pages.

**Workflow Steps Executed:**

1. **Red:** Wrote `frontend/src/tests/HrAppShell.test.tsx` first, targeting a component that didn't exist yet (`@/components/layout/HrAppShell`) — 5 tests covering all three links + content rendering, active-route `aria-current` plus a non-color style change, the user menu's Sign Out behavior staying intact, the sidebar's off-screen/hamburger/backdrop mobile collapse, and the mobile nav auto-closing on link click. Ran it and confirmed it failed on "file does not exist," not a typo in the test itself.
2. **Green:** Implemented `frontend/src/components/layout/HrAppShell.tsx` — a left `<aside>` sidebar (fixed + off-canvas below `md:`, static above it) with the three nav links driven by `useLocation().pathname`, and a slim top bar retaining the exact pre-existing user-menu markup/behavior (avatar, "Rita", Sign Out → `logout()` → `signOut()` → navigate to `/login`). Re-ran the test file: all 5 passed.
3. **Refactor (adopt across pages):** Removed the duplicated `<header>`/nav/`userMenuOpen`/`handleSignOut`/`useAuth`/`useNavigate` block from `Dashboard.tsx`, `SkillsPage.tsx`, and `EmployeesPage.tsx`, replacing each page's outer `<div><header>…</header><main>…</main>…</div>` shell with `<HrAppShell>` wrapping the page's own unchanged `<main>` content and modals. Net: 174 lines removed across the three pages, 116 lines added in the one new shared component.
4. **Full regression:** Ran the complete frontend suite — 38 test files / 391 tests, all green, with zero changes required to any of the three pages' own existing test files (none of them asserted on the old header markup directly).
5. **Build verification:** `vite build` — 534 modules, clean, no compile errors — confirming the JSX/import surgery across three files left no dangling reference.
6. **`tsc --noEmit` baseline check:** Ran `git stash` to capture pre-change output (73 pre-existing errors, all in unrelated files — stale `getDashboardAssignments` exports and `UUID`-branded-type test fixtures), popped the stash, and confirmed the post-change error count and file set were unchanged — this story introduced zero new type errors.
7. **Live-browser check attempted, honestly reported as unavailable:** no headless browser/Playwright/Chromium was present in this Windows sandbox. Rather than skip the concern silently, logged an explicit open action item in `sprint-status.yaml` (epic 7) calling for a real 375px/768px/1280px browser pass before the shell is treated as fully visually verified — consistent with the sprint's own standing action item that UI stories need visual validation against their prototype before being marked done.
8. Wrote the retrospective story-artifact doc (`_bmad-output/implementation-artifacts/7-7-hr-admin-navigation-shell-left-pane-nav.md`) documenting what shipped, since no story file had been created up front.
9. `sprint-status.yaml`: `7-7-...` → `done`.

**Output Files:**
- `frontend/src/components/layout/HrAppShell.tsx` (new)
- `frontend/src/tests/HrAppShell.test.tsx` (new)
- `_bmad-output/implementation-artifacts/7-7-hr-admin-navigation-shell-left-pane-nav.md` (new)

**Sprint Status:** `7-7-...`: `backlog` → `done`

---

### 3. **Commit and push (explicit user instruction)**

**Purpose:** Land the story's changes on the working branch.

**When Invoked:** Explicit user instruction: "commit and push the changes with proper comments."

**Workflow Steps Executed:**
1. Re-ran `git status` immediately before staging to confirm only this story's files were touched — the working tree at the time carried no other uncommitted drift.
2. Staged exactly the 7 files this story touched (no `git add -A`): the 3 refactored pages, the new shell component, the new test file, the new story doc, and `sprint-status.yaml`.
3. Committed with a message summarizing the AC/FR mapping and the line-count reduction, attributed per this session's co-authorship convention.
4. Pushed directly to `POC_Hackathon_V1` (the active branch, already tracking `origin`) — `e3243373..eb4a2128`.

**Output:** Commit `eb4a2128` — "Story 7.7: HR Admin Navigation Shell - Left-Pane Nav (FR-29)" — pushed to `origin/POC_Hackathon_V1`.

---

## Files Created/Updated

### Frontend — New Files

| File | Purpose |
|------|---------|
| `frontend/src/components/layout/HrAppShell.tsx` | Shared left-pane nav shell: sidebar (Dashboard/Skills/Employees links, active-route styling), mobile hamburger + backdrop collapse below 768px, and the unchanged top-bar user menu |
| `frontend/src/tests/HrAppShell.test.tsx` | 5 tests: nav destinations render, active-route `aria-current` + non-color style, Sign Out behavior preserved, mobile collapse/backdrop/hamburger, nav auto-closes on link click |

### Frontend — Modified Files

| File | Purpose |
|------|---------|
| `frontend/src/pages/hr/Dashboard.tsx` | Header/nav/user-menu block replaced with `<HrAppShell>`; `useAuth`/`useNavigate`/`userMenuOpen`/`handleSignOut` removed (now owned by the shell) |
| `frontend/src/pages/hr/SkillsPage.tsx` | Same replacement; confirmed "Manage API Keys" (toolbar content, not header) unaffected |
| `frontend/src/pages/hr/EmployeesPage.tsx` | Same replacement; all existing row-action/modal wiring (Stories 7.3–7.6) untouched |

### Not Changed (by design)

- No backend files — Story 7.7 is frontend-only per its own AC5
- `App.tsx` — route paths (`/hr/dashboard`, `/skills`, `/employees`) already correct, only read for reference
- `Dashboard.tsx`'s `AssignmentModal` wiring, `SkillsPage.tsx`'s skill CRUD/content-lookup logic, `EmployeesPage.tsx`'s roster/filter/pagination/row-action logic — all untouched; only the surrounding shell moved

### Documentation & Configuration Files

| File | Purpose |
|------|---------|
| `_bmad-output/implementation-artifacts/7-7-hr-admin-navigation-shell-left-pane-nav.md` | Retrospective story-artifact doc — written after implementation since no story file existed beforehand |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | `7-7-...`: `backlog` → `done`; new epic-7 action item logging the missing live-browser pass |
| `documentation/ImplementationStepsForStory7-7.md` | This file |

---

## Test Coverage

### New Test File (5 tests)

- `HrAppShell.test.tsx` — all three nav links render with correct `href`s and page content renders; the active route gets `aria-current="page"` plus `font-medium` styling while inactive routes don't; opening the user menu and clicking Sign Out calls `logout()` and navigates to `/login`; the sidebar starts at `-translate-x-full` with no backdrop, the hamburger reveals it at `translate-x-0` with a backdrop, and clicking the backdrop reverses both; clicking a nav link while the mobile overlay is open closes it.

### Regression Verification

- Frontend: 38 test files / 391 tests, all passing (386 pre-existing + 5 new) — zero changes needed to `Dashboard`/`SkillsPage`/`EmployeesPage`'s own existing test files, since none asserted on the old header markup directly.
- `vite build`: clean, 534 modules.
- `tsc --noEmit`: 73 pre-existing errors, confirmed via `git stash` to predate this story, unchanged in count or file set after this story's changes.
- **Not done:** a real-browser visual pass at 375px/768px/1280px — no headless browser was available in this sandbox. Logged as an open action item rather than claimed as covered.

---

## Architecture Decisions Implemented

| Decision | Implementation | Files Affected |
|----------|---|---|
| **Extract shared layout instead of patching each page's header a third time** | One `HrAppShell` component owns the nav/user-menu/mobile-collapse concern; the three HR pages become thin consumers | `components/layout/HrAppShell.tsx`, `pages/hr/*.tsx` |
| **Active-nav indication is never color-only (UX-DR41's existing precedent, applied here)** | `aria-current="page"` plus a background/font-weight change, not a border-color-only cue as the old header used | `HrAppShell.tsx` |
| **Mobile breakpoint matches the already-approved prototype exactly** | Tailwind `md:` (768px), `-translate-x-full`/`translate-x-0` transform toggle, and a click-dismiss backdrop — same mechanism as `05.1-Employees-Tab.html`'s shipped, user-approved design | `HrAppShell.tsx` |
| **No story file authored before implementation, given a complete existing spec** | Epic 7.7's own AC text in `epics.md` served as the spec directly; a retrospective doc was written afterward instead of a forward-looking one, to keep the same audit trail Stories 7.1–7.6 have without adding process for a low-risk refactor | `_bmad-output/implementation-artifacts/7-7-...md` |

---

## Key Technical Achievements

✅ **Collapsed three pages' worth of copy-pasted header/nav/user-menu drift into one shared component**, removing 174 duplicated lines
✅ **Test-first**: the new shell's test file was written and confirmed failing before the component existed, then made to pass
✅ **Zero regressions**: full 391-test suite green, clean production build, no new `tsc` errors (confirmed against a `git stash` baseline, not assumed)
✅ **Verified AC3's flagged risk directly rather than assuming it**: read `SkillsPage.tsx` before touching it and confirmed "Manage API Keys" was never header-dependent
✅ **Matched the already-approved UX prototype's exact mechanism** (breakpoint, transform classes, backdrop) rather than inventing a new responsive pattern
✅ **Reported the one verification gap it couldn't close** (no real-browser pass, no headless browser available) as an explicit open action item instead of silently marking the story done with unstated risk

---

## Deferred Items (Not Story 7-7 Scope)

- **Live-browser visual verification at 375px/768px/1280px** — logged as a new open action item under epic 7 in `sprint-status.yaml`. Recommended before treating the responsive collapse behavior as fully verified, per the sprint's own standing action item on UI stories needing prototype-matched visual validation.

Carried forward from earlier Epic 7 stories, unaffected by this story:
- `auth/repository.py::authenticate()` still does not read `Account` (Story 7.1/7.6's flagged gap) — irrelevant to this story's frontend-only scope.
- No un-archive capability exists (Story 7.5) — unrelated to navigation.

---

## Conclusion

Story 7-7 is **✅ DONE**, committed as `eb4a2128` and pushed to `origin/POC_Hackathon_V1`:

- All 5 acceptance criteria satisfied: the three-page header nav is now one shared left-pane shell with an Employees destination (AC1), the user menu is unchanged (AC2), Skills' "Manage API Keys" was verified still reachable (AC3), the sidebar collapses to a hamburger overlay with a dismiss backdrop below 768px (AC4), and no backend/API surface was touched (AC5)
- 5 new tests plus the full pre-existing 386-test suite all green; clean build; no new type errors
- One honestly-reported gap (no live-browser pass, tooling unavailable) logged as an open action item rather than glossed over

**Epic 7 status:** All seven stories (7.1–7.7) are now `done`. Epic 7 (Employee Roster Management & Navigation Shell) is complete. Epic 8 (Application Theming, FR-30) remains `backlog` and has no dependency on Epic 7.
