# Scenario: Employee Watches an Assigned Video

**Entry point:** Employee Content Discovery → clicking an `AssignmentCard` with content

## Steps

1. Employee lands on Content Discovery grid (`/employee/content`), sees cards grouped by In Progress / To Start / Completed
2. Clicks a card (or Enter/Space when focused) → page swaps in place to inline video mode (no route change; `playingVideo` is local state)
3. `VideoPlayer` mounts: loads YouTube IFrame API if needed, initializes at `item.watch_position` (resume point)
4. Video plays; a `CaptureService` posts watch-progress samples periodically (every 12s or after 3+ samples) via the YouTube adapter
5. Employee clicks "← Back to Assignments" (or the "Assignments" nav item) → returns to grid mode, which re-fetches so progress/status reflects the session just watched

## Alternate Path — Direct Route (`AssignmentWatch.tsx`)
A second, separate route (`/assignments/:assignmentId/watch`) exists that also mounts `VideoPlayer`, but only works if arrived at with `videoUrl`/`startSeconds` in router state (i.e. from a card click that navigates rather than swaps state). Direct visits or refreshes have no state to render from and redirect back to `/employee/content`.

**Flagged in `page-assignment-watch.md`:** unclear whether this route is an intentional second entry point or dead/legacy code now that Content Discovery's inline mode covers the same need — needs a product decision before prototyping.

## Error States
- Player init failure or playback error (`onPlayerError_Internal`): "This video couldn't be loaded." + [Try again], which tears down and re-initializes the player from scratch
- Retry uses a fresh DOM node each attempt (YouTube's IFrame API replaces its mount element, so the same node can't be reused across retries)

## Success Path
Progress is periodically captured server-side; on return to the grid, the card reflects updated status/percentage (Not Started → In Progress → Completed, driven by backend-derived `status_percentage`, not independently recalculated client-side).
