# UX Scenarios: TalentPilot-AI

> Scenario outlines connecting Trigger Map personas to concrete user journeys

**Created:** 2026-07-08  
**Author:** TalentPilot with Claude Code  
**Method:** Whiteport Design Studio (WDS)

---

## Scenario Summary

| ID | Scenario | Persona | Pages | Priority | Status |
|----|----------|---------|-------|----------|--------|
| 01 | Rita's Trust Call | Rita the Referee | 2 | ⭐ P1 | ✅ Outlined |
| 02 | Casey's Resume & Watch | Casey the Continuer | 2 | ⭐ P1 | ✅ Outlined |
| 03 | Rita's Assignment & Track | Rita the Referee | 2 | ⭐ P1 | ✅ Outlined |
| 04 | Rita's Content Curation | Rita the Referee | 1 | 🔹 P2 | ✅ Spec Complete |
| 05 | Rita's Roster Management | Rita the Referee | 3 | 🔹 P3 (Admin/Enabling) | ✅ Spec Complete |
| 06 | Rita's Pulse Check | Rita the Referee | 1 | 🔹 P2 | ✅ Outlined |

**Total Page Inventory:** 11 core views across 6 scenarios | **Total Scenarios:** 6

`[ADDED 2026-09-08]` Scenario 04 is new — added via `bmad-prd` update (PRD §4.6, FR-16–FR-19) after the original Phase 3 scenario set was outlined; it did not go through the original Phase 2/3 workshop sequence the same way 01–03 did, but follows the same Q1-Q8 Effect Mapping structure and ties to an existing Trigger Map objective (Objective 5, fast/relevant content discovery).

