# Key Decisions Log

**Project:** TalentPilot-AI
**Format:** Append-only decision log

---

## Decision 1: Skip Alignment & Signoff workflow

**Date:** 2026-07-08
**Step:** Alignment & Signoff — step-01a/01b
**Session:** 1

**Context:**
The Alignment & Signoff workflow opens by asking whether the user needs stakeholder alignment (consultant, business owner hiring suppliers, manager/employee seeking approval) or has full autonomy.

**What was decided:**
TalentPilot is doing this for themselves, with full autonomy — no stakeholder alignment or signoff document needed. Routed directly to the Project Brief workflow instead.

**Why:**
This is a solo-driven, internal hackathon-pitch build for SAILS Software's own HR function. TalentPilot has full decision authority; there is no external client or approval committee to align.

**Impact:**
No alignment/signoff documents (`pitch.md`, `contract.md`/`signoff.md`) will be produced. All subsequent BMAD work proceeds directly through Project Brief → later phases.

**Alternatives considered:**
- Running the full Alignment & Signoff workflow anyway — rejected as unnecessary overhead for a self-directed project.

**Documented in:** This session (no separate alignment artifact created)

---

## Decision 2: Complete (not Simplified) Product Brief

**Date:** 2026-07-08
**Step:** Project Brief — workflow init / brief_level routing
**Session:** 1

