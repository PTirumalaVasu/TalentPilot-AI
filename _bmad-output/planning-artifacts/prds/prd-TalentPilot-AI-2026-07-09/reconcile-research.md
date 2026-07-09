# Reconciliation: PRD/Addendum vs. Source Research

**Scope:** Completeness check only — no rewrite. Compares `prd.md` + `addendum.md` (2026-07-09) against the five research reports in `_bmad-output/planning-artifacts/research/`. For each source, lists what's present in the source but not reflected anywhere in the PRD or addendum, focused on: product-scope-relevant constraints missing from Constraints/Guardrails or Cross-Cutting NFRs; explicit risks not captured as an Open Question or Constraint; and positioning/competitive facts missing from "Why Now." Pure implementation/library detail correctly scoped to the addendum only is NOT flagged unless missing from the addendum too.

---

## 1. `domain-corporate-skill-tracking-ai-video-learning-platforms-research-2026-07-07.md`

**Covered adequately:** LMS/LXP category-blurring-since-2022 framing (→ PRD "Why Now"), auto-captured video-progress-as-proven-tech framing, "narrower and more honest" positioning angle.

**Gaps:**

- **iMocha is missing entirely from the addendum's competitor list.** The domain report singles it out with a full business-model snapshot as the **closest named overlap** on the "readiness dashboard" concept ("Closest overlap on 'readiness dashboard' concept, but built on *assessment* data, not passive video-consumption signals"). The addendum's "Market Landscape Detail" competitor tiers (carried over from the market report) list Eightfold/Gloat/Reejig/365Talents/Fuel50/Skillpanel, Cornerstone/Degreed/LinkedIn Learning/Docebo/Litmos/D2L/Pluralsight, and Valamis/Paradiso/TechClass/Disco — but never iMocha. This drops the single most directly comparable named competitor from the record.
- **"Why Now" stats not carried forward.** The domain report explicitly recommends using "87% of CHROs forecast greater AI adoption within HR processes in 2026" and the "Training Is Dead. Long Live Real-Time Upskilling." industry-consensus framing as the pitch's timing hook. Neither appears in the PRD's "Why Now" section or the addendum's "Market Landscape Detail" / "Innovation Strategy Notes." The PRD's Why Now relies solely on the category-consolidation argument.
- **Deloitte data-trust stat not carried forward.** "95% of L&D organizations don't excel at using data to align learning with business objectives, and 69% lack the skills to link learning outcomes to business results" — cited by the domain report as validating the "Trust/Freshness Dashboard" concept "beyond this project's internal reasoning." Not in the addendum's "Key stats" list (which has the 88%/20%/87%/35%/70–80% stats from the market report, but not this one).

---

## 2. `market-ai-talent-pool-management-platform-research-2026-07-07.md`

**Covered adequately:** Market sizing, buying-journey mechanics (noted as not directly relevant to an internal pilot), competitor tiers list, core pain-point stats, HRIS-integration gap (→ Open Question 5), the "assignment-first / auto-capture / consumer UX" undefended-positioning-gap claim (→ Why Now).

**Gaps:**

- **"Big-platform embedding" competitive threat not reflected as a risk.** Section 4 ("Competitive Threats") explicitly flags: *"Gloat's integration into Microsoft 365 Copilot/Teams signals large platforms embedding into daily-use tools, which could out-distribute a standalone tool on convenience grounds."* The addendum's competitor-tiers list mentions the Microsoft 365 integration only as a parenthetical fact about Gloat ("now embedded in Microsoft 365 Copilot/Teams") — the *threat framing* (a named competitive risk to TalentPilot-AI specifically) is dropped. Not reflected in PRD's Open Questions or Constraints either.
- **"Why Now" market-timing stats not carried forward.** Section 5 ("Market Opportunity Assessment") gives the specific timing argument: *"87% of companies report current or expected skill gaps, 6 in 10 employees will need upskilling/reskilling by 2027 (WEF)... the LMS/LXP category is still consolidating rather than settled."* Only the consolidation clause made it into the PRD's Why Now; the 87%/WEF-6-in-10 stats (the report's own explicit "why now" hook, reiterated in the Executive Summary and Recommendations sections) are absent from both prd.md and addendum.md.
- **Category-ambiguity risk not named.** Section 7 ("Market Risk Analysis") flags that TalentPilot-AI's niche "isn't yet analyst-defined," meaning positioning/messaging carries extra friction. This is implicit in the PRD's narrow-wedge framing but never stated as a risk anywhere (no Open Question or Constraint captures it). Minor — arguably a GTM/messaging risk more than a product-scope one, but the task brief asked to check explicit flagged risks.

---

## 3. `technical-overall-stack-architecture-for-talentpilot-ai-research-2026-07-08.md`

**Covered adequately:** Full stack (Python/FastAPI, React/Vite, Postgres+pgvector, JWT-in-cookie, shadcn/ui, SQLAlchemy-vs-SQLModel, REST design) — all in addendum's "Technical Stack (locked)" and "Rejected Technical Alternatives." The "coaching-only" enforcement-at-service/repository-layer requirement is correctly promoted into the PRD's Constraints and Guardrails ("must be enforced structurally at the data-access/service layer — not merely a UI-copy or documentation commitment"), matching the source's flag of this as "a compliance-shaped requirement hiding inside a technical decision."

