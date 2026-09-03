# Story HR-Dashboard.6: HR Dashboard - Pagination & Footer

**View**: HR Dashboard (Grid)
**Section**: 6 of 7
**Complexity**: Simple
**Estimated Time**: 10 minutes (planned) — pulled forward alongside Sections 4-5's accelerated build after user flagged it missing

---

## 🎯 Goal

Previous/current-page/Next pagination controls and the "App v0.1.0" footer caption, matching the reference screenshot's layout.

---

## ⚠️ Process Note

Pulled forward out of sequence: after Sections 4-5 were built to match the reference screenshot, the user reported pagination was missing (along with a button-placement issue on Section 2). Built now rather than waiting for the original Section 6 slot, since it's a small, well-specified addition and the user is actively reviewing this exact page.

---

## 📋 What Was Built

### HTML

```html
<div id="hr-dashboard-pagination" hidden class="flex items-center justify-center gap-2 mt-4 text-sm">
  <button id="hr-dashboard-page-prev" onclick="handlePageChange(-1)"
          class="px-3 py-1 rounded border border-gray-200 text-gray-400 disabled:cursor-not-allowed hover:border-gray-300 disabled:hover:border-gray-200">Previous</button>
  <button id="hr-dashboard-page-current" class="px-3 py-1 rounded border border-talentpilot-600 bg-talentpilot-50 text-talentpilot-700 font-medium">1</button>
  <button id="hr-dashboard-page-next" onclick="handlePageChange(1)"
          class="px-3 py-1 rounded border border-gray-200 text-gray-400 disabled:cursor-not-allowed hover:border-gray-300 disabled:hover:border-gray-200">Next</button>
</div>
<p class="text-center text-xs text-gray-400 mt-8">App v0.1.0</p>
```

### JavaScript

```javascript
const PAGE_SIZE = 50; // matches production's default page size
let currentPage = 1;

function totalPages() {
  return Math.max(1, Math.ceil(assignments.length / PAGE_SIZE));
}

function handlePageChange(delta) {
  const newPage = Math.max(1, Math.min(currentPage + delta, totalPages()));
  if (newPage !== currentPage) {
    currentPage = newPage;
    renderGrid();
  }
  renderPaginationControls();
}

function renderPaginationControls() {
  document.getElementById('hr-dashboard-page-current').textContent = currentPage;
  document.getElementById('hr-dashboard-page-prev').disabled = currentPage === 1;
  document.getElementById('hr-dashboard-page-next').disabled = currentPage >= totalPages();
}
```

`renderContent()` shows/hides `#hr-dashboard-pagination` alongside the grid/empty state; `handleDeleteRow()` re-checks it when a delete empties the list.

---

## 🚫 Explicitly Out of Scope

- With only 5 sample assignments and `PAGE_SIZE = 50`, pagination always shows "1 of 1" with both buttons disabled — this matches production's behavior for any HR Admin with under 50 assignments; it's not broken, just correctly inert at this data volume. `renderGrid()` doesn't yet actually slice `assignments` by page (no reason to at 5 items) — that slicing logic is a real gap if this prototype's sample dataset ever grows past `PAGE_SIZE`, noted here rather than silently incomplete.

---

## ✅ Acceptance Criteria

### Agent-Verifiable (static / structural)

| # | Criterion | How Verified |
|---|-----------|--------------|
| 1 | Previous/current/Next controls present | grep for object IDs |
| 2 | Footer caption "App v0.1.0" present | grep |
| 3 | Pagination hidden during loading/empty/error, shown with grid | Code read: `renderContent()` |
| 4 | Previous disabled on page 1, Next disabled on last page | Code read: `renderPaginationControls()` |
| 5 | No syntax errors | `node --check` |

### User-Evaluable (Qualitative)

- [ ] Pagination visually matches the reference screenshot's position/style
- [ ] Footer caption reads as a quiet trailing detail, not competing for attention

---

## 📊 Status Tracking

**Status**: ✅ Complete & Approved
**Started**: 2026-09-03
**Completed**: 2026-09-03
**Approved By**: Vasu — "Overall admin dashboard looks good for me" (2026-09-03)
**Notes**: Built alongside the Section 2 button-placement fix, both in response to the same round of user feedback.

---

## 🔄 Changes from Original Plan

- Pulled forward from its original Section 6 slot (after Section 4-5, before Section 7) directly in response to user feedback that it was missing from the just-reviewed page — not built in the original sequential order.

### Issue found during the drill-down modal's debugging (Section 8)

**Problem**: This section combined the native `hidden` attribute with Tailwind's `flex` class (`hidden class="flex items-center justify-center ..."`) — the same root-cause bug diagnosed in `HR-Dashboard.8-provenance-drilldown.md`. Author-stylesheet `.flex{display:flex}` beats the user-agent `[hidden]{display:none}` rule regardless of the attribute's state, so this row was likely visible from page load rather than truly hidden until the grid loaded.

**Solution**: Same fix applied here — replaced `hidden` with `style="display: none"` on the static element, and both JS toggle points (`renderContent()`, `handleDeleteRow()`) now set `pagination.style.display = 'none' / 'flex'` instead of `.hidden`.