**Context:**
`brief_level` was not set anywhere in project config (`wds-workflow-status.yaml` doesn't exist yet), so the workflow required an explicit choice between Simplified (5-10 min) and Complete (30-60+ min) brief depth.

**What was decided:**
Run the Complete brief flow.

**Why:**
Given the volume of existing discovery (brainstorming, design thinking, market/domain/technical research, PRFAQ stress-test), the Complete flow can move fast — it's mostly confirming/sharpening already-made decisions rather than starting blank, and produces a more durable strategic foundation than the Simplified flow would.

**Impact:**
Full step sequence (Client Profile → Vision → Positioning → Business Model → Target Users → Success Criteria → Competitive Landscape → Constraints → Platform Strategy → Tone of Voice → Create Product Brief), potentially continuing into Content/Visual/Platform documents.

**Alternatives considered:**
- Simplified brief — rejected as it would under-use the extensive existing research and produce a thinner artifact than the project already supports.

**Documented in:** `dialog/00-context.md`, `dialog/progress-tracker.md`

---

## Decision 3: Client organisation confirmed as SAILS Software (internal HR tool)

**Date:** 2026-07-08
**Step:** Project Brief — step 01a Client Profile
**Session:** 1

**Context:**
Client Profile step needed to establish who the work is actually for, distinct from the product's own end users (HR/Employees).

**What was decided:**
TalentPilot-AI is an internal tool being built for/within SAILS Software's own HR function. TalentPilot is the sole driver, with full decision authority, no team currently named, and no external stakeholders/approvers. The project is still framed as a **1-week hackathon pitch** (per the existing research docs) — this framing remains active, not superseded by the later "internal pilot" framing from the PRFAQ; the two coexist (a hackathon-style fast build of a genuinely internal-use tool).

**Why:**
Confirms the working context: fast-iterative, solo-driven, no committee — shapes how directive vs. collaborative subsequent Product Brief steps should be, and confirms the 13 July 2026 launch date sits inside a compressed hackathon-style timeline rather than a standard enterprise procurement/build cycle.

**Impact:**
Subsequent steps (Vision, Positioning, Business Model, Constraints) should assume fast decision-making, no approval-chain friction, and a compressed timeline as real constraints.

**Alternatives considered:**
- Treating this as a client/agency relationship — rejected, this is internal and solo-driven.

**Documented in:** `dialog/client-profile.md`

---

## Decision 4: Business Model — Internal only, no commercial ambition

**Date:** 2026-07-08
**Step:** Project Brief — step 05 Business Model
**Session:** 1

**Context:**
The innovation-strategy document (2026-07-07) had floated a "Focused Wedge — Category Leader" GTM strategy with per-employee SaaS pricing and multi-year ARR targets ($500K–$15M across three years). This step needed to confirm whether that commercial ambition is still live, since it changes what "business model" even means for the brief.

**What was decided:**
No B2B or B2C model applies. TalentPilot-AI is confirmed as an internal pilot tool for SAILS Software's own HR function only — the earlier commercial/GTM framing from the innovation-strategy doc is fully set aside in favor of "internal pilot only, no unit economics," consistent with the PRFAQ's locked framing.

**Why:**
The PRFAQ stress-test (2026-07-08) already made this call explicit and adversarially tested it — no external customers, no pricing, no unit economics. This step re-confirmed it holds rather than silently assuming.

**Impact:**
No Business Customers section is needed (step-06 skipped). Target Users step focuses entirely on the two in-product roles (HR admins, Employees) as internal users, not paying customers. Success criteria and positioning should not reference ARR, CAC, or pricing — those belong to the shelved commercial-strategy document, not this brief.

**Alternatives considered:**
- Reviving the Option A "Focused Wedge" commercial strategy — rejected; user confirmed this is fully set aside, not a live option being kept warm.

**Documented in:** `dialog/decisions.md` (this entry)

---

## Decision 5: Two open empathy-map assumptions resolved (daily usage; resigned not tolerant)

**Date:** 2026-07-08
**Step:** Project Brief — step 07 Target Users
**Session:** 1

**Context:**
The 2026-07-07 design-thinking session explicitly flagged two open questions it could not resolve without real HR interviews (which were deliberately skipped): (1) how often HR actually opens the spreadsheet, and (2) whether "no workarounds" meant the process was tolerable or that people had given up on it ("tolerable vs. resigned").

**What was decided:**
Both resolved directly by the user, without formal interviews: (1) HR opens the spreadsheet **daily**; (2) HR is **resigned**, not tolerant — they've given up trying to improve the process.

**Why:**
The user has direct, first-hand knowledge of SAILS HR's actual behavior; no interview was needed to close this gap once asked directly.

**Impact:**
"Daily" usage frequency makes dashboard live-ness a hard requirement, not a nice-to-have — freshness indicators and the Needs Attention filter must reflect near-real-time state. "Resigned" (not tolerant) strengthens the core premise: there's real latent appetite for a better tool, not inertia to overcome, which de-risks the root-cause hypothesis somewhat (though it remains formally unvalidated by telemetry until post-launch, per the PRFAQ).

**Alternatives considered:**
- Leaving both as open/tracked assumptions in the brief, unresolved — superseded once the user provided direct answers.

**Documented in:** `dialog/03-users.md`

---

## Decision 6: Success criteria — specific telemetry thresholds locked in advance

**Date:** 2026-07-08
**Step:** Project Brief — step 08 Success Criteria
**Session:** 1

**Context:**
The PRFAQ's Internal FAQ had explicitly flagged that telemetry thresholds for confirming/refuting the root-cause hypothesis needed to be decided in advance, in writing — not read favorably after the fact once real numbers came in. The existing brief only said staleness should drop "to near-zero" and adoption meant HR uses the dashboard "as primary reference," without specific numbers or measurement method.

**What was decided:**
- **Staleness threshold:** Success = self-reported skill data staleness drops below **5%** within 60 days of launch, driven by automated progress tracking replacing manual self-reports.
- **Dashboard adoption:** Success = HR uses TalentPilot-AI as the primary source during talent reviews, with minimal-to-no reliance on the legacy spreadsheet — measured via **dashboard usage analytics + direct stakeholder feedback** (not self-report alone).
- **Timeline:** Launch **13 July 2026**; primary success checkpoint at **60 days post-launch (~11 September 2026)**, evaluating adoption, data freshness, and stakeholder confidence together.

**Why:**
Closes a real, named gap from the PRFAQ verdict — thresholds are now committed in writing before any pilot data exists, preventing the failure mode of reinterpreting ambiguous "near-zero" language favorably after seeing results.

**Impact:**
Any post-launch telemetry/instrumentation work should track specifically: % of self-reported rows stale beyond the threshold window, dashboard login/usage frequency by HR, and a structured stakeholder-feedback checkpoint at day 60 — not just generic "adoption" tracking.

**Alternatives considered:**
- Leaving thresholds vague/qualitative ("near-zero," "primary reference") — rejected per the PRFAQ's explicit instruction to decide numbers in advance.

**Documented in:** `dialog/decisions.md` (this entry)

---

## Decision 7: Competitive landscape — the durable advantage is the evidence pipeline, not first-mover speed

**Date:** 2026-07-08
**Step:** Project Brief — step 09 Competitive Landscape
**Session:** 1

**Context:**
Explored realistic alternatives to building TalentPilot-AI: (1) do nothing / keep the spreadsheet, (2) enforce the spreadsheet harder, (3) buy an existing LMS/talent-intelligence platform. All three were already effectively addressed in prior research/PRFAQ. The open question was the reality-check: if the pilot succeeds, what stops SAILS from just buying Cornerstone/Degreed later instead of continuing to invest here — is there a durable advantage, or just a speed advantage?

**What was decided:**
- **The bet:** Cheaply and quickly prove that automated, evidence-based learning signals meaningfully outperform manual self-reporting for skill readiness, before SAILS commits to a larger investment in either direction.
- **The durable advantage is the evidence pipeline, not first-mover speed.** A commercial LMS manages learning content; TalentPilot-AI's differentiator is the automated collection of verifiable, confidence-labeled learning evidence tailored to SAILS' actual workflow.
- **Three honest post-pilot-success outcomes, not one:** (a) keep evolving TalentPilot-AI standalone, (b) integrate its evidence pipeline into a future LMS, (c) adopt a commercial platform outright if one closes the gap — with the evidence pipeline remaining the valuable, hard-to-replace piece in any of the three.

**Why:**
This directly answers the "post-pilot-success path" question the PRFAQ had explicitly left undecided ("expand to other departments vs. ship fast-follows vs. something else... worth naming before the pilot phase ends"). It also reframes the competitive threat: incumbent LMS/LXP vendors adding an "assignment mode" feature (the risk flagged in the innovation-strategy doc) doesn't fully neutralize TalentPilot-AI, because the evidence pipeline — not the assignment UI — is the actual asset.

**Impact:**
Architecture/build decisions should treat the evidence pipeline (video-progress capture, confidence labeling, freshness metadata) as the component worth investing in most durably, even if other parts of the product (dashboard UI, content discovery) are eventually replaced or absorbed by a bought platform.

**Alternatives considered:**
- Claiming "first-mover advantage" as the moat — rejected as weak/not durable, consistent with the innovation-strategy doc's own risk analysis (feature-parity risk within 12-24 months).

**Documented in:** `dialog/decisions.md` (this entry)

---

## Decision 8: Constraints — hard lines vs. flexibility

**Date:** 2026-07-08
**Step:** Project Brief — step 10 Constraints
**Session:** 1

**Context:**
Mapped the actual design parameters to clarify what's genuinely fixed vs. flexible, and to explicitly document two items the PRFAQ had flagged as open gaps.

**What was decided:**

**Fixed constraints:**
- **Timeline:** 13 July 2026 launch is a hard line, not movable.
- **Budget:** Effectively zero — YouTube chosen specifically for zero cost; AI embedding cost is negligible.
- **Technical stack (shape):** YouTube IFrame API (polling-based), Postgres + pgvector, no new infrastructure required — per completed technical research.
- **Team:** Solo-driven (TalentPilot only) as of now; TalentPilot owns content-approval, bug fixes, and success-metric monitoring post-launch.
- **Brand/design system:** None — `design_system_mode: none` in config; internal tool with no external brand requirement.

**Flexible:**
- Exact tech stack details beyond the researched shape (specific libraries, frameworks)
- Feature scope beyond MVP (fast-follows can be adjusted based on pilot learnings)
- Post-pilot direction (the three documented outcomes: standalone, integrate with LMS, or adopt commercial platform)

**Explicitly open/unresolved (by choice):**
- **Legal/compliance revisit trigger:** No written condition yet for when the current waiver (internal pilot, coaching-only data) becomes invalid and legal review becomes mandatory. User chose to leave this genuinely open rather than define a trigger now.
- **5-week phased plan:** Remains aspirational with no committed team/roles/timeline behind it yet — must be resolved before Pilot & Validation phase begins (per PRFAQ), but not required before 13 July build start.

**Why:**
Clarifies what's actually negotiable vs. non-negotiable, and explicitly documents two items that were open questions in the PRFAQ rather than silently treating them as resolved.

**Impact:**
The 13 July hard-line date is the binding constraint all other decisions must work within. Post-launch, TalentPilot is the sole named owner for operational responsibilities; if that needs to change, it's an active decision to make, not something assumed to happen on its own.

**Alternatives considered:**
- Defining a specific legal-review trigger condition now — rejected; user chose to keep this genuinely open.

**Documented in:** `dialog/decisions.md` (this entry)

---

## Decision 9: Platform strategy — responsive web app, desktop-first, modern browsers

**Date:** 2026-07-08
**Step:** Project Brief — step 10a Platform Strategy
**Session:** 1

**Context:**
This is an internal web tool for SAILS employees (HR admins + employees), not a consumer mobile/native product. Usage context confirms desktop-primary: HR checks the dashboard daily from their desk, employees watch assigned videos at a computer.

**What was decided:**
- **Primary platform:** Responsive web application
- **Device priority:** Desktop-first, scales to tablets/mobile (responsive)
- **Browser support:** All modern browsers (Chrome, Firefox, Edge, Safari — assumes evergreen browsers, no legacy IE11 unless explicitly flagged later)
- **Interaction models:** Mouse and keyboard (primary), touch (secondary for tablet/mobile)
- **Native features needed:** None — standard web APIs (video embed, `sendBeacon` for unload-safety, no offline/PWA/push-notification requirements)

**Why:**
Fits the actual usage pattern (HR/employees at desks, not on the go), fastest time to market (no app store approval, no separate mobile codebase), and aligns with zero-budget constraint (no native app infrastructure cost).

**Impact:**
No need to design native mobile UX flows or offline-first architecture. Video resume/continue-watching works via standard YouTube IFrame API + `sendBeacon` on tab close; no mobile-app-specific persistence layer needed.

**Alternatives considered:**
- Native mobile app, PWA, desktop-only — all rejected as unnecessary for the actual use case and timeline.

**Documented in:** `dialog/decisions.md` (this entry)

---

## Decision 10: Tone of voice — clear, calm, honest about uncertainty

**Date:** 2026-07-08
**Step:** Project Brief — step 11 Tone of Voice
**Session:** 1

**Context:**
Tone of voice needed to reflect the product's core trust mechanic — the PRFAQ explicitly warned that mislabeled/ambiguous status is worse than the spreadsheet it replaces, so UI microcopy carries real risk if it's unclear.

**What was decided:**

**Tone Attributes:**
1. **Clear & unambiguous** — never leave room for HR to misread "self-reported" as "verified"; no cute abbreviations or icon-only status without text.
2. **Calm & matter-of-fact** — reads like a confident colleague stating a fact, not a system seeking delight.
3. **Honest about uncertainty** — plainly states missing/stale data ("No signal yet," "Last updated 12 days ago") rather than hiding gaps behind a neutral blank.
4. **Quietly encouraging (employee-facing only)** — warmth is acceptable for resume prompts/progress nudges, closer to a streaming app, but never at the cost of clarity.

**Example microcopy:**
- Dashboard cell (video, current): "Verified · 92% watched, 2 hours ago" (not "✓ Complete")
- Dashboard cell (self-reported, stale): "Self-reported · Not updated in 14 days" (not "In Progress")
- Needs-attention flag: "Needs a second look" (not "Warning")
- Employee resume prompt: "Pick up where you left off — 8 min remaining" (not "Continue")
- No signal yet: "No activity recorded yet" (not "N/A")

**Why:**
Directly operationalizes the "mixed trust, clearly labeled" positioning (Decision in Positioning step) at the microcopy level — the labeling UI's clarity was flagged by the PRFAQ as the single point of failure for the entire trust story, so tone of voice guidelines exist specifically to prevent that failure mode.

**Impact:**
All future UI copy (dashboard cells, status labels, employee-facing prompts) should be checked against these attributes before ship — especially the "clear & unambiguous" rule, given the documented risk of HR misreading status.

**Alternatives considered:**
- More playful/consumer-app tone throughout — rejected for HR-facing surfaces since this is a system of record, not a consumer product; acceptable only for employee-facing resume/progress nudges.

**Documented in:** `dialog/decisions.md` (this entry)

---

_Continue appending decisions as they're made throughout the Product Brief process._
