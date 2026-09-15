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
- [x] ~~Update 01.1's and 04.1's nav specs to the left-pane shell...~~ **Done 2026-09-15** — see Progress entry below. User reported the resulting bug directly (clicking "Dashboard" from 04.1 landed on the old 01.1 grid, not the real 06.1 landing page), confirming the risk this item had been flagging since 2026-09-11.
- [ ] Build it — start agentic development for Scenario 05 (all 3 pages specified + mocked, none yet wired into a real/tested prototype)
- [ ] `[ADDED 2026-09-15]` Decide the fate of the two diverged `05.1-Employees-Tab.html` copies — `01-Ritas-Trust-Call-Prototype/` (updated for Epic 10, inline mock data) and `05-Ritas-Roster-Management-Prototype/` (untouched, wired to a real `data/demo-data.js` + `shared/prototype-api.js` layer). Not resynced this session — copying the simpler version over the richer one would have destroyed real, differently-architected work. Needs an explicit decision: port Epic 10's changes into the data-layer version separately, deprecate one copy, or something else.
- [ ] `[ADDED 2026-09-15]` `shared/auth.js`'s mock login credential store (Rita/Casey/Morgan/Jordan/Sam, `@sailssoftware.com` emails) was not updated to match Story 10.1's real-backend seed-reduction (1 HR Admin + 1 Skill, `admin@sails.example.com`) — deliberately out of this session's scope (it's a separate, already-documented "not a real credential store," spans multiple prototype folders). Only the account's *displayed* name/avatar in each page's top-right menu was updated to "Sails Admin"; the underlying login form still accepts the old demo accounts. Revisit if/when the mocks get resynced with the real backend's seed shape.

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

### 2026-09-15 — Phase 4: Dashboard Gains a Third Ring (Days in Talent Pool), Layout Compaction, Employees-Page Quick-Filter Chips (Story 10.14, FR-41)

**Agent:** Freya with Claude Code, same rapid-fire refinement thread, continuing directly from the item above

**1. Third dashboard card — Days in Talent Pool ring (new FR-41, Story 10.14).** Added a third ring+legend card alongside Assignment Progress and Experience Distribution, computed from `employees.created_at`. **Bucket-boundary gap resolved the same way as before:** the requested "15, 30, 45, 60, 75, more than 90" boundaries left a 76–90 day range uncovered — added an explicit 7th bucket (76–90 days) to close it, flagged in both the PRD and epics.md rather than silently absorbed into a neighbor, mirroring exactly how the Experience buckets' own 15–19 gap was resolved earlier this session. `demo-data.js` employees gained `createdAt` values spread across all 7 buckets (data version bumped to 3).

**2. Experience Distribution's dashboard presentation converted from a button-grid to a ring**, matching Assignment Progress's visual language — per the user's "all in circle format" request. Its Employees-page copy is explicitly unaffected (see item 4 below — it changed too, but to something else entirely, on its own separate request).

**3. Shared bucket-selection/results infrastructure generalized, not duplicated.** Rather than writing near-identical selection/pagination logic twice (once per card), factored a single `{ kind: 'experience'|'talentPool', bucket }` selection state, a shared `renderBucketRing()` helper parameterized by bucket set, and one shared full-width results section below all three cards — selecting a bucket in either card clears the other's selection, since only one result set displays at a time. Verified via `node --check` + tag-balance after the rewrite, not assumed correct from the refactor alone.

**4. Ring + legend moved side-by-side within each card, at the user's explicit request "to reduce the height of the page".** All three cards changed from a stacked (ring on top, legend list below, full card width) to a side-by-side layout (ring left, legend right) — ring size reduced (40→32 Tailwind units) and legend row padding tightened, both intentional further height reductions once 3 cards × up to 7-row legends made vertical space the binding constraint.

**5. Employees page's Experience Distribution converted from box cards to quick-filter chips**, per direct request ("make it as Quick filter instead of boxes") — pill-shaped `"{label} ({count})"` buttons in a compact filter-bar row instead of a grid of large stat boxes, dropping the standalone panel card entirely (no longer its own bordered section, just an inline filter row under the toolbar).

**6. Employees page: Archive/Delete icon legend added**, per direct request — a small explanatory line above the grid (🗄 Archive vs. ✕ Delete, what triggers each) so the icon distinction (Story 10.3) is explained up front rather than only discoverable by opening each row's confirm modal.

**Verification:** every file re-checked after each change (`node --check` on all inline scripts, tag-balance checks) — same discipline as every other change this session, not skipped under time pressure.

**Documents updated:** `prd.md` (new FR-41, FR-36 gained a per-surface presentation note), `epics.md` (new Story 10.14, Story 10.14 gained a layout AC, Epic 10 goal/count bumped to 14 stories/FR-34–41 throughout), `sprint-status.yaml` (10-14 entry), this design log, `project-context.md`.

**Next:** none of this session's Epic 10 work (Stories 10.1–10.14) is implemented in the real app — all mockup/planning-only. The mockups now visually diverge further from the real `SkillAssignmentDashboard.tsx`/`EmployeesPage.tsx` than at session start; `bmad-create-story`/`bmad-dev-story` is the next real step whenever implementation begins, using these mockups and the epics.md ACs as the spec.

