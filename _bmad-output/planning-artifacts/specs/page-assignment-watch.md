# Page Specification: Assignment Watch

## Overview
- **Purpose:** Standalone route that mounts the `VideoPlayer` for a given assignment, reached only via a Content Discovery card click.
- **URL:** `/assignments/:assignmentId/watch` (requires auth)
- **Type:** Thin wrapper / video playback
- **Source:** `frontend/src/pages/employee/AssignmentWatch.tsx`

## Layout Structure (Desktop)
1. Page container (`max-w-3xl`, `p-8`) — no header/nav/user menu on this route
2. `VideoPlayer` (assignmentId, videoUrl, startSeconds from router state)

## Component List

| Component | Location | Variant | Notes |
|---|---|---|---|
| `VideoPlayer` | Full page | loading/ready/error | Identical component instance used in Content Discovery's inline mode |

## Content Strategy
No page-level copy — all content strategy lives inside `VideoPlayer` (see its notes under `page-content-discovery.md`).

## Responsive Behavior
Single-column, `max-w-3xl` container; no breakpoint-specific rules observed.

## Interactions
- **Guard clause:** requires `videoUrl` (string) and `startSeconds` (number) in `location.state`. If missing or malformed, `useEffect` redirects to `/employee/content` (`replace: true`) and the component renders `null` — this means a page refresh or direct URL visit always bounces back, since router state doesn't survive a reload.
- No second data fetch for resume position — the position is passed in via router state from the originating card click, not re-queried here.

## Open Question for Design/Product
This route exists in parallel with Content Discovery's own inline video mode (Mode B in `page-content-discovery.md`), which achieves the same UI without a route change. Confirm whether both entry points are intentional (e.g. one is a deep-link/share target) or whether this route is legacy from before the inline mode was built — worth a decision before this feeds into prototyping.
