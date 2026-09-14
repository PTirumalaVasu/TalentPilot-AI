---
baseline_commit: 89008eb1
---

# Story 9.5: Frontend: Nav Shell — Add "Skill Assignments" Entry

Status: done

## Story

As an **HR Admin**,
I want the full assignment grid to keep its own clear place in the nav,
so that relocating "Dashboard" to the new landing page doesn't cost me access to the detailed view I already rely on (FR-29 amendment, UX-DR47, UX-DR48).

## Scope Notes (read before starting)

1. **Frontend-only. Zero backend/API changes.** Epic 9's other four stories (9.1/9.2 backend, 9.3/9.4 frontend) already shipped both consumed endpoints and both pages this story links between. This story only repoints existing nav entries — no new component, no new route, no new endpoint.

2. **This is a small, surgical change to exactly one file's data, plus its test file, plus one pre-existing but undocumented gap (Task 2 below).** `frontend/src/components/layout/HrAppShell.tsx`'s `NAV_LINKS` array (lines 15-19) currently has 3 entries:
   ```
   { to: '/hr/dashboard', label: 'Dashboard', testId: 'app-nav-link-dashboard' },
   { to: '/skills', label: 'Skills', testId: 'app-nav-link-skills' },
   { to: '/employees', label: 'Employees', testId: 'app-nav-link-employees' },
   ```
   Change to 4 entries, in this exact order (epics.md AC1: "Dashboard, Skill Assignments, Skills, Employees"):
   ```
   { to: '/dashboard', label: 'Dashboard', testId: 'app-nav-link-dashboard' },
   { to: '/hr/dashboard', label: 'Skill Assignments', testId: 'app-nav-link-skill-assignments' },
   { to: '/skills', label: 'Skills', testId: 'app-nav-link-skills' },
   { to: '/employees', label: 'Employees', testId: 'app-nav-link-employees' },
   ```
   **Both routes already exist and are already wrapped in `<RequireAuth>`** — `App.tsx` already registers `/dashboard` → `SkillAssignmentDashboard` (Story 9.3) and `/hr/dashboard` → `Dashboard` (the full grid), both behind `<RequireAuth>`. **Correction applied during code review: `<RequireAuth>` gates authentication only — it has no role check (see `RequireAuth.tsx`) — so this is not frontend role-gating; access control for HR-only data comes from the backend's own 403 responses, same as every other HR page today.** This story does not touch `App.tsx`, either page component, or auth gating. **Do not rename or move either route** — only which label/nav-link points at which existing path changes.

3. **`app-nav-link-dashboard`'s `testId` is reused for the relabeled "Dashboard" entry (now pointing at `/dashboard`) — do not rename it.** `HrAppShell.tsx`'s render loop (`NAV_LINKS.map(...)`) auto-derives everything from the array; you only edit the array, not the render logic. Only `app-nav-link-skill-assignments` is a genuinely new testId, for the new 4th entry.

4. **Real, undocumented consequence found while researching this story — not in epics.md's AC text, but required for the system to work end-to-end (see workflow's own "leave the system working end-to-end" rule): `Login.tsx`'s post-login redirect for `HR_ADMIN` still hardcodes `/hr/dashboard`** (`frontend/src/pages/Login.tsx` line 43: `navigate(role === 'HR_ADMIN' ? '/hr/dashboard' : '/employee/content', { replace: true })`). The PRD's own UJ-1 user journey (`prd.md` line 40) explicitly states the HR Admin's **entry state is now "Authenticated, on the Skill Assignment Dashboard (§4.10)"** — "previously she landed directly on the full row grid described below." §4.10's glossary entry for "Readiness Dashboard" (`prd.md` line 76) says the same: "this is no longer the HR Admin's first screen." No other Epic 9 story touches `Login.tsx`, and this story is the last one in the epic — if this redirect isn't updated here, the epic ships with HR Admins still landing on the full grid post-login, directly contradicting the PRD's own already-updated UJ-1. **Task 2 below fixes this as part of this story**, scoped tightly (one ternary branch, one test assertion) — not a reinterpretation of epics.md's AC text, which is silent on Login.tsx rather than forbidding it (contrast with this story's explicit "frontend-only, HrAppShell.tsx" framing, which is about backend/API scope, not about which frontend files are in bounds).

