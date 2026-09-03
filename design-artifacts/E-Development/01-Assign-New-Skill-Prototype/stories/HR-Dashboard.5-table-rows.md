# Story HR-Dashboard.5: HR Dashboard - Assignment Table Rows

**View**: HR Dashboard (Grid)
**Section**: 5 of 7
**Complexity**: Medium
**Estimated Time**: 30 minutes (planned) — built together with Section 4, see process note in that story file

---

## 🎯 Goal

Per-row table content inside each expanded employee group, matching the real production dashboard exactly: Assigned Skill, Status pill, Progress bar, Last Updated (+ staleness), View Details link, delete icon — columns and behavior confirmed against the user's reference screenshot of `localhost:5173/hr/dashboard`.

---

## ⚠️ Process Note

Built together with Section 4 (Accordion Structure) in one accelerated pass — see that story's Process Note for the full explanation. This file documents the row-content portion.

---

## 📋 What Was Built

### HTML (generated per row in `renderGrid()`)

```html
<table class="w-full border-collapse text-sm" style="table-layout: fixed">
  <colgroup><!-- 22/18/18/18/16/8% --></colgroup>
  <thead>
    <tr class="border-b border-gray-300 text-left text-gray-600">
      <th>Assigned Skill</th><th>Status</th><th>Progress</th><th>Last Updated</th><th>Actions</th><th><span class="sr-only">Delete</span></th>
    </tr>
  </thead>
  <tbody>
    <tr class="border-b border-gray-200 hover:bg-gray-100 transition-colors align-middle">
      <td>{skill_name}</td>
      <td><!-- status pill --></td>
      <td><!-- progress bar/text --></td>
      <td id="hr-dashboard-row-lastupdated-{assignmentId}"><!-- relative time [+ stale suffix] --></td>
      <td><button id="hr-dashboard-row-viewdetails-{assignmentId}">View Details</button></td>
      <td><button id="hr-dashboard-row-delete-{assignmentId}"><!-- trash icon --></button></td>
    </tr>
  </tbody>
</table>
```

### JavaScript

```javascript
function statusPillHtml(row) { /* In Progress (blue/talentpilot) | Completed (green) | Not Started (gray) — text always included, never color-only */ }
function progressCellHtml(row) { /* thin bar + %, full green bar for Completed, "-" for Not Started */ }
function lastUpdatedCellHtml(row) { /* relative time; red + explicit day-count text when provenance === "Needs Attention" */ }
function formatRelativeTime(iso) { /* hand-rolled — no date-fns bundled in this static prototype */ }
function staleDaysSince(iso) { /* days since last_updated, floor, clamped >= 0 */ }
function formatStaleDaysText(days) { /* "Not updated today" at 0, else "N days stale" */ }

function handleViewDetails(assignmentId) {
  console.log(`[prototype] View Details clicked for ${assignmentId} — drill-down modal is out of this scenario's scope`);
}