**Addendum, same thread, three final quick fixes:** (1) Employee roster's default view switched from Table to Card/Grid, matching the Skills tab's own default — "make the default view in all pages grid," per direct request; toggle button state, container visibility, and the `currentView` JS default all updated together (learned from the earlier Skills-tab bug that these three must move in lockstep). (2) `01.1`'s accordion table had a real dark-mode bug: the "Assigned Skill" cell had no text color class at all, so it inherited default black text — invisible against the dark-mode accordion background. Fixed, and proactively checked `statusBadge()`/`progressBar()` for the same issue (`progressBar()` already correct from the earlier darkify pass; the colored status/provenance badges use hardcoded light pastel colors with no `dark:` variant — legible on their own, just not theme-matched, logged as a minor known gap rather than expanded into a new task uninvited).

---

### 2026-09-15 — Phase 4/2/6: Five More Direct Requests — Nav Simplification, Skills View Toggle, List Placement, Dark Mode, Admin-Row Refinements

**Agent:** Freya with Claude Code, same click-through-and-refine thread, continuing directly from the Employee Segmentation → Experience Distribution work above

**1. Left nav drops the Dashboard entry (Story 10.12, amends FR-29 and Story 9.5).** Removed `Dashboard` from all 4 pages' left-pane nav — down to 3 entries (Skill Assignments, Skills, Employees). The `TalentPilot-AI` logo (already pointing to `06.1` on every page from the earlier nav-shell fix) and the existing post-login redirect are the Dashboard's access points now — no nav-pane entry duplicates that job. On `06.1` itself, no nav item is highlighted active, since the page has no entry of its own to highlight. `prd.md` FR-29 updated (original "four entries, not three" text struck through, kept for history).

**2. Skills tab gains a Table/Card view toggle (Story 10.13, extends FR-37).** Added a Table view (Skill name, Status, Approved Content, Days to Complete, Actions columns) alongside the existing card grid, with a toggle matching the Employee roster's exact interaction pattern, both views sharing search/pagination state. **Real bug caught immediately by the user, not by review:** the toggle buttons visually showed "Card" as selected by default, but the Table view was the one actually visible — I'd left `skills-table-wrap` without a `hidden` class and put `hidden` on the card grid instead, backwards from the intended default. Fixed.

**3. Experience Distribution bucket list moved below both cards (refines Story 10.11).** The click-through list was nested inside the Experience Distribution card itself — user asked for it full-width, below both the Progress ring and Experience Distribution cards. Restructured; also made it paginated (15/page) and styled as bordered name/role/experience row-cards, matching the Employee roster's own presentation ("similar to employee" — the user's own words), rather than a bare name list.

**4. Dark mode added to all 4 mockups — a real, pre-existing gap, not a regression.** These prototype pages predate Epic 8 (Application Theming, FR-30 — `done` in the real app) and never got a toggle at all. Built `shared/theme.js` (prefers-color-scheme default, localStorage-persisted override, matching FR-30's actual spec) reused across all 4 pages, added `darkMode: 'class'` to each Tailwind config, a toggle button next to the user menu, and `dark:` variant classes across ~370 occurrences of the recurring structural utility classes (backgrounds, text, borders) via a scripted pass — verified with a tag-balance/quote-integrity check afterward rather than trusting the regex blindly (one odd-quote-count flag on `04.1` traced to a pre-existing, unrelated `escAttr()` regex literal, not corruption). Known scope limit, not fixed: form inputs keep their native light background/text in both themes (a common, acceptable "light input on dark page" pattern) since they had no existing bg-white/text-gray-900 classes for the script to darkify — full input theming would need separate, explicit styling. No new FR needed — FR-30 already exists and is shipped; this only catches the mockup layer up to it.

**5. Admin-row refinements on the Employees page (extends Story 10.2), three follow-up requests in sequence:**
   - Excluded from search/filter/bucket-filter results (any active filter criterion drops it), but still shown in the default unfiltered view.
   - Days in Talent Pool renders blank ("—") for this row — not a meaningful metric for the org's own admin, not guessed.
   - **Correction from the user after my first pass over-restricted this:** I'd initially removed *all* of Regenerate Password along with Archive/Delete for the self row. Corrected — only the destructive action (Archive/Delete) is blocked, matching the real backend's actual self-delete guard scope; Edit and Regenerate Password (a self-service password reset) stay available.

**Verification:** every file re-checked after each change — inline scripts via `node --check`, tag balance programmatically — across all edits in this entry.

**Documents updated:** `prd.md` (FR-29 struck-through/updated, FR-37 extended for the view toggle, FR-25 gained the admin-row consequence, FR-36 gained the list-placement consequence), `epics.md` (Stories 10.12, 10.13 added; Story 10.11's AC amended for list placement; Story 10.2's AC amended for the admin-row refinements; Epic 10 goal/build-order/story-count updated throughout), `sprint-status.yaml` (10-12, 10-13 entries), this design log, `project-context.md`. UX-scenario spec docs were **not** re-touched in this pass beyond what the Employee Segmentation change already updated — a proportionate-effort call given the volume of change this turn, logged here rather than silently left inconsistent.

**Next:** none of items 1-5 above are implemented in the real app — all mockup-only, matching every other Epic 10 story's current state (`backlog`).

---

### 2026-09-15 — Phase 4: "Data not showing in Experience Distribution" — sessionStorage staleness, not a code bug

**Bug reported:** the new Experience Distribution panel on `06.1` showed no/empty data.

**Root cause:** `shared/prototype-api.js`'s `PrototypeAPI._load()` only ever seeded `sessionStorage` from `window.DEMO_DATA` when storage was completely empty — an already-open browser tab from earlier in this same session had cached the *old* `data/demo-data.js` shape (before Story 10.11's `experienceYears` fields were added to it), and kept serving that stale cache indefinitely regardless of what the source file changed to. Not a rendering/logic bug — `demo-data.js`'s actual content was already correct.

