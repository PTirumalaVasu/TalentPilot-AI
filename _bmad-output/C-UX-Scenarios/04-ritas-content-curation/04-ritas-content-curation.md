# 04: Rita's Content Curation

**Project:** TalentPilot-AI
**Created:** 2026-09-08
**Method:** Whiteport Design Studio (WDS)

---

## Transaction (Q1)

**What this scenario covers:**
Rita opens the Skills tab, picks a Skill that has no (or thin) recommended Content yet, searches YouTube and/or Udemy for a suitable course — or pastes a link she already has in mind — reviews the candidate(s) including an estimated days-to-complete, and approves one to attach as Content for that Skill.

---

## Business Goal (Q2)

**Goal:** TERTIARY: Eliminate the Self-Report Chore → Objective 5, Fast/relevant content discovery
**Objective:** Employees only ever see relevant, HR-approved Content for an assigned Skill. Batch auto-matching (§4.2) covers most Skills over time, but a newly-added or niche Skill can sit with no matched Content until the next ingestion run — this scenario lets Rita close that gap immediately instead of waiting on the batch job or leaving an Employee's assignment contentless.

---

## User & Situation (Q3)

**Persona:** Rita the Referee (PRIMARY 👥)
**Situation:** Rita just assigned a newly-added Skill to an Employee (Scenario 03) and saw the assignment flow's own "No approved content found yet for this skill" state. Rather than leaving it contentless or waiting for tomorrow's batch ingestion run, she goes to the Skills tab to source something herself, right now.

---

## Driving Forces (Q4)

**Hope:** Find a good course in under a minute and have it show up for the Employee immediately — no waiting on a nightly job, no asking IT for help.

**Worry:** The search comes back empty or irrelevant, or she isn't sure a Udemy/YouTube result is actually appropriate, and she ends up guessing or picking something low-quality just to fill the gap.

---

## Device & Starting Point (Q5 + Q6)

**Device:** Desktop
**Entry:** Rita is on the Skills Dashboard (01.1) or mid-way through the Skill Assignment Flow (03.1) and sees a Skill has no approved Content. She clicks "Skills" in the primary nav to open the Skills tab (04.1).

---

## Best Outcome (Q7)

**User Success:**
Rita finds the Skill in the list, clicks "Find Content," searches YouTube (her only configured source, or Udemy too if SAILS's org credential is set up), sees 3-5 candidate links each with a duration and an estimated "≈ N days to complete (at 5 hrs/day)," picks the best one, and approves it. It's now visible to any Employee assigned that Skill — no batch job, no waiting.

**Business Success:**
The Skill no longer sits with a "No recommended content yet" gap; the Employee's Content Discovery list (§4.2) shows a real, HR-approved recommendation the next time they open it.

---

## Shortest Path (Q8)

1. **Skills Tab (04.1)** — Rita lands on the full list of Skills in the system, finds the one she needs, clicks "Find Content."
2. **Content Lookup panel** — She searches (or pastes a link), reviews candidates with duration/days-to-complete, and clicks Approve on the one she wants. ✓

---

## Trigger Map Connections

**Persona:** Rita the Referee (PRIMARY 👥)

**Driving Forces Addressed:**
- ✅ **Want:** Close a content gap immediately, without waiting on a batch process or asking for engineering help
- ❌ **Fear:** Ending up with no good option and having to guess, or approving something low-quality just to unblock an assignment

**Business Goal:** TERTIARY: Eliminate the Self-Report Chore → Objective 5 (fast/relevant content discovery) — extended here to cover the admin-curation gap-filling path, alongside the primary batch-matching path (§4.2)

---

## Scenario Steps

Steps are outlined one at a time after scenario creation. The first step is processed automatically.

| Step | Folder | Purpose | Exit Action |
|------|--------|---------|-------------|
| 04.1 | `04.1-skills-content-sourcing/` | See all Skills, manage source credentials, search/paste and approve Content for a Skill | Scenario complete ✓ |

---

## Related PRD Requirements

FR-16 (credential management), FR-17 (live search), FR-17a (manual link entry), FR-18 (review + attach), FR-19 (estimated days-to-complete) — `_bmad-output/planning-artifacts/prds/prd-TalentPilot-AI-2026-07-09/prd.md` §4.6.

---

_Generated with Whiteport Design Studio framework_