function handleDeleteRow(assignmentId) {
  assignments = assignments.filter((row) => row.assignment_id !== assignmentId);
  renderTotalCount();
  assignments.length === 0 ? showOnly('hr-dashboard-empty') : renderGrid();
}
```

### Tailwind Classes Used

- Status pill (In Progress): `bg-talentpilot-100 text-talentpilot-700 px-2 py-1 rounded` — **note**: standardized to `talentpilot-*` per `design-system.md`, where real production's own inline table pill actually already uses plain `blue-100`/`blue-700` for this (not the separate `StatusBadge.tsx` component's yellow, which appears elsewhere in the app, not on this page)
- Status pill (Completed): `bg-green-100 text-green-700`
- Status pill (Not Started): `bg-gray-100 text-gray-700`
- Progress bar track/fill: `w-16 h-1 bg-gray-200 rounded-full overflow-hidden` / `bg-talentpilot-600` (or `bg-green-600` for Completed)
- Staleness text: `text-red-700 font-medium` (paired with explicit day-count text, never color-only)
- Delete icon button: `w-9 h-9 rounded-full text-red-600 hover:bg-red-100 hover:text-red-700`

---

## 🔗 Dependencies

Section 4 (accordion shell — rows render inside its expanded panel). `data/demo-data.json`'s `sampleAssignments` (5 synthesized rows, added during Section 3's issue-fix).

---

## 🚫 Explicitly Out of Scope (documented, not silently dropped)

- **View Details** click only logs to console. The real production app opens a `ProvenanceDrillDownModal` (4 provenance states, Mark-as-Ready / Reverse-Override sub-flows) — that modal is **not part of this scenario's Logical View Map** (only View 1 Dashboard + View 2 Assign modal are in scope for "Assign a New Skill"). Building it would be new scope, not a fix to what was asked.
- **Delete** is real within this session (removes from local `assignments`, re-renders, updates the total count) but does **not** show a toast — that's Section 7's planned scope, not yet built.
- **date-fns** isn't bundled (no build step, CDN-Tailwind-only prototype) — `formatRelativeTime`/`staleDaysSince`/`formatStaleDaysText` are small hand-rolled equivalents, not pixel-identical to `date-fns`' exact wording at every boundary (e.g. "about 2 months ago" phrasing matches the screenshot; exact day/hour rounding rules may differ slightly).

---

## ✅ Acceptance Criteria

### Agent-Verifiable (static / structural)

| # | Criterion | How Verified |
|---|-----------|--------------|
| 1 | Columns match reference: Assigned Skill, Status, Progress, Last Updated, Actions (+ delete) | grep of `<th>` labels |
| 2 | Status pill always includes text, never color-only | Code read: every branch returns text + background class together |
| 3 | Staleness (Needs Attention) row shows red text + explicit day count | Code read: `lastUpdatedCellHtml()` |
| 4 | Delete removes the row and updates the total count | Code read: `handleDeleteRow()` |
| 5 | Delete emptying the group's last row falls back to empty state correctly | Code read: `assignments.length === 0` branch |
| 6 | No syntax errors | `node --check` |

### User-Evaluable (Qualitative — needs your eyes, this is the main ask)

- [ ] **Does this match the reference screenshot?** (columns, pill colors, progress bars, spacing)
- [ ] Status/progress/staleness read clearly at a glance
- [ ] Delete button and View Details are both reachable and behave sensibly (even if View Details is just a console log for now)

---

## 📊 Status Tracking

**Status**: ✅ Complete & Approved
**Started**: 2026-09-03
**Completed**: 2026-09-03
**Approved By**: Vasu — "Overall admin dashboard looks good for me" (2026-09-03)
**Notes**: See Section 4's story for the full process note on the combined build.

---

## 🔄 Changes from Original Plan

### User-requested simplification: Last Updated column

User asked for plain relative-time text only ("10 days ago"), first removing the "(N days stale)" suffix, then a follow-up removing the red staleness coloring too. Both applied — `lastUpdatedCellHtml()` now always renders `text-gray-500`, no conditional styling or suffix by provenance.

**Documented tradeoff**: real production explicitly treats this as a "never color-only" accessibility requirement (staleness must be conveyed by text, not color alone — see `design-system.md` Patterns, sourced from the real code's own AC comments). This prototype no longer reflects that requirement at all — an intentional, user-directed simplification for this mockup, not an oversight. Worth revisiting before this feeds production work.

Removed `formatStaleDaysText()` as dead code once its only caller was removed.

- Built together with Section 4 instead of sequentially, per direct user request (reference screenshot).
- View Details deliberately left as a console-log placeholder — the real drill-down modal isn't in this scenario's Logical View Map; flagged here rather than silently built or silently skipped.
- Delete worked locally but had no toast at first — reported by user as "row disappears but nothing else updates." Resolved by pulling Section 7 (Toast) forward; see `HR-Dashboard.7-toast-live-announcements.md`. View Details' silence was reported too ("nothing visible happens") and got the same toast-based fix.
