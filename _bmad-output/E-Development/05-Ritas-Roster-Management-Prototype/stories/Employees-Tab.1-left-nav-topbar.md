# Story: Employees-Tab.1 — Left Nav Pane + Top Bar

**Status:** Implemented
**Spec reference:** `work/Employees-Tab-Work.yaml` → section-1; PRD FR-29

**Purpose:** Introduce the new shared left-pane nav shell (Dashboard/Skills/Employees), replacing the old top-header nav for this page, plus a slim top bar carrying only the user menu.

**Objects:** `app-nav-sidebar`, `app-nav-logo`, `app-nav-link-dashboard`, `app-nav-link-skills`, `app-nav-link-employees`, `app-topbar-user-menu`

**Acceptance criteria:**
- [x] Sidebar shows all 3 links, "Employees" visually active (`aria-current="page"`)
- [x] Top bar shows only the user menu, no nav links
- [x] `requireRole('HR')` gate redirects to `login.html` when unauthenticated (via `shared/auth.js`)
- [x] Sidebar links to Dashboard/Skills point at the sibling `01-Ritas-Trust-Call-Prototype/` folder's pages

**User-evaluable:** Does the nav feel like a natural home for "Employees" alongside Dashboard/Skills?
