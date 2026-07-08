# Project Brief: TalentPilot-AI

> Complete Strategic Foundation

**Created:** 2026-07-08
**Author:** TalentPilot
**Brief Type:** Complete

---

## Strategic Summary

TalentPilot-AI is an internal pilot tool being built by TalentPilot for SAILS Software's own HR function. It replaces the shared spreadsheet HR uses to track employee skill development with a dashboard built on automatically-captured signal instead of self-reported status. The real problem isn't the spreadsheet format — it's the incentive-free chore of manual self-reporting that makes HR's data untrustworthy in the first place. TalentPilot-AI kills that chore for video-based learning by auto-capturing watch progress, and is deliberately honest — not universally trustworthy — about everything else on the dashboard.

This is a solo-driven, fast-iterative build framed as a 1-week hackathon pitch, with a hard launch date of 13 July 2026 and zero budget. There is no external stakeholder alignment gate — TalentPilot has full decision authority — and no commercial ambition: this is an internal pilot, not a product with unit economics. Extensive prior discovery (brainstorming, design thinking, market/domain/technical research, and a full PRFAQ stress-test) already grounds this brief; it confirms and sharpens those findings rather than starting from zero.

---

## Vision

Replace SAILS HR's spreadsheet-dependent skill tracking with a dashboard built on automatically-captured signal, not self-reported status — so HR can open it and simply trust what it says, without chasing anyone for an update.

**Key Insights from Discussion:**
- The root-cause reframe carries forward unchanged from the PRFAQ: the villain is manual self-reporting, not the spreadsheet format itself.
- The clearest success marker, in TalentPilot's own words: "HR opens the dashboard and just trusts it."
- Nothing has changed in direction since the PRFAQ was completed on 2026-07-08 — this vision step served as confirmation, not new discovery.

---

## Positioning Statement

For SAILS HR admins who need trustworthy, low-effort visibility into employee skill readiness, TalentPilot-AI is an internal skill-assignment and tracking dashboard that replaces self-reported spreadsheet status with automatically-captured video-progress signal. Unlike the current spreadsheet — or a heavyweight LMS/talent-intelligence suite that would be disproportionate for testing this one hypothesis — TalentPilot-AI is narrow, fast to stand up, and honest about what it can and can't verify: video progress is auto-verified, everything else is clearly labeled as self-reported.

**Breakdown:**

- **Target Customer:** SAILS HR/L&D admins (primary); Employees (secondary, in-product role)
- **Need/Opportunity:** Trustworthy, low-effort skill-readiness visibility without manual chasing or self-reporting
- **Category:** Internal HR skill-assignment and tracking dashboard
- **Key Benefit:** A dashboard HR can open daily and simply trust, because it tells you which cells are verified vs. self-reported instead of blending everything into one indistinguishable grid
- **Differentiator:** Fully automatic video-progress capture (zero manual entry) + "mixed trust, clearly labeled" data model — a narrower, more honest claim than "the dashboard is fully trustworthy"

---

## Business Model

**Type:** Internal only — no B2B or B2C model applies

TalentPilot-AI is confirmed as an internal pilot tool for SAILS Software's own HR function only. An earlier commercial/GTM framing (per-employee SaaS pricing, multi-year ARR targets) was explored in an early innovation-strategy exercise but has been fully set aside in favor of "internal pilot only, no unit economics" — this was explicitly re-confirmed during this brief, consistent with the PRFAQ's locked framing. No Business Customer Profile applies; the two roles in scope (HR, Employee) are internal users, not paying customers.

---

## Target Users

### Primary User: HR Admin

- **Role:** HR/L&D admin at SAILS Software — assigns must-do skills/courses, judges project-readiness
- **Daily behavior (confirmed):** Opens the shared Excel sheet **daily** to add/update assignments; periodically reviews status to judge readiness; chases employees who haven't self-reported
- **Emotional state toward current process:** Resigned, not tolerant — has given up trying to fix the spreadsheet process, not just quietly accepting it
- **Frustrations:** Doesn't trust the status column since it depends on someone else remembering to update it; anxious making real staffing calls on data they suspect is stale
- **Goals:** A single, live source of truth for who's ready — no manual check-ins, no chasing

