# Story HR-Dashboard.7: HR Dashboard - Toast & Live Announcements

**View**: HR Dashboard (Grid)
**Section**: 7 of 7 (final section)
**Complexity**: Simple
**Estimated Time**: 15 minutes (planned) — pulled forward after Delete/View Details were reported as "not functioning"

---

## 🎯 Goal

Bottom-center success toast and a hidden aria-live region, so every interactive action on this page (delete, and the placeholder actions for View Details / + New Assignment) has a visible confirmation instead of being silent.

---

## ⚠️ Process Note

Pulled forward directly from user feedback: Delete was reported as "row disappears but nothing else updates," and View Details as producing no visible reaction at all. Both were true — Delete only updated a small, easy-to-miss count text, and View Details/+ New Assignment only logged to the console (invisible without devtools open). Section 7's toast — the real production confirmation mechanism for these exact actions — directly solves both, so it was built now instead of waiting for its original slot.

---

## 📋 What Was Built

### HTML

```html
<div aria-live="polite" id="hr-dashboard-live-region" class="sr-only"></div>

<div id="hr-dashboard-toast" hidden role="status" aria-live="polite"
     class="fixed inset-x-0 bottom-6 z-50 mx-auto w-fit max-w-[90vw] rounded-lg bg-gray-900 px-4 py-2 text-sm text-white shadow-lg">
</div>
```

### JavaScript

```javascript
let toastTimer = null;

function showToast(message) {
  const toast = document.getElementById('hr-dashboard-toast');
  toast.textContent = message;
  toast.hidden = false;
  if (toastTimer) window.clearTimeout(toastTimer);
  toastTimer = window.setTimeout(() => { toast.hidden = true; }, 4000);
}

function announceLive(message) {
  document.getElementById('hr-dashboard-live-region').textContent = message;
}
```

**Wired into:**
- `handleDeleteRow()` — real production copy: `"{FirstName} — {SkillName} removed."` (matches `page-hr-dashboard.md`'s captured toast text exactly), plus an aria-live announcement
- `handleViewDetails()` — since the real drill-down modal is out of scope, the toast honestly says so instead of pretending to open something: `"View Details — not part of this prototype (drill-down modal is a different scenario)"`
- `handleNewAssignmentClick()` — same honesty pattern: `"+ New Assignment — View 2 (Assign modal) not built yet"`

---

## 🚫 Explicitly Out of Scope

- No assignment-created toast wiring yet — that requires View 2 (Assign modal) to exist first; the placeholder toast above stands in for it until then.
- `announceLive()` is only called from delete right now (matching the one interactive change this prototype can actually make). Production's aria-live region also announces poll-driven background changes — no polling exists in this static prototype, so that portion isn't replicated.

---

## ✅ Acceptance Criteria

### Agent-Verifiable (static / structural)

| # | Criterion | How Verified |
|---|-----------|--------------|
| 1 | Toast + live region elements present | grep for object IDs |
| 2 | Toast hidden by default | `hidden` attribute in static HTML |
| 3 | Delete toast text matches production copy exactly | grep for the template literal |
| 4 | Toast auto-dismisses after 4s | Code read: `setTimeout(..., 4000)` |
| 5 | Repeated triggers reset the dismiss timer (no early cutoff) | Code read: `clearTimeout` before re-arming |
| 6 | No syntax errors | `node --check` |

### User-Evaluable (Qualitative)

- [ ] Delete now clearly confirms what happened
- [ ] View Details / + New Assignment no longer feel broken — the toast is honest that they're not built yet, not silent
- [ ] Toast position/style doesn't clash with the pagination row directly above it

---

## 📊 Status Tracking

**Status**: ✅ Complete & Approved
**Started**: 2026-09-03
**Completed**: 2026-09-03
**Approved By**: Vasu — "Overall admin dashboard looks good for me" (2026-09-03)
**Notes**: This completes all 7 planned sections for View 1 (HR Dashboard). Next milestone after approval: Step 5 Finalization, then View 2 (Assign New Skill Modal).

---

## 🔄 Changes from Original Plan

- Pulled forward from its original Section 7 slot, directly in response to user feedback that Delete and View Details felt non-functional — both needed exactly this section's toast mechanism to actually resolve.