**Fix:** added a `_version` field to `window.DEMO_DATA` (bumped to `2`) and a version check in `_load()` — a cached copy whose `_version` doesn't match the current `window.DEMO_DATA._version` is automatically reseeded, no manual cache-clear needed. This is a real recurring-risk fix, not just a one-off patch: this same class of "edited demo-data.js mid-session, already-open tab doesn't see it" issue would otherwise resurface on every future edit to that file.

**Scope:** fixed in `01-Ritas-Trust-Call-Prototype/shared/prototype-api.js` and `data/demo-data.js` only (the canonical folder for this session's work) — not propagated to `05-Ritas-Roster-Management-Prototype/`'s separate copy, consistent with that folder being left untouched per the earlier Backlog decision.

**Verification:** both files syntax-checked via `node --check`.

---

### 2026-09-15 — Phase 4/2/6: Skill Assignment Dashboard's Employee Segmentation Retired, Replaced by Experience Distribution (Story 10.11)

**Agent:** Freya with Claude Code, at the user's direct request during mockup work — confirmed via `AskUserQuestion` as a real, deliberate product decision (not a mockup-only exploration), reversing already-shipped Epic 9 work (Stories 9.2/9.3/9.4, all `done`).

**What changed:** `06.1-Skill-Assignment-Dashboard.html`'s Employee Segmentation pie chart (On Track/In Progress/Needs Attention) and its Needs Attention popover/click-through are fully removed, replaced by the Experience Distribution panel (FR-36) in the same primary-card visual position — reusing the exact bucket set/interaction already built for `05.1-Employees-Tab.html`, not a second implementation. `data/demo-data.js`'s employees gained `experienceYears` values to feed it.

**Real, accepted trade-off — stated plainly, not smoothed over:** this removes the dashboard's only actionable, org-wide "who needs attention" capability. The sole remaining way to find a `Needs Attention` Assignment is the per-row flag inside the full Readiness Dashboard grid (`Skill Assignments` nav) — there is no more org-wide summary of it. This was specifically the mechanic that earned the dashboard its 3-point Trigger Map score (Want #2/#3 connection) — flagged for re-evaluation there, not silently re-scored.

**Documents updated to match** (per explicit user request, "update all the documents accordingly"):
- `prd.md`: FR-32 marked `[SUPERSEDED]` (Assignment Progress ring half stays current; Employee Segmentation half retired, original text struck through and kept for history); FR-33 updated (path (b) retired); FR-36 updated (now also renders on the dashboard); §4.10 description updated.
- `epics.md`: new **Story 10.11** added to Epic 10 (11th story); FR Coverage Map rows for FR-32/33/36 updated to reflect Done/Superseded/Retired sub-statuses; Epic 10 goal, build order, Epic List entry, and frontmatter `extensionNote` all updated.
- `sprint-status.yaml`: `10-11-...` story entry added (`backlog`).
- `B-Trigger-Map/06-Feature-Impact.md`, `05-Key-Insights.md`, `00-trigger-map.md`: all three flag the score/design-implications reversal explicitly, struck-through original text kept for history (matching this document's own established convention for prior drift, e.g. the 2026-09-13 Needs-Attention-Filter note).
- `06.1-skill-assignment-dashboard.md` (UX spec): given a prominent superseded banner rather than a full line-by-line rewrite of its ~20 scattered Segmentation mentions — proportionate effort call, logged explicitly rather than silently left half-updated.
- This design log, `project-context.md`, `sprint-change-proposal-2026-09-15.md` (addendum note, original approved text left unchanged).

**Verification:** inline scripts (all 3) syntax-checked via `node --check`, `<div>`/`<button>`/`<ul>` tag balance checked programmatically, `demo-data.js` syntax-checked — all pass.

**Next:** Story 10.11 is `backlog` — real implementation (removing `SkillAssignmentDashboard.tsx`'s segmentation UI, retiring `dashboard/service.py`'s segmentation endpoint per the AC's "retire, don't delete" instruction, wiring Story 10.4's Experience Distribution component onto this page) is not done, only planned + mocked. The Trigger Map's flagged re-score is also still open.

---

### 2026-09-15 — Phase 4: Two More User-Reported Bugs Fixed (01.1, 05.1)

**Agent:** Freya with Claude Code, continuing the same click-through bug-report thread

**Bug 1 — "progress not showing in %" on 01.1's Skill Assignments grid:** confirmed via code read — `progressBar(percent)` rendered only a visual fill-width bar, with no percentage text anywhere, ever (not a regression from today's other changes — pre-existing since the function was first written). Fixed: added a `<span>` showing the numeric percentage next to the bar. This is also a real accessibility gap by this project's own established rule (never a color/visual-only signal, always paired with text — the same principle already locked for Status badges and Provenance Labels, NFR-A2), just never applied to this specific bar before.
- **Not fixed, flagged instead:** checked `06.1-Skill-Assignment-Dashboard.html`'s own Assignment Progress ring (`renderDashboard()`'s `overallPercent` calculation and `.ring-percent-label` text update) line by line — data shapes, element IDs, and function logic all check out correctly by static reading; no bug found. Since "skill assignment dashboard" could mean either page (01.1's nav label is "Skill Assignments," 06.1's H1/PRD term is "Skill Assignment Dashboard") and this environment has no live-browser tool to verify visually, left 06.1 untouched rather than guess at a fix for a bug that may not exist there — asked the user to confirm exactly what they see if the 01.1 fix isn't what they meant.

**Bug 2 — "Admin user not showing" on 05.1's Employees roster:** the mock's `employees` array only ever had the 5 EMPLOYEE-role demo accounts (Casey/Morgan/Jordan/Sam/Alex) — the seeded HR Admin ("Sails Admin") was never in it. Checked against the real backend's actual behavior first (`core/seeds.py::seed_employees` creates the HR Admin as an `employees` table row too, not just an `accounts` row; `delete_or_archive_employee_service`'s real self-delete guard, "You cannot delete or archive your own account," only makes sense if the admin IS a roster row) — confirmed this belongs, not guessed. Added "Sails Admin" as `EMP-1000`, and gave it an `isSelf` flag that suppresses the Archive/Delete action (shows "(you)" instead) rather than exposing a button that would always fail, mirroring the real backend's constraint.

