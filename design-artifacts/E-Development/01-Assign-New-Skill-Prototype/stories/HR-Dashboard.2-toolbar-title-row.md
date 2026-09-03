# Story HR-Dashboard.2: HR Dashboard - Toolbar & Title Row

**View**: HR Dashboard (Grid)
**Section**: 2 of 7
**Complexity**: Simple
**Estimated Time**: 10 minutes

---

## 🎯 Goal

Add the "+ New Assignment" button (View 2's future trigger) and the "Skill Assignments" title row with a live total count, sourced from in-memory demo state rather than hardcoded.

---

## 📋 What to Build

### HTML Elements

Inserted into `<main id="hr-dashboard-main">`, above the Section 3+ placeholder:

```html
<div class="py-3 flex items-center justify-between">
  <div></div>
  <button id="hr-dashboard-new-assignment-button" onclick="handleNewAssignmentClick()"
          class="bg-talentpilot-600 text-white text-sm font-semibold px-4 py-2 rounded-lg hover:bg-talentpilot-700 transition-colors">
    + New Assignment
  </button>
</div>

<div class="flex items-center justify-between mb-4">
  <h2 id="hr-dashboard-title" class="text-2xl font-black text-gray-900">Skill Assignments</h2>
  <span id="hr-dashboard-total-count" class="text-sm text-gray-500">Total: 0 assignments</span>
</div>
```

### JavaScript

```javascript
// In-memory assignment store for this prototype session (populated by
// Sections 4-5; empty here since Section 2 only wires the count display).
let assignments = [];

function getAssignmentCount() {
  return assignments.length;
}

function renderTotalCount() {
  const count = getAssignmentCount();
  const label = count === 1 ? '1 assignment' : `${count} assignments`;
  document.getElementById('hr-dashboard-total-count').textContent = `Total: ${label}`;
}

// Placeholder until View 2 (Assign New Skill Modal) exists.
function handleNewAssignmentClick() {
  console.log('[prototype] + New Assignment clicked — View 2 (Assign modal) not built yet');
}
```

Call `renderTotalCount()` from `initPage()` (extends Section 1's `initPage`, does not replace it).

### Tailwind Classes to Use

**Key classes for this section**:
- Toolbar row: `py-3 flex items-center justify-between`
- Primary button: `bg-talentpilot-600 text-white text-sm font-semibold px-4 py-2 rounded-lg hover:bg-talentpilot-700 transition-colors`
- Title: `text-2xl font-black text-gray-900`
- Count: `text-sm text-gray-500`

---

## 🔗 Dependencies

**Shared code**:
- ✅ `shared/init.js` (already loaded from Section 1)

**Prior sections**: Section 1 (`hr-dashboard.html`, `initPage()`) must exist — this section extends it, doesn't replace it.

---

## 📸 Baseline State

Extends Section 1's implementation. No prior Section 2 content to diff against.

---

## 📝 Implementation Steps

### Step 1: Toolbar row
Add the toolbar div with the "+ New Assignment" button above the placeholder block.

### Step 2: Title row
Add the "Skill Assignments" heading + total count span.

### Step 3: Wire count logic
Add `assignments` array, `getAssignmentCount()`, `renderTotalCount()`, and call `renderTotalCount()` at the end of `initPage()`.

### Step 4: Wire placeholder click handler
Add `handleNewAssignmentClick()` as a console-logged placeholder.

---

## ✅ Acceptance Criteria

### Agent-Verifiable (Puppeteer / static)

| # | Criterion | Element | Expected | How to Verify |
|---|-----------|---------|----------|----------------|
| 1 | Button renders with correct label | `#hr-dashboard-new-assignment-button` | Text = "+ New Assignment" | `textContent` |
| 2 | Button has correct classes | `#hr-dashboard-new-assignment-button` | Contains `bg-talentpilot-600` | `classList.contains` |
| 3 | Title renders | `#hr-dashboard-title` | Text = "Skill Assignments" | `textContent` |
| 4 | Count starts at 0, correct pluralization | `#hr-dashboard-total-count` | Text = "Total: 0 assignments" | `textContent` |
| 5 | Click handler wired, no error | `#hr-dashboard-new-assignment-button` | Console logs placeholder message, no thrown error | Click + console listener |
| 6 | No console/syntax errors | — | 0 errors | `node --check` + console listener |

### User-Evaluable (Qualitative)

- [ ] Button placement/size feels like a natural primary action
- [ ] Title hierarchy is clear against the header above it
- [ ] Spacing between toolbar and title row feels right, not cramped or too loose

---

## 🧪 How to Test

### Self-Verification (Agent)

No Puppeteer available in this environment (noted in Section 1) — verification is structural: grep for object IDs/classes in the file, `node --check` on the script, manual trace of `renderTotalCount()`'s pluralization logic for count=0 and count=1.

### User Qualitative Review

Open `hr-dashboard.html` (via local server, same caveat as Section 1) and evaluate the qualitative checklist above.

---

## 🐛 Common Issues & Fixes

### Issue: Total count doesn't update
**Symptom**: Count stays "Total: 0 assignments" even after `assignments` array changes later (Section 4/5)
**Cause**: `renderTotalCount()` only called once in `initPage()`, not re-called after `assignments` mutates
**Fix**: Sections 4/5's row-add/delete logic must call `renderTotalCount()` again after mutating `assignments`

---

## 🎨 Design Notes

**Visual requirements**:
- Button color must be `talentpilot-600`/`talentpilot-700` (not `blue-600`), consistent with Section 1's standardization

**UX considerations**:
- "+ New Assignment" is the primary action on this page — placement (top-right of an otherwise empty toolbar) should make that obvious even before Sections 3-5 add content below it

---

## 💡 Tips

- Keep `assignments` as a simple in-memory array for now — Section 4/5 will populate it from `DEMO_DATA`-adjacent interactive state (real assignments aren't seeded, so this starts empty by design, not by omission)

---

## ➡️ Next Section

After this section is approved: `HR-Dashboard.3-loading-empty-error-states.md`

---

## 📊 Status Tracking

**Status**: ✅ Complete
**Started**: 2026-09-03
**Completed**: 2026-09-03
**Approved By**: Vasu
**Notes**: Implemented in `hr-dashboard.html`. 7/7 structural checks passed (no Puppeteer in this environment). User approved after browser review.

---

## 🔄 Changes from Original Plan

### Issue reported after Sections 4-5 review

**Problem**: "+ New Assignment" button was right-aligned (via `flex justify-between` with an empty spacer div); user's reference screenshot shows it top-left, directly below the header.

**Root cause**: Built from this story's own illustrative HTML, which right-aligned it without checking against the real production layout closely enough — the reference screenshot wasn't available yet when this section was first built.

**Solution**: Removed the `flex justify-between` wrapper and empty spacer div; button now sits alone in a plain `<div class="py-3">`, left-aligned by default.

**Learned**: Once a real reference screenshot exists, re-check earlier "planned from spec text alone" sections against it rather than assuming they're still correct.
