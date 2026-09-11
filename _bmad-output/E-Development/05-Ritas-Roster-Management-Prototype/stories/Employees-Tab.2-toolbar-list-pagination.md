# Story: Employees-Tab.2 — Toolbar + Table/Card View + Pagination

**Status:** Implemented
**Spec reference:** `work/Employees-Tab-Work.yaml` → section-2; PRD FR-25

**Purpose:** Let Rita see, search, filter, and toggle the presentation of the current roster.

**Objects:** `employees-tab-heading-title`, `employees-tab-summary-count`, `employees-tab-search-input`, `employees-tab-filter-department`, `employees-tab-filter-position`, `employees-tab-toggle-archived`, `employees-tab-view-toggle`, `employees-tab-btn-new-employee`, `employees-table`, `employees-grid`, `employees-table-pagination`

**Acceptance criteria:**
- [x] Table is the default view; Card view toggle preserves search/filter/page state
- [x] Search, Department filter, Position filter, and Show Archived all compose correctly
- [x] Pagination renders at 15/page (verify with a synthetic >15-employee dataset during acceptance testing — only 4 seeded by default)
- [x] Table view is horizontally scrollable (`overflow-x-auto`, `min-w-[720px]`) rather than cramped at narrow widths

**User-evaluable:** Does switching Table ↔ Card feel instant and lossless (filters/search/page preserved)?
