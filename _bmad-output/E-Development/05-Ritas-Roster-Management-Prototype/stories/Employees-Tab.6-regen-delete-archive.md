# Story: Employees-Tab.6 — Regenerate Password + Delete/Archive Confirmations

**Status:** Implemented
**Spec reference:** `05.1-employees-roster.md` (Regenerate Password Panel, Delete/Archive Confirmation sections); PRD FR-27, FR-28

**Purpose:** Handle credential recovery and roster removal, with removal branching on assignment history.

**Objects:** `regen-password-heading`, `regen-password-summary`, `regen-password-btn-confirm`, `delete-employee-heading`, `delete-employee-summary-hard`, `delete-employee-summary-archive`, `delete-employee-btn-confirm`

**Acceptance criteria:**
- [x] Regenerate hands off directly into the Password Reveal modal (section 4) in "regenerate" mode
- [x] An Employee with `hasAssignments: true` (Casey, Morgan) shows the **archive** copy and "Archive Employee" label; confirming sets status → Archived (record retained)
- [x] An Employee with `hasAssignments: false` (Jordan, Sam) shows the **hard-delete** copy and "Remove Employee" label; confirming removes the record entirely
- [x] Canceling either modal leaves the record untouched

**Test data:** Casey/Morgan (hasAssignments=true) exercise the archive path; Jordan/Sam (hasAssignments=false) exercise the hard-delete path.

**User-evaluable:** Is it clear *before* confirming which behavior (archive vs. remove) will happen?