**Gap (the one material finding from this source):**

- **Deployment/hosting is explicitly undecided, and this is not surfaced anywhere as a Constraint or Open Question.** The source states plainly: *"Deployment/hosting: explicitly out of scope / deferred in the technical research"* and *"Cloud Infrastructure and Deployment: Explicitly out of scope for now... production hosting choice... is deferred to a later pass, not decided here."* The addendum repeats this once ("Deployment/hosting: explicitly out of scope / deferred in the technical research") but never as a flagged risk. Given the PRD's own Constraints and Guardrails locks a **launch date of 2026-07-13** — four days from today (2026-07-09) — and states "the dashboard launches clean on 2026-07-13," an undecided hosting/deployment target this close to launch is a product-scope-relevant gap that arguably belongs as an Open Question (parallel to Open Question 3, "no named post-pilot owner... exists"), not left as a bare technical-research note.

---

## 4. `technical-rag-and-vector-database-approach-for-matching-hr-assigned-skills-to-tutorials-research-2026-07-08.md`

**Covered adequately:** The core "AI slop"/content-quality risk is genuinely captured — PRD's Non-Goals ("Not a content-approval workflow... an accepted risk, not an oversight"), Constraints and Guardrails ("Content quality: No human-approval gate exists... Accepted risk, revisit if pilot feedback surfaces real quality problems"), and MVP Out-of-Scope all reflect the decision to *not* adopt the source's recommended human-approval checkpoint — a real deviation from the source's advice, but one the PRD explicitly owns as an accepted risk rather than silently dropping. The YouTube quota constraint is captured (Constraints and Guardrails, FR-3/FR-4 NFR). The filter-then-rank / metadata-first pattern is correctly addendum-only detail.

**Gaps:**

- **No mitigation-lite alternative captured.** Since the PRD explicitly declines the source's recommended human-approval gate, the source's own fallback/cheaper mitigation — a hand-built ground-truth set evaluated via Precision@k/Recall@k *before wider rollout* — is not mentioned anywhere as a considered (even if also rejected) alternative. The Constraints section's "revisit if pilot feedback surfaces real quality problems" is reactive-only; the source's proposed evaluation step would have been a proactive, cheap check. Not necessarily a missing requirement, but the PRD's reasoning trail for accepting this risk doesn't show this cheaper alternative was considered and rejected — it just isn't there.
- **Quota specifics slightly softened.** The source is specific: *"~100 calls/day since a June 2026 policy change... no paid tier to buy more (only a manual quota-increase application to Google)."* The PRD's Constraint says only "a hard daily quota that cannot support on-demand querying" and its `[NOTE FOR PM]` implies the ingestion cadence itself is "the first constraint to revisit" if broader coverage is needed later — without noting that quota headroom specifically **cannot be purchased**, only informally requested from Google with no guarantee. This is a minor precision gap, not a missing constraint category.

---

## 5. `technical-third-party-video-embeds-youtubevimeo-with-custom-watch-progress-tracking-research-2026-07-07.md`

**Covered adequately:** Provider choice (YouTube) and rationale, mandatory-branding ToS constraint, Adapter pattern, conditional-write persistence — all correctly and fully captured in the addendum's "Technical Stack (locked)" and FR-7 / Cross-Cutting NFRs (data integrity). This source's findings are the most completely reflected of the five.

**No material gaps found.** One very minor note: the source flags that Vimeo's stronger privacy tiers (fully-private, non-public hosting) were a factor in the provider trade-off ("if training videos must stay fully private... Vimeo's free tier won't satisfy that") — implying that on YouTube, video content is at minimum Unlisted/Public-adjacent. Neither PRD nor addendum states what privacy level the actual assigned training videos will be hosted at (Public vs. Unlisted). Low severity — arguably pure implementation detail correctly left out, flagged here only for completeness.

---

## Summary — Top Gaps by Severity

1. **Deployment/hosting undecided, launch date fixed at 2026-07-13, no Open Question or Constraint covers this** (source: technical-overall-stack). Highest severity given proximity to launch.
2. **"Why Now" omits the market/domain reports' own recommended timing hooks** — 87% CHROs AI-adoption stat, WEF "6 in 10 by 2027" stat, "Training Is Dead" framing — present in both domain and market reports, absent from PRD and addendum.
3. **iMocha dropped from the competitor list** despite being named the closest existing competitor on the "readiness dashboard" concept (domain report).
4. **Gloat/Microsoft 365 Copilot-Teams "big-platform embedding" competitive threat** stated explicitly in the market report's Risk Assessment, reduced in the addendum to a parenthetical fact with no risk framing carried anywhere.
5. Minor/lower-severity: Deloitte 95%/69% data-trust stat (domain report) not in addendum's stats list; YouTube quota's "no paid tier, manual application only" nuance softened in the PRD's Constraint; RAG report's Precision@k/Recall@k evaluation fallback not mentioned as a considered alternative to the declined human-approval gate.
