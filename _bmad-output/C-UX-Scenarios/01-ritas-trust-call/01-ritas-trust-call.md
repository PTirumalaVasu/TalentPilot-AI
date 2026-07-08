# 01: Rita's Trust Call

**Project:** TalentPilot-AI  
**Created:** 2026-07-08  
**Method:** Whiteport Design Studio (WDS)

---

## Transaction (Q1)

**What this scenario covers:**
Rita opens her daily dashboard to make a confident readiness decision on who's ready for a critical project assignment — filtering through 15–20 employee rows, spotting inconsistencies, and drilling down on labeling to confirm verified vs. self-reported signal.

---

## Business Goal (Q2)

**Goal:** PRIMARY: Prove the evidence pipeline  
**Objective:** Staleness below 5% within 60 days of launch — Rita's use of verified labels without second-guessing (instead of cross-referencing her memory against the spreadsheet) is the literal measurement that this hypothesis holds.

---

## User & Situation (Q3)

**Persona:** Rita the Referee (PRIMARY 👥)  
**Situation:** It's Wednesday morning at SAILS Software. A project lead Slack-messages Rita asking "who can we staff on the Q3 skills initiative?" Rita is at her desk, and she needs to answer this question in minutes with confidence — not hours of manual verification.

---

## Driving Forces (Q4)

**Hope:** Open the dashboard and instantly trust which rows are verified so she can answer the readiness question without a second thought.

**Worry:** The dashboard looks professional but hides stale data behind polished design, causing her to make a confident staffing call on wrong information.

---

## Device & Starting Point (Q5 + Q6)

**Device:** Desktop  
**Entry:** Rita is at her desk when the project lead Slack-messages asking "who can we staff on the Q3 initiative?" She clicks the TalentPilot-AI bookmark in her browser and opens the Assignment Dashboard.

---

## Best Outcome (Q7)

**User Success:**
Rita filters to the relevant skills, sees three employees marked "Verified · 100% watched" and one marked "Self-reported · Not updated in 21 days," and confidently tells the project lead "Three are ready, one needs attention" — all in 90 seconds, with no cross-reference to the spreadsheet.

**Business Success:**
Rita used the mixed-trust labeling model as intended; she didn't mistake self-reported for verified; the staleness metric shows < 5% of dashboard rows are more than 5 days stale.

---

## Shortest Path (Q8)

1. **Assignment Dashboard** — Rita scans the skill rows and immediately sees provenance labels (Verified · 92% / Self-reported · 14 days / Assigned · Awaiting / Needs Attention) next to each employee name; she spots the inconsistency (one employee verified, another stale).
2. **Provenance Drill-Down** — Rita clicks on the stale row to see the raw data (watch-%, timestamp). ✓

---

## Trigger Map Connections

**Persona:** Rita the Referee (PRIMARY 👥)

**Driving Forces Addressed:**
- ✅ **Want:** Open dashboard and simply trust what it says (no cross-referencing needed)
- ❌ **Fear:** Dashboard looks trustworthy but hides stale/unverified data, causing confident wrong calls

**Business Goal:** PRIMARY: Prove the evidence pipeline — staleness < 5% within 60 days

---

## Scenario Steps

Steps are outlined one at a time after scenario creation. The first step is processed automatically.

| Step | Folder | Purpose | Exit Action |
|------|--------|---------|-------------|
| 01.1 | `01.1-assignment-dashboard/` | See provenance labels at a glance and identify inconsistencies | Click on a stale row to see raw data |
| 01.2 | `01.2-provenance-drill-down/` | View the raw data (watch-%, timestamp) to confirm the signal source | Scenario complete ✓ |

---

_Generated with Whiteport Design Studio framework_