**Verification:** both files' inline scripts re-checked via `node --check` (all pass), `<div>` tag balance re-verified (both balanced).

---

### 2026-09-15 — Phase 4: Nav-Shell Catch-Up Bug Fix (01.1, 04.1, 05.1) — long-flagged Backlog item finally closed

**Agent:** Freya with Claude Code, responding to a bug the user found by actually clicking through the mockups after the Epic 10 update above

**Bug reported:** From the Skills page (04.1), clicking "Dashboard" landed on the old `01.1-Skills-Dashboard.html` grid, not the real `06.1-Skill-Assignment-Dashboard.html` landing page — and the Skills page itself still showed a top-header nav instead of the left-pane shell 05.1/06.1 already had.

**Root cause, confirmed by reading the actual markup:** `01.1`'s own top-header nav self-labeled its "Dashboard" link as `href="#"` (i.e., the *old* grid was presenting itself as "Dashboard," a leftover from before 06.1/FR-29's 4-link nav existed), with no link to 06.1 or to Employees anywhere on the page. `04.1` had the same stale 2-link top-header (Dashboard→01.1, Skills→self). This is exactly the risk the Backlog had been carrying since 2026-09-11 ("compounds each time a page is added without this catch-up") — it just hadn't produced a user-visible symptom until Epic 10's changes made someone actually click through 04.1→Dashboard.

**Fix:** Replaced `01.1` and `04.1`'s old top-header nav with the same left-pane shell markup as `06.1` (the correct, current reference — not `05.1`'s own nav, which turned out to still be the older 3-link version missing "Skill Assignments"). All 4 pages (`01.1`, `04.1`, `05.1`, `06.1`) now share byte-identical nav structure: Dashboard→06.1, Skill Assignments→01.1, Skills→04.1, Employees→05.1, each page's own entry self-referencing (`href="#"`, highlighted) rather than pointing at a different page. Every page's logo now points to 06.1 (previously inconsistent: 06.1's logo pointed to itself, 05.1's pointed to 01.1). Verified: all 4 pages' nav link targets cross-checked against each other programmatically (each of the 4 links resolves to exactly the expected file on every page); all 12 inline `<script>` blocks (3 per page × 4 pages) syntax-checked via `node --check`; `<div>`/`<aside>`/`<header>`/`<main>` tag balance checked on the 2 structurally-changed pages (01.1, 04.1) — all pass.

**Scope note:** fixed in the HTML mockups only, per the user's explicit ask ("in the prototype only"). The corresponding UX-scenario spec docs (`01.1-assignment-dashboard.md`, `04.1-skills-content-sourcing.md`) still describe the old nav in their own Header Section tables — not updated this pass, logged below rather than silently left inconsistent.

**Next:** Backlog item closed. Remaining open items: the diverged `05.1` copy, `shared/auth.js`'s stale demo accounts (both logged above), and now also updating `01.1`/`04.1`'s own spec docs' Header Section to describe the left-pane shell instead of the old top-header (not done this pass).

---

### 2026-09-15 — Phase 4: Mockups Updated for Epic 10 (01.1, 04.1, 05.1)

**Agent:** Freya (Dream Up mode, `wds-4-ux-design`) with Claude Code

**Scope:** Updated the 3 already-built HTML mockups touched by Epic 10 (FR-34–40), skipping a full Phase 3 (new UX Scenarios) pass per the user's own confirmation — Epic 10 refines already-specced pages rather than introducing new ones.