`[ADDED 2026-09-13]` Scenarios 05 and 06 were likewise added via later `bmad-prd`/Trigger Map updates and had never been folded into this index — a pre-existing gap (05 was created 2026-09-11 but this file was never updated for it), caught and fixed while adding 06. Scenario 05 (Employee Roster Management) is filed as pure Enabling/Admin infrastructure (P3, outside the psychological scoring model — see `06-Feature-Impact.md`'s Enabling Features section). Scenario 06 (Skill Assignment Dashboard) is P2 — scored on the real Feature-Impact rubric (3/8) since it has a genuine, if complementary, connection to Rita's driving forces, not pure plumbing.

---

## Scenarios

### [01: Rita's Trust Call](01-ritas-trust-call/01-ritas-trust-call.md)
**Persona:** Rita the Referee (PRIMARY 👥) — "Open the dashboard and simply trust what it says"  
**Pages:** Assignment Dashboard, Provenance Drill-Down  
**User Value:** Makes a confident readiness decision in minutes without cross-referencing or manual verification  
**Business Value:** Demonstrates that auto-captured signal is trustworthy; Rita's adoption validates the evidence-pipeline hypothesis  
**Format:** Storyboard (state transitions between dashboard and drill-down)

**Key Interaction:** Rita scans provenance labels (Verified · 92% / Self-reported · 14 days / Assigned · Awaiting / Needs Attention) on the Assignment Dashboard, spots inconsistencies, drills down to see raw data (watch-%, timestamp), and confirms the signal's accuracy.

---

### [02: Casey's Resume & Watch](02-caseys-resume-and-watch/02-caseys-resume-and-watch.md)
**Persona:** Casey the Continuer (SECONDARY 💼) — "Resume exactly where I left off, never self-report"  
**Pages:** Content Discovery, Resume/Continue Watching  
**User Value:** Seamless, friction-free learning with zero self-reporting burden; Netflix-style resume works perfectly on first use  
**Business Value:** Casey's passive, honest engagement generates clean auto-captured signal for Rita's dashboard; frictionless experience keeps participation honest  
**Format:** Storyboard (state transitions: assignment → discovery → watch → close → resume)

**Key Interaction:** Casey sees assigned skill with human-approved AI-surfaced content (no search), watches video to 14:32, closes tab, returns 3 days later, clicks "Continue Watching" and resumes at exactly 14:32. Watch-position is captured continuously and auto-updates Rita's dashboard.

---

### [03: Rita's Assignment & Track](03-ritas-assignment-and-track/03-ritas-assignment-and-track.md)
**Persona:** Rita the Referee (PRIMARY 👥) — "Assign a skill and trust it auto-updates without chasing anyone"  
**Pages:** Skill Assignment Flow, Assignment Confirmation & Auto-Update  
**User Value:** Administrative relief: assigns skill in < 2 minutes, optionally links content, watches dashboard auto-update with verified progress without follow-up  
**Business Value:** Closes the flywheel — assignment → passive signal generation → verified dashboard → confident next assignment, all frictionless; eliminates Rita's chasing burden  
**Format:** Screen Flow (multi-step form) + Storyboard (Rita's perception of frictionless update)

**Key Interaction:** Rita clicks [+ New Assignment], selects employee and skill, system auto-links top-approved content, Rita confirms. New row appears on dashboard: `Assigned · Awaiting first watch`. Later, as Casey watches, row auto-updates to `Verified · [watch%]` without any action from Rita.

### [04: Rita's Content Curation](04-ritas-content-curation/04-ritas-content-curation.md)
**Persona:** Rita the Referee (PRIMARY 👥) — "Close a content gap myself, right now, without waiting on a batch job"
**Pages:** Skills Tab (Content Sourcing)
**User Value:** Sources a learning-content link (search YouTube/Udemy, or paste one directly) and approves it for a Skill in under a minute, instead of leaving an assignment contentless or waiting for the next ingestion run
**Business Value:** Extends Objective 5 (fast/relevant content discovery) to cover the gap-filling case the primary AI-matched batch pipeline (§4.2) can't close same-day
**Format:** Single page with two modal sub-flows (Content Lookup, API Keys)

**Key Interaction:** Rita opens the Skills tab, sees every Skill with its approved-Content count, clicks "Find Content" on one with a gap, searches YouTube/Udemy (or pastes a link), reviews candidates with an estimated days-to-complete (at 5 hrs/day), and approves one — visible to Employees immediately, no batch job involved.

---

### [05: Rita's Roster Management](05-ritas-roster-management/05-ritas-roster-management.md)
**Persona:** Rita the Referee (PRIMARY 👥) — "This takes two minutes and I never have to think about it again"
**Pages:** Employees Tab (Roster), Create Employee Panel, Password Reveal Panel
**User Value:** Onboards a new hire herself — creates the Employee record, gets a one-time system-generated password to share out-of-band — without waiting on engineering to add them to a hardcoded list
**Business Value:** Closes the roster-provisioning gap (PRD Open Question 9); the roster reflects real headcount instead of demo data
**Format:** Screen Flow (list → create form → password reveal)

**Key Interaction:** Rita clicks "+ New Employee" from the roster list, enters Name/Email/Employee ID/Code, submits, and sees a system-generated password shown once — she copies it to share with the new hire, who is now immediately selectable in the Skill Assignment Flow (Scenario 03).

**Filed as Enabling/Admin infrastructure** (P3, outside the 8-point psychological scoring rubric) — see `06-Feature-Impact.md`'s Enabling Features section. Rita's actual design test here is whether this stays genuinely low-friction, given her named Fear #3 ("the chore just relocates instead of disappearing").

---

### [06: Rita's Pulse Check](06-ritas-pulse-check/06-ritas-pulse-check.md)
**Persona:** Rita the Referee (PRIMARY 👥) — "I see at a glance that things are basically fine, and if they're not, I know exactly who to look at"
**Pages:** Skill Assignment Dashboard (landing page)
**User Value:** Confirms org-wide readiness health, or immediately spots who needs attention, within seconds of logging in — before anyone's asked a specific staffing question
**Business Value:** Widens "primary source of truth" adoption to general check-ins, not only specific staffing calls (UJ-1's existing scope) — direct evidence toward Objective 1 and Objective 3
**Format:** Storyboard (single view, on-page states only — no page-to-page navigation required for scenario success)

**Key Interaction:** Rita logs in, lands on the new `Dashboard` landing page, and reads the org-wide stats, Assignment Progress ring, and Employee Segmentation pie chart (On Track / In Progress / Needs Attention) — the scenario succeeds the moment she has her answer, with no further click required.

**Scored on the real Feature-Impact rubric** (3/8, not filed as Enabling) — it has a genuine, if complementary, connection to Rita's Want #2/#3 and Fear #2. Its two drill-down exits (full grid, per-employee view) both reuse Scenario 01's existing page (01.1), not new pages of their own.

---

## Page Coverage Matrix

| Page | Scenario | Purpose in Flow |
|------|----------|----------------|
| Assignment Dashboard | 01 | Rita scans skill rows and sees provenance labels; identifies inconsistencies requiring attention |
| Provenance Drill-Down | 01 | Rita views raw data (watch-%, timestamp) to confirm the signal source and accuracy |
| Content Discovery | 02 | Casey sees assigned skill with human-approved AI-surfaced content recommendation ready to watch |
| Resume/Continue Watching | 02 | Casey returns to assignment and resumes video at exact position (14:32); system tracks continued progress in real-time |
| Skill Assignment Flow | 03 | Rita opens form, selects employee & skill, system auto-links approved content, Rita confirms assignment |
| Assignment Confirmation & Auto-Update | 03 | New assignment row appears on dashboard; status shows `Assigned · Awaiting first watch` |
| Skills Tab (Content Sourcing) | 04 | Rita searches YouTube/Udemy or pastes a link, reviews candidates with a days-to-complete estimate, approves one for a Skill |
| Employees Tab (Roster) | 05 | Rita sees the current roster (table/card toggle), initiates adding a new hire |
| Create Employee Panel | 05 | Rita enters Name/Email/Employee ID/Code, submits |
| Password Reveal Panel | 05 | Rita sees and copies the one-time system-generated password |
| Skill Assignment Dashboard | 06 | Rita reads org-wide stats, Assignment Progress ring, and Employee Segmentation pie chart; confirms health or spots who needs attention |

**Coverage:** 11/11 pages assigned to scenarios

**Page Not Yet Assigned:** Needs Attention Filter View — `[FLAGGED 2026-09-13]` this was never actually built as a dedicated filter control; PRD §6.2 explicitly decided against it in favor of per-row drill-down (FR-9) + visual flagging (FR-10). Scenario 06's Employee Segmentation pie chart (Needs Attention as one of its three buckets) is the closest thing that's actually shipped to this — but it's an org-wide per-Employee summary, not a row-level filter, so this line item stays only partially resolved. See `06-Feature-Impact.md`'s flagged drift.

---

## Scenario Interconnections

### The Flywheel in Three Acts

**Act 1 (Scenario 03):** Rita assigns a skill to Casey. System auto-links approved content.

**Act 2 (Scenario 02):** Casey watches the assigned content. Resume mechanics capture watch-position continuously. Same write auto-updates Rita's dashboard.

**Act 3 (Scenario 01):** Rita opens her dashboard the next day. She sees `Verified · 92% watched, 2 hours ago`. The provenance label tells her exactly what kind of signal this is (auto-captured video, not self-report). She trusts it and makes a confident readiness decision without cross-referencing or chasing.

**The Loop Closes:** Rita assigns the next skill, confident in the process. No manual chasing. No stale data. The evidence pipeline works.

---

## Trigger Map Alignment

### Business Goals
- **PRIMARY:** Prove the evidence pipeline (staleness < 5% within 60 days) — **Scenario 01 measures this directly**
- **SECONDARY:** Earn Rita's trust as primary source of truth — **Scenarios 01 & 03 demonstrate this**
- **TERTIARY:** Eliminate the self-report chore — **Scenario 02 demonstrates this**

### Personas
- **Rita the Referee (PRIMARY 👥):** Scenarios 01 & 03 (assignment & readiness decision)
- **Casey the Continuer (SECONDARY 💼):** Scenario 02 (engagement & signal generation)

### Driving Forces Addressed
- Rita's **Want:** Open dashboard and simply trust it → **Scenario 01**
- Rita's **Fear:** Dashboard looks trustworthy but hides stale data → **Scenario 01 (provenance labels mitigate this)**
- Rita's **Want:** Stop chasing people for updates → **Scenario 03 (auto-update proves no chasing needed)**
- Casey's **Want:** Resume exactly where they left off → **Scenario 02**
- Casey's **Want:** Never self-report progress → **Scenario 02 (passive capture)**
- Casey's **Fear:** Losing place and getting no credit → **Scenario 02 (resume + auto-capture address both)**

---

## POC Hypothesis Tests

Each scenario tests a critical component of the POC hypothesis:

**Scenario 01:** Does the mixed-trust labeling model (Verified vs. Self-reported vs. Needs Attention) actually change Rita's behavior? Can she trust the provenance labels and skip cross-referencing?

**Scenario 02:** Does frictionless resume + passive auto-capture keep Casey's engagement honest? Does Casey use the system as intended without feeling surveilled?

**Scenario 03:** Can Rita assign a skill in < 2 minutes with zero friction? Does the assignment-to-auto-update pipeline work without manual sync steps?

---

## Design Phase Input (Phase 4)

These three scenarios define the six pages that feed into UX Design:

- **01.1 - Assignment Dashboard:** Grid UX with provenance labels (color + text, never color-only)
- **01.2 - Provenance Drill-Down:** Modal/panel showing raw data (watch-%, timestamp, assignment date, last activity)
- **02.1 - Content Discovery:** Card-based assignment view with single human-approved AI-recommendation (no search box)
- **02.2 - Resume/Continue Watching:** Card-based resume interface with progress bar, "14 min remaining" text, large play button
- **03.1 - Skill Assignment Flow:** Multi-step form (select employee, select skill, review content, confirm)
- **03.2 - Assignment Confirmation & Auto-Update:** Assignment Dashboard with new row highlighted, status = `Assigned · Awaiting first watch`

Each page spec in Phase 4 will detail:
- Wireframe sketches
- Component definitions
- Interaction details
- Real-time update mechanisms
- Accessibility requirements

---

## Next Phase: Phase 4 - UX Design

Phase 4 (UX Design) takes each scenario and each page, and produces:
- Detailed page specifications with wireframes
- Component library definitions
- Interaction documentation
- Real-time update architecture (WebSocket, polling, sendBeacon)
- Accessibility (WCAG AA) requirements
- Responsive behavior (desktop-primary, no mobile version)

The design phase starts from Scenario 01, Step 01.1 (Assignment Dashboard) and proceeds linearly through all steps.

---

## Document Navigation

**By Scenario:**
- [Scenario 01: Rita's Trust Call](01-ritas-trust-call/01-ritas-trust-call.md)
- [Scenario 02: Casey's Resume & Watch](02-caseys-resume-and-watch/02-caseys-resume-and-watch.md)
- [Scenario 03: Rita's Assignment & Track](03-ritas-assignment-and-track/03-ritas-assignment-and-track.md)
- [Scenario 04: Rita's Content Curation](04-ritas-content-curation/04-ritas-content-curation.md)
- [Scenario 05: Rita's Roster Management](05-ritas-roster-management/05-ritas-roster-management.md)
- [Scenario 06: Rita's Pulse Check](06-ritas-pulse-check/06-ritas-pulse-check.md)

**By Page:**
- [01.1 - Assignment Dashboard](01-ritas-trust-call/01.1-assignment-dashboard/01.1-assignment-dashboard.md)
- [01.2 - Provenance Drill-Down](01-ritas-trust-call/01.2-provenance-drill-down/01.2-provenance-drill-down.md)
- [02.1 - Content Discovery](02-caseys-resume-and-watch/02.1-content-discovery/02.1-content-discovery.md)
- [02.2 - Resume/Continue Watching](02-caseys-resume-and-watch/02.2-resume-continue-watching/02.2-resume-continue-watching.md)
- [03.1 - Skill Assignment Flow](03-ritas-assignment-and-track/03.1-skill-assignment-flow/03.1-skill-assignment-flow.md)
- [03.2 - Assignment Confirmation & Auto-Update](03-ritas-assignment-and-track/03.2-assignment-confirmation-and-auto-update/03.2-assignment-confirmation-and-auto-update.md)
- [04.1 - Skills Tab (Content Sourcing)](04-ritas-content-curation/04.1-skills-content-sourcing/04.1-skills-content-sourcing.md)
- [05.1 - Employees Tab (Roster)](05-ritas-roster-management/05.1-employees-roster/05.1-employees-roster.md)
- [05.2 - Create Employee Panel](05-ritas-roster-management/05.2-create-employee/05.2-create-employee.md)
- [05.3 - Password Reveal Panel](05-ritas-roster-management/05.3-password-reveal/05.3-password-reveal.md)
- [06.1 - Skill Assignment Dashboard](06-ritas-pulse-check/06.1-skill-assignment-dashboard/06.1-skill-assignment-dashboard.md)

---

_Generated with Whiteport Design Studio framework — Phase 3 Complete_
