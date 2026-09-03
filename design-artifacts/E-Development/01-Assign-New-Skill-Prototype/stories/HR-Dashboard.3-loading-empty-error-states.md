# Story HR-Dashboard.3: HR Dashboard - Loading / Empty / Error States

**View**: HR Dashboard (Grid)
**Section**: 3 of 7
**Complexity**: Medium
**Estimated Time**: 15 minutes

---

## 🎯 Goal

Build the three non-happy-path renders of the main content area, and the content container Sections 4-5 will later populate with the real grid. Empty must be built and tested as the **true default** — this prototype has no seeded Assignments, same as the real backend.

---

## 📋 What to Build

### HTML Elements

Replaces the Section 3-7 placeholder block from Section 2, inside `<main id="hr-dashboard-main">`:

```html
<div id="hr-dashboard-content">
  <!-- Loading state -->
  <div id="hr-dashboard-loading" class="space-y-3">
    <div class="h-6 bg-gray-100 rounded animate-pulse w-full"></div>
    <div class="h-6 bg-gray-100 rounded animate-pulse w-full"></div>
    <div class="h-6 bg-gray-100 rounded animate-pulse w-full"></div>
  </div>

  <!-- Empty state -->
  <div id="hr-dashboard-empty" hidden class="text-center py-12 border-2 border-dashed border-gray-200 rounded-lg text-gray-500">
    No assignments yet — click <strong>+ New Assignment</strong> to get started
  </div>

  <!-- Error state -->
  <div id="hr-dashboard-error" hidden class="text-center py-12 border-2 border-dashed border-red-200 rounded-lg">
    <p class="text-red-700 mb-3">Couldn't load your assignments.</p>
    <button id="hr-dashboard-error-retry" onclick="handleRetryLoad()"
            class="bg-talentpilot-600 text-white text-sm font-semibold px-4 py-2 rounded-lg hover:bg-talentpilot-700 transition-colors">
      Try again
    </button>
  </div>

  <!-- Grid (Sections 4-5 render here once assignments.length > 0) -->
  <div id="hr-dashboard-grid" hidden></div>
</div>
```

### JavaScript

```javascript
// Simulated load — this prototype has no real backend, so "loading" is a
// short artificial delay and "error" only occurs if forced (see test hook
// below). Resolves to empty by default since `assignments` starts at [].
function simulateLoad(forceError = false) {
  showOnly('hr-dashboard-loading');

  window.setTimeout(() => {
    if (forceError) {
      showOnly('hr-dashboard-error');
      return;
    }
    renderContent();
  }, 400);
}

// Decides which of empty/grid to show based on current `assignments` state.
// Sections 4-5 extend this once the grid itself exists; for now (0 items
// always) it only ever reaches the empty branch.
function renderContent() {
  if (assignments.length === 0) {
    showOnly('hr-dashboard-empty');
  } else {
    showOnly('hr-dashboard-grid');
  }
}

function showOnly(idToShow) {
  ['hr-dashboard-loading', 'hr-dashboard-empty', 'hr-dashboard-error', 'hr-dashboard-grid'].forEach((id) => {
    document.getElementById(id).hidden = id !== idToShow;
  });
}

function handleRetryLoad() {
  simulateLoad();
}

// Test-only console hook (not a UI element) so the error state can actually
// be seen during review, since there's no real backend to fail against.
// Documented here, not a new feature — purely a manual-testing affordance.
window.__simulateError = () => simulateLoad(true);
```

