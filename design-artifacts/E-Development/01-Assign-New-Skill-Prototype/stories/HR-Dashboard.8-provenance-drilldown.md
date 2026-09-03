# Story HR-Dashboard.8: Provenance Drill-Down Modal (Scope Addition)

**View**: HR Dashboard — **new logical view** (View 3, not in the original Logical-View-Map.md)
**Section**: 8 (beyond the original 7-section plan)
**Complexity**: Medium
**Estimated Time**: n/a (unplanned) — built ahead of any estimate, directly from user reference

---

## ⚠️ Process Note — Scope Addition

`Logical-View-Map.md` (Step 2 of Prototyping) defined exactly 2 logical views for this scenario: HR Dashboard (Grid) and the Assign New Skill Modal. The **Provenance Drill-Down Modal** was explicitly out of scope — flagged as such in `HR-Dashboard.5-table-rows.md`'s "Explicitly Out of Scope" section, since "View Details" isn't part of the Assign-a-New-Skill user journey.

The user shared a screenshot of the real production `ProvenanceDrillDownModal` (matching `frontend/src/features/dashboard/ProvenanceDrillDownModal.tsx`, already fully captured during the Reverse Engineering activity) and asked for it directly, a second time redirecting scope via a concrete reference image. Built now rather than re-litigating scope a third time, since the ask was unambiguous and the source component was already fully read and understood.

**This is logged here as a formal scope addition, not silently absorbed into the original 7-section count.**

---

## 📋 What Was Built

Faithful reproduction of `ProvenanceDrillDownModal.tsx`'s **read-only detail view** only (loading/error/confirm sub-states from the real component are NOT built — see Out of Scope below):

- Header: `{employee_name} — {skill_name}` + a StatusBadge-style pill
- **Important fidelity note**: this pill is **yellow** for "In Progress" (`bg-yellow-100 text-yellow-800`), matching the real `components/StatusBadge.tsx` exactly — deliberately different from Section 5's dashboard-table pill, which is **blue/talentpilot** for the same status. This is a genuine inconsistency that exists in real production too (documented in `design-system.md`'s Notes #2), reproduced faithfully here, not accidentally introduced.
- Provenance section — all 5 real branches implemented (Verified / Self-reported / Needs Attention / HR Override / Not Started), even though this session's sample data only exercises 4 of them (no `HR Override` row exists in `sampleAssignments`)
- Footer: "Mark as Ready" (or "Reverse Override" for HR Override rows) + "Close"
- Backdrop click and Escape key both close the modal

### JavaScript

```javascript
function handleViewDetails(assignmentId) {
  const row = assignments.find((a) => a.assignment_id === assignmentId);
  if (row) openDrillDown(row);
}

function openDrillDown(row) { /* populates title/status/provenance, shows backdrop */ }
function closeDrillDown() { /* hides backdrop */ }
function drilldownStatusBadgeHtml(row) { /* yellow/gray/green pill, matches StatusBadge.tsx */ }
function drilldownProvenanceHtml(row) { /* switch on row.provenance, 5 branches */ }
function handleMarkAsReady() { /* toast placeholder, see Out of Scope */ }
```

---

## 🚫 Explicitly Out of Scope (this round)

- **Mark as Ready / Reverse Override confirm flow** — the real component's reason-textarea + Confirm/Cancel sub-view, and its 4-branch reversal-toast messaging (`describeReversalToastMessage`), are a materially deeper feature than the read-only detail view a single screenshot specified. Wired to an honest "not built yet" toast instead. If requested next, this is the natural next increment — the provenance-branch logic already built here is most of what it needs.
- **Loading/error states for the modal itself** — the real component fetches drill-down data async; this prototype already has the row data in memory (no fetch needed), so those states don't apply here.
- Not added to `Logical-View-Map.md` as a formally re-planned View 3 with its own section breakdown — built directly instead, given the reference was unambiguous. Worth doing properly (own work file) if this view grows further.

---

## ✅ Acceptance Criteria

### Agent-Verifiable (static / structural)

| # | Criterion | How Verified |
|---|-----------|--------------|
| 1 | Modal hidden by default | `hidden` attribute present |
| 2 | View Details opens it with correct row data | Code read: `handleViewDetails` → `openDrillDown` |
| 3 | Status pill is yellow for In Progress (matches StatusBadge.tsx, not Section 5's blue) | Code read: `bg-yellow-100 text-yellow-800` |
| 4 | All 5 provenance branches implemented | Code read: `switch` statement |
| 5 | Backdrop click and Escape both close it | Code read |
| 6 | No syntax errors | `node --check` |

### User-Evaluable (Qualitative — this is the main ask)

- [ ] **Does this match your reference screenshot?**
- [ ] Provenance text reads correctly for different sample rows (try Casey's "Data Visualization" — Verified, Jordan's "Python Programming" — Self-reported, Sam's "Communication Skills" — Needs Attention)
- [ ] Mark as Ready's placeholder toast is an acceptable stand-in for now, or should it be built out next?

---

## 📊 Status Tracking

**Status**: ✅ Complete & Approved
**Started**: 2026-09-03
**Completed**: 2026-09-03
**Approved By**: Vasu — "Overall admin dashboard looks good for me" (2026-09-03)
**Notes**: Formal scope addition beyond the original 7-section HR Dashboard plan — see Process Note.

---

## 🔄 Changes from Original Plan

- Entirely new scope: this logical view was explicitly excluded in `Logical-View-Map.md` and `HR-Dashboard.5-table-rows.md`. Added after a second user-directed screenshot reference, not part of any prior estimate.

### Issue: modal appeared on page load, empty, with a non-functioning Close button

**Problem**: User reported the drill-down popup appeared immediately on page load (no click), with no data, and Close did nothing.

**Root cause**: `#hr-dashboard-drilldown-backdrop` combined the native `hidden` HTML attribute with Tailwind's `flex` utility class. CSS cascade resolves by *origin* before specificity/order: the browser's default `[hidden] { display: none }` rule lives in the **user-agent** stylesheet, which is always beaten by **author** stylesheet rules of equal or lower specificity — including Tailwind's generated `.flex { display: flex }`. So the element was visually `display: flex` from first paint, completely independent of the `hidden` attribute's true/false state. Toggling `.hidden` in JS (`element.hidden = true/false`) therefore never had any visual effect — it changed an attribute that wasn't actually controlling display. The "empty" content was simply because `openDrillDown()` (which populates the fields) had never actually run — the element was visible without ever being properly opened.

**Solution**: Replaced the `hidden` attribute with an inline `style="display: none"` on both the static markup and every JS toggle (`element.style.display = 'none' / 'flex'`) for this element. Inline styles have higher specificity than any class-based stylesheet rule, so this can't lose to `.flex` regardless of Tailwind's internal rule ordering.

**Same bug found and fixed in**: `#hr-dashboard-pagination` (also combines `hidden` + `flex`) — likely causing the pagination row to be visible from page load too, just less noticeably than a full-screen modal backdrop.

**Learned — carry forward to View 2 (Assign New Skill Modal)**: never combine the native `hidden` attribute with a `flex`/`block`/`grid`/`inline-*` Tailwind utility class on the same element. View 2's modal will use this exact same backdrop+flex-centering pattern — build it with `style.display` toggling (or `hidden:flex`-style conditional classing) from the start, not `hidden` + `flex` together.
