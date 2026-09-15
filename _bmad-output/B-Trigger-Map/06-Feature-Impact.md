# Feature Impact Analysis: TalentPilot-AI

## Scoring

**Primary Persona (⭐ Rita the Referee):** High = 5 pts | Medium = 3 pts | Low = 1 pt
**Secondary Persona (Casey the Continuer):** High = 3 pts | Medium = 1 pt | Low = 0 pts

**Max Possible Score:** 8 (with 2 personas)
**Must Have Threshold:** 5+ or Primary High (5)

---

## Prioritized Features

| Rank | Feature | Score | Decision |
| ---- | ------- | ----- | -------- |
| 1 | Auto-Captured Video Progress Tracking | 8 | Must Have MVP |
| 2 | AI Content Discovery (skill → matched content) | 6 | Must Have MVP |
| 2 | HR Assignment Flow | 6 | Must Have MVP |
| 2 | Continue-Watching / Resume Card | 6 | Must Have MVP |
| 5 | Provenance-Labeled Dashboard (Verified/Self-reported/Needs Attention) | 5 | Must Have MVP |
| 5 | "Needs Attention" Filter + Drill-Down Reasoning | 5 | Must Have MVP |
| 7 | Proxy-Signal Tracking for Docs/Websites (scroll-depth, time-on-page) | 3 | Consider for MVP |
| 7 | HR "Assessed Live" Flag with Audit Trail (manual override for sub-skills) | 3 | Consider for MVP |
| 7 | Skill Assignment Dashboard (org-wide stats + Assignment Progress ring) `[ADDED 2026-09-13, RE-EVALUATED 2026-09-15]` | 3 → **flagged, see below** | MVP (already committed via PRD) |
| 9 | "Your Week in Learning" Recap for Employees | 2 | Defer |

---

## Decisions

**Must Have MVP (Primary High OR Top Tier Score):**

- Auto-Captured Video Progress Tracking (8) — the evidence-pipeline engine itself; every other objective depends on this working
- AI Content Discovery (6) — removes Casey's "what do I even watch" friction and shortens Rita's assignment-to-engagement gap
- HR Assignment Flow (6) — Rita's actual daily recurring task; the entry point for everything downstream
- Continue-Watching / Resume Card (6) — inseparable from tracking by product design ("one signal, two payoffs"); see Strategic Rationale below
- Provenance-Labeled Dashboard (5) — the specific mechanic that prevents Rita's "looks more trustworthy than it is" fear
- "Needs Attention" Filter + Drill-Down Reasoning (5) — converts Rita's habitual full-grid scanning into a targeted, efficient workflow

**Consider for MVP:**

- Proxy-Signal Tracking for Docs/Websites (3) — extends the trust model beyond video, directly addressing Rita's fear that "the chore just moves elsewhere," but is explicitly flagged in source discovery work as scope-expanding beyond the current MVP
- HR "Assessed Live" Flag with Audit Trail (3) — gives Rita a manual override with accountability for non-video sub-skills, but is a secondary safety net, not the core mechanic
- Skill Assignment Dashboard (3, `[ADDED 2026-09-13]`) — **`[RE-EVALUATED 2026-09-15]` The specific mechanic this score was earned by no longer exists on this page.** Original reasoning (kept for history): org-wide stats + an Employee Segmentation pie chart (On Track / In Progress / Needs Attention), added to the PRD (§4.10, FR-31–33) as a new HR Admin landing page, scored Medium/Primary for Rita because it genuinely served Want #3 ("a fast, confident readiness call") and Want #2 ("stop chasing people," by surfacing who needs attention before she's even asked). **Story 10.11 (2026-09-15) removed the Employee Segmentation pie chart and its Needs Attention click-through from this page entirely, replacing it with the Experience Distribution panel** — a pure headcount-by-experience breakdown that, per this same document's Enabling Features section (2026-09-15 entry), has no connection to either persona's driving forces. The page's remaining content (org-wide stats, Assignment Progress ring) has a much weaker, more diffuse connection to Want #3 than the retired segmentation chart did — arguably not enough on its own to justify a 3-point score under this rubric's own logic, but not formally re-scored here since (a) it was already committed to MVP scope via the PRD before the original scoring pass ran, same as before, and (b) a real re-score is a judgment call for the user to make deliberately, not something to silently downgrade mid-edit. **Flagged, not resolved:** the next Trigger Map session touching this document should either re-score this row (likely toward Enabling, alongside Employee Roster Management) or explicitly decide the remaining stats/ring content still earns its keep on the current rubric.

