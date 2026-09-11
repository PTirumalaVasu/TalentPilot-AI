# Story: Employees-Tab.5 — Edit Employee Modal

**Status:** Implemented
**Spec reference:** `05.1-employees-roster.md` (Edit Employee Panel section); PRD FR-26

**Purpose:** Rita edits a roster entry's profile fields — always available, unlike a Skill's identity-lock.

**Objects:** `edit-employee-id-readonly`, `edit-employee-fields`, `edit-employee-btn-save`

**Acceptance criteria:**
- [x] Employee ID/Code renders read-only (disabled input), never editable
- [x] Saving updates the roster row/card in place without a full re-render flash
- [x] Available regardless of `hasAssignments` (no lock, per spec)

**User-evaluable:** Does editing feel like routine maintenance, not a heavyweight operation?
