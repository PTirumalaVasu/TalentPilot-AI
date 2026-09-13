# 06: Rita's Pulse Check

**Project:** TalentPilot-AI
**Created:** 2026-09-13
**Method:** Whiteport Design Studio (WDS)

---

## Transaction (Q1)

**What this scenario covers:**
Rita confirms the org's overall skill-readiness health at a glance, and spots exactly who needs attention, without opening the full row grid first.

---

## Business Goal (Q2)

**Goal:** Secondary — Earn HR's Trust
**Objective:** Objective 3, "Make trust legible, not just present" (every data point carries visible evidence, not a uniform-looking grid) — applied here at the org-wide level rather than the per-row level FR-8/9/10 already cover. Also reinforces Objective 1, "become HR's primary source of truth" (dashboard usage analytics).

---

## User & Situation (Q3)

**Persona:** Rita the Referee (Primary 👥)
**Situation:** Start of Rita's workday, at her desk. She logs into TalentPilot-AI out of habit — the same way she used to open the shared spreadsheet daily — before anyone has asked her a specific staffing question yet.

---

## Driving Forces (Q4)

**Hope:** I see at a glance that things are basically fine, and if they're not, I know exactly who to look at.

**Worry:** A clean-looking summary number is quietly masking two or three people who are actually falling behind.

---

## Device & Starting Point (Q5 + Q6)

**Device:** Desktop
**Entry:** Rita logs into TalentPilot-AI at her desk, first thing in the morning — the `Dashboard` nav entry now opens directly on this landing page instead of the row grid.

---

## Best Outcome (Q7)

**User Success:**
Rita confirms org-wide readiness is healthy — or immediately spots the handful of employees flagged Needs Attention — within seconds of logging in, before anyone has asked her a specific staffing question.

**Business Success:**
TalentPilot-AI becomes Rita's habitual first stop even for a general check-in, not only when a specific staffing question comes in (UJ-1's existing scope) — direct evidence toward Objective 1 (primary source of truth) and Objective 3 (trust made legible at a glance, org-wide).

---

## Shortest Path (Q8)

1. **Skill Assignment Dashboard (06.1)** — Rita lands here right after login: Total Employees / Total Skills Assigned / Total Completed, the Assignment Progress ring, and the Employee Segmentation pie chart (On Track / In Progress / Needs Attention). She confirms overall health, or immediately sees who needs attention. ✓

---

## Trigger Map Connections

**Persona:** Rita the Referee (Primary)

**Driving Forces Addressed:**
- ✅ **Want:** "Make a fast, confident readiness call under real pressure" / "Stop chasing people for updates" (Rita's persona doc, Wants #3 and #2) — extended here to a general check-in, not only a specific staffing question
- ❌ **Fear:** "A dashboard that looks more trustworthy than it actually is" (Rita's persona doc, Fear #2) — the real design risk this scenario tests: does the aggregate view actually surface real problems, or does it just look reassuring?

**Business Goal:** Secondary — Earn HR's Trust, Objective 3 (trust legible, not just present) + Objective 1 (primary source of truth)

**Note:** Unlike Scenario 05 (filed as pure Enabling Feature infrastructure), this scenario was scored on the Feature-Impact rubric (3/8 — Medium/Primary) because it has a genuine, if complementary, connection to Rita's named driving forces — see `06-Feature-Impact.md`'s 2026-09-13 addition.

---

## Scenario Steps

Steps are outlined one at a time after scenario creation. The first step is processed automatically.

| Step | Folder | Purpose | Exit Action |
|------|--------|---------|-------------|
| 06.1 | `06.1-skill-assignment-dashboard/` | See org-wide stats, Assignment Progress ring, and Employee Segmentation pie chart; confirm health or spot who needs attention | Scenario complete ✓ (drilling into the full grid or a specific employee is Scenario 01's territory — `Skill Assignments`/01.1, not a new page here) |

---

## Related PRD Requirements

FR-31 (org-wide stats), FR-32 (Assignment Progress + Employee Segmentation), FR-33 (drill-down exits, owned by page 01.1) — `_bmad-output/planning-artifacts/prds/prd-TalentPilot-AI-2026-07-09/prd.md` §4.10.

---

_Generated with Whiteport Design Studio framework_
