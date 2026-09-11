# Prototype Roadmap: Scenario 05 — Rita's Roster Management

**Project:** TalentPilot-AI
**Created:** 2026-09-11
**Method:** Whiteport Design Studio (WDS) — Phase 5 Agentic Development, [P] Prototyping

---

## Scenario Overview

Rita onboards a new hire into TalentPilot-AI herself — creating their Employee record and getting them a working login — so she can assign them a skill immediately, without waiting on engineering. Realizes PRD §4.7 (FR-24–28, Employee Roster Management) and §4.8 (FR-29, HR Admin Navigation Shell).

**Full scenario/page specs:** `_bmad-output/C-UX-Scenarios/05-ritas-roster-management/`

---

## Initiation Decisions

| Question | Decision |
|---|---|
| **Device Compatibility** | Fully Responsive (375px–1920px+). Breakpoints at 768px/1024px/1280px. Deliberately covers the Backlog item flagged in Phase 4: the left-pane nav needs a collapsed/hamburger treatment on narrow viewports — explored here, not deferred again. |
| **Design Fidelity** | Matches the existing pages' de facto style (Tailwind + the `talentpilot` blue palette, Inter font) — no formal Design System doc exists (`design_system_mode: none`), but 01.1/04.1 already share this look and this prototype stays consistent with it. |
| **Languages** | Single language (English) — skipped per project config (`product_languages: ["en"]`). |
| **Demo Data** | Reuses the canon 5-account demo roster already established in `shared/auth.js` across every other prototype folder (Rita + Casey/Morgan/Jordan/Sam) — not reinvented with new names. One new fictional hire, **Taylor Brooks**, is the deliberate "new hire" this scenario's story is about; intentionally not pre-seeded in the roster (see `data/demo-data.js`), since Rita creates them live during 05.2/05.3. |

---

## Pages

| Page | Name | Spec | Status |
|------|------|------|--------|
| 05.1 | Employees Tab (Roster) | [spec](../../C-UX-Scenarios/05-ritas-roster-management/05.1-employees-roster/05.1-employees-roster.md) | Not started |
| 05.2 | Create Employee Panel | [spec](../../C-UX-Scenarios/05-ritas-roster-management/05.2-create-employee/05.2-create-employee.md) | Not started |
| 05.3 | Password Reveal Panel | [spec](../../C-UX-Scenarios/05-ritas-roster-management/05.3-password-reveal/05.3-password-reveal.md) | Not started |

*(05.2 and 05.3 are modals over 05.1, not separate HTML files — built as part of 05.1's implementation, matching how 04.1's modals were built alongside its own page rather than as separate files.)*

---

## Known Backlog Items Folded Into This Build

Per explicit user direction, these carry over from Phase 4 rather than being handled separately beforehand:

1. **Password Reveal modal's title must be conditional** — "Employee created" (from 05.2's Create flow) vs. "Password regenerated" (from FR-28's Regenerate action). The Phase 4 HTML mock (`01-Ritas-Trust-Call-Prototype/05.1-Employees-Tab.html`) hardcoded "Employee created" for both — fix in this build.
2. **Responsive states for 05.1** — now in scope via the Fully Responsive device decision above (was undecided in Phase 4).
3. **01.1 and 04.1's nav shell** — both still show the old top-header nav (Dashboard/Skills links). This prototype introduces the new left-pane shell (FR-29) for 05.1; updating 01.1/04.1 to match is a **separate, not-yet-scheduled task** — flagged again here so it isn't lost, but not silently done as a side effect of this scenario's build (would touch prototypes outside Scenario 05's own scope).

---

## Reference Materials

- [Trigger Map Key Insights](../../B-Trigger-Map/05-Key-Insights.md) — the chore-relocation risk this whole scenario is designed against
- [PRD §4.7/§4.8](../../planning-artifacts/prds/prd-TalentPilot-AI-2026-07-09/prd.md) — FR-24 through FR-29
- [Phase 4 HTML mock](../01-Ritas-Trust-Call-Prototype/05.1-Employees-Tab.html) — starting point for this build; this prototype supersedes it as the validated version once complete

---

_Roadmap for Scenario 05 prototyping (Phase 5, [P] Prototyping workflow)_