**Defer (Nice-to-Have or Low Strategic Value):**

- "Your Week in Learning" Recap for Employees (2) — motivational and reuses existing watch-position data cheaply, but addresses no confirmed pain point from either persona; a fast-follow once the core loop is proven, not a launch requirement

---

## Enabling Features (Outside the Psychological Scoring Model)

`[ADDED 2026-09-11]` Not every buildable capability competes with Rita/Casey's driving forces for priority — some are structural plumbing the product needs regardless of psychological pull, the same way Authentication (FR-13/FR-14) never appears in the scoring table above despite being load-bearing. Three additions from the 2026-09-11 PRD update belong in this same category, not force-fit into the 8-point rubric:

- **Employee Roster Management** (PRD §4.7, FR-24–28) — HR Admin CRUD on Employee records, replacing the hand-seeded demo list as the real roster/login source. Structurally necessary (the product can't function on 5 hardcoded demo accounts forever) but not something either persona *wants* in the driving-forces sense — nobody's psychological pull is "I want a CRUD screen." See the Key Insights doc for a real risk this raises, not just a neutral scoring omission.
- **HR Admin Navigation Shell** (PRD §4.8, FR-29) — top nav relocated to a left-side pane. Mild usability/findability quality-of-life change; doesn't move any named want or fear.
- **Application Theming** (PRD §4.9, FR-30) — Light/Dark mode, app-wide. Personal comfort/accessibility nicety with no connection to either persona's driving forces — same tier as the already-deferred "Your Week in Learning" recap, just infrastructure-flavored rather than feature-flavored.

`[ADDED 2026-09-15]` Six more additions from the same day's `bmad-correct-course` → PRD §4.11 update (Epic 10, FR-34–40) extend this same Enabling category rather than scoring separately — none of them serve a named want or fear the way Auto-Capture or the Provenance-Labeled Dashboard do:

- **Employee Grid Columns, 90-Day Talent-Pool Flag, Delete/Archive Icon Clarity, Experience Distribution Panel** (FR-34, FR-35, FR-36; Story 10.3) — all direct extensions of the already-Enabling Employee Roster Management above (more columns, a roster-hygiene flag, icon-level clarity, a headcount-by-experience panel). `[NOTE]` The 90-day flag (FR-35) *looks* structurally similar to Rita's Fear #1 (stale data) but isn't the same mechanic — it flags Employee tenure in the Talent Pool, not assignment/skill readiness staleness (that's FR-10's existing 7-day Needs-Attention rule, already scored). Surfaced here so the resemblance isn't mistaken for a real connection to the scored trust mechanic.
- **Skills Tab & Skill Assignments Grid Search/Pagination** (FR-37, FR-38) — pure findability/scale tooling as the roster and catalog grow, same category as Employee Roster's existing FR-25 pagination. No persona-psychology angle.
- **New-Skill Content-Sourcing Reliability, Seeded Credential, Credential-Gated Skill Creation** (FR-39, FR-40; Stories 10.8/10.9) — reliability/hardening fixes on the **existing, already-unscored** Admin-Assisted Content Sourcing capability (Epic 6, FR-16–23) — see the flagged gap below. These don't introduce new psychological pull; they fix a real reported gap in Rita's ability to complete the HR Assignment Flow (already scored 6, Must Have) when a brand-new Skill has no content yet.
- **Seeded Identity Rename, Seed-Data Minimization** (Stories 10.1, 10.10) — pure internal/ops housekeeping (account email/display name, dev seed shape). Zero user-facing psychological connection at all — these arguably aren't "features" in this document's sense any more than a database migration is, included here only for completeness.

`[FLAGGED 2026-09-15]` **A second, pre-existing gap found while placing Epic 10, not introduced by it:** Epic 6 (Admin-Assisted Content Sourcing, FR-16–23, added to the PRD 2026-09-08) was **never run through Trigger Mapping at all** — zero mention anywhere in this document or `05-Key-Insights.md` before today. Unlike Employee Roster/Nav/Theming (explicitly filed as Enabling on 2026-09-11) or the Skill Assignment Dashboard (explicitly scored on 2026-09-13), Epic 6 simply skipped this phase. It's plausibly Enabling in the same sense as Employee Roster Management (an HR Admin content-curation CRUD tool, not something either persona *wants* in the driving-forces sense) — but that's an inference made now, not a decision made at the time. Not reconciled here (out of this pass's requested scope, extending for Epic 10) — flagged so it isn't mistaken for a deliberate, considered omission.

**Why these aren't scored, not just scored low:** Scoring them at 0-1 points on the existing rubric would misrepresent them as *failed* candidates for psychological priority, when they were never candidates for it in the first place — same reasoning that kept Authentication out of this table originally.

---

## Strategic Rationale

**Why Continue-Watching/Resume scores as Must Have despite Casey being secondary:** The product brief explicitly frames auto-capture and resume as **one atomic mechanic**, not two separable features — "a single video watch-position data pipe is simultaneously the auto-captured trust signal powering HR's dashboard and the resume/continue-watching mechanic for employees." Scoring them as fully independent features would misrepresent the architecture: shipping tracking without resume (or vice versa) isn't a real option, because they're generated by the same write operation. This feature ships bundled with #1 regardless of its isolated score — the scoring here confirms priority, it doesn't gate a build decision that's already structurally locked in.

**Why the Provenance-Labeled Dashboard and Needs-Attention Filter are separate line items, not one feature:** They serve two different moments in Rita's workflow — provenance labeling is what she sees passively on every visit; the Needs-Attention filter is what she actively reaches for during a readiness judgment. Both score identically (5) because both are required for the "trust legible, not just present" objective, but they're independently buildable and testable.

**Why Proxy-Signal Tracking and the Audit-Trail Flag are "Consider," not "Must Have":** Both directly address a real, named risk (the trust gap moving to non-video content, flagged explicitly in the design thinking session as unresolved even post-launch). They score lower here purely because they weren't part of the committed MVP scope in the Product Brief — this is a scope decision already made upstream, not a psychology-driven deprioritization. Flagging them here keeps the gap visible rather than silently dropped.

**Connection to Business Goals:** The six Must-Have features map directly onto the Business Goals document's three-tier structure — Auto-Capture and Assignment Flow serve the PRIMARY GOAL (prove the evidence pipeline); the Dashboard, Needs-Attention filter, and Content Discovery serve EARN HR'S TRUST; the Resume Card is the direct deliverable of ELIMINATE THE SELF-REPORT CHORE.

**`[FLAGGED 2026-09-13]` Pre-existing, unreconciled drift: the "Needs Attention Filter" scored above (rank 5) was never actually built.** This document (created 2026-07-08) scores a dedicated "Needs Attention" Filter + Drill-Down Reasoning as Must Have MVP, and 05-Key-Insights.md still lists "surface a 'Needs Attention' filter as a primary, prominent action" as a Design Implication. `prd.md` §6.2 (Out of Scope for MVP) explicitly reverses this: *"Dedicated 'Needs Attention' filter control — considered ... and explicitly not added; FR-9's per-row drill-down plus FR-10's visual flagging is the MVP interaction model instead."* That PRD decision predates this trigger-mapping session and was never carried back into these Phase 2 docs — discovered only now, while assessing where the new Skill Assignment Dashboard fits. The new dashboard's Employee Segmentation pie chart (Needs Attention as one of its three buckets, §4.10/FR-32) is the closest thing that has actually shipped to what this document originally scored — but it's an org-wide, per-Employee summary on a landing page, not a row-level filter control on the grid itself, so it only partially closes this gap, not fully. Not fixed here (out of this session's requested scope, extend-for-the-new-dashboard) — flagging it so it isn't mistaken for settled.

**Development Phases Aligned with the Flywheel:**
- **Phase 1 (Launch, 13 July 2026):** All six Must-Have features — nothing in this tier is separable from the 13 July deadline without breaking the core hypothesis test
- **Phase 2 (Post-pilot, informed by 60-day checkpoint data):** Consider-tier items (proxy-signal tracking, audit-trail flag) — only pursued if real usage data shows the video-only trust story is genuinely limiting Rita's confidence on non-video assignments
- **Phase 3 (Opportunistic fast-follow):** Defer-tier items (weekly recap) — cheap to build once the core data pipe is proven, but not a condition of pilot success

---

## Related Documents

- **[00-trigger-map.md](00-trigger-map.md)** - Visual overview and navigation
- **[01-Business-Goals.md](01-Business-Goals.md)** - Objectives and metrics
- **[02-Rita-the-Referee.md](02-Rita-the-Referee.md)** - Primary persona
- **[03-Casey-the-Continuer.md](03-Casey-the-Continuer.md)** - Secondary persona
- **[05-Key-Insights.md](05-Key-Insights.md)** - Strategic implications

---

_Generated with Whiteport Design Studio framework_
_Strategic input for Phase 4: UX Design and Phase 6: PRD/Development_