5. **No dedicated UX design spec exists for this story** (unlike Stories 9.3/9.4's `06.1-skill-assignment-dashboard.md`). PRD FR-29's own `[NOTE FOR PM]` (line 463) says the nav pane's layout has no UX scenario/prototype — "no separate accessibility statement needed" beyond the existing blanket WCAG 2.1 AA commitment. The complete spec for this story is epics.md's own AC text + UX-DR47/UX-DR48 (both defined inline in epics.md's Design Decisions register, not a separate file) + Story 7.7's already-shipped nav pattern (`HrAppShell.tsx`, read in full below) — this is a relabeling of an existing, already-accessible pattern, not new UX design work.

6. **Do not touch**: `App.tsx` (routes unchanged), `SkillAssignmentDashboard.tsx` or `Dashboard.tsx`/`DashboardPage.tsx` (both pages unchanged — their own internal links, e.g. the Empty-state "+ New Assignment" CTA and the Needs Attention popover's `/hr/dashboard?assignmentId=...` links, already correctly target the full-grid route by path, not by nav label, so they need no change), any backend file, `ThemeToggle`/user-menu (Story 8.1/7.7, unrelated).

## Acceptance Criteria

**AC1 — Four nav entries, in order (FR-29 amendment):**
**Given** the existing left-pane nav (Story 7.7: Dashboard, Skills, Employees)
**When** this story ships
**Then** it shows four entries — Dashboard, **Skill Assignments**, Skills, Employees — in that order, with the same active-state/keyboard/aria-label treatment Story 7.7 already established for the other three (no new pattern invented).

**AC2 — "Dashboard" now opens the landing page (UX-DR47):**
**Given** the "Dashboard" link
**When** it is clicked
**Then** it opens the new Skill Assignment Dashboard (Story 9.3, route `/dashboard`) — it no longer opens the full grid directly, which is the one behavior change to an already-shipped nav entry this story makes.

**AC3 — "Skill Assignments" opens the existing full grid, unfiltered (UX-DR48):**
**Given** the new "Skill Assignments" link
**When** it is clicked
**Then** it opens the existing full Readiness Dashboard grid (route `/hr/dashboard`), completely unfiltered, exactly as it rendered before this epic — UJ-1's already-validated "scan 15-20 rows" flow is unchanged, just relocated one nav click.

**AC4 — Frontend-only (AR-26 framing):**
**And** this story is frontend-only (`HrAppShell.tsx` per Story 7.7's precedent) — no backend/API change.

**AC5 — Post-login landing matches the PRD's updated UJ-1 (added by this story, Scope Note 4):**
**Given** an HR Admin successfully logs in
**When** the login redirect fires
**Then** they land on `/dashboard` (the Skill Assignment Dashboard), not `/hr/dashboard` — matching PRD UJ-1's "Entry state: Authenticated, on the Skill Assignment Dashboard."

## Tasks / Subtasks

- [x] **Task 1: Repoint and extend the nav** (AC1, AC2, AC3, AC4) — `frontend/src/components/layout/HrAppShell.tsx`
  - [x] Update `NAV_LINKS` exactly as shown in Scope Note 2 (4 entries, order Dashboard/Skill Assignments/Skills/Employees; `Dashboard`'s `to` becomes `/dashboard`, its `testId` stays `app-nav-link-dashboard`; new `Skill Assignments` entry has `to: '/hr/dashboard'`, `testId: 'app-nav-link-skill-assignments'`).
  - [x] No other change to this file — active-state logic (`location.pathname === link.to`), rendering, mobile-nav-close-on-click, and the top-bar/user-menu are all untouched and correctly generalize to 4 entries with zero code changes (confirmed by reading the `.map()` loop, Scope Note 3). Also updated the file's own header doc comment to describe the 4-entry nav and the two distinct `/dashboard`/`/hr/dashboard` destinations.

- [x] **Task 2: Fix post-login landing redirect** (AC5, Scope Note 4) — `frontend/src/pages/Login.tsx`
  - [x] Line 43: changed `navigate(role === 'HR_ADMIN' ? '/hr/dashboard' : '/employee/content', { replace: true });` to `navigate(role === 'HR_ADMIN' ? '/dashboard' : '/employee/content', { replace: true });`.
  - [x] No other change to this file.

- [x] **Task 3: Tests** (all ACs) — `frontend/src/tests/HrAppShell.test.tsx`, `frontend/src/tests/Login.test.tsx`
  - [x] `HrAppShell.test.tsx`: updated the existing `'renders all three nav destinations...'` test (renamed to "all four") to assert all four — `app-nav-link-dashboard` → `/dashboard`, `app-nav-link-skill-assignments` → `/hr/dashboard`, `app-nav-link-skills` → `/skills`, `app-nav-link-employees` → `/employees`.
  - [x] `HrAppShell.test.tsx`: added a new test asserting `app-nav-link-skill-assignments`'s active-state treatment (`aria-current="page"`, `font-medium` class) when rendered at `/hr/dashboard`, mirroring the existing `/employees` active-state test — confirms AC1's "same active-state... treatment" for the new entry.
  - [x] `HrAppShell.test.tsx`: the mobile-nav-closes-on-click test (clicks `app-nav-link-skills`) required no change — re-ran, still passes.
  - [x] `Login.test.tsx`: updated `'redirects an HR_ADMIN to the HR dashboard...'` → renamed to `'redirects an HR_ADMIN to the Skill Assignment Dashboard on successful login'`, asserted target changed from `/hr/dashboard` to `/dashboard`.
  - [x] Confirmed no test changes needed in `SkillAssignmentDashboard.test.tsx` or `DashboardPage.test.tsx`/`Dashboard.test.tsx` — neither page's own internal links change (Scope Note 6); full regression run (Task 4) confirms zero incidental breakage there.
  - [x] Red phase confirmed before implementation: 3 tests failed as expected (2 `HrAppShell.test.tsx`, 1 `Login.test.tsx`) against the unmodified source.

- [x] **Task 4: Regression check**
  - [x] `npx vitest run` — 422/422 passing (421 baseline + 1 net new test: +1 new `HrAppShell` active-state test, 1 `Login` test renamed not added), 0 regressions.
  - [x] `npx tsc --noEmit` — 31 errors, unchanged from the pre-existing baseline; none in any file this story touched.
  - [x] `npx vite build` — clean, 537 modules (unchanged — no new files created).
  - [x] Live-verified via Playwright (Chromium, installed ad hoc via `npm install --no-save playwright` + `npx playwright install chromium`, fully removed after use via `npm uninstall playwright` + `git checkout -- package-lock.json`) against a freshly rebuilt `talentpilot-ui` Docker container (found unhealthy/stale at session start, matching Stories 9.3/9.4's documented trap — rebuilt via `docker compose build frontend && docker compose up -d frontend`). All 12 checks passed as HR Admin (`rita@sails.example.com`): post-login lands on `/dashboard` (AC5); all 4 nav entries render in order; "Dashboard" link points at `/dashboard` and is marked active there (AC2); clicking "Skill Assignments" opens `/hr/dashboard` and is marked active there, rendering the full unfiltered grid — both seeded Employees (Casey the Continuer, Sam the Stellar) visible (AC3); Skills/Employees nav unchanged; clicking "Dashboard" again from elsewhere returns to the landing page, not the full grid; at a 375px mobile viewport, the hamburger overlay shows all 4 entries and closes on link click.

### Review Findings

_(`bmad-code-review`, 2026-09-14, 3 parallel adversarial layers — Blind Hunter, Edge Case Hunter, Acceptance Auditor, run against the uncommitted diff with this story file as spec context.)_

- [x] [Review][Decision] `Login.tsx`'s redirect change (Task 2/AC5) touched an auth-flow file without literal coverage from the `AskUserQuestion` scope confirmation — The option the user selected ("Proceed frontend-only (Recommended)") was described as "implement the `HrAppShell.tsx` nav changes... No backend work" — it never mentioned `Login.tsx`. The Acceptance Auditor independently verified the change is well-justified (traces cleanly to the PRD's UJ-1/§4.10 updates, and epics.md's own stale generic login AC — line 510 — never pinned a specific route) and not backend/API scope creep. **Resolved by user during code review (2026-09-14): keep as shipped, explicitly flagged.** The user confirmed the `Login.tsx` redirect change should stand as implemented — no code change — but this note records, for the permanent record, that this specific expansion (an authentication-flow redirect affecting every HR Admin login) went beyond what the earlier `AskUserQuestion` scope confirmation literally covered, and was only retroactively approved during this code-review pass rather than before implementation. **Process lesson for future stories:** when a story's own research surfaces a judgment call that expands into a file/behavior category not covered by an earlier scope question (auth, security, cross-cutting config), raise a fresh `AskUserQuestion` before implementing it, even if the earlier answer was "proceed frontend-only" — don't fold it into the story unannounced, however well-justified.
- [x] [Review][Patch] Inaccurate "already role-gated" claim in this story's References section and in `project-context.md`/`sprint-status.yaml` prose — `frontend/src/lib/auth/RequireAuth.tsx` only checks `auth.status === 'authenticated'`, with zero role branching; there is no frontend route-level role gate on `/dashboard` or `/hr/dashboard` (confirmed by reading the file directly). This is pre-existing, app-wide behavior — Story 9.3 already established the identical pattern for `/dashboard` (relying on the backend's 403 + an Error-state UI, not a frontend guard) — not a regression introduced by this diff. **Fixed:** corrected the wording in this story's Scope Note 2/References, `project-context.md`, and `sprint-status.yaml` to say "wrapped in `<RequireAuth>`" (authentication-only) instead of "role-gated," with a note pointing to the deferred item below. [_bmad-output/implementation-artifacts/9-5-frontend-nav-shell-add-skill-assignments-entry.md, _bmad-output/project-context.md, _bmad-output/implementation-artifacts/sprint-status.yaml]
- [x] [Review][Patch] No test asserts the one behavior AC2 actually changed — `HrAppShell.test.tsx`'s active-state coverage exists for `/employees` and `/hr/dashboard` (the new Skill Assignments entry) but not for `/dashboard`, the new target of the repointed "Dashboard" link. **Fixed:** added `'marks Dashboard active with the same treatment when on the landing page route'`, asserting `aria-current="page"`/`font-medium` on `app-nav-link-dashboard` at `/dashboard` and no `aria-current` on `app-nav-link-skill-assignments` there. [frontend/src/tests/HrAppShell.test.tsx]
- [x] [Review][Patch] AC1's literal nav order ("Dashboard, Skill Assignments, Skills, Employees ... in that order") has no automated assertion — the "renders all four nav destinations" test uses `getByTestId` lookups, which pass regardless of DOM order. **Fixed:** the renamed `'renders all four nav destinations, in order, and the page content'` test now asserts the sidebar's `nav a` elements' `textContent` equals `['Dashboard', 'Skill Assignments', 'Skills', 'Employees']` in that exact order. Verified this assertion actually catches a real regression by temporarily swapping the first two `NAV_LINKS` entries and confirming the test failed, then restoring the correct order and confirming green again. [frontend/src/tests/HrAppShell.test.tsx]
- [x] [Review][Patch] Stale comment in `SkillAssignmentDashboard.tsx` still says the Dashboard nav link "points at `/hr/dashboard` until Story 9.5 repoints it — a deliberate scope boundary, not a gap." This diff *is* Story 9.5 and *does* repoint it; the comment now documents a future state that has already happened. **Fixed:** updated the comment to past tense ("was repointed to `/dashboard` by Story 9.5"). [frontend/src/pages/hr/SkillAssignmentDashboard.tsx:6-9]
- [x] [Review][Patch] `HrAppShell.tsx`'s new doc comment overclaims — "two distinct destinations, not one page linking to the other" is only true at the *nav* level (matches `prd.md` line 460's precise phrasing); the landing page's own Needs Attention popover (Story 9.4) and Empty-state CTA already deep-link into `/hr/dashboard` at the content level. **Fixed:** reworded to scope the claim explicitly to nav entries, with an added sentence acknowledging the existing content-level deep links. [frontend/src/components/layout/HrAppShell.tsx:11-18]
- [x] [Review/Defer] No frontend role-based route gate exists on any HR page (`/dashboard`, `/hr/dashboard`, `/skills`, `/employees`) — access relies entirely on backend 403 responses plus each page's own Error-state UI. Real, pre-existing, app-wide gap (established at least since Story 9.3), not introduced or worsened by this diff, and out of scope for a nav-relabeling story to fix. [frontend/src/lib/auth/RequireAuth.tsx] — deferred, pre-existing.
- [x] [Review/Defer] `Login.tsx`'s redirect change is verified only via a mocked `navigateMock` assertion, not an integration-level check that `/dashboard` actually renders `SkillAssignmentDashboard` end-to-end — matches this test file's pre-existing pattern from Story 1.x, not something this story introduced. [frontend/src/tests/Login.test.tsx] — deferred, pre-existing test-architecture pattern.
- Dismissed as non-issues after verification: the nav relabeling being "confusing" for existing muscle memory is the literal, explicitly-specified behavior change mandated by epics.md AC2 and the PRD (UX-DR47) — spec-conformant, not a defect; the ad hoc Playwright install/verify/remove pattern being "unreproducible" matches this project's own established convention across every Epic 8/9 story, not a new problem; a "self-attested status transition with no reviewer in this diff" is exactly what this code-review pass is — the review, not a gap; narrative prose in `sprint-status.yaml` comments is a pre-existing project-wide convention, already noted and kept in Story 9.4's own review; `Login.tsx`'s non-`HR_ADMIN` ternary fallback (Edge Case Hunter) is completely unchanged pre-existing logic, and `role` is a validated backend enum (`HR_ADMIN`/`EMPLOYEE` only, since Story 1.3) with no reachable third value; two Edge Case Hunter "deletion risk" findings (other files assuming Dashboard→`/hr/dashboard`, or HR_ADMIN landing on `/hr/dashboard` post-login) were both explicitly low-confidence and verified unfounded via direct grep — no other file in `frontend/src` makes either assumption.

Full regression re-verified after patches: frontend 423/423 (422 baseline + 1 new order/wording-adjacent test — `renders all four...` was renamed/extended in place, `marks Dashboard active...` is the 1 net-new test), `tsc --noEmit` unchanged at 31 pre-existing errors, `vite build` clean.

## Dev Notes

### This is the smallest story in Epic 9 — data-only changes to an already-correct render loop

`HrAppShell.tsx`'s nav is a `.map()` over `NAV_LINKS`; nothing about its rendering, active-state, keyboard, `aria-current`, or mobile-collapse logic is specific to 3 entries. Adding a 4th and repointing one existing entry's `to` is purely a data change (Task 1) — no new JSX, no new state, no new CSS. Story 7.7's own AC1 for the original 3-entry nav already established every visual/interaction pattern this story reuses verbatim.

### Why Task 2 (Login.tsx) is in this story despite epics.md's AC text not mentioning it

Epics.md's Story 9.5 section says "this story is frontend-only (`HrAppShell.tsx` per Story 7.7's precedent)" when describing *layer* (frontend vs. backend), not an exhaustive file allowlist — it doesn't say "and no other frontend file." The PRD (the higher-authority document epics.md itself was derived from) explicitly updated UJ-1's entry state to the new landing page as part of the same 2026-09-12 update that added §4.10/FR-33 (`prd.md` lines 40, 76 — both carry `[UPDATED 2026-09-12]` tags). Since Story 9.5 is the last story in Epic 9, and no other story in the epic touches `Login.tsx`, omitting this fix would leave the epic complete-per-its-own-ACs but still contradicting the PRD it's supposed to realize — a real "leave the system working end-to-end" gap per this workflow's own standing instruction, not scope creep. The fix itself is minimal (one ternary branch) and carries no risk to the EMPLOYEE redirect path, which is untouched.

### Existing pages' internal links already point at the right paths by URL, not by nav label — nothing else needs to change

Verified by reading both consuming pages directly:
- `SkillAssignmentDashboard.tsx`'s Empty-state CTA (`to="/hr/dashboard"`, line 305) and the Needs Attention popover's item links (`` `/hr/dashboard?assignmentId=${...}` ``) already hardcode the full-grid route path — they were written this way by Stories 9.3/9.4 specifically anticipating this story's nav repoint (Story 9.3's own file header comment: "The left-nav 'Dashboard' link still points at `/hr/dashboard` until Story 9.5 repoints it").
- Nothing in `Dashboard.tsx`/`DashboardPage.tsx` references the nav or a "Dashboard" label at all.

So Task 1 + Task 2 are the complete set of production-code changes this story requires.

## Architecture Compliance

- AR-26: read-composition owned by `dashboard/` (backend) — unaffected; zero backend code touched.
- FR-29 (amendment): this story is exactly what completes it — 4-entry left-pane nav, `Dashboard`/`Skill Assignments` as distinct destinations (per `prd.md` line 460's explicit "two distinct, separately-reachable nav destinations, not one page with an internal link to the other").
- FR-33 / §4.10: Task 2 closes the PRD's UJ-1 entry-state gap (see Dev Notes above).

## References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 9.5] — full AC text, this story's exact scope; also UX-DR47/UX-DR48 definitions (Design Decisions register) and the Epic 9 "Recommended build order" note confirming 9.5 is last, dependent on 9.3's `/dashboard` route existing
- [Source: _bmad-output/planning-artifacts/prds/prd-TalentPilot-AI-2026-07-09/prd.md#4.8] — FR-29 full text and consequences, including the `[NOTE FOR PM]` on no dedicated UX spec existing
- [Source: _bmad-output/planning-artifacts/prds/prd-TalentPilot-AI-2026-07-09/prd.md#UJ-1] — updated entry state ("Authenticated, on the Skill Assignment Dashboard"), motivating Task 2
- [Source: _bmad-output/planning-artifacts/prds/prd-TalentPilot-AI-2026-07-09/prd.md#4.10] — Readiness Dashboard glossary update ("no longer the HR Admin's first screen")
- [Source: _bmad-output/implementation-artifacts/9-3-frontend-skill-assignment-dashboard-landing-page.md] — created `/dashboard` route + `SkillAssignmentDashboard.tsx`; its own file header explicitly hands off the nav repoint to this story
- [Source: _bmad-output/implementation-artifacts/9-4-frontend-needs-attention-popover-and-drill-down.md] — added the `/hr/dashboard?assignmentId=...` deep-link this story's Skill Assignments entry must not break; its Scope Note 9/AC5 also explicitly defer nav wiring to this story
- [Source: frontend/src/components/layout/HrAppShell.tsx] — file to modify (`NAV_LINKS`, Task 1)
- [Source: frontend/src/pages/Login.tsx] — file to modify (post-login redirect, Task 2)
- [Source: frontend/src/App.tsx] — confirms both `/dashboard` and `/hr/dashboard` routes already exist and are wrapped in `<RequireAuth>` identically (authentication-only gating — see `RequireAuth.tsx`; no frontend role check exists on either route, correction applied during code review); not modified by this story
- [Source: frontend/src/tests/HrAppShell.test.tsx] — existing test file/mocking pattern to extend (Task 3)
- [Source: frontend/src/tests/Login.test.tsx] — existing test file/mocking pattern to extend (Task 3)
- [Source: _bmad-output/implementation-artifacts/7-7-hr-admin-navigation-shell-left-pane-nav.md] — original 3-entry nav story; established the active-state/keyboard/aria pattern this story extends without modification

## Dev Agent Record

### Agent Model Used

Claude Sonnet 5

### Debug Log References

- `npx vitest run` (before starting) → 421/421 passed — confirmed as the exact baseline to preserve, not assumed from Story 9.4's record.
- `npx tsc --noEmit` (before starting) → 31 `error TS` occurrences — confirmed as the exact baseline to preserve.
- `npx vitest run src/tests/HrAppShell.test.tsx src/tests/Login.test.tsx` (red phase, before implementation) → 3 failed / 10 passed, confirming the updated tests genuinely exercise the new behavior.
- `npx vitest run src/tests/HrAppShell.test.tsx src/tests/Login.test.tsx` (green phase, after implementation) → 13/13 passed (6 + 7).
- `npx vitest run` (full suite) → 422/422 passed, 0 failed, 0 regressions.
- `npx tsc --noEmit` (after) → 31 errors, unchanged; none in `HrAppShell.tsx`, `Login.tsx`, or either test file.
- `npx vite build` → clean, 537 modules (same as Story 9.4's baseline — no new files).
- `docker compose build frontend && docker compose up -d frontend` — `talentpilot-ui` was unhealthy/stale at session start (predates this story); rebuilt and restarted.
- Playwright (Chromium, `npm install --no-save playwright` + `npx playwright install chromium`, both removed after use via `npm uninstall playwright`; `git checkout -- package-lock.json` discarded incidental lockfile churn) against the rebuilt `talentpilot-ui` container at `http://localhost:5173`: 12/12 live checks passed as HR Admin (`rita@sails.example.com`) — see Task 4 for the full step-by-step trace. Two initial assertion failures in the verification script itself (not the app) were corrected before the final passing run: the active-state check needed a short settle delay after the router navigation, and the "grid renders rows" check needed to target the grid's actual accordion-by-Employee structure (`Casey the Continuer`, `Sam the Stellar` visible) rather than an assumed `<table>` row structure — both script bugs, not application bugs, confirmed by inspecting the real rendered DOM via `outerHTML`/`innerText` dumps before fixing the assertions.

### Completion Notes List

- Smallest story in Epic 9: two one-line production changes (`HrAppShell.tsx`'s `NAV_LINKS` array; `Login.tsx`'s one ternary branch), both already anticipated by Stories 9.3/9.4's own code comments deferring this exact work to Story 9.5.
- **Task 2 (Login.tsx redirect) was not in epics.md's literal AC text for this story** — added after finding a real, documented PRD/epics drift: the PRD's UJ-1 user journey and §4.10 Readiness Dashboard glossary entry (`prd.md` lines 40/76, both `[UPDATED 2026-09-12]`) explicitly state the HR Admin's post-login entry state is now the Skill Assignment Dashboard, not the full grid — but no story in Epic 9 (including this one's own epics.md AC text) mentions updating `Login.tsx`. Since this is the epic's last story and the PRD is the higher-authority source epics.md was derived from, fixed it here rather than leaving Epic 9 "complete" while still contradicting its own PRD. Full reasoning recorded in the story's Dev Notes and Scope Note 4.
- Both routes (`/dashboard`, `/hr/dashboard`) and their `<RequireAuth>` wrapping already existed (`App.tsx`, unmodified) — this story is purely a relabeling/repointing of existing nav data plus one redirect target, confirmed via direct reads of `HrAppShell.tsx`'s render loop (nothing else needed to change for a 4th entry) and both consuming pages (`SkillAssignmentDashboard.tsx`, `Dashboard.tsx`/`DashboardPage.tsx` — neither references the nav or needs updating, Scope Note 6).
- All 5 ACs covered by automated tests (3 `HrAppShell.test.tsx` changes/additions after code review, 1 `Login.test.tsx` rename+assertion change) plus a full live Playwright pass through the real nav → login-redirect → both-destination flow against the real Docker stack.
- Zero regressions: 423/423 frontend tests (421 baseline + 2 net new after code-review patches), `tsc --noEmit` unchanged at the 31-error baseline, `vite build` clean.
- **Code review (`bmad-code-review`, same session) found and fixed 5 real gaps**, resolved 1 decision-needed item, and deferred 2 pre-existing items — see Review Findings above. Most consequential: this story's own documentation (References, `project-context.md`, `sprint-status.yaml`) had inaccurately called both routes "role-gated," when `RequireAuth.tsx` only checks authentication — a pre-existing, app-wide gap (not introduced by this story) now corrected in the record and logged in `deferred-work.md`. Also added the two missing test assertions AC1 (nav order) and AC2 (`/dashboard` active-state) actually needed, and fixed a stale cross-story comment and an overclaiming doc comment.

### File List

**Modified:**
- `frontend/src/components/layout/HrAppShell.tsx` — `NAV_LINKS` array: 3 → 4 entries; `Dashboard` repointed to `/dashboard`; new `Skill Assignments` entry (`/hr/dashboard`); updated file header doc comment (reworded again during code review to scope the "two distinct destinations" claim to nav entries specifically)
- `frontend/src/pages/Login.tsx` — post-login `HR_ADMIN` redirect target changed from `/hr/dashboard` to `/dashboard`
- `frontend/src/pages/hr/SkillAssignmentDashboard.tsx` — code-review patch: fixed the stale "until Story 9.5 repoints it" doc comment (lines 6-9) to past tense
- `frontend/src/tests/HrAppShell.test.tsx` — updated the 3-destination test to 4 (and, after code review, added a nav-order assertion to it); added active-state tests for both the "Skill Assignments" entry and (code-review patch) the "Dashboard" entry at its new `/dashboard` target
- `frontend/src/tests/Login.test.tsx` — renamed and updated the HR_ADMIN redirect test's asserted target
- `_bmad-output/implementation-artifacts/sprint-status.yaml` — story/epic status tracking; code-review patch corrected an inaccurate "role-gated" claim to "wrapped in `<RequireAuth>`"
- `_bmad-output/project-context.md` — Story 9.5 entry (required before this story can be marked done, per the Epic 8 retro's blocking gate); code-review patch applied the same "role-gated" wording correction
- `_bmad-output/implementation-artifacts/deferred-work.md` — 2 deferred code-review findings logged (no frontend role-based route gate app-wide; `Login.tsx` redirect tested only via mock)

**No changes to:**
- `frontend/src/App.tsx` — both routes (`/dashboard`, `/hr/dashboard`) and their `<RequireAuth>` wrapping already existed
- `frontend/src/pages/hr/Dashboard.tsx`, `frontend/src/features/dashboard/DashboardPage.tsx` — neither page references the nav or a "Dashboard" label; their own internal links already hardcode the correct route paths (Scope Note 6)
- Any backend file (`backend/`) — this story is entirely frontend

## Change Log

- 2026-09-14: Story created (`bmad-create-story`), at user's explicit request to start API + UI development for Story 9.5. Confirmed frontend-only via `AskUserQuestion` — epics.md scopes this story as `HrAppShell.tsx`-only nav relabeling, no backend/API work, consistent with the Story 9.2 precedent of an initial "both API and UI" request sometimes diverging from the epic's actual scope. Found and resolved one real, undocumented PRD/epics drift: `Login.tsx`'s post-login HR_ADMIN redirect still targets `/hr/dashboard`, contradicting the PRD's own already-updated UJ-1 entry state ("Authenticated, on the Skill Assignment Dashboard") — added as Task 2/AC5, since no other Epic 9 story touches `Login.tsx` and this is the epic's last story.
- 2026-09-14: Implementation complete (`bmad-dev-story`/Amelia, same session as creation). Both tasks done: `HrAppShell.tsx`'s `NAV_LINKS` repointed/extended to 4 entries (Dashboard → `/dashboard`, new Skill Assignments → `/hr/dashboard`, Skills, Employees); `Login.tsx`'s HR_ADMIN redirect changed to `/dashboard`. True TDD: `HrAppShell.test.tsx`/`Login.test.tsx` updated and confirmed RED (3 failing) before any production code change, then GREEN after. 1 net new test (2 changed/added in `HrAppShell.test.tsx`, 1 renamed in `Login.test.tsx`). Zero regressions (422/422 frontend, `tsc --noEmit` unchanged at 31 pre-existing errors, `vite build` clean, 537 modules unchanged — no new files). Live-verified end-to-end via Playwright (installed ad hoc, fully removed after use) against a freshly rebuilt `talentpilot-ui` container (found unhealthy/stale at session start): full flow confirmed — post-login lands on `/dashboard`, all 4 nav entries render in order, "Dashboard"/"Skill Assignments" both open the correct distinct destinations with correct active-state, full grid renders unfiltered, Skills/Employees unaffected, mobile hamburger nav shows all 4 entries and closes on click. Status → `review`.
- 2026-09-14: Code review (`bmad-code-review`, 3 parallel adversarial layers — Blind Hunter, Edge Case Hunter, Acceptance Auditor, run against the uncommitted diff with this story file as spec context). 1 decision-needed resolved by user (Task 2's `Login.tsx` redirect change — an auth-flow file — had gone beyond what the earlier `AskUserQuestion` scope confirmation literally covered; user chose to keep it as shipped but have it explicitly flagged in the permanent record, with a process lesson recorded for future stories), 5 patches applied, 2 deferred (`deferred-work.md`), 7 dismissed as non-issues after verification. **Most consequential finding**: this story's own documentation (References section, `project-context.md`, `sprint-status.yaml`) inaccurately claimed both nav routes were "already role-gated" — `RequireAuth.tsx` only checks authentication, with zero role branching, confirmed by reading the file directly. This is a real, pre-existing, app-wide gap (established at least since Story 9.3, not introduced by this diff), so no code fix was made to `RequireAuth.tsx` itself, but the inaccurate wording was corrected everywhere it appeared and the underlying gap logged in `deferred-work.md`. Four other patches: added the missing `/dashboard` active-state test AC2's own claim was never actually asserting; added a DOM-order assertion for AC1's literal "in that order" requirement (verified it actually catches a regression by temporarily swapping two `NAV_LINKS` entries and confirming the test failed, then restoring and confirming green); fixed a stale `SkillAssignmentDashboard.tsx` comment still describing Story 9.5 as a future event; reworded `HrAppShell.tsx`'s new doc comment, which overclaimed "not one page linking to the other" when the landing page's Story 9.4 popover already deep-links into the full grid at the content level. Two items deferred, both pre-existing and out of this story's scope: the app-wide missing frontend role-gate itself (relies entirely on backend 403 + Error-state UI); `Login.tsx`'s redirect being tested only via a mocked `navigateMock` assertion, not integration-level route rendering. Full regression re-verified: frontend 423/423 (421 baseline + 2 net new), `tsc --noEmit` unchanged at 31 pre-existing errors, `vite build` clean. Status → `done`.
