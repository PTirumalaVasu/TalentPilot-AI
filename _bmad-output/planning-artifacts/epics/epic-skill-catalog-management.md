---
status: implemented-in-prototype
source: User request during Phase 5 Prototyping (2026-09-03) — "create a story to show the skills in the skill tab in admin dashboard and also add the new skills to the list"
relatedPrototype: design-artifacts/E-Development/01-Assign-New-Skill-Prototype/hr-dashboard.html
implementationStory: design-artifacts/E-Development/01-Assign-New-Skill-Prototype/stories/HR-Dashboard.10-skills-view.md (Stories 0-1); HR-Dashboard.13-inline-content-approval.md (Story 2, current); HR-Dashboard.12-api-keys-view.md (Story 3, and Story 0's third view)
---

# Epic: Skill Catalog Management

## Overview

The real production HR Dashboard header has a "Skills" nav item next to "Dashboard" — captured during Reverse Engineering (`_bmad-output/planning-artifacts/specs/page-hr-dashboard.md`) as a **deliberate dead link** (`href="#"`, no destination), matching the actual current production code. This epic proposes giving that nav item a real destination: a Skills tab where an HR Admin can see the organization's skill catalog and add new skills to it.

Today, skills only exist via the backend seed data (`backend/app/core/seeds.py` — 5 hardcoded skills, no create endpoint). This epic is new scope beyond current production, not a reverse-engineered reproduction of an existing feature — flagged here explicitly, the same way every other scope decision in this prototyping effort has been logged.

**Goal:** Let an HR Admin view and extend the skill catalog directly from the dashboard, without needing engineering/database changes to add a skill that becomes assignable.

**Note on numbering:** this repo's real `epics.md` (referenced throughout the source code's own comments — e.g. "Story 5.1", "Story 5.6", "epics.md AC text") is not present in this checkout/branch, so this epic is numbered independently rather than guessing at a slot in that scheme and risking a collision. Renumber to fit the authoritative epics.md when this is merged into real planning.

---

## Story 0: Add a Working Skills Tab to the Header Navigation

As an **HR Admin**,
I want **the "Skills" nav item in the header to actually go somewhere**,
So that **I have a real place to manage the skill catalog, instead of a link that does nothing**.

This is the foundational story beneath Stories 1-3 — the navigation/view-switching mechanism itself, split out as its own explicit unit of work rather than left implicit inside Story 1's "view the catalog" scope. Real production's "Skills" link is `href="#"` with no destination (captured during Reverse Engineering, `page-hr-dashboard.md`) — this story is what replaces that with a real page.

**Acceptance Criteria:**

**Given** I am on the HR Dashboard (the default "Dashboard" view)
**When** I click "Skills" in the header nav
**Then** the page swaps to a Skills view in place (no full page navigation/reload), "Skills" becomes the active nav item, and "Dashboard" becomes inactive

**Given** I am on the Skills view
**When** I click "Dashboard" in the header nav
**Then** the page swaps back to the assignment dashboard, and nav active/inactive state swaps back correspondingly

**Given** the page supports more than two views (Dashboard, Skills, and — per `epic-automated-content-discovery.md` Story 1 — an API Keys screen reachable only from within Skills)
**When** any of these views is active
**Then** exactly one is visible at a time, and the header nav reflects the correct active state for all of them (API Keys keeps "Skills" highlighted, since it's reached from there, not from a nav item of its own)

**Implementation note**: built as a `mainView` state variable (`'dashboard' | 'skills' | 'api-keys'`) with a `switchMainView()` function toggling three container divs' visibility and the nav's active/inactive classes — not three separate HTML pages/routes. See `HR-Dashboard.10-skills-view.md` for the original build and `HR-Dashboard.12-api-keys-view.md` for the third view added afterward.

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

**Revised via Correct Course, 2026-09-03**: this story's AC previously said the skill "appears in the skills list immediately" on clicking "+ Add Skill." That's no longer accurate — `epic-automated-content-discovery.md` Stories 2-3 now make content search + approving at least one candidate a **prerequisite** for creation, not a follow-up. The AC below reflects the current, combined flow; the search/approve mechanics themselves live in that other epic, not repeated here.

**Acceptance Criteria:**

**Given** I am on the Skills tab
**When** I enter a skill name (and optional description) and trigger the search (see `epic-automated-content-discovery.md` Story 2)
**Then** candidate content is shown inline, and I must approve at least one before "+ Add Skill" becomes available to click (see that epic's Story 3 for the full review/approve mechanics)

**Given** I have approved at least one candidate and click "+ Add Skill"
**When** that completes
**Then** the new skill (with its approved content already attached) appears in the skills list, and the total count updates

**Given** I attempt to add a skill with an empty name
**When** I try to trigger the search
**Then** I see a validation message and no search runs

**Given** I have just added a new skill
**When** I open "+ New Assignment" and reach the skill-selection step
**Then** the newly added skill is selectable there too, already carrying its approved content — the catalog is a single source shared by both the Skills tab and the Assign wizard

---

## Story 3: Skill Creation Requires Configured API Keys

As an **HR Admin**,
I want **the Skills tab to clearly show whether content-search API keys are configured, and block the Add-Skill flow until they are**,
So that **I never attempt a skill creation whose required content search can't actually run**.

Added after Story 2's auto-search behavior was introduced (`epic-automated-content-discovery.md`, Story 1) — since adding a skill now triggers a content search, the Skills tab itself needs to reflect whether that search can actually run. This story describes the Skills-tab-visible behavior; the underlying API-key data model, encryption, and scope (now a **shared organization-wide key**, revised via Correct Course 2026-09-03 — see that epic's Story 1) are specified in `epic-automated-content-discovery.md`, not repeated here.

**Acceptance Criteria:**

**Given** I open the Skills tab and the organization's API keys are not fully configured
**When** the page renders
**Then** a status banner at the top lists each integration individually — green "✓ configured" or red "✗ not configured" per provider — and the search step of the Add-Skill flow is disabled with a visible reason and a link to configure keys

**Given** both required keys are configured (by any HR Admin — the key is shared, not tied to whoever set it)
**When** I view the Skills tab
**Then** the banner shows all-green / "All API keys configured", and the Add-Skill flow's search step is enabled for me too, even if I personally never configured anything

**Given** the keys become unconfigured again (e.g. cleared by any HR Admin)
**When** any HR Admin views the Skills tab
**Then** the banner and the gate both reflect that immediately, for everyone — never a stale "configured" state

---

## Out of Scope / Notes

- **No persistence beyond the browser session.** This is a static HTML prototype with no backend — added skills live only in an in-memory array for the current page load and are lost on refresh. A real implementation needs a `POST /api/skills` endpoint (none exists today — `backend/app/assignments/repository.py`'s `list_skills()` is read-only) plus a DB write, migration, and embedding generation (skills carry a `pgvector` embedding for content-matching, per `backend/app/core/seeds.py`'s `embed_text()` — a real create-skill flow must generate one, not just insert a name/description).
- **No edit or delete** of existing skills — this epic covers view + add only, matching the user's literal request.
- **No duplicate-name validation** specified — worth deciding before real implementation whether skill names must be unique.