**Design implication:** Because HR checks the spreadsheet daily, "live" is a hard product requirement, not a nice-to-have. Freshness indicators and the "Needs Attention" filter need to reflect near-real-time state.

### Secondary Users: Employees

- **Role:** Individual contributors assigned must-do skills/courses by HR
- **Daily behavior:** Self-report progress into the same shared sheet today — an easy-to-deprioritize chore with no personal payoff
- **Goals:** Find the right learning content fast; resume exactly where they left off, consumer-app style (Netflix/Spotify pattern)

---

## Product Concept

**Core Structural Idea:** One signal, two payoffs. A single video watch-position data pipe is simultaneously the auto-captured trust signal powering HR's dashboard and the resume/"continue watching" mechanic for employees — not two features sharing a database table, but one signal deliberately designed to serve two audiences at once.

**Paired discipline on the dashboard side:** Labeled trust, not uniform trust. Every data point carries an explicit provenance label — verified (auto-captured video), self-reported (employee-entered, non-video), or needs attention (stale/inconsistent/unclear) — with drill-down reasoning. A blank or "Unknown" cell beats a guessed one.

**Concrete example:** An employee watches a video and closes the tab at 73%. The same watch-position write that lets them resume exactly at 73% next time is the same write that updates their row on HR's dashboard as "verified, 73% complete, updated 2 minutes ago." No separate sync step.

**Why this structural choice matters:** It avoids two failure modes — tracking and resume drifting out of sync if built as separate efforts, and a uniform-looking dashboard that's worse than the spreadsheet it replaces because it looks more trustworthy than it actually is.

---

## Success Criteria

**Primary metric (data quality):** Self-reported skill data staleness drops below **5%** within 60 days of launch, driven by automated (video) progress tracking replacing manual self-reports.

**Primary metric (adoption):** HR uses TalentPilot-AI as the primary source of truth during talent reviews, with minimal-to-no reliance on the legacy spreadsheet — measured via **dashboard usage analytics + direct stakeholder feedback**, not self-report alone.

**Timeline:** Launch **13 July 2026** (hard line). Primary success checkpoint at **60 days post-launch (~11 September 2026)**, evaluating adoption, data freshness, and stakeholder confidence together.

These thresholds were deliberately locked in advance — closing a gap the PRFAQ's Internal FAQ had explicitly flagged: telemetry thresholds for confirming/refuting the root-cause hypothesis must be decided before data exists, not read favorably after the fact.

---

## Competitive Landscape

**Alternative 1 — Do nothing / keep the spreadsheet:** The actual status quo the success metrics are measured against. HR keeps chasing status, keeps distrusting the data, keeps making staffing calls off numbers they suspect are stale.

**Alternative 2 — Enforce the spreadsheet harder:** Rejected. Self-reporting has zero personal benefit to the person doing it, so it's always the first thing deprioritized under load — no amount of policy enforcement fixes an incentive-free chore.

**Alternative 3 — Buy an existing LMS/talent-intelligence platform** (Cornerstone, Degreed, LinkedIn Learning, Eightfold, Gloat): Rejected. No reviewed vendor does granular auto-polled watch-% as its core trust signal — their "skill signals" remain self-reported/peer-endorsed. Heavyweight implementation commonly costs 20–50% of license again — disproportionate for testing one narrow hypothesis on a 5-week internal pilot.

### Our Unfair Advantage

**The bet:** Cheaply and quickly prove that automated, evidence-based learning signals meaningfully outperform manual self-reporting for skill readiness, before SAILS commits to a larger investment in either direction.

**The durable advantage is the evidence pipeline, not first-mover speed.** A commercial LMS manages learning content; TalentPilot-AI's differentiator is the automated collection of verifiable, confidence-labeled learning evidence tailored to SAILS' actual workflow. Even if incumbent LMS/LXP vendors add an "assignment mode" feature later (a documented risk — category convergence since 2022), that doesn't fully neutralize TalentPilot-AI, because the evidence pipeline — not the assignment UI — is the actual asset.

