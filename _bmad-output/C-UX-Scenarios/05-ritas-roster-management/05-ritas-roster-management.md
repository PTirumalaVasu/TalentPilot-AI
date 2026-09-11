# 05: Rita's Roster Management

**Project:** TalentPilot-AI
**Created:** 2026-09-11
**Method:** Whiteport Design Studio (WDS)

---

## Transaction (Q1)

**What this scenario covers:**
Rita onboards a new hire into TalentPilot-AI herself — creating their Employee record and getting them a working login — so she can assign them a skill immediately, without waiting on engineering to add them to a hardcoded list.

---

## Business Goal (Q2)

**Goal:** Secondary — Earn HR's Trust
**Objective:** Objective 2, feature-complete launch. This is an enabling/infrastructure chain, not a direct driving-force fulfillment (see Trigger Map's Feature-Impact "Enabling Features" section) — it's a structural precondition for Objective 2 and indirectly for the Primary Goal, since the Skill Assignment Flow (FR-1) cannot target an Employee who doesn't exist in the system yet.

---

## User & Situation (Q3)

**Persona:** Rita the Referee (Primary 👥)
**Situation:** Rita is at her desk mid-morning. She's just been told a new hire starts Monday and needs onboarding skills assigned before their first day — but right now, the only employees in the system are the ones that were there when the pilot launched.

---

## Driving Forces (Q4)

**Hope:** This takes two minutes and I never have to think about it again.

**Worry:** This becomes yet another system I have to maintain on top of everything else.

---

## Device & Starting Point (Q5 + Q6)

**Device:** Desktop
**Entry:** Rita is already on the Dashboard — her daily entry point — and clicks **Employees** in the left-side nav because she needs to add the new hire before she can assign them anything.

---

## Best Outcome (Q7)

**User Success:**
Rita creates the new Employee record, gets a system-generated password on screen, copies it to share with the new hire, and the employee is immediately selectable in the Skill Assignment Flow — all in one sitting, no second system, no waiting on anyone.

**Business Success:**
The roster reflects real headcount for the first time — TalentPilot-AI can onboard an actual new hire without a demo-data workaround, closing the roster-provisioning gap named in PRD Open Question 9.

---

## Shortest Path (Q8)

1. **Employees Tab (Roster List)** — Rita arrives via the left nav, sees the current roster, clicks "+ New Employee"
2. **Employees Tab (Create Employee panel)** — Rita enters Name, Email, and Employee ID/Code (the only required fields), submits
3. **Employees Tab (Password Reveal)** — Rita sees the system-generated password shown once, copies it to share with the new hire out-of-band ✓

---

## Trigger Map Connections

**Persona:** Rita the Referee (Primary)

**Driving Forces Addressed:**
- ✅ **Want:** "This isn't a second system you have to maintain — it's the same place you already work" (Rita's persona doc, "What Rita Needs to See on the Dashboard" #5)
- ❌ **Fear:** "The chore just moves, instead of disappearing" — this scenario's actual design test is whether the 3-step path above stays this short in practice, or grows into exactly the kind of relocated chore Rita fears

**Business Goal:** Secondary — Earn HR's Trust, Objective 2 (feature-complete launch); structurally enables the Primary Goal's Assignment Flow

---

## Scenario Steps

Steps are outlined one at a time after scenario creation. The first step is processed automatically.

| Step | Folder | Purpose | Exit Action |
|------|--------|---------|-------------|
| 05.1 | `05.1-employees-roster/` | See the current roster, initiate adding a new hire | Clicks "+ New Employee" |
| 05.2 | `05.2-create-employee/` | Enter the new hire's identifying details | Submits the form |
| 05.3 | `05.3-password-reveal/` | Receive the one-time system-generated password | Copies password, closes panel — scenario success ✓ |

**First step** (05.1) includes full entry context (Q3 + Q4 + Q5 + Q6).
**On-step interactions** (that don't leave the step) are documented as storyboard items within each page spec — e.g., the Employees Tab's search/filter and archived-toggle live within 05.1 as on-page interactions, not separate steps.
