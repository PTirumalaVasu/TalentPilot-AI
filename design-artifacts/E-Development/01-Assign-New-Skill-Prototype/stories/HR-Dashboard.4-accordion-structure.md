# Story HR-Dashboard.4: HR Dashboard - Assignment Grid — Accordion Structure

**View**: HR Dashboard (Grid)
**Section**: 4 of 7
**Complexity**: Medium
**Estimated Time**: 20 minutes (planned) — built together with Section 5 in an accelerated pass, see note below

---

## 🎯 Goal

Employee-grouped accordion shell: group header (name + skill count + chevron), expand/collapse behavior, alphabetical sort.

---

## ⚠️ Process Note

This section was **not** built through the normal 4a → 4b → 4c loop in isolation. During Section 3's review, the user shared a screenshot of the real production HR Dashboard (`localhost:5173/hr/dashboard`) and directly requested the actual grouped-accordion table with the exact production column layout (Assigned Skill, Status, Progress, Last Updated, Actions). Sections 4 and 5 were implemented together in one pass to match that reference, rather than sequentially with separate announce/story/implement rounds each. This story file documents Section 4's portion of that combined implementation, created retroactively rather than just-in-time before coding, since the reference screenshot already fully specified requirements normally gathered in Step 4a.

See `HR-Dashboard.5-table-rows.md` for the row-content portion of the same implementation.

---

## 📋 What Was Built

### HTML (generated dynamically in `renderGrid()`, not static markup)

```html
<div id="hr-dashboard-employee-group-{employeeId}" class="border-b border-gray-200 [border-b-0 on last]">
  <button onclick="toggleEmployeeGroup('{employeeId}')"
          class="w-full flex items-center justify-between px-4 py-3 text-left font-medium text-gray-900 hover:bg-gray-50 transition-colors">
    <span class="font-semibold">{Employee Name} ({N} skills)</span>
    <span id="hr-dashboard-employee-chevron-{employeeId}" class="text-gray-500 transition-transform [rotate-180 if expanded]">▼</span>
  </button>
  <!-- table (Section 5) renders here only when expanded -->
</div>
```

### JavaScript

```javascript
const expandedGroups = new Set();

function toggleEmployeeGroup(employeeId) {
  if (expandedGroups.has(employeeId)) expandedGroups.delete(employeeId);
  else expandedGroups.add(employeeId);
  renderGrid();
}

function groupAssignmentsByEmployee(rows) {
  const grouped = new Map();
  rows.forEach((row) => {
    if (!grouped.has(row.employee_id)) grouped.set(row.employee_id, { name: row.employee_name, rows: [] });
    grouped.get(row.employee_id).rows.push(row);
  });
  return grouped;
}
```

`renderGrid()` (shared with Section 5) sorts group keys alphabetically by employee name via `localeCompare`, matching production's `Array.from(groupedAssignments.keys()).sort()` behavior.

### Tailwind Classes Used

- Group header: `w-full flex items-center justify-between px-4 py-3 text-left font-medium text-gray-900 hover:bg-gray-50 transition-colors`
- Chevron: `text-gray-500 transition-transform`, `rotate-180` when expanded
- Container: `bg-white rounded-lg overflow-hidden shadow-sm`

---

## 🔗 Dependencies

Sections 1-3 (page shell, toolbar/count, state container). Section 5 (table rows) renders inside this section's expanded panel — the two are implemented in the same `renderGrid()` function, not independently composable.

---

## ✅ Acceptance Criteria

### Agent-Verifiable (static / structural)

| # | Criterion | How Verified |
|---|-----------|--------------|
| 1 | Groups sorted alphabetically by employee name | Code read: `.sort((a,b) => name.localeCompare(name))` |
| 2 | Collapsed by default (matches production) | `expandedGroups` starts as empty `Set()` |
| 3 | Toggle click adds/removes from `expandedGroups` and re-renders | Code read: `toggleEmployeeGroup()` |
| 4 | Chevron rotates on expand | `rotate-180` class conditional on `isExpanded` |
| 5 | No syntax errors | `node --check` |

### User-Evaluable (Qualitative — needs your eyes)

- [ ] Matches the reference screenshot's accordion look (header row, chevron, spacing)
- [ ] Expand/collapse feels responsive, no visible flicker
- [ ] Multiple groups can be expanded independently

---

## 📊 Status Tracking

**Status**: ✅ Complete & Approved
**Started**: 2026-09-03
**Completed**: 2026-09-03
**Approved By**: Vasu — "Overall admin dashboard looks good for me" (2026-09-03)
**Notes**: See process note above. Combined implementation lives entirely in `hr-dashboard.html`'s `renderGrid()` function.

---

## 🔄 Changes from Original Plan

- Built together with Section 5 in one accelerated pass, in direct response to the user's reference screenshot request during Section 3's review — not sequential 4a→4g per section as originally planned. Both sections' object IDs and acceptance criteria from the original work file are preserved; only the build *process* (announce/story/implement cadence) was compressed.