Call `simulateLoad()` at the end of `initPage()` (after Section 1/2's setup).

### Tailwind Classes to Use

**Key classes for this section**:
- Skeleton row: `h-6 bg-gray-100 rounded animate-pulse w-full`
- Empty box: `text-center py-12 border-2 border-dashed border-gray-200 rounded-lg text-gray-500`
- Error box: `text-center py-12 border-2 border-dashed border-red-200 rounded-lg`
- Retry button: same primary-button pattern as Section 2 (`bg-talentpilot-600 ... hover:bg-talentpilot-700`)

---

## 🔗 Dependencies

**Shared code**: `shared/init.js` (already loaded)
**Prior sections**: Sections 1-2 must exist. This section **replaces** the placeholder div Section 2 left in place.

---

## 📸 Baseline State

Replaces Section 2's placeholder `<div>` (the "🚧 Sections 3-7 coming next" block) — that placeholder is removed as part of this section, not left behind.

---

## 📝 Implementation Steps

### Step 1: Content container + three state divs
Add `#hr-dashboard-content` with loading/empty/error/grid children, replacing the Section 2 placeholder.

### Step 2: State-switching logic
Add `simulateLoad()`, `renderContent()`, `showOnly()`, `handleRetryLoad()`.

### Step 3: Wire into initPage
Call `simulateLoad()` at the end of `initPage()`.

### Step 4: Test hook for error state
Add `window.__simulateError()` as documented, console-only escape hatch for manual review.

---

## ✅ Acceptance Criteria

### Agent-Verifiable (static / structural)

| # | Criterion | Element | Expected | How to Verify |
|---|-----------|---------|----------|----------------|
| 1 | All 4 state elements present | `#hr-dashboard-loading/-empty/-error/-error-retry` | Exist in DOM | grep/id check |
| 2 | Loading visible, others hidden on initial render | — | `#hr-dashboard-loading` no `hidden`; others have `hidden` | Static HTML read |
| 3 | Empty message text correct | `#hr-dashboard-empty` | Contains "No assignments yet" | `textContent` |
| 4 | Error message + retry button text correct | `#hr-dashboard-error` | "Couldn't load your assignments." + "Try again" | `textContent` |
| 5 | `showOnly()` toggles exactly one visible at a time | — | Code trace: all 4 ids covered, no overlap | Manual code read |
| 6 | No syntax errors | — | `node --check` passes | Static |

### User-Evaluable (Qualitative — needs your eyes)

- [ ] After the ~400ms simulated load, the empty state appears (this is the true first-run experience — confirm it doesn't feel broken or like something failed to load)
- [ ] Skeleton rows look like a believable stand-in for the future grid, not jarring
- [ ] Error state (via `window.__simulateError()` in the browser console) reads clearly and Retry visibly re-triggers loading

---

## 🧪 How to Test

### Self-Verification (Agent)
No Puppeteer in this environment — structural checks only (element presence, hidden-attribute state, text content, syntax check), consistent with Sections 1-2.

### User Qualitative Review
1. Reload `hr-dashboard.html` (local server, same CORS caveat)
2. Watch the ~400ms loading → empty transition
3. Open the browser console, run `__simulateError()`, confirm the error state renders and Retry brings back loading → empty

---

## 🐛 Common Issues & Fixes

### Issue: All three states show at once
**Symptom**: Loading, empty, and error all visible simultaneously
**Cause**: `showOnly()` not called, or called with a typo'd id
**Fix**: Verify `showOnly()` iterates the same 4 ids used in the HTML exactly

### Issue: Empty state never appears, stuck on loading
**Symptom**: Skeleton never resolves
**Cause**: `simulateLoad()` not called from `initPage()`, or the `setTimeout` callback throws before reaching `renderContent()`
**Fix**: Confirm `simulateLoad()` is called at the end of `initPage()`; check console for a thrown error inside the timeout callback

---

## 🎨 Design Notes

**Visual requirements**:
- Empty and error boxes use the same `py-12 border-2 border-dashed rounded-lg` shape, differing only by border/text color (gray vs red) and content — keep them visually parallel, not redesigned independently

**UX considerations**:
- The empty state must not read as an error or a broken page — it's the expected first-run state for a fresh HR Admin session

---

## 💡 Tips

- `window.__simulateError()` is a manual QA convenience, not a real feature — don't wire any visible UI button to it

---

## ➡️ Next Section

After this section is approved: `HR-Dashboard.4-accordion-structure.md`

---

## 📊 Status Tracking

**Status**: ✅ Complete
**Started**: 2026-09-03
**Completed**: 2026-09-03
**Approved By**: Vasu (superseded by the Section 4+5 combined build below — see Round 2 notes)
**Notes**: Loading/empty/error state machine itself (structural criteria 1-6) verified and unchanged. The "sample data not showing" issue thread ended with the user directing an accelerated build straight into Sections 4-5's real accordion+table, which now supersedes this story's interim placeholder/flat-list fixes — those were transitional, not the final design.

---

## 🔄 Changes from Original Plan

### Issue reported during Step 4d review

**Problem**: User reported "sample data is not showing in the mockup screen" — the dashboard rendered the empty state and stayed there.

**Root cause**: `assignments` was initialized as `[]` because the real backend seeds zero Assignment rows (only Employees/Skills/Content are pre-seeded) — this was a deliberate choice to match production's true first-run state (see work file's `edge_cases`). But that meant there was no way to visually verify anything beyond the empty state during review, and Sections 4-5 (which render actual rows) don't exist yet either.

**Solution**: Added 5 synthesized sample assignment records to `data/demo-data.json` (`sampleAssignments`) — built from the real seeded employees/skills (since no real Assignment rows exist to pull from), spanning every status/provenance combination Sections 4-5 will need (In Progress w/ %, Completed, Not Started, Self-reported, and a 10-day-stale Needs Attention row). `assignments` now loads from this in `initPage()`. Since the real grid (accordion + table) is still Sections 4-5's job, `renderContent()`'s grid branch shows an honest interim placeholder ("N sample assignments loaded — full grid UI is Sections 4-5") rather than faking a populated table ahead of schedule.

**Code change**: `data/demo-data.json` — added `sampleAssignments` array + note; `hr-dashboard.html` — `initPage()` now sets `assignments` from `DEMO_DATA.sampleAssignments`, `renderContent()`'s grid branch renders a count-confirming placeholder instead of an empty div.

**Learned**: When seed/real data has zero rows for something the prototype needs to visually demonstrate, say so explicitly in the roadmap *before* building the state that will show it — the empty-state decision was individually correct (matches production) but its interaction with "there's nothing to look at yet during early-section review" wasn't called out to the user in advance. Flag that tradeoff proactively next time instead of waiting for it to surface as a bug report.

### Round 2: "assignment list not showing" (follow-up on the same issue)

**Problem**: The count-confirming placeholder message ("N sample assignments loaded...") didn't satisfy the request — user wanted to actually see the list of assignments, not a message about them.

**Root cause**: Misjudged the fix — a text confirmation proves data exists but doesn't show it, and "showing" was the literal ask both times.

**Resolution (user decision, asked directly rather than guessing again)**: Added a deliberately plain flat list (employee — skill — status/percentage per row, no grouping/pills/progress-bars/actions) into the grid slot. Explicitly NOT the final Section 4-5 design — that grouped-accordion table with status pills, progress bars, staleness formatting, and row actions is still built on the original schedule. This flat list exists solely so real sample data is visibly present now.

**Learned**: On a second failed attempt at the same issue, stop guessing and ask — `AskUserQuestion` surfaced that "flat list now, styled table still later" was the actual want, distinct from either of my two unprompted guesses (message-only, or skip-ahead-and-build-everything).
