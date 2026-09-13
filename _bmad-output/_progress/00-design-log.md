# Design Log: TalentPilot-AI

> Project progress and key decisions across design phases

**Project:** TalentPilot-AI  
**Owner:** TalentPilot  
**Started:** 2026-07-08

---

## Current

| Scenario | Page | Task |
|----------|------|------|
| _(none)_ | | Scenario 06 (06.1) confirmed working by user 2026-09-13, live in a real browser (login.html HR_HOME fix included) — Phase 5 complete. `05-ritas-roster-management`'s "awaiting live-browser review" note above was stale (left here since 2026-09-11 without being cleared) — 05.1-05.3 remain mocked-but-unbuilt per the Backlog below, not actively in progress. |

## Backlog

- [ ] Fix `password-reveal-modal`'s title to be conditional ("Employee created" vs. "Password regenerated") — flagged during 05.3's spec sync, not fixed in the mock
- [ ] Explore responsive (tablet/mobile) states for 05.1 Employees Tab — flagged during 05.1's Page Transition, not yet started
- [ ] Update 01.1's and 04.1's nav specs to the left-pane shell (currently pre-FR-29 top-header), AND update 01.1/04.1/05.1 to the current 4-link nav (Dashboard/Skill Assignments/Skills/Employees) — 05.1 already has the left-pane shell but only 3 links; 06.1 (2026-09-13) is the only page spec'd/mocked with the current 4-link version. Compounds each time a page is added without this catch-up — flagged in 05.1's Out of Scope (2026-09-11) and again in 06.1's (2026-09-13), not yet scheduled.
- [ ] Build it — start agentic development for Scenario 05 (all 3 pages specified + mocked, none yet wired into a real/tested prototype)

## Design Loop Status

`[ADDED 2026-09-11]` This section did not previously exist in this design log — added per the wds-4-ux-design workflow's adaptive-dashboard requirement (per-page status tracking). Rows below start from Scenario 05; Scenarios 01-04 predate this tracking table and are not backfilled (their completion is already documented narratively in Progress/Quality Scores below).

| Scenario | Page | Page Name | Status | Date |
|----------|------|-----------|--------|------|
| 05-ritas-roster-management | 05.1 | Employees Tab (Roster) | discussed | 2026-09-11 |
| 05-ritas-roster-management | 05.1 | Employees Tab (Roster) | wireframed | 2026-09-11 |
| 05-ritas-roster-management | 05.1 | Employees Tab (Roster) | mocked (HTML, in place of PNG export, per user request) | 2026-09-11 |
| 05-ritas-roster-management | 05.2 | Create Employee Panel | discussed | 2026-09-11 |
| 05-ritas-roster-management | 05.2 | Create Employee Panel | specified | 2026-09-11 |
| 05-ritas-roster-management | 05.3 | Password Reveal Panel | discussed | 2026-09-11 |
| 05-ritas-roster-management | 05.3 | Password Reveal Panel | specified | 2026-09-11 |
| 05-ritas-roster-management | 05.1 | Employees Tab (Roster) | building | 2026-09-11 |
| 05-ritas-roster-management | 05.2 | Create Employee Panel | building | 2026-09-11 |
| 05-ritas-roster-management | 05.3 | Password Reveal Panel | building | 2026-09-11 |
| 05-ritas-roster-management | 05.1 | Employees Tab (Roster) | built | 2026-09-11 |
| 05-ritas-roster-management | 05.2 | Create Employee Panel | built | 2026-09-11 |
| 05-ritas-roster-management | 05.3 | Password Reveal Panel | built | 2026-09-11 |
| 06-ritas-pulse-check | 06.1 | Skill Assignment Dashboard | discussed | 2026-09-13 |
| 06-ritas-pulse-check | 06.1 | Skill Assignment Dashboard | wireframed | 2026-09-13 |
| 06-ritas-pulse-check | 06.1 | Skill Assignment Dashboard | specified | 2026-09-13 |
| 06-ritas-pulse-check | 06.1 | Skill Assignment Dashboard | mocked (HTML, in place of PNG export, per user request — matches 04.1/05.1 precedent) | 2026-09-13 |
| 06-ritas-pulse-check | 06.1 | Skill Assignment Dashboard | building | 2026-09-13 |
| 06-ritas-pulse-check | 06.1 | Skill Assignment Dashboard | built | 2026-09-13 |

---

## Progress

### 2026-07-08 — Phase 3: UX Scenarios Complete

**Agent:** Saga (Scenario Outline) with Claude Code  
**Scenarios:** 3 scenarios covering 6 of 7 core pages  
**Quality:** ✅ Excellent (all scenarios 7/7 / 7/7 / 7/7 / 4/4)

