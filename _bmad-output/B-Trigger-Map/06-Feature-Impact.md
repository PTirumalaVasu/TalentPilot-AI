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

**Defer (Nice-to-Have or Low Strategic Value):**

- "Your Week in Learning" Recap for Employees (2) — motivational and reuses existing watch-position data cheaply, but addresses no confirmed pain point from either persona; a fast-follow once the core loop is proven, not a launch requirement

---

## Enabling Features (Outside the Psychological Scoring Model)

`[ADDED 2026-09-11]` Not every buildable capability competes with Rita/Casey's driving forces for priority — some are structural plumbing the product needs regardless of psychological pull, the same way Authentication (FR-13/FR-14) never appears in the scoring table above despite being load-bearing. Three additions from the 2026-09-11 PRD update belong in this same category, not force-fit into the 8-point rubric:

- **Employee Roster Management** (PRD §4.7, FR-24–28) — HR Admin CRUD on Employee records, replacing the hand-seeded demo list as the real roster/login source. Structurally necessary (the product can't function on 5 hardcoded demo accounts forever) but not something either persona *wants* in the driving-forces sense — nobody's psychological pull is "I want a CRUD screen." See the Key Insights doc for a real risk this raises, not just a neutral scoring omission.
- **HR Admin Navigation Shell** (PRD §4.8, FR-29) — top nav relocated to a left-side pane. Mild usability/findability quality-of-life change; doesn't move any named want or fear.
- **Application Theming** (PRD §4.9, FR-30) — Light/Dark mode, app-wide. Personal comfort/accessibility nicety with no connection to either persona's driving forces — same tier as the already-deferred "Your Week in Learning" recap, just infrastructure-flavored rather than feature-flavored.

**Why these aren't scored, not just scored low:** Scoring them at 0-1 points on the existing rubric would misrepresent them as *failed* candidates for psychological priority, when they were never candidates for it in the first place — same reasoning that kept Authentication out of this table originally.

---

## Strategic Rationale

**Why Continue-Watching/Resume scores as Must Have despite Casey being secondary:** The product brief explicitly frames auto-capture and resume as **one atomic mechanic**, not two separable features — "a single video watch-position data pipe is simultaneously the auto-captured trust signal powering HR's dashboard and the resume/continue-watching mechanic for employees." Scoring them as fully independent features would misrepresent the architecture: shipping tracking without resume (or vice versa) isn't a real option, because they're generated by the same write operation. This feature ships bundled with #1 regardless of its isolated score — the scoring here confirms priority, it doesn't gate a build decision that's already structurally locked in.

**Why the Provenance-Labeled Dashboard and Needs-Attention Filter are separate line items, not one feature:** They serve two different moments in Rita's workflow — provenance labeling is what she sees passively on every visit; the Needs-Attention filter is what she actively reaches for during a readiness judgment. Both score identically (5) because both are required for the "trust legible, not just present" objective, but they're independently buildable and testable.

**Why Proxy-Signal Tracking and the Audit-Trail Flag are "Consider," not "Must Have":** Both directly address a real, named risk (the trust gap moving to non-video content, flagged explicitly in the design thinking session as unresolved even post-launch). They score lower here purely because they weren't part of the committed MVP scope in the Product Brief — this is a scope decision already made upstream, not a psychology-driven deprioritization. Flagging them here keeps the gap visible rather than silently dropped.

**Connection to Business Goals:** The six Must-Have features map directly onto the Business Goals document's three-tier structure — Auto-Capture and Assignment Flow serve the PRIMARY GOAL (prove the evidence pipeline); the Dashboard, Needs-Attention filter, and Content Discovery serve EARN HR'S TRUST; the Resume Card is the direct deliverable of ELIMINATE THE SELF-REPORT CHORE.

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
