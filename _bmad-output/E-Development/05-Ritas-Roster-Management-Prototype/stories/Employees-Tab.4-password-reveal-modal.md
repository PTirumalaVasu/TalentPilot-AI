# Story: Employees-Tab.4 — Password Reveal Modal

**Status:** Implemented
**Spec reference:** `05.3-password-reveal.md`; PRD FR-24, FR-28

**Purpose:** Show the one-time, system-generated password — shared between the Create and Regenerate flows.

**Objects:** `password-reveal-title`, `password-reveal-summary`, `password-reveal-value`, `password-reveal-btn-copy`, `password-reveal-recovery-note`, `password-reveal-btn-done`

**Acceptance criteria:**
- [x] **Title is conditional**: "Employee created" when opened via Create (05.2), "Password regenerated" when opened via Regenerate — fixes the Phase 4 mock's hardcoded-title bug (PROTOTYPE-ROADMAP.md Backlog #1)
- [x] Copy button copies the exact displayed password and shows a toast
- [x] Done closes the modal; the new/updated Employee is visible on the roster afterward

**User-evaluable:** Does the recovery note ("use Regenerate Password") genuinely read as reassuring rather than an afterthought warning?
