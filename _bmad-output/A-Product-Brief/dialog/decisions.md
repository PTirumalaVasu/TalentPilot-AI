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

_Continue appending decisions as they're made throughout the Product Brief process._