**Artifacts Created:**
- `C-UX-Scenarios/00-ux-scenarios.md` — Master scenario index with coverage matrix and POC hypothesis alignment
- `C-UX-Scenarios/01-ritas-trust-call/01-ritas-trust-call.md` — Scenario 01 outline (Rita's readiness decision workflow)
- `C-UX-Scenarios/01-ritas-trust-call/01.1-assignment-dashboard/01.1-assignment-dashboard.md` — Step 01.1 page spec (provenance labels, dashboard grid)
- `C-UX-Scenarios/01-ritas-trust-call/01.2-provenance-drill-down/01.2-provenance-drill-down.md` — Step 01.2 page spec (raw data view, modal/panel)
- `C-UX-Scenarios/02-caseys-resume-and-watch/02-caseys-resume-and-watch.md` — Scenario 02 outline (frictionless resume + auto-capture)
- `C-UX-Scenarios/02-caseys-resume-and-watch/02.1-content-discovery/02.1-content-discovery.md` — Step 02.1 page spec (single human-approved recommendation)
- `C-UX-Scenarios/02-caseys-resume-and-watch/02.2-resume-continue-watching/02.2-resume-continue-watching.md` — Step 02.2 page spec (resume at exact position, real-time tracking)
- `C-UX-Scenarios/03-ritas-assignment-and-track/03-ritas-assignment-and-track.md` — Scenario 03 outline (frictionless assignment + auto-update)
- `C-UX-Scenarios/03-ritas-assignment-and-track/03.1-skill-assignment-flow/03.1-skill-assignment-flow.md` — Step 03.1 page spec (multi-step form with auto-linked content)
- `C-UX-Scenarios/03-ritas-assignment-and-track/03.2-assignment-confirmation-and-auto-update/03.2-assignment-confirmation-and-auto-update.md` — Step 03.2 page spec (new row appears on dashboard)

**Summary:** Three scenarios were outlined covering the full POC hypothesis: (1) Rita's Trust Call tests whether provenance labeling (Verified / Self-reported / Needs Attention) actually changes Rita's behavior and eliminates cross-referencing; (2) Casey's Resume & Watch tests whether frictionless resume + passive auto-capture generates honest signal without surveillance anxiety; (3) Rita's Assignment & Track tests whether frictionless assignment flow with auto-linked content and auto-updating dashboard eliminates Rita's chasing burden. Key design decision: removed the "Needs Attention" filter as a separate page since drill-down directly from dashboard rows is simpler and addresses the same need. All scenarios are grounded in Trigger Map personas, driving forces, and business goals. Page coverage: 6 of 7 core pages assigned; Employee Profile View explicitly deferred (not needed for POC scope).

**Next:** Phase 4 — UX Design (detailed page specs, wireframes, component definitions, interaction design)

---

### 2026-07-08 — Phase 4: Validation (Steps 1-4) + Targeted Retrofit

**Agent:** Freya (Validate Specs) with Claude Code
**Scope:** All 6 page specs, validation steps 1-4 of 10 (Page Metadata, Navigation, Page Overview, Page Sections)

**Root cause found:** All 6 specs were authored to an older/informal format that predates the project's current `page-specification.template.md`. Steps 5-10 deferred rather than run mechanically, since they'd re-surface the same root cause.

**Fixes applied (targeted retrofit):**
- Object IDs renamed on all 6 pages from `PREFIX-###-NAME` to standard lowercase-hyphenated format (~85 IDs)
- Reference Materials sections added to all 6 pages (links to Product Brief, Trigger Map, related pages)
- Loading/Empty/Error states added to all 6 pages' Page States sections (previously happy-path only)
- 02.2 Continue Watching: backfilled missing Scenario Entry Context (User Situation/Mental State)

**Deferred (still open):** Page Metadata section standardization (01.1, 03.1, 03.2), nav-block Prev/Next links (all 6), Object Registry/Layout Structure/Open Questions/Checklist sections (all 6). See `_progress/validation-report.md` for full detail.

**Next:** [H] Design Delivery handoff, or address deferred items first.

---

### 2026-07-08 — Phase 4: Design Delivery Handoff Complete (DD-001)

**Agent:** Freya (Design Delivery) with Claude Code

**Artifacts created:**
- `deliveries/DD-001-poc-hypothesis-flows.yaml` — status: in_development, assigned to `wds-5-agentic-development`
- `deliveries/TS-001-poc-hypothesis-flows.yaml` — 24 tests across happy path/error/edge case/accessibility/usability/performance
- `deliveries/DD-001-handoff-log.md` — full 10-phase handoff record

**Scope:** All 3 scenarios / 6 pages (Rita's Trust Call, Casey's Resume & Watch, Rita's Assignment & Track). Design System N/A (`design_system_mode: none`).

**Next:** `wds-5-agentic-development` [P] Prototyping — build section-by-section against these specs, validate against TS-001 once a scenario is testable.

---

### 2026-07-08 — Phase 5: Prototype Built — Scenario 01 Rita's Trust Call

**Agent:** wds-5-agentic-development [P] Prototyping, with Claude Code
**Scope:** Skills Dashboard + Provenance Drill-Down modal (single logical view, both pages 01.1/01.2 per `work/Logical-View-Map.md`)

**Artifacts:** `E-Development/01-Ritas-Trust-Call-Prototype/` — `01.1-Skills-Dashboard.html`, shared JS, demo data, 6 section story files, work file, roadmap.

**Result:** All 6 sections built and approved, 8/8 states working (dashboard: Loaded/Loading/Empty/Error, modal: Open/Loading/Error/Closed), full integration test passed. One real bug found and fixed: `fetch()` of local JSON is blocked under `file://` — switched to a `<script>`-tag global-variable pattern (`data/demo-data.js`), documented for reuse in Scenarios 02/03.

**Scenario 01 prototype: complete.** Scenarios 02 (Casey's Resume & Watch) and 03 (Rita's Assignment & Track) remain unbuilt.

**Next:** Start Scenario 02/03 prototype setup, or run [T] Acceptance Testing against TS-001 for Scenario 01.

| Skills Dashboard (01.1) | 01.1 | Skills Dashboard | built | 2026-07-08 |
| Provenance Drill-Down (01.2) | 01.2 | Provenance Drill-Down | built | 2026-07-08 |

---

### 2026-07-08 — Phase 5: Prototype Built — Scenario 02, Content Discovery (02.1)

**Agent:** wds-5-agentic-development [P] Prototyping, with Claude Code
**Scope:** Content Discovery only (Continue Watching is a separate logical view, not yet built)

**Artifacts:** `E-Development/02-Caseys-Resume-and-Watch-Prototype/02.1-Content-Discovery.html` + shared JS/demo data, 4 section story files, work file.

**Result:** All 4 sections built and approved, 4/4 states working (Loaded/Loading/Empty/Error). No bugs this time — reused the fetch()/file:// fix from Scenario 01 from the start.

**Next:** Build 02.2 Continue Watching (same scenario, second logical view).

| Content Discovery (02.1) | 02.1 | Content Discovery | built | 2026-07-08 |

---

### 2026-07-08 — Phase 5: Prototype Built — Scenario 02 Complete (Continue Watching, 02.2)

**Agent:** wds-5-agentic-development [P] Prototyping, with Claude Code
**Scope:** Continue Watching — second and final logical view for Scenario 02

**Artifacts:** `E-Development/02-Caseys-Resume-and-Watch-Prototype/02.2-Continue-Watching.html` + 4 section story files, work file.

**Result:** All 4 sections built and approved, 4/4 states working (Continue Watching/Loading/Empty/Error). No bugs.

**Scenario 02 prototype: complete** (both Content Discovery and Continue Watching built). Scenario 03 (Rita's Assignment & Track) remains unbuilt.

| Continue Watching (02.2) | 02.2 | Continue Watching | built | 2026-07-08 |

---

### 2026-07-08 — Phase 5: Prototype Built — Scenario 03 Complete (all 3 scenarios done)

**Agent:** wds-5-agentic-development [P] Prototyping, with Claude Code
**Scope:** Skill Assignment Flow modal (03.1) + Toast/New-Row-Highlight (03.2), extending a duplicated copy of Scenario 01's dashboard

**Artifacts:** `E-Development/03-Ritas-Assignment-and-Track-Prototype/03-Skills-Dashboard.html` + shared JS/demo data (extended `createAssignment`/`getContentForSkill`), 6 section story files, work file. Folder structured per-scenario per project convention (duplication accepted as a known trade-off — see roadmap).

**Result:** All 6 sections built and approved. Full end-to-end flow confirmed: Rita assigns Casey to Python Basics via the 3-step form, new row appears with toast + highlight, both this modal and the Provenance Drill-Down modal coexist correctly (Escape/click-outside each close only the open one).

**All 3 scenarios (01, 02, 03) now have working prototypes — full POC hypothesis is demonstrable end-to-end.**

| Skill Assignment Flow (03.1) | 03.1 | Skill Assignment Flow | built | 2026-07-08 |
| Assignment Confirmation (03.2) | 03.2 | Assignment Confirmation | built | 2026-07-08 |

---

### 2026-07-09 — Phase 8: Product Evolution — Authentication Login Gate

**Agent:** wds-8-product-evolution ([S] Scope → [D] Design → [I] Implement → [T] Test), with Claude Code
**Scope:** Backfill a login/session gate into all 3 built prototypes — flagged retroactively as a gap missed during the original brainstorming/Design Thinking phases (no persona driving force ever surfaced "who can open this," so no login gate was ever scoped).

**Artifacts:** `evolution/scenarios/authentication-login-gate.md`, `evolution/specs/authentication-login-gate.md`, `evolution/test-reports/authentication-login-gate.md`. Branch: `evolution/authentication-login-gate`.

**Result:** One shared login page design (`login.html`, duplicated per folder per the existing shared/-file convention) + `shared/auth.js` mock credential store (Rita=HR, Casey/Morgan/Jordan/Sam=Employee) + a 2-line session guard on each existing protected page. 9/9 acceptance criteria passed after browser-driven testing (Playwright) caught and fixed one real bug: Employee logins other than Casey silently saw Casey's data because `login.html` doesn't load `shared/prototype-api.js`. Zero visual/behavioral change to any existing authorized page, confirmed via screenshot comparison. Two pre-existing, unrelated issues surfaced during testing (Dev Mode toggle button overlapping the header user-menu; Provenance Drill-Down modal has no row-click handler) — logged in the test report and `project-context.md`, not fixed here.

**Next:** Merge `evolution/authentication-login-gate` when ready; consider the two logged pre-existing issues as separate follow-up scenarios.

---

### 2026-09-08 — Phase 4: New Scenario 04 — Rita's Content Curation (Skills Tab spec)

**Agent:** Freya (Suggest/Dream mode) with Claude Code
**Scope:** New page spec for the Admin-Assisted Content Sourcing feature (PRD §4.6, FR-16–FR-19, added same day via `bmad-prd` update) — HR Admin credential management (YouTube personal key + Udemy org-wide credential), live search or manual link entry, review-and-approve, estimated days-to-complete.

**Artifacts:**
- `C-UX-Scenarios/04-ritas-content-curation/04-ritas-content-curation.md` — new scenario outline (Q1-Q8), ties to Trigger Map Objective 5 (fast/relevant content discovery)
- `C-UX-Scenarios/04-ritas-content-curation/04.1-skills-content-sourcing/04.1-skills-content-sourcing.md` — full page spec: Skills List landing view, Content Lookup modal (search/manual-entry sub-views, per-source empty/error states, days-to-complete display rule), API Keys modal (personal vs. org-wide credential framing)
- `C-UX-Scenarios/00-ux-scenarios.md` updated — Scenario 04 added to the master index (4 scenarios, 8 pages, 7/8 assigned)

**Result:** Spec complete, not yet prototyped. This page also fulfills the existing "Skills" primary-nav item (`01.1-Skills-Dashboard.html`, renamed from "Assignments" earlier this session) — previously a stub route with no page behind it.

**Next:** `wds-5-agentic-development` [P] Prototyping to build `04.1-Skills-Tab.html`, or continue refining the spec first.

---

### 2026-09-08 — Phase 4/5: Mock Screen Built — Skills Tab (04.1)

**Agent:** Freya (mock screen, ad hoc — lighter than a full wds-5 build) with Claude Code

**Artifacts:** `E-Development/01-Ritas-Trust-Call-Prototype/04.1-Skills-Tab.html` — `[MOVED same day]` initially scaffolded as its own folder (`04-Ritas-Content-Curation-Prototype/`, duplicating `shared/`+`components/`+`login.html` per the established per-folder convention), then merged into the existing Scenario 01 folder per user request — one prototype folder now serves both Scenario 01 and Scenario 04, sharing `shared/`/`components/`/`login.html`. 01.1's "Skills" nav link now points to `04.1-Skills-Tab.html` (was a `#` stub); 04.1's "Dashboard" nav link points back to `01.1-Skills-Dashboard.html`, both same-folder relative links now.

**Result:** Single-file mock (inline mock data, no `demo-data.js`/`PrototypeAPI` dependency — lighter-weight than the fully-wired Scenario 01-03 prototypes) covering: Skills list (approved-content badges), Content Lookup modal (Search tab with YouTube/Udemy result cards + days-to-complete, Paste-a-link tab, Approve interaction), API Keys modal (personal YouTube key vs. org-wide Udemy credential framing). Not yet run through full state-by-state acceptance testing like Scenarios 01-03 — this is a visual mock, not a validated prototype.

**Next:** Review the mock; if approved, promote to a fully-wired prototype (Loading/Empty/Error states, `PrototypeAPI` data layer) via `wds-5-agentic-development`, matching Scenario 01-03's rigor.

**Revision (same day):** Landing view changed from a data table (Skill + count badge + Find Content) to a card grid — each Skill card now lists its actual approved Content links inline (source, clickable title, days-to-complete), not just a count. Reason: a count alone still required opening Content Lookup to see *what* was approved; the card answers "does this Skill already have something good?" at a glance. `04.1-Skills-Tab.html` and `04.1-skills-content-sourcing.md` both updated to match.

**Revision (same day):** Card body simplified to show exactly **one** approved link (the most recently approved), never a list — mirrors FR-4's existing "exactly one recommendation per Skill" rule for Employee-facing Content Discovery. New PRD consequence added to FR-18.

**Revision (same day):** New capability added — FR-20, "HR Admin creates a new Skill." Closes a real gap: no prior FR covered Skill creation (Skills only ever came from the seed script). `[+ New Skill]` button added to the toolbar; a New Skill modal (name required, description optional, duplicate-name detection) opens on click, and on create flows straight into the Content Lookup modal for the new Skill with the search term pre-filled — the "brand-new Skill, zero content" gap is closed at the moment of creation. `04.1-Skills-Tab.html` and `04.1-skills-content-sourcing.md` both updated; `prd.md` §4.6 gained FR-20.

**Revision (same day):** Content links now open an in-app Watch Modal (embeds YouTube via iframe; explicit "preview not available" + Open-in-new-tab fallback for Udemy/manual) instead of a bare new-tab redirect — applies to both the pre-approval "View" action and an already-approved link on a Skill card. Corrected an earlier assumption that an established "opens in new tab" pattern existed elsewhere in the product for this — checked, and it didn't (the real video player was explicitly out of scope in every Employee-facing prototype too). `prd.md` FR-18 consequence corrected to match.

**Revision (same day):** Full Skill CRUD added — FR-21 (edit) and FR-22 (delete), both permanently locked the moment a Skill is ever assigned to an Employee (a one-way gate, not a live assignment count, so historical Assignment/audit records always resolve to a stable Skill identity). Skill Card gained a utility row: unassigned Skills show Edit/Delete icon buttons; assigned Skills show a 🔒 "Locked — assigned to an Employee" indicator in their place. New/Edit Skill modal is shared (same fields, different title/submit copy/behavior); Delete requires confirmation, mirroring FR-15's Assignment-removal pattern. Delete is a hard delete (not soft like FR-15) since a deletable Skill has zero Assignments by definition. Mock data gained an `assigned` flag (4 of 10 seeded Skills marked assigned, independent of whether they have approved content, to demonstrate both axes). New PRD Open Question 16 flags that Skills has never had a proper owning module — now a real architecture gap given real HR-facing writes with a business-critical lock invariant, not yet resolved. `04.1-Skills-Tab.html` and `04.1-skills-content-sourcing.md` both updated; `prd.md` §4.6 gained FR-21/FR-22.

**Revision (same day):** Edit (FR-21) merged into the Content Lookup Panel per direct feedback — editing a Skill now opens the same popup as Find Content (FR-17/18), showing a "Currently Approved" section (the existing link, if any) plus editable Name/Description fields at the top, plus the normal Search/Paste-a-link flow to find and approve a replacement. Replaces the standalone rename-only Edit modal built earlier the same day. New Skill Panel reverts to create-only (it still needs its own small modal, since a brand-new Skill has no content/name to look up yet). `04.1-Skills-Tab.html` and `04.1-skills-content-sourcing.md` both updated; `prd.md` FR-21 gained a consequence describing the merged flow.

**Revision (same day):** Two more changes per direct feedback. (1) New FR-23: a "Reject" button added next to the Currently Approved link, letting Rita explicitly remove it independent of approving a replacement — no confirmation, works even on assigned/locked Skills (content-sourcing was never gated by the FR-21/22 identity lock, only rename/delete are). This reverses FR-18's old open assumption about removal mechanics. (2) The Skill card's "Find Content" footer button was removed for unassigned Skills (redundant with Edit, which opens the same panel) — but **kept for assigned/locked Skills**, since they have no Edit icon and would otherwise lose the ability to source/replace Content entirely; flagged this nuance rather than silently dropping the capability for already-assigned Skills, which is arguably the more important case. `prd.md` gained FR-23 plus a new FR-17 consequence documenting the entry-point split; `04.1-Skills-Tab.html` and `04.1-skills-content-sourcing.md` both updated.

**Revision (same day):** "Find Content" removed from every card, including assigned/locked ones, per direct feedback overriding the tradeoff logged in the previous entry. Consequence, flagged rather than silently absorbed: **an assigned Skill now has no UI entry point into content-sourcing (FR-17/18/19/23) at all**, even though those FRs' own wording says the capability isn't gated by assignment status — only Skill identity (rename/delete) is. Logged as new PRD Open Question 17 with two unresolved options (narrow the FRs to unassigned Skills only, vs. design a different entry point e.g. from the Provenance Drill-Down modal, 01.2) — not decided here, not a blocker for the unassigned-Skill path. Also: the API Keys modal's Udemy row restructured (Client ID on its own row, Client secret + Save/Remove on a second row matching YouTube's row shape) and all three credential inputs given equal fixed width, per direct feedback. `prd.md`, `04.1-skills-content-sourcing.md`, and `04.1-Skills-Tab.html` all updated.

---

### 2026-09-08 — Phase 6/Epics: Epic 6 (Admin-Assisted Content Sourcing) Created

**Agent:** `bmad-create-epics-and-stories` (extension mode, not the skill's default from-scratch flow) with Claude Code

**Pre-work:** Resolved the two open architecture/product gaps flagged during UX design before writing stories against them. PRD Open Question 16 (Skills has no owning module) resolved via new architecture decision **AD-11**: new `skills/` module, permanent edit/delete lock implemented as a local `ever_assigned` boolean set by `assignments/` (same dependency shape `assignments/` already has toward `content/`). PRD Open Question 17 (no UI entry point for an assigned Skill's content-sourcing) confirmed at the architecture level as a UX gap, not a backend one — stays open, not resolved.

**Artifacts:** `_bmad-output/planning-artifacts/epics.md` — extended, not regenerated (Epics 1-5 untouched). New **Epic 6: Admin-Assisted Content Sourcing**, 10 stories (6.1 `skills/` module foundation & migration, 6.2 Skill creation, 6.3 Skill edit/delete + permanent lock, 6.4 wiring `ever_assigned` into Assignment creation, 6.5 credential storage, 6.6 live search YouTube+Udemy, 6.7 manual link entry, 6.8 review/approve/days-estimate, 6.9 reject content, 6.10 Skills Tab frontend). Requirements Inventory extended (FR-16-23 + backfilled FR-15, new NFRs, AR-22/23, UX-DR25-33), FR Coverage Map and Epic List updated. `ARCHITECTURE-SPINE.md` gained AD-11 plus frontmatter/paradigm-table/dependency-diagram/ER-diagram/source-tree/capability-map updates; `prd.md` Open Questions 16/17 updated to match. `project-context.md` updated with a full session-arc summary per this project's own mandatory-maintenance convention.

**Next:** Route Epic 6 through `bmad-create-story`/`bmad-dev-story` for implementation, same as Epics 1-5. Resolve PRD Open Question 17 (assigned-Skill content-sourcing entry point) before Story 6.10's known gap needs closing.

---

### 2026-09-11 — Phase 2: Trigger Map Extended for New PRD Capabilities

**Agent:** Saga (Trigger Mapping) with Claude Code

**Context:** `prd.md` was updated the same day (via `bmad-prd`) to add three new capabilities — Employee Roster Management (§4.7, FR-24–28), HR Admin Navigation Shell (§4.8, FR-29), and Application Theming (§4.9, FR-30) — none of which existed when Phase 2 was originally completed (2026-07-08). Rather than re-running Trigger Mapping from scratch (which would discard the validated Rita/Casey work), the existing artifacts were extended for just the delta, following the same precedent already set by Authentication (FR-13/FR-14) never appearing in the Feature-Impact scoring table.

**Analysis:** All three new capabilities are enabling/infrastructure work, not psychology-driven features — none of them serve a named want or fear in Rita's or Casey's driving forces the way Auto-Capture or Content Discovery do. Scoring them low on the existing 8-point rubric would misrepresent them as failed priority candidates rather than a different category entirely.

**One genuine risk surfaced, not just a scoring omission:** Employee Roster Management lands new manual data-entry work directly on Rita (creating accounts, sharing passwords out-of-band, maintaining profiles) — this is in real tension with Rita's own named Fear #3, **"the chore just relocates instead of disappearing."** Flagged as an explicit design constraint for FR-24–28, not a neutral addition.

**Artifacts updated:**
- `B-Trigger-Map/06-Feature-Impact.md` — new "Enabling Features (Outside the Psychological Scoring Model)" section
- `B-Trigger-Map/05-Key-Insights.md` — new "Employee Roster Management Must" design-implications subsection, naming the chore-relocation risk explicitly
- `B-Trigger-Map/00-trigger-map.md` — Feature Priorities summary gained an "Enabling" line pointing to both

**Next:** Carry the chore-relocation risk forward into UX design for FR-24 (creation flow) and FR-27 (archive flow) when Phase 4 work reaches those screens.

---

### 2026-09-11 — Phase 3 → Phase 4: Scenario 05 Outlined and 05.1 Discussed

**Agent:** Saga (Scenarios) → Freya (UX Design) with Claude Code

**Phase 3:** New Scenario 05 "Rita's Roster Management" created via Suggest mode (all 8 questions drafted from Trigger Map/PRD context, user-reviewed) — `C-UX-Scenarios/05-ritas-roster-management/`. Single-page-in-scope treatment (Employees Tab hosts Create/Edit/Password-Reveal/Regenerate/Delete-Archive as states, not separate pages), matching 04.1's precedent. 3-step linear sunshine path outlined: 05.1 Employees Roster → 05.2 Create Employee → 05.3 Password Reveal. Priority 3 (Admin Task) — enabling infrastructure, not a driving-force-fulfillment chain, consistent with the Trigger Map's earlier "Enabling Features" classification.

**Phase 4 (05.1 only so far):** D1/D2 discussed. Key decision: Employee list defaults to a **Table view** (11 profile fields + 15-per-page pagination suit rows/columns better than 04.1's card-grid default), with a **Card view available via a toggle** — both share the same pagination, filters, and search state. This page also introduces FR-29's new **left-pane nav shell** for the first time — 01.1 and 04.1's specs still describe the old top-header nav and need a follow-up update pass when FR-29 is actually built (logged in Backlog above, not done here).

**Next:** Choose visualization for 05.1 (wireframe / sketch / spec-only), then continue to 05.2 and 05.3.

---

### 2026-09-13 — Phase 2: Trigger Map Extended for Skill Assignment Dashboard

**Agent:** Saga (Trigger Mapping) with Claude Code

**Context:** `prd.md` gained a new capability the prior day (2026-09-12, via `bmad-prd`) — the Skill Assignment Dashboard (§4.10, FR-31–33), a new HR Admin landing page with org-wide stats and an Employee Segmentation pie chart (On Track / In Progress / Needs Attention). Following the same precedent set by the 2026-09-11 extension (Employee Roster/Nav/Theming), the existing Trigger Map was extended for just this delta rather than rebuilt from scratch — confirmed with the user first, since a from-scratch redo was the other option on the table.

**Analysis, and a key difference from the 2026-09-11 precedent:** Unlike Employee Roster Management/Nav/Theming (filed as "Enabling Features," outside the psychological scoring model), this new dashboard has a genuine, non-infrastructure connection to Rita's named driving forces — it directly complements Want #3 ("a fast, confident readiness call") and Want #2 ("stop chasing people") by surfacing an org-wide temperature check before she even opens the row grid. It was scored on the existing 8-point rubric (Medium/Primary = 3, Low/Secondary = 0, total 3) rather than filed as Enabling — reasoned as a complementary lens on top of the already-scored Provenance-Labeled Dashboard / Needs-Attention mechanic, not a replacement for either.

**Genuine drift discovered, not introduced by this session:** while placing the new feature, found that `06-Feature-Impact.md` (created 2026-07-08) still scores a dedicated "Needs Attention" Filter Control as Must-Have MVP, and `05-Key-Insights.md` still lists it as a Design Implication — but `prd.md` §6.2 explicitly decided against building a dedicated filter control (per-row drill-down instead), a decision that was never carried back into these Phase 2 docs. Flagged inline in both files rather than silently fixed, since reconciling it isn't part of this session's requested scope. The new dashboard's Needs-Attention pie segment is the closest thing that's actually shipped to that original scored item, but it's an org-wide per-Employee summary, not a row-level filter — only a partial, not full, resolution of the gap.

**Artifacts updated:**
- `B-Trigger-Map/06-Feature-Impact.md` — new scored table row + Decisions entry for Skill Assignment Dashboard; new Strategic Rationale note flagging the unreconciled Needs-Attention-Filter drift
- `B-Trigger-Map/05-Key-Insights.md` — new "Skill Assignment Dashboard (Landing Page) Must" design-implications subsection
- `B-Trigger-Map/00-trigger-map.md` — Feature Priorities summary gained a new line for the scored addition

**Next:** Carry the "Needs Attention pie segment must lead straight to specific employees, not just an inert count" requirement forward into UX design for FR-32/FR-33 when Phase 4 work reaches this page. Decide, at some point (not blocking), whether the Needs-Attention-Filter drift needs a deliberate reconciliation pass of its own.

---

### 2026-09-11 — Phase 4: Scenario 05 Fully Designed (05.1–05.3)

**Agent:** Freya (UX Design) with Claude Code

**05.1 (Employees Tab):** Wireframed (Excalidraw, agreed with no changes) then, per direct request, also built as a single-file HTML mock (`E-Development/01-Ritas-Trust-Call-Prototype/05.1-Employees-Tab.html`) in place of a static PNG export — matching 04.1 Skills Tab's precedent of a lighter-weight inline-mock-data visual mock. The mock fully implements: the new FR-29 left-pane nav shell (first page to introduce it — 01.1/04.1 still show the old top-header nav and need a follow-up pass, logged in Backlog), a functional Table/Card view toggle sharing one pagination/filter/search state, and all 5 modals (Create → Password Reveal, Edit, Regenerate Password, Delete/Archive with server-decided hard-delete-vs-archive copy).

**05.2 (Create Employee) and 05.3 (Password Reveal):** Both discussed (D1/D2) and specified directly against the already-built HTML mock rather than drawn as separate wireframes — the mock's modals already fully implement each page's interaction. One real gap caught during 05.3's spec sync, not yet fixed in the mock: the Password Reveal modal's title reads "Employee created" even when opened via Regenerate, which is misleading — logged to Backlog rather than silently ignored or fixed off-spec.

**Scenario 05 status:** All 3 pages specified end-to-end (matches the "Wireframed/Specified" bar the Phase Completion Checklist below still lists as outstanding for Scenarios 01-04's 7 original pages — Scenario 05 is now ahead of them on that front). Not yet run through acceptance testing or wired into a real backend — this is a visual mock, same caveat as 04.1.

**Next:** Backlog items above (title fix, responsive-state exploration, 01.1/04.1 nav-shell catch-up), or start agentic development (`wds-5-agentic-development`) for Scenario 05.

---

### 2026-09-13 — Phase 3: Scenario 06 Outlined (Rita's Pulse Check)

**Agent:** Saga (Scenario Outline) with Claude Code

**Scenarios:** 1 new scenario (06) covering 1 new page, extending the existing 5-scenario/10-page set to 6 scenarios/11 pages total

**Quality:** ✅ Excellent (7/7 Complete, 7/7 Quality, 7/7 Mistakes Avoided, 4/4 Best Practices)

**Artifacts Created:**
- `C-UX-Scenarios/06-ritas-pulse-check/06-ritas-pulse-check.md` — Scenario 06 outline (Rita's Pulse Check)
- `C-UX-Scenarios/06-ritas-pulse-check/06.1-skill-assignment-dashboard/06.1-skill-assignment-dashboard.md` — Step 06.1 page metadata (entry context, mental state, on-page interactions)

**Artifacts Updated:**
- `C-UX-Scenarios/00-ux-scenarios.md` — added Scenario 06's summary row, blurb, and page-coverage-matrix row; also caught and fixed a pre-existing gap where Scenario 05 (created 2026-09-11) had never been added to this index at all — backfilled its row, blurb, coverage-matrix rows, and navigation links in the same pass

**Summary:** Scenario 06 covers the Skill Assignment Dashboard (PRD §4.10, FR-31–33) — the new HR Admin landing page added via the prior day's `bmad-prd` update. Ran in Suggest mode (all 8 questions drafted from Trigger Map/persona context, user-approved) per the same precedent set by Scenarios 04/05. Key decision made during scoping (step 2/3): this is a single-page, single-step scenario — the drill-down exits (full grid via `Skill Assignments` nav, per-employee Skill Progress) deliberately stay owned by Scenario 01/page 01.1, not duplicated here, to avoid page-assignment overlap. Flagged, not silently resolved: the page's Employee Segmentation "Needs Attention" pie segment is the closest thing that's actually shipped to the "Needs Attention Filter" line item `06-Feature-Impact.md` scored as Must-Have MVP back in Phase 2 — but PRD §6.2 explicitly decided against building a dedicated filter control, so this only partially closes that long-standing, previously-undiscovered drift.

**Next:** Phase 4 — UX Design for page 06.1 (wireframe/spec the landing page's layout, stats row, progress ring, and pie chart), or continue with Scenario 05's still-open Backlog items above.

---

### 2026-09-13 — Phase 4: Page 06.1 Fully Designed (Discuss → Wireframe → Spec → Mock)

**Agent:** Freya (Discuss mode) with Claude Code

**Scope:** Skill Assignment Dashboard (06.1) — the only page in Scenario 06, handed off directly from Phase 3 completion

**D1/D2 outcome:** Primary action is "quickly identify which employees need attention," not passively displaying stats — this reshaped the whole page's visual hierarchy. Page kept (not simplified away): all 3 top-line stats and the Assignment Progress ring stay, but are demoted to secondary/supporting weight; the Employee Segmentation pie chart — specifically its Needs Attention segment — is the primary visual focus and the only genuinely actionable element. Resolved a decision PRD FR-32 had explicitly left open (`[NOTE FOR PM]` exact interaction not specified): clicking Needs Attention opens a lightweight on-page popover naming just those employees, which is what's actually clickable through to the per-employee drill-down — On Track/In Progress stay informational-only, a deliberate asymmetry.

**Wireframed:** `Sketches/06.1-skill-assignment-dashboard-wireframe.excalidraw` (+ approved PNG) — reuses 05.1's established sidebar/top-bar dimensions exactly, extended to the current 4-link nav (Dashboard/Skill Assignments/Skills/Employees) for the first time in this project's Phase 4 artifacts. Segmentation card drawn visibly larger (680px) than the Progress Ring card (450px), confirming the hierarchy decision visually, not just narratively.

**Specified:** Full page specification written to `06.1-skill-assignment-dashboard.md` (Page Basics through Design Constraints, matching 01.1/05.1's established house format rather than the generic WDS template, since this project's `design_system_mode: none` and single-language English make several of the generic template's sections inapplicable). No form validation applies — page is entirely read-only.

**Mocked (per user request, same day):** `E-Development/01-Ritas-Trust-Call-Prototype/06.1-Skill-Assignment-Dashboard.html` — single-file HTML mock (CSS `conic-gradient` for the ring/pie, no chart library, consistent with this project's lightweight-mock precedent for 04.1/05.1), placed in the same shared prototype folder as 01.1/04.1/05.1 (reuses `shared/auth.js` login gate, `components/dev-mode.*`, the `talentpilot` Tailwind palette). Implements the functional Needs Attention popover (click to open, click a name or outside/Escape to close) and a `?demo_state=loading|empty|error` toggle matching 01.1's existing debug pattern. Static verification only (no live-browser tool in this environment): div-tag balance checked (32/32), inline `<script>` blocks syntax-checked via `node --check`.

**Known, explicitly-flagged gap carried forward (not fixed here):** 01.1, 04.1, and 05.1 all still show an older nav version (01.1/04.1 predate FR-29 entirely; 05.1 has the 3-link version) — this page is the first with the current 4-link nav, widening the gap those three pages' specs had already flagged as a follow-up.

**Next:** Nav-shell catch-up pass for 01.1/04.1/05.1 (Backlog candidate, not yet scheduled), or start agentic development (`wds-5-agentic-development`) to promote this mock to a fully-wired, tested prototype like Scenario 01.

---

## Key Decisions

| Date | Decision | Phase | Contributors |
|------|----------|-------|---------------|
| 2026-07-08 | Removed Needs Attention Filter as separate page; integrated into Assignment Dashboard via direct drill-down on stale rows | Phase 3: Scenarios | Claude Code + TalentPilot |
| 2026-07-08 | Deferred Employee Profile View (not required for POC scope); all persona-specific data flows demonstrated through 6-page scenario outlines | Phase 3: Scenarios | Claude Code + TalentPilot |
| 2026-07-08 | Confirmed "Needs Attention" as implicit label state on Assignment Dashboard rows rather than a separate filter UI | Phase 3: Scenarios | Claude Code + TalentPilot |
| 2026-09-13 | Scenario 06 (Skill Assignment Dashboard) kept as a single page/single step; both drill-down exits (full grid, per-employee view) assigned to existing Scenario 01/page 01.1 instead of new pages, to avoid page-assignment overlap | Phase 3: Scenarios | Saga (Claude Code) + TalentPilot |
| 2026-09-13 | Continued (not restarted) Phase 3 for the new dashboard; also backfilled Scenario 05 into `00-ux-scenarios.md`'s index, which had been missing since 2026-09-11 | Phase 3: Scenarios | Saga (Claude Code) + TalentPilot |

---

## Quality Scores

### Phase 3: UX Scenarios

| Scenario | Completeness | Quality | Mistakes Avoided | Best Practices | Overall |
|----------|--------------|---------|------------------|----------------|---------|
| 01: Rita's Trust Call | 7/7 | 7/7 | 7/7 | 4/4 | ✅ Excellent |
| 02: Casey's Resume & Watch | 7/7 | 7/7 | 7/7 | 4/4 | ✅ Excellent |
| 03: Rita's Assignment & Track | 7/7 | 7/7 | 7/7 | 4/4 | ✅ Excellent |

**Overall Quality Rating:** Excellent — All scenarios exceed minimum thresholds. All 7 mistakes avoided in all scenarios. No gaps identified.

---

## Phase Completion Checklist

### Phase 1: Product Brief ✅
- [x] Strategic summary defined
- [x] Vision statement locked
- [x] Target users identified
- [x] Success criteria established

### Phase 2: Trigger Mapping ✅
- [x] Business goals mapped (Primary/Secondary/Tertiary)
- [x] Personas detailed (Rita, Casey)
- [x] Driving forces documented (wants + fears)
- [x] Trigger map created with visual flow

### Phase 3: UX Scenarios ✅
- [x] Scenario plan approved (3 scenarios, 6 pages)
- [x] All scenarios outlined (8-question format, Q1-Q8 answered)
- [x] All scenario steps detailed (6 page specs created)
- [x] Overview index created (00-ux-scenarios.md)
- [x] Quality review passed (all scenarios Excellent)
- [x] Design log updated

### Phase 4: UX Design ✅ (Scenario Specifications Complete)
- [x] Page context defined (01.1 - Skills Dashboard) — page purpose, entry point, mental state, goals captured
- [x] Page 01.1 (Skills Dashboard) specification complete — layout, components, interactions, states, spacing, typography
- [x] Page 01.2 (Assignment Details modal) specification complete — simplified modal with employee and skill info
- [x] Page 02.1 (Content Discovery) specification complete — employee-facing assignment card with AI-recommended content
- [x] Page 02.2 (Continue Watching) specification complete — resume interface with progress tracking
- [x] Page 03.1 (Skill Assignment Flow) specification complete — multi-step form for Rita to assign skills
- [x] Page 03.2 (Assignment Confirmation & Auto-Update) specification complete — dashboard confirmation with real-time updates
- [x] Page 04.1 (Skills Tab / Content Sourcing) specification complete — skills list, credential management, search/manual-entry lookup, review-and-approve, days-to-complete estimate `[ADDED 2026-09-08]`
- [ ] Wireframes and visual design (all 7 pages)
- [ ] Component definitions and design system extraction
- [ ] Real-time update architecture documentation
- [ ] Accessibility verification and WCAG AA audit

---

_Design log for TalentPilot-AI project, maintained throughout WDS phases_