**Three honest outcomes if the pilot succeeds** (not just one): keep evolving TalentPilot-AI standalone, integrate its evidence pipeline into a future LMS, or adopt a commercial platform outright if one closes the gap — with the evidence pipeline remaining the valuable, hard-to-replace piece in any of the three. This resolves the PRFAQ's previously open "post-pilot success path" question.

---

## Constraints

**Fixed:**
- **Timeline:** 13 July 2026 launch is a hard line, not movable.
- **Budget:** Effectively zero — YouTube chosen specifically for zero cost; AI embedding cost (`text-embedding-3-small`) is negligible.
- **Technical stack (shape):** YouTube IFrame API (polling-based), Postgres + pgvector, no new infrastructure required — per completed technical research.
- **Team:** Solo-driven (TalentPilot) as of now; TalentPilot owns content-approval, bug fixes, and success-metric monitoring post-launch.
- **Brand/design system:** None — internal tool, no external brand requirement.

**Flexible:**
- Exact tech stack details beyond the researched shape (specific libraries/frameworks)
- Feature scope beyond MVP — fast-follows can adjust based on pilot learnings
- Post-pilot direction (the three documented outcomes above)

**Explicitly open, by choice:**
- **Legal/compliance revisit trigger:** No written condition yet for when the current waiver (internal pilot, coaching-only data, no external customers) becomes invalid. Left genuinely open.
- **5-week phased plan:** Remains aspirational, with no committed team/roles/timeline behind it — must be resolved before the Pilot & Validation phase begins, not before the 13 July build start.

---

## Platform & Device Strategy

**Primary Platform:** Responsive web application

**Supported Devices:** Desktop (primary), tablet/mobile (responsive scaling)

**Device Priority:** Desktop-first — matches actual usage: HR checks the dashboard daily from their desk; employees watch assigned videos at a computer

**Interaction Models:** Mouse and keyboard (primary), touch (secondary)

**Technical Requirements:**
- **Offline Functionality:** None required
- **Native Features:** None — standard web APIs only (YouTube IFrame embed, `sendBeacon` for unload-safety)

**Platform Rationale:**
Fits the actual usage pattern (HR/employees at desks, not on the go), fastest time to market (no app store approval, no separate mobile codebase), and aligns with the zero-budget constraint (no native app infrastructure cost).

**Browser Support:** All modern evergreen browsers (Chrome, Firefox, Edge, Safari) — no legacy browser support required.

**Design Implications:** No native mobile UX flows or offline-first architecture needed.

**Development Implications:** Video resume/continue-watching works via standard YouTube IFrame API + `sendBeacon` on tab close; no mobile-app-specific persistence layer required.

---

## Tone of Voice

**For UI Microcopy & System Messages**

### Tone Attributes

1. **Clear & unambiguous**: Never leave room for HR to misread "self-reported" as "verified" — no cute abbreviations, no icon-only status without text. The PRFAQ warned that mislabeled trust is worse than the spreadsheet it replaces.
2. **Calm & matter-of-fact**: Reads like a confident colleague stating a fact, not a system seeking delight — this is a daily-use decision-making tool, not a consumer app.
3. **Honest about uncertainty**: States missing/stale data plainly ("No signal yet," "Last updated 12 days ago") rather than hiding gaps behind a neutral-looking blank.
4. **Quietly encouraging (employee-facing only)**: Warmth is acceptable for resume prompts and progress nudges — closer to a streaming app — but never at the cost of clarity, and never on HR-facing surfaces.

### Examples

**Dashboard Status (HR-facing):**
- ✅ "Verified · 92% watched, 2 hours ago"
- ❌ "✓ Complete"

**Stale Data (HR-facing):**
- ✅ "Self-reported · Not updated in 14 days"
- ❌ "In Progress"

**Needs-Attention Flag:**
- ✅ "Needs a second look"
- ❌ "Warning"