**`05.1-Employees-Tab.html`** (canonical copy confirmed by the user as `01-Ritas-Trust-Call-Prototype/`, not the diverged `05-Ritas-Roster-Management-Prototype/` copy — see Backlog): First/Last Name split (display "{Last}, {First}"), grid gains Location/Technologies/Experience/Days-in-Talent-Pool columns (red-flagged past 90 days, paired with a ⚠ icon + text, never color-only), Experience Distribution panel (7 buckets, click-through filters the existing table/pagination), and the Delete/Archive icon now differs by state (Story 10.3) instead of always showing a trash icon. **Mid-session correction from the user:** Department dropped as a column (kept as a stored field/filter), Project added instead — `prd.md` FR-34 and `epics.md` Story 10.2 both updated to match, since this went beyond what the original Sprint Change Proposal specified.

**`04.1-Skills-Tab.html`**: search input + 15/page pagination over the Skills card grid (FR-37); "+ New Skill" now disabled with a hover tooltip when neither YouTube nor Udemy has a configured credential (FR-40) — wired the previously-inert API Keys modal Save/Remove buttons to real state so the gate is actually demonstrable, defaulting to both sources "connected" (mirroring Story 10.8's seeded-credential default).

**`01.1-Skills-Dashboard.html`**: search (Employee or Skill name) + real pagination (FR-38) — the existing pagination control block was previously a static, non-functional placeholder (hardcoded "Previous / 1 / Next"). Since this grid is accordion-by-Employee rather than a flat row list, pagination operates on Employee groups (15/page), each still expanding to their full assignment table underneath, unchanged.

**Identity housekeeping (Story 10.1):** all four pages' top-right user-menu now show "Sails Admin" instead of "Rita" — this is the account's real login/display identity, not the PRD's narrative persona name, which stays "Rita" per the user's explicit correction earlier this session (see the mid-session correction logged in the Trigger Map entry below... no, above — this entry follows chronologically after Trigger Mapping in the log, see the 2026-09-15 Trigger Map entry).

**Verification:** static only (no live-browser tool available) — every inline `<script>` block syntax-checked via `node --check` (all pass), `<div>`/`<th>` tag balance checked programmatically (all balanced), matching this project's established verification convention for these single-file mocks.

**Two items deliberately not touched, logged to Backlog rather than silently skipped:** the diverged `05-Ritas-Roster-Management-Prototype/` copy of 05.1 (has its own real data layer, not a byte-duplicate — overwriting it would have destroyed work), and `shared/auth.js`'s mock login credential store (still has the old Rita/Casey/Morgan/Jordan/Sam demo accounts — only the *displayed* name was updated, not the underlying login form).

**Next:** Resolve the two Backlog items above, or proceed to `bmad-dev-story` for Story 10.1/10.10 (real backend implementation) — the mockups are visual references for that work, not a substitute for it.

---

### 2026-09-15 — Phase 2: Trigger Map Extended for Epic 10 (Post-MVP Admin & Roster Refinements)

**Agent:** Saga (Trigger Mapping) with Claude Code

**Context:** Same-day pipeline: 11 user-reported post-launch change requests were triaged via `bmad-correct-course` into a Sprint Change Proposal (approved), which drove a PRD update (§4.11, FR-34–40, Epic 10) and `epics.md` authoring (10 stories). Following the exact precedent set by the 2026-09-11 and 2026-09-13 extensions, the existing Trigger Map was extended for just this delta rather than rebuilt — the third time this pattern has been used.

**Analysis:** Unlike the Skill Assignment Dashboard (2026-09-13, which earned a real score), none of Epic 10 connects newly to Rita/Casey's named driving forces. It sorts into three buckets: (1) FR-34–36 + Story 10.3 extend the already-Enabling Employee Roster Management; (2) FR-37–40 + Stories 10.8/10.9 are reliability/hardening fixes on the existing (already-unscored) Admin-Assisted Content Sourcing capability — closing a real gap in the already-Must-Have HR Assignment Flow, not adding new pull; (3) Stories 10.1/10.10 are pure internal housekeeping (seeded-account identity, dev seed shape) with no persona-facing psychology at all.

**Genuine gap found, not introduced by this session:** while placing Epic 10's content-sourcing-adjacent items, discovered Epic 6 (Admin-Assisted Content Sourcing, FR-16–23, added 2026-09-08) was **never run through Trigger Mapping** — no mention anywhere in these docs before today. Flagged inline in `06-Feature-Impact.md` rather than silently reconciled, matching this document's existing convention for the "Needs Attention Filter" drift found 2026-09-13.

**Artifacts updated:**
- `B-Trigger-Map/06-Feature-Impact.md` — new Enabling Features entries for Epic 10 + the flagged Epic 6 gap
- `B-Trigger-Map/05-Key-Insights.md` — new "Post-MVP Admin & Roster Refinements Must" design-implications subsection, including an explicit warning against conflating the new 90-day Talent-Pool flag with the existing 7-day Needs-Attention staleness flag
- `B-Trigger-Map/00-trigger-map.md` — Feature Priorities summary gained an Epic 10 Enabling line

**Next:** Carry the "don't conflate the two red flags" and "chore-relocation" design constraints forward when Epic 10's stories reach UX/frontend work (Stories 10.2, 10.4). Decide, at some point (not blocking), whether Epic 6 deserves a retroactive Trigger Mapping pass of its own.

---

### 2026-09-15 — Phase 4: Row-Action Icon-Button Consistency Across 01.1/04.1/05.1; Skill Assignments Toolbar Layout Matched to Skills Page

**Agent:** Freya with Claude Code, same rapid-fire refinement thread, continuing directly from the items above

**Consistency fix (direct request — "make the consistence in all pages for delete edit and view buttons"):** Row-action buttons (Edit/Delete/Archive/View/Regenerate Password) had drifted into two different visual languages across the three data-grid pages: 01.1 used a designed circular icon-button (`w-9 h-9 rounded-full`, tinted hover background) for Delete but a plain text link ("View Details") for the view action, while 04.1 and 05.1 used plain emoji-character buttons with only a text-color hover change and no button shape/background at all. Unified all three onto one pattern — a circular icon-button (`w-8`/`w-9 h-9 rounded-full`, neutral default, semantic-tinted hover background + text color: talentpilot for Edit/Regenerate, amber for Archive, red for Delete, talentpilot for View) — reusing 01.1's existing Delete button as the reference size/shape since it was the most fully "designed" of the three. Also added missing `dark:` hover-background variants to 01.1's Delete button (it previously had light-mode-only `hover:bg-red-100`) and converted 01.1's "View Details" text link to a matching eye-icon button, adjusting the accordion table's header cell (previously a single "Actions" label spanning the text-link column) to two `sr-only`-labeled icon columns instead. No behavior changed — only button chrome.

**Layout fix (direct request — "the heading and searchbar and new button should be in the same line and toolbar should show under the heading similarly like skill page"):** 01.1's Skill Assignments page previously split its heading (with employee/skill count text) into a separate row inside Main Content, below a toolbar row that held only the search box and "+ New Assignment" button — a different structure from 04.1's Skills page, which keeps the heading + count stacked on the left and the search/action controls on the right, all in one toolbar row. Restructured 01.1 to match: heading and count now live inside the toolbar row (left side), with search input and the New Assignment button on the right (same row) — removing the now-redundant standalone heading row from Main Content. Element IDs (`skills-dashboard-heading-title`, `skills-dashboard-summary-count`) were kept unchanged, so the existing search/count-rendering JS needed no changes.

**Scope confirmation, no code change needed:** A follow-up message ("default view in all pages are in grid view only in employee and skill pages") was a scope check, not a new request — confirmed only 04.1 (Skills) and 05.1 (Employees) have a Grid/Card view toggle at all (`grep` for `setSkillsView`/`setEmployeesView`/`currentView` matches only those two files); 01.1 and 06.1 have no such toggle, so the earlier "default view in all pages is grid" work was already correctly scoped and nothing further was needed.

**Verification:** All 4 mockup files (01.1, 04.1, 05.1, 06.1) re-passed the established checks — inline `<script>` blocks extracted and `node --check`-ed clean, and open/close tag-balance counts (div/table/tr/td/th/button/ul/li/a/span/aside/main/header) matched exactly, before and after these edits.

**Follow-up fix, same day (direct request — "employee page delete button is not sync with the other pages and also show some difference between the Archive and Delete buttons"):** The first consistency pass above left one real mismatch: 01.1's View/Delete buttons were `w-9 h-9` with permanently-colored icons (talentpilot/red at rest, darkening further on hover), while 04.1/05.1's Edit/Delete/Archive/Regenerate buttons were `w-8 h-8` and neutral gray at rest, tinting only on hover — the two pages actually looked different at a glance despite sharing the same shape convention. Also, within 05.1 itself, Archive and Delete were only distinguishable by icon glyph (🗄 vs ✕) and by a hover color that isn't visible until the pointer is over the button — at rest, both looked like plain neutral buttons. Fixed both in one pass: (1) resized 01.1's View/Delete to `w-8 h-8` to match the other two pages exactly, and changed View to neutral-gray-at-rest (matching Edit's treatment elsewhere) so only genuinely destructive actions carry color; (2) introduced a second, permanently-visible button tier for the two row-removing actions — Archive (05.1) gets an always-on amber-tinted pill (`bg-amber-50 dark:bg-amber-900/20 text-amber-600...`), Delete (01.1, 04.1, 05.1 — wherever it appears) gets an always-on red-tinted pill — while Edit/Regenerate Password/View stay neutral-gray-at-rest, hover-tint-only. Archive and Delete are now visually distinct from each other and from the safe actions without needing to hover, across all three pages.

**Verification:** Re-ran the same inline-script `node --check` + tag-balance checks on 01.1/04.1/05.1 after this fix; all clean.

**Third fix, same day (direct request — "when minimize the left pane and select any menu in minimized mode page is flickering"):** Root cause was a page-load-timing bug in `shared/nav.js`, not a CSS/animation problem. `shared/nav.js` is `<script src>`-included in `<head>`, alongside `shared/theme.js` — but unlike theme.js (which only ever touches `<html>`'s class list, always available even in `<head>`), nav.js needs `#app-nav-sidebar` and its child nav links/labels/icons, which don't exist yet when a `<head>` script runs. So `TalentPilotNav.init()` was deferred to the `DOMContentLoaded` event — which only fires after the *entire* document (every element on the page, not just the sidebar) has finished parsing. Since each page here is a full server-rendered reload (not an SPA), every click on a nav link while collapsed re-triggers this from scratch: the browser paints the sidebar in its default `w-56` expanded markup first, then `DOMContentLoaded` fires and JS snaps/animates it (the sidebar's own `transition-all duration-200`) down to `w-16` collapsed — a visible flash on every single navigation, not just the first load. Fixed by adding one inline `<script>window.TalentPilotNav && window.TalentPilotNav.init();</script>` as the last child inside `<aside id="app-nav-sidebar">`, right before its closing tag, in all 4 mockups — by the time the parser reaches that point, the entire sidebar subtree (links, labels, icons, toggle button) already exists, so `init()` can apply the correct collapsed/expanded state immediately, before the rest of the document (and any meaningful first paint) happens, instead of waiting for the whole page. `shared/nav.js`'s own `DOMContentLoaded` listener was left in place as a harmless, idempotent fallback (re-applying the same classes is a no-op). No changes to `shared/nav.js`, `shared/theme.js`, or the transition CSS itself were needed — this was purely an initialization-timing fix, four identical inline-script insertions.

**Verification:** Re-ran inline-script `node --check` + tag-balance checks on all 4 mockups after this fix (one false-positive `aside` tag-count mismatch was traced to the new HTML comment's own prose literally containing the string `<aside>`, not a real structural issue — reworded the comment, re-verified clean).

**Documentation catch-up (direct request — "update all the document based on these changes including stories and all if needed update the claude.md file as well"):** Two real gaps found and closed while writing this up, not just a restatement of what's already logged above. (1) Story 10.3 ("Delete/Archive Icon Reflects the Real Action Before the Click") already existed for the Archive-vs-Delete icon *distinction*, but had no AC describing the concrete visual treatment — added one documenting the two-tier button system (neutral-gray-hover-only for safe actions, permanent amber/red tinted pill for Archive/Delete) decided in this pass. (2) The collapsible/expandable left-pane nav itself (`shared/nav.js`, added earlier this session per a direct request) turned out to have **no FR or Story coverage anywhere** — a real documentation gap, not something deliberately deferred. Closed it: added **FR-42** (`prd.md` §4.11) and **Story 10.15** (`epics.md`, Epic 10 goal/story-count updated 14→15, `Source`/build-order updated, FR Coverage Map gained an FR-42 row), explicitly marked `[documented retroactively]` since the feature predates the story. `sprint-status.yaml` gained a `10-15-...: backlog` entry with the same explanatory comment style as the other late-added Epic 10 stories. `CLAUDE.md`'s "Current status" section was stale (`FR-34–FR-40`/`10-1...10-10`) — updated to `FR-34–FR-42`/`10-1...10-15`, plus a new sentence clarifying the mockups now diverge from the real `frontend/src/pages/hr/*` components and shouldn't be read as current app behavior. UX-scenario spec docs (`C-UX-Scenarios/`) were **not** re-touched for this pass, same proportionate-effort call already established and logged earlier this session for the sheer volume of same-day mockup changes.

**Fourth addition, same day (direct request — "Add one setting under the logout button to configure the Company name to show just right beside the collapse and open menu"):** New client-only (`localStorage`, no backend) "Company Settings" capability, added identically across all 4 mockups. A "Company Settings" item was added to the user dropdown, directly below Sign Out (as literally requested); it opens a small modal (name input + Save/Cancel, styled like the existing Delete/Archive confirmation modals) backed by a new `shared/company.js` (same include-in-`<head>`/localStorage-persistence pattern as `shared/theme.js`/`shared/nav.js`). The saved name renders into a small label positioned immediately beside the nav pane's collapse/expand toggle button — the toggle's previously-bare `<button>` was wrapped in a flex row alongside a new `.app-nav-company-name` span, which also carries the existing `.app-nav-label` class so it automatically hides when the pane is collapsed, reusing `shared/nav.js`'s existing collapse logic rather than adding new toggle logic. The label's initial render was wired into the same inline early-init `<script>` added for the flicker fix above (now calls both `TalentPilotNav.init()` and `TalentPilotCompany.init()`), so it's correct on first paint too, not just after a later `DOMContentLoaded`.

**Real bug caught during this pass, not shipped:** three of the four mockups (01.1, 04.1, 06.1) have no generic `openModal(id)`/`closeModal(id)` helper at all — only 05.1 does, each modal elsewhere is opened/closed by its own dedicated function. The first implementation pass wired the new modal's Cancel/Save buttons to the generic helpers, which would have thrown a `ReferenceError` on click in those three files. Caught by checking each file's actual modal-handling code before assuming the helper existed everywhere, not by trial and error — fixed by making `openCompanySettingsModal()`/`closeCompanySettingsModal()` self-contained (direct `classList` calls) in all 4 files instead of relying on a helper only one of them has.

**Verification:** `node --check` on the new `shared/company.js` plus all 4 mockups' inline scripts, and open/close tag-balance, both before and after the helper-dependency fix; all clean.

**Immediate positioning correction, same day (direct request — "in header session need to show the company name right side of the <<"):** the Company Name label had been placed to the *left* of the collapse toggle ("«"); swapped the flex order in all 4 mockups so the toggle renders first and the label renders second, immediately to its right, matching the correction literally. A scripted swap introduced a cosmetic whitespace glitch (the toggle button's opening tag landed on the same source line as the wrapping `<div>`, no functional effect but poor source readability) — caught and reformatted properly in a follow-up pass before considering this done. Re-verified `node --check` + tag-balance on all 4 files; clean.

**Structural correction, same day (direct request — "company name should not be in the toggle menu[,] after the toggle menu"):** the toggle button and the company-name label had been sharing one `flex`-sized wrapper `<div>` — meaning the toggle's own screen position shifted depending on whether the label was present (expanded) or hidden (collapsed), since the wrapper's `right`-anchored box grows/shrinks with its content. Split them into two independent, absolutely-positioned siblings instead of one nested inside a shared container: the toggle keeps its original always-fixed `-right-3 top-6` position (visually unchanged and stable in every state, collapsed or expanded), and the label is now separately positioned at a fixed offset (`right-[1.125rem] top-6`) immediately to the toggle's left/inward side — still reading "after" the toggle in DOM order, just no longer nested inside its container. A short `AskUserQuestion` round beforehand (left-vs-right ordering inside that div) confirmed the current toggle-first/label-second order was already correct, so only the *nesting*, not the order, needed to change. Re-verified `node --check` + tag-balance on all 4 files after both this change and a follow-up indentation cleanup; all clean.

**Relocated, same day (direct request — "just before the dark/light button"):** the label's home moved a third and final time — out of the `<aside>` sidebar entirely and into the top `<header>` bar, as a normal flex child positioned immediately before `#app-theme-toggle` (the 🌙/☀️ button), rather than anywhere near the sidebar's collapse toggle. It no longer carries `.app-nav-label` (that class's collapse-tied visibility no longer applies once the label isn't in the sidebar) — it's now always visible regardless of the nav's collapsed/expanded state. `shared/company.js`'s header comment and the modal's own helper copy ("Shown next to the collapse/expand toggle...") were both updated to describe the new location, not left stale.

**Two follow-up styling refinements, same day, in quick succession (direct requests: "make the text bigger and align the ... span to left"; then "make the label little bigger and change the color in"):** (1) the header was `justify-end`, which packed the company-name label into the same right-aligned cluster as the theme toggle and user avatar — restructured to `justify-between` with the theme-toggle + user-menu now grouped in their own `flex items-center` wrapper, so the label anchors to the opposite (left) edge of the header instead, a more conventional "brand/org name left, controls right" top-bar layout; text size bumped `text-sm` → `text-lg`. (2) Bumped again to `text-xl font-bold` and recolored from neutral gray to the `talentpilot` brand color (`text-talentpilot-700 dark:text-talentpilot-300`), so it reads as a deliberate label rather than blending into the header's other muted text.

Two more quick size-only bumps followed the same day ("company label increase the font side" [size]; then "little more"): `text-lg` → `text-xl` → `text-2xl` → `text-3xl`, each applied identically across all 4 files. Finally, "increase/auto the span width based on the company name" — the span had carried `max-w-[16rem] truncate` since its first version, which would silently ellipsis-clip a long name; dropped both classes (kept `whitespace-nowrap` so it still can't wrap to a second line and disrupt the header's height) so the span now sizes itself to whatever name is actually set, with no artificial cap.

**Verification:** `node --check` + tag-balance re-run on all 4 files after each of these passes (relocation, left-alignment restructure, size/color bumps, and the width-cap removal); all clean throughout.

**Documentation sync, same day (direct request — "update all the documents with these html design changes including stories and epics and also claude.md file as well"):** Story 10.16 (`epics.md`) and FR-43 (`prd.md`) had been written to describe the *first* implementation of the Company Name label (beside the sidebar's collapse toggle, capped/truncated width) — both were rewritten to describe the shape it actually shipped in after all the corrections above: header-anchored left of a `justify-between` split, `text-3xl` bold brand-colored, auto-width with no truncation cap. Story 10.16's title changed from "...Beside the Nav Collapse Toggle" to "...Shown in the Top Header"; its AC gained explicit ACs for the header-restructure and auto-width behaviors, each citing the direct-feedback correction that produced it rather than presenting the final shape as the original plan. `sprint-status.yaml`'s `10-16-...` key was renamed to match (still `backlog`, so safe to rename — nothing else references the old key yet) and its comment rewritten with the full correction sequence. `epics.md`'s `extensionNote` frontmatter got the same rewrite. Checked `CLAUDE.md`'s Epic 10 status line — already accurate (FR-34–FR-43, 16 stories, `10-1...10-16`) since none of this changed the FR/story count, only Story 10.16's internal detail — so no edit was needed there this time, unlike the two prior doc-sync passes.

**Next:** Still-open Backlog items above (diverged 05.1 copy, `shared/auth.js` stale demo accounts, unstyled status/provenance badges in dark mode) remain untouched by this pass.

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
