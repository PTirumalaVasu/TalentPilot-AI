# Page Specification: Employee Content Discovery

## Overview
- **Purpose:** Let an employee see their assigned skills, track progress, and start/resume watching training video content.
- **URL:** `/employee/content` (requires auth)
- **Type:** Employee dashboard, two render modes on one route (grid view / inline video view)
- **Source:** `frontend/src/pages/employee/ContentDiscovery.tsx`

## Layout Structure (Desktop)

**Mode A — Assignment Grid (default)**
1. Header: logo, nav ("Assignments" active / "Continue Watching" disabled-gray placeholder), user menu
2. Main
   - "Assigned Skills" title + subtitle
   - Employee Info card (gradient blue background): Name, Role ("Individual Contributor", hardcoded), Email, Skills Assigned count
   - 4 stat tiles: Total / In Progress / To Start / Completed
   - Grouped card grids (only rendered if count > 0): "In Progress", "To Start", "Completed" — each a heading + count + responsive card grid

**Mode B — Inline Video View** (replaces the whole body when a card is selected)
1. Header: logo, nav ("Assignments" now clickable to go back / "Continue Watching" now active-styled), user menu
2. Main: "← Back to Assignments" link, video title (h1), `VideoPlayer`

## Component List

| Component | Location | Variant | Notes |
|---|---|---|---|
| User menu (`UserMenuButton`, local) | Header | open/closed | Second hand-rolled copy, distinct from HR Dashboard's |
| `AssignmentCard` | Card grids | with/without content, 3 progress states | Keyboard-operable (`role="button"`, Enter/Space) |
| Stat tile (inline markup) | Grid summary | — | 4 repeated blocks, not extracted as a component |
| `VideoPlayer` | Inline video mode | loading/ready/error | Same component as Assignment Watch page |
| Loading skeleton | Initial load | `animate-pulse`, 3 placeholder tiles | `data-testid="content-discovery-loading"` |
| Error state | Failed fetch | — | "Couldn't load your assignments." + Try again `Button` |
| Empty state | 0 assignments | — | "Nothing in progress right now." |

## Content Strategy
- Title: "Assigned Skills", subtitle: "Select a video to continue watching or start a new one"
- Info card labels (uppercase, tracking-wide): Name / Role / Email / Skills Assigned
- Section headers: "In Progress (n)" / "To Start (n)" / "Completed (n)"
- Card status pill: "To Start" (⊕) / "In Progress" (⟳) / "Completed" (✓)
- No-content fallback: "No recommended content yet for this skill." + mailto link "Contact Rita" (hardcoded contact)
- Progress copy on cards: "{n}% watched" / "100% watched" / "Not started yet"

## Responsive Behavior
- Stat tiles: `grid-cols-2 md:grid-cols-4`
- Card grids: `grid-cols-1 md:grid-cols-2 lg:grid-cols-3`
- Main content capped at `max-w-5xl`, centered

## Interactions
- Two parallel data fetches on mount/reload: assignments list + profile (`/api/auth/me`) — profile resolves the header's real name (fixes a prior bug where every user showed "Casey")
- Background poll every 30s (paused on tab-hidden via `visibilitychange`), console-logged, silently merges into loaded state (no skeleton flash)
- Selecting a card with content swaps the whole page body into Mode B (no route change — `playingVideo` is local state, not reflected in the URL)
- "← Back to Assignments" / nav "Assignments" both return to Mode A
- Retry button on error re-triggers both fetches via `reloadToken` bump

## Cross-References
Renders `VideoPlayer` (shared with `page-assignment-watch.md`). Uses `Button` from `ui/`.
