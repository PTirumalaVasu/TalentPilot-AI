---
status: proposed
source: User request during Phase 5 Prototyping (2026-09-03) — "create a story to show the skills in the skill tab in admin dashboard and also add the new skills to the list"
relatedPrototype: design-artifacts/E-Development/01-Assign-New-Skill-Prototype/hr-dashboard.html
---

# Epic: Skill Catalog Management

## Overview

The real production HR Dashboard header has a "Skills" nav item next to "Dashboard" — captured during Reverse Engineering (`_bmad-output/planning-artifacts/specs/page-hr-dashboard.md`) as a **deliberate dead link** (`href="#"`, no destination), matching the actual current production code. This epic proposes giving that nav item a real destination: a Skills tab where an HR Admin can see the organization's skill catalog and add new skills to it.

Today, skills only exist via the backend seed data (`backend/app/core/seeds.py` — 5 hardcoded skills, no create endpoint). This epic is new scope beyond current production, not a reverse-engineered reproduction of an existing feature — flagged here explicitly, the same way every other scope decision in this prototyping effort has been logged.

**Goal:** Let an HR Admin view and extend the skill catalog directly from the dashboard, without needing engineering/database changes to add a skill that becomes assignable.

**Note on numbering:** this repo's real `epics.md` (referenced throughout the source code's own comments — e.g. "Story 5.1", "Story 5.6", "epics.md AC text") is not present in this checkout/branch, so this epic is numbered independently rather than guessing at a slot in that scheme and risking a collision. Renumber to fit the authoritative epics.md when this is merged into real planning.

---

## Story 1: View the Skill Catalog

As an **HR Admin**,
I want **to see a list of all skills when I click the Skills tab**,
So that **I can review what skills are currently available for assignment**.

**Acceptance Criteria:**

**Given** I am on the HR Dashboard
**When** I click "Skills" in the header nav
**Then** the page swaps to a Skills view listing every skill's name and description, and "Dashboard" is no longer shown as the active nav item

**Given** the Skills view is displayed
**When** it renders
**Then** a total skill count is shown

**Given** I am viewing the Skills tab
**When** I click "Dashboard" in the nav
**Then** I return to the assignment grid, with the "Dashboard" nav item active again

---

## Story 2: Add a New Skill

As an **HR Admin**,
I want **to add a new skill to the catalog from the Skills tab**,
So that **a newly relevant skill becomes assignable without needing engineering or database changes**.

**Acceptance Criteria:**

**Given** I am on the Skills tab
**When** I enter a skill name (and optional description) and click "+ Add Skill"
**Then** the new skill appears in the skills list immediately, and the total count updates

**Given** I attempt to add a skill with an empty name
**When** I click "+ Add Skill"
**Then** I see a validation message and no skill is added

**Given** I have just added a new skill
**When** I open "+ New Assignment" and reach the skill-selection step
**Then** the newly added skill is selectable there too — the catalog is a single source shared by both the Skills tab and the Assign wizard

---

## Out of Scope / Notes

- **No persistence beyond the browser session.** This is a static HTML prototype with no backend — added skills live only in an in-memory array for the current page load and are lost on refresh. A real implementation needs a `POST /api/skills` endpoint (none exists today — `backend/app/assignments/repository.py`'s `list_skills()` is read-only) plus a DB write, migration, and embedding generation (skills carry a `pgvector` embedding for content-matching, per `backend/app/core/seeds.py`'s `embed_text()` — a real create-skill flow must generate one, not just insert a name/description).
- **No edit or delete** of existing skills — this epic covers view + add only, matching the user's literal request.
- **No duplicate-name validation** specified — worth deciding before real implementation whether skill names must be unique.
