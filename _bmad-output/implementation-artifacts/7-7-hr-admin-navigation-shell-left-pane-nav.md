---
baseline_commit: e3243373
---

# Story 7.7: HR Admin Navigation Shell — Left-Pane Nav

Status: done

## Story

As an **HR Admin**,
I want the primary navigation relocated to a left-side pane with an Employees destination,
So that I can reach the roster (Stories 7.2–7.6) the same way I reach Dashboard and Skills today (FR-29).

## Scope

Frontend-only (per epics.md AC5) — no backend/API changes. Realizes FR-29, UX-DR40.

## What shipped

1. **New shared component: `frontend/src/components/layout/HrAppShell.tsx`.** Extracted from the three near-identical header blocks in `Dashboard.tsx`/`SkillsPage.tsx`/`EmployeesPage.tsx` (all three had drifted into copy-pasted duplicates of the same top-header nav + user menu). `HrAppShell` owns:
   - A fixed/static left sidebar (`app-nav-sidebar`) with the TalentPilot-AI wordmark and three links — Dashboard (`/hr/dashboard`), Skills (`/skills`), Employees (`/employees`) — active link determined by `useLocation().pathname`, marked with `aria-current="page"` **and** a non-color style change (`bg-blue-50 font-medium text-blue-700`, not color alone), matching UX-DR41's "never color-only" pattern already established for status badges.
   - A slim top bar carrying only the user menu (avatar + "Rita" + Sign Out dropdown) — unchanged in position, copy, and sign-out behavior (`logout()` → `signOut()` → navigate to `/login`), per AC2's "only the Dashboard/Skills links move, not the whole header."
   - Mobile collapse below the 768px breakpoint (Tailwind `md:`, matching the prototype's `05.1-Employees-Tab.html` reference exactly): the sidebar sits at `-translate-x-full` off-screen by default and slides to `translate-x-0` when a hamburger button (top bar, `md:hidden`) is clicked; a click-to-dismiss backdrop (`app-nav-backdrop`) appears alongside it; clicking a nav link also closes the mobile overlay. Matches UX-DR40.

2. **`Dashboard.tsx`, `SkillsPage.tsx`, `EmployeesPage.tsx` refactored** to render `<HrAppShell>...</HrAppShell>` instead of their own `<div><header>...</header><main>...</main></div>` shell. Each page keeps its own `<main>` content and modals exactly as before — only the header/nav/user-menu block moved. `useAuth`/`logout`/`useNavigate` imports and the `userMenuOpen` state, now owned by `HrAppShell`, were removed from all three pages.

3. **Skills tab's "Manage API Keys" entry point verified still reachable** (AC3) — it was never in the header to begin with; it's a toolbar button inside `SkillsPage.tsx`'s `<main>` content (`skills-tab-btn-manage-keys`), untouched by this refactor. No "header duplication" existed to fix; confirmed by reading the file before starting, not assumed.

## Testing (red → green)

- New `frontend/src/tests/HrAppShell.test.tsx` (5 tests, written first and confirmed failing before the component existed): all three nav links render with correct hrefs; the active route gets `aria-current="page"` plus the non-color style, inactive routes don't; the user menu opens and Sign Out still calls `logout()` and navigates to `/login`; the sidebar starts off-screen and the hamburger reveals it with a dismissible backdrop; clicking a nav link closes the mobile overlay.
- Full existing suite re-run after the refactor: **38 test files / 391 tests, all green** — no existing `Dashboard`/`SkillsPage`/`EmployeesPage` test referenced the old header markup directly, so none needed changes.
- `vite build` succeeds cleanly (534 modules, no compile errors) — confirms the three pages' import/JSX surgery didn't leave a dangling reference.
- Pre-existing, unrelated `tsc --noEmit` errors (UUID branded-type mismatches in `useResumePosition.test.ts`, a stale `getDashboardAssignments` export in two other test files) were confirmed present on `HEAD` **before** this story's changes (`git stash` + re-run) — not introduced here, out of this story's scope.

## Known limitation

No headless browser/Playwright is available in this sandbox to capture literal screenshots at 375px/768px/1280px. Responsive behavior is verified via the class-level assertions above (matching the already-shipped `05.1-Employees-Tab.html` prototype's exact Tailwind classes) plus a clean production build, not a rendered-pixel check. Recommend a manual live-browser pass before this is considered fully done end-to-end, per the sprint's own action item on UI stories needing visual validation.
