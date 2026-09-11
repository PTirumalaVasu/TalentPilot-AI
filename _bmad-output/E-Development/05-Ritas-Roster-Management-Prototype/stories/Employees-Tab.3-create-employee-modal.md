# Story: Employees-Tab.3 — Create Employee Modal

**Status:** Implemented
**Spec reference:** `05.2-create-employee.md`; PRD FR-24

**Purpose:** Rita enters a new hire's details and creates the Employee record.

**Objects:** `create-emp-id`, `create-emp-name`, `create-emp-email`, `create-emp-position`, `create-emp-department`, `create-emp-phone`, `create-emp-location`, `create-emp-manager`, `create-emp-project`, `create-emp-technologies`, `create-emp-experience`, `create-emp-duplicate-notice`, `create-employee-btn-submit`

**Acceptance criteria:**
- [x] Submitting with ID/Name/Email blank shows the required-fields notice, modal stays open
- [x] Submitting a duplicate ID or Email (against Casey/Morgan/Jordan/Sam) shows the duplicate notice
- [x] Valid submit closes this modal and opens Password Reveal in "create" mode
- [x] Canceling (X) returns to the roster with no record created

**Test data:** Use Taylor Brooks (EMP-1005, taylor.brooks@sailssoftware.com) as the golden-path new hire.

**User-evaluable:** Does filling in just the 3 required fields feel genuinely fast (the scenario's "two minutes" Hope)?
