# 03: Rita's Assignment & Track

**Project:** TalentPilot-AI  
**Created:** 2026-07-08  
**Method:** Whiteport Design Studio (WDS)

---

## Transaction (Q1)

**What this scenario covers:**
Rita creates a new skill assignment for an employee, selects/searches a skill, the system surfaces AI-recommended human-approved content, Rita confirms the assignment — and then, without any action from Rita, the dashboard auto-updates with verified progress as the employee watches.

---

## Business Goal (Q2)

**Goal:** POC Hypothesis Test  
**Objective:** Does the assignment-to-auto-update flow work frictionlessly? Can Rita assign once and trust the dashboard to auto-populate with verified signal without chasing?

---

## User & Situation (Q3)

**Persona:** Rita the Referee (PRIMARY 👥)  
**Situation:** Rita is at her desk and decides to assign a new must-do skill to an employee.

---

## Driving Forces (Q4)

**Hope:** Assign a skill, optionally link content, and trust that the dashboard will auto-update with verified progress without any follow-up or chasing.

**Worry:** Dashboard doesn't update, remains stale/blank, and Rita has to chase the employee anyway — the old behavior returns, making the tool worse than useless.

---

## Device & Starting Point (Q5 + Q6)

**Device:** Desktop  
**Entry:** Rita is at her desk and decides to assign a new must-do skill to an employee. She clicks a [+ New Assignment] button on the Assignment Dashboard or main navigation.

---

## Best Outcome (Q7)

**User Success:**
Rita assigns "Python Basics" to Casey in 2 minutes. System auto-links the top-approved content recommendation. Rita confirms. Done. She returns to the dashboard and sees the new row: `Assigned · Awaiting first watch`. Later that day, without Rita doing anything, the row updates to `Verified · 23% watched, 2 hours ago` as Casey watches.

**Business Success:**
The assignment flow is fast and low-friction. Auto-linking approved content means Rita never has to manually select content. Dashboard auto-updates prove the signal pipeline works — no manual sync, no chasing, no staleness.

---

## Shortest Path (Q8)

1. **Skill Assignment Flow** — Rita clicks [+ New Assignment] and the assignment modal/form opens, showing steps: select employee, select/search skill, review AI-recommended approved content, confirm.
2. **Assignment Confirmation** — Rita completes the form (selects employee, skill, auto-linked content), clicks [Assign], and returns to the Assignment Dashboard.
3. **Dashboard Auto-Update** — The new assignment row appears immediately: `Assigned · Awaiting first watch`. Later, as Casey watches the video, the row auto-updates to `Verified · [watch%]` without any further action from Rita. ✓

---

## Trigger Map Connections

**Persona:** Rita the Referee (PRIMARY 👥)

**Driving Forces Addressed:**
- ✅ **Want:** Stop chasing people for updates, assign once and trust auto-update
- ❌ **Fear:** Dashboard remains stale/blank, forcing return to manual chasing

**POC Hypothesis:** Frictionless assignment + auto-update mechanism eliminates Rita's chasing burden and closes the flywheel.

---

## Scenario Steps

Steps are outlined one at a time after scenario creation. The first step is processed automatically.

| Step | Folder | Purpose | Exit Action |
|------|--------|---------|-------------|
| 03.1 | `03.1-skill-assignment-flow/` | Open assignment form, select employee & skill, review AI-recommended content | Click [Assign] to confirm |
| 03.2 | `03.2-assignment-confirmation-and-auto-update/` | Confirm assignment completes; dashboard updates with new row; later auto-updates as employee watches | Dashboard auto-updates with verified signal ✓ |

---

_Generated with Whiteport Design Studio framework_
