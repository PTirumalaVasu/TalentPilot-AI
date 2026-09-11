# Logical View Map — Scenario 05: Rita's Roster Management

**Created:** 2026-09-11
**Confirmed by:** TalentPilot

---

## Views

### View 1: Employees Tab

**File:** `05.1-Employees-Tab.html` (single file — matches 04.1 Skills Tab's precedent of one page hosting all its own modals)

**Base state used by:** Scenario step 05.1

**Modal overlays used by:**
| Modal | Scenario Step | Source FR |
|-------|---------------|-----------|
| Create Employee Panel | 05.2 | FR-24 |
| Password Reveal Panel | 05.3 (also reused by Regenerate) | FR-24, FR-28 |
| Edit Employee Panel | *(on-page interaction, no dedicated scenario step)* | FR-26 |
| Regenerate Password Confirmation | *(on-page interaction, no dedicated scenario step)* | FR-28 |
| Delete/Archive Confirmation | *(on-page interaction, no dedicated scenario step)* | FR-27 |

**No other logical views exist in this scenario.** All 3 scenario steps (05.1–05.3) and the additional on-page interactions from 05.1's spec resolve to this one view.

---

## Build Order

1. Employees Tab — base state (left-pane nav shell, toolbar, table/card toggle, sample roster, pagination)
2. Create Employee Panel (05.2)
3. Password Reveal Panel (05.3) — shared by Create and Regenerate
4. Edit Employee Panel
5. Regenerate Password Confirmation
6. Delete/Archive Confirmation

---

## Notes

- This view introduces the new left-pane nav shell (PRD FR-29) for the first time in this prototype tree — 01.1 and 04.1 (in the sibling `01-Ritas-Trust-Call-Prototype/` folder) still use the old top-header nav. Not updated as part of this build (see PROTOTYPE-ROADMAP.md's Known Backlog Items #3).
- A Phase 4 HTML mock already exists at `../01-Ritas-Trust-Call-Prototype/05.1-Employees-Tab.html` — this build supersedes it as the validated, fully-responsive, acceptance-testable version, built fresh in this scenario's own prototype folder rather than edited in place.
