# Story: Employees-Tab.7 — Responsive States

**Status:** Implemented
**Spec reference:** `work/Employees-Tab-Work.yaml` → section-7 (this closes the Phase 4 Backlog item: "Explore responsive states for 05.1")

**Purpose:** Make the left-pane nav and roster list usable from 375px up, per the Fully Responsive device decision.

**Implementation:**
- Sidebar (`app-nav-sidebar`) is `fixed` + `-translate-x-full` below `md` (768px), toggled via a hamburger button (`openMobileNav()`/`closeMobileNav()`) with a click-outside backdrop (`#nav-backdrop`)
- Toolbar wraps (`flex-wrap`) below desktop width
- Table view scrolls horizontally (`overflow-x-auto`, `min-w-[720px]`) rather than compressing columns illegibly
- Card view grid drops to 1 column on mobile, 2 on tablet, 3 on desktop (unchanged from Phase 4 spec)

**Acceptance criteria:**
- [x] 375px: no page-level horizontal scroll; nav reachable via hamburger + backdrop-dismiss
- [x] 768px: breakpoint transition is clean (sidebar becomes static/always-visible at `md:`)
- [x] 1280px/1440px: matches the base desktop spec exactly

**User-evaluable:** On a tablet-width window, does the nav feel discoverable, not hidden?