**Employee Resume Prompt:**
- ✅ "Pick up where you left off — 8 min remaining"
- ❌ "Continue"

**No Signal Yet:**
- ✅ "No activity recorded yet"
- ❌ "N/A"

### Guidelines

**Do:**
- Always pair a status with its provenance label (verified / self-reported / needs attention)
- State staleness explicitly with a timestamp or day-count, never hide it
- Keep HR-facing copy factual and confident; reserve warmth for employee-facing resume/progress moments

**Don't:**
- Never use a visual treatment (color, icon) as the *only* signal of trust level — always pair with text
- Never use ambiguous terms like "In Progress" or "Pending" that could apply to both verified and self-reported data
- Don't apply playful/consumer tone to HR-facing status displays — this is a system of record

*Note: Tone of Voice applies to UI microcopy (labels, buttons, errors, system messages). Strategic content (headlines, feature descriptions, value propositions) uses the Content Creation Workshop based on page-specific purpose and context.*

---

## Additional Context

**Client Profile:** TalentPilot-AI is built by TalentPilot, solo, for SAILS Software's internal HR function. Full decision autonomy — no stakeholder alignment/signoff required (the Alignment & Signoff workflow was explicitly skipped by user choice). Still framed as a 1-week hackathon pitch, working fast-iteratively, with no formal approval chain.

**Grounding documents:** This brief builds on and confirms an extensive body of prior BMAD discovery work: a brainstorming session and design-thinking session (2026-07-07), an innovation-strategy exploration (2026-07-07, largely superseded by the internal-pilot framing below), three technical/market/domain research reports (2026-07-07/08), an existing draft brief (`_bmad-output/planning-artifacts/briefs/brief-TalentPilot-AI-2026-07-08/brief.md`), and a full PRFAQ stress-test (2026-07-08) whose verdict was "Forged, with two structural cracks requiring active tending" — an untested freshness/labeling UI, and a named-but-informal owner (TalentPilot) for post-pilot operations.

**Open items intentionally carried forward, not resolved here:**
- The root-cause hypothesis ("self-reporting, not spreadsheet format, is the real pain") remains unvalidated by direct interviews — by design, to be confirmed or refuted via the locked telemetry thresholds above, not assumed.
- The legal/compliance waiver has no documented revisit trigger — left open by explicit user choice.
- The freshness/labeling UI has not yet been usability-tested with a real HR person — flagged by the PRFAQ as a pre-launch risk worth a dedicated check.

---

## Business Context

- **Primary Goal:** Prove, cheaply and quickly, that automated evidence-based learning signals meaningfully outperform manual self-reporting for skill readiness — before SAILS commits to any larger investment.
- **Solution:** HR assigns must-do skills → AI surfaces matching video/doc/website content → video watch-% is auto-captured (never self-reported) → HR dashboard shows verified vs. self-reported vs. needs-attention status with drill-down reasoning.
- **Target Users:** SAILS HR admins (primary), Employees (secondary)

*Full strategic analysis (business goals, personas, driving forces) is developed in Phase 2: Trigger Mapping.*

---

## Next Steps

This complete brief provides strategic foundation for all design work:

- [ ] **Phase 2: Trigger Mapping** - Map user psychology to business goals
- [ ] **Phase 3: PRD Platform** - Define technical foundation
- [ ] **Phase 4: UX Design** - Begin sketching and specifications
- [ ] **Phase 5: Design System** - If enabled, build components (currently `design_system_mode: none`)
- [ ] **Phase 6: PRD Finalization** - Compile for development handoff

**Outstanding decisions carried forward, not blockers to starting Phase 2:**
- Relationship between this brief and the existing `planning-artifacts/briefs/brief-TalentPilot-AI-2026-07-08/brief.md` (keep both vs. consolidate) — deferred by user request during this session
- Legal/compliance revisit trigger — left genuinely open by choice
- Named owner for post-pilot maintenance beyond 13 July build — currently TalentPilot alone, informal

---

_Generated by Whiteport Design Studio_
