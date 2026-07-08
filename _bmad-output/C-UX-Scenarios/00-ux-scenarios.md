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

**Total Page Inventory:** 7 core views across 3 scenarios | **Total Scenarios:** 3

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

**Coverage:** 6/7 pages assigned to scenarios

**Page Not Yet Assigned:** Needs Attention Filter View (skipped per user decision; integrated into Assignment Dashboard via direct drill-down on stale rows)

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

**By Page:**
- [01.1 - Assignment Dashboard](01-ritas-trust-call/01.1-assignment-dashboard/01.1-assignment-dashboard.md)
- [01.2 - Provenance Drill-Down](01-ritas-trust-call/01.2-provenance-drill-down/01.2-provenance-drill-down.md)
- [02.1 - Content Discovery](02-caseys-resume-and-watch/02.1-content-discovery/02.1-content-discovery.md)
- [02.2 - Resume/Continue Watching](02-caseys-resume-and-watch/02.2-resume-continue-watching/02.2-resume-continue-watching.md)
- [03.1 - Skill Assignment Flow](03-ritas-assignment-and-track/03.1-skill-assignment-flow/03.1-skill-assignment-flow.md)
- [03.2 - Assignment Confirmation & Auto-Update](03-ritas-assignment-and-track/03.2-assignment-confirmation-and-auto-update/03.2-assignment-confirmation-and-auto-update.md)

---

_Generated with Whiteport Design Studio framework — Phase 3 Complete_
