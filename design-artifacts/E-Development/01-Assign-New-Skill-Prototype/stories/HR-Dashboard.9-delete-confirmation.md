# Story HR-Dashboard.9: Delete Confirmation Modal (Scope Addition)

**View**: HR Dashboard — extends View 1 (delete flow) via a new confirmation step
**Section**: 9 (beyond the original 7-section plan, second addition after the Provenance Drill-Down modal)
**Complexity**: Simple
**Estimated Time**: n/a (unplanned) — built directly from the real `DeleteAssignmentModal.tsx` source, already captured during Reverse Engineering

---

## ⚠️ Process Note — Scope Addition

Delete previously removed a row immediately on click (see `HR-Dashboard.5-table-rows.md`). User reported no confirmation step existed — matching real production's `DeleteAssignmentModal.tsx`, which requires an explicit confirm before deleting. Built directly since the real component source was already fully read during Reverse Engineering.

---

## 📋 What Was Built

Faithful reproduction of `DeleteAssignmentModal.tsx`:

- Title: "Remove this assignment?"
- Body: `{employee_name} — {skill_name}`
- Conditional progress warning (only shown if `status !== "Not Started"`): `"This assignment has recorded progress ({X}% watched | Completed). Removing it will take it off the dashboard; the history is retained for audit."`
- Footer: "Cancel" (text link) / "Remove Assignment" (red button)
- Backdrop click + Escape both cancel

### JavaScript

```javascript
let pendingDeleteId = null;

function openDeleteConfirm(assignmentId) {
  const row = assignments.find((a) => a.assignment_id === assignmentId);
  if (!row) return;
  pendingDeleteId = assignmentId;
  // populate body text + conditional progress warning
  document.getElementById('hr-dashboard-delete-confirm-backdrop').style.display = 'flex';
}

function closeDeleteConfirm() {
  pendingDeleteId = null;
  document.getElementById('hr-dashboard-delete-confirm-backdrop').style.display = 'none';
}

function confirmDelete() {
  if (!pendingDeleteId) return;
  const assignmentId = pendingDeleteId;
  closeDeleteConfirm();
  handleDeleteRow(assignmentId); // existing Section 5/7 logic — filter, toast, re-render
}
```

The row's trash-icon button now calls `openDeleteConfirm(id)` instead of deleting directly; the actual removal (`handleDeleteRow`) is unchanged, just moved behind confirmation.

**Built the `style.display` way from the start** — this modal reuses the exact backdrop+`flex items-center justify-center` pattern that caused the `hidden`+`flex` bug in `HR-Dashboard.8-provenance-drilldown.md`. Applied the lesson immediately rather than repeating the mistake.

---

## ✅ Acceptance Criteria

### Agent-Verifiable (static / structural)

| # | Criterion | How Verified |
|---|-----------|--------------|
| 1 | Confirmation modal present, hidden via `style="display:none"` (not `hidden` attribute) | grep |
| 2 | Trash icon opens confirm modal, not immediate delete | grep for `openDeleteConfirm(` on the button |
| 3 | Progress warning only shows for non-"Not Started" rows | Code read |
| 4 | Cancel and backdrop-click both abort without deleting | Code read: `closeDeleteConfirm()` doesn't call `handleDeleteRow` |
| 5 | Confirm actually deletes and shows the existing toast | Code read: `confirmDelete()` → `handleDeleteRow()` |
| 6 | No syntax errors | `node --check` |

### User-Evaluable (Qualitative)

- [ ] Matches expected production confirmation behavior
- [ ] Progress warning text reads correctly for an In Progress row (e.g. Casey's "Data Visualization", 45%) vs. a Not Started row (e.g. Morgan's "Salesforce Admin", no warning expected)
- [ ] Cancel and the red "Remove Assignment" button both behave as expected

---

## 📊 Status Tracking

**Status**: ✅ Complete & Approved
**Started**: 2026-09-03
**Completed**: 2026-09-03
**Approved By**: Vasu — "Overall admin dashboard looks good for me" (2026-09-03)

---

## 🔄 Changes from Original Plan

- Entirely new scope, added after user feedback that delete lacked a confirmation step matching production.
