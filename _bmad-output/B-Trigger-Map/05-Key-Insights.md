# Key Insights & Strategic Implications

> How the Trigger Map informs design and development decisions

**Document:** Trigger Map - Key Insights
**Created:** 2026-07-08
**Status:** COMPLETE

---

## The Flywheel: Rita's Trust Drives Everything

**THE ENGINE (Priority #1):**
- Proving the evidence-pipeline hypothesis (staleness below 5% within 60 days) is THE PRIMARY GOAL
- Timeline: 60 days from the 13 July 2026 launch (checkpoint ~11 September 2026)
- This is a single technical bet — auto-captured video watch-% as trust signal — that either holds up under real usage or doesn't
- It creates the flywheel that drives ALL other objectives — nothing else matters strategically if this doesn't hold

**Earning HR's Trust (Priority #2):**
- Driven BY the evidence pipeline succeeding in practice, not by feature count
- Rita adopting TalentPilot-AI as primary source of truth, on-time launch, legible provenance labeling
- Timeline: Present at launch, confirmed by the 60-day checkpoint
- Focus: Converting a proven technical signal into Rita's actual daily behavior change

**Eliminating the Self-Report Chore (Priority #3):**
- Real-world benefit FOR Casey, not a company metric dressed up as one
- Zero manual logging for video content, fast content discovery
- Timeline: Present at launch
- **Key benefit:** Casey gets a consumer-app-quality resume experience for free, as a side effect of the same mechanic that solves Rita's trust problem

---

## Primary Development Focus

1. **Make Rita's Trust the Design North Star** — every screen Rita touches should be evaluated against "does this help her act with confidence, faster, without double-checking?"
2. **Ship Tracking and Resume as One Mechanic, Not Two** — the Product Brief is explicit that this is a single data pipe with two payoffs; building them separately risks drift and duplicated logic
3. **Make Provenance Impossible to Miss** — every status must be labeled verified / self-reported / needs attention in text, never color-only, because a mislabeled trust signal is worse than the spreadsheet it replaces
4. **Build "Needs Attention" as a First-Class View, Not an Afterthought** — this is the specific mechanic that turns Rita's habitual full-grid scanning into an efficient, targeted workflow
5. **Keep Casey's Experience Invisible and Frictionless** — the less Casey has to think about being tracked, the more honest and continuous the underlying signal stays

---

## Critical Success Factors

- **Freshness stated in plain language**: "Not updated in 14 days" instead of vague terms like "In Progress" — the tone-of-voice guidance is explicit that ambiguous status words are a named failure mode to avoid
- **Provenance always paired with text, never color-only**: prevents Rita from misreading a self-reported cell as verified, which the Product Brief calls out as worse than the spreadsheet it replaces
- **One-click drill-down on every readiness call**: Rita needs to defend a staffing decision if questioned — "why is this employee ready" must be answerable in one click, not buried
- **Zero manual steps for Casey on video content**: the entire trust pipeline depends on Casey's participation staying passive; any added friction (extra confirmation, manual logging) risks breaking the signal at its source
- **Resume accuracy on the very first use**: Casey's trust in the whole system hinges on the first "Continue Watching" click landing exactly where they left off — a wrong resume point breaks confidence immediately, with little chance to recover it

---

## Design Implications

### Dashboard Screen (Rita-facing) Must:
- Pair every status with an explicit provenance label (Verified / Self-reported / Needs Attention) in text, not just color
- Surface a "Needs Attention" filter as a primary, prominent action — not a secondary menu item
- State staleness with a timestamp or day-count on every non-fresh cell, never hidden behind a neutral-looking blank

### Drill-Down / Detail View Must:
- Show the underlying signal behind any status ("92% watched, 2 hours ago") in one click from the dashboard
- Read as factual and confident, consistent with the "system of record" tone — no playful or ambiguous language on this surface
- Clearly distinguish a genuine gap ("No activity recorded yet") from an unverifiable one, rather than guessing

### HR Assignment Flow Must:
- Feel like the same continuous system as the dashboard, not a disconnected second tool
- Let Rita assign a skill and immediately trigger AI content discovery for the employee, collapsing "assign" and "here's what to watch" into one action
- Require no more manual effort from Rita than the spreadsheet did — the value has to come from what happens automatically afterward, not from extra upfront data entry

### Employee Content & Resume Experience Must:
- Frame the resume prompt in personal-benefit language ("Pick up where you left off — 8 min remaining"), never surveillance language
- Surface AI-matched content inline the moment a skill is assigned, with no separate search step
- Capture watch-position continuously, including on abrupt tab close (`sendBeacon`), so no session's progress is ever silently lost

### Cross-Cutting Tone & Trust Must:
- Never use ambiguous terms ("In Progress," "Pending") that could describe both verified and self-reported data
- Reserve warmth and encouragement for employee-facing surfaces only — HR-facing status displays stay factual and calm, per the locked Tone of Voice guidance
- Treat a blank or "Unknown" cell as strictly better than a guessed one, at every layer of the product

---

## Emotional Transformation Goals

- **Rita:** "I open this dashboard and act on what it tells me — I don't need to double-check it against my own memory anymore."
- **Rita:** "I spend my attention on the handful of cases that genuinely need it, not on scanning every row out of habit."
- **Casey:** "I watch what I'm assigned and that's the whole interaction — nobody's asking me to also go log it somewhere."
- **Casey:** "I come back to a video and it just picks up exactly where I stopped — like it should."
- **Rita:** "When someone questions a staffing call I made, I can show them exactly why, in one click."

---

## Design Focus Statement

**TalentPilot-AI transforms Rita from someone who compensates daily for data she doesn't trust into someone who acts confidently on data she doesn't have to verify — as a byproduct of Casey's engagement simply working the way a modern app should, not because either of them was asked to change their behavior.**

**Primary Design Target:** Rita the Referee (HR/L&D Admin)

**Must Address (Critical for the Pilot's Success Metric):**
1. Fear of making a wrong staffing call on stale data → explicit, always-visible freshness timestamps
2. Fear of a dashboard that looks more trustworthy than it is → mixed-trust labeling, never a uniform "looks fine" grid
3. Fear that the chore just relocates instead of disappearing → explicit "Self-reported"/"No activity recorded" labels on non-video gaps, not a silent blend
4. Want to stop chasing people entirely → fully automated, zero-touch video signal for Casey
5. Want a fast, confident readiness call under real pressure → "Needs Attention" filter + one-click drill-down

**Should Address (Supporting the Overall Trust Loop):**
1. Casey needs a resume experience that's accurate on the first try, or their trust in the mechanism breaks immediately
2. Casey needs the tracking to feel like personal convenience, not surveillance, or engagement (and thus signal quality) suffers
3. Casey needs relevant content surfaced instantly on assignment, or the "zero friction" promise breaks at the very first step
4. The still-open non-video trust gap (sub-skills, status fields) should be visibly and honestly flagged, not silently ignored, even though it's out of MVP scope
5. Integration between assignment flow and dashboard should feel seamless — Rita should never feel like she's using two separate tools

---

## Development Phases

### First Deliverable: TalentPilot-AI MVP (13 July 2026 Launch)

Focus on proving the evidence pipeline and making Rita's trust visible from day one:
- **HR Assignment Flow** — Rita's daily entry point, unchanged in effort from the spreadsheet
- **AI Content Discovery** — collapses assignment and content-finding into one action for Casey
- **Auto-Captured Video Progress Tracking** — the core engine; zero self-report for video content
- **Continue-Watching / Resume Card** — Casey's direct payoff, generated by the same signal as Rita's dashboard
- **Provenance-Labeled Dashboard** — verified / self-reported / needs-attention, always paired with text
- **"Needs Attention" Filter + Drill-Down** — Rita's actual daily readiness-judgment workflow

### Future Phases: Additional Content

- **Phase 2** (post-60-day checkpoint, if warranted by real usage data): Proxy-signal tracking for docs/websites, extending the trust model beyond video
- **Phase 3**: HR "Assessed Live" audit-trail flag for manually-judged sub-skills
- **Phase 4**: "Your Week in Learning" employee recap, reusing existing watch-position data for a motivational, non-critical-path feature
- **Phase 5**: Resolution of the still-open legal/compliance revisit trigger and named post-pilot ownership, ahead of any expansion beyond the current internal-pilot scope

---

## Related Documents

- **[00-trigger-map.md](00-trigger-map.md)** - Visual overview and navigation
- **[01-Business-Goals.md](01-Business-Goals.md)** - Objectives and metrics
- **[02-Rita-the-Referee.md](02-Rita-the-Referee.md)** - Primary persona
- **[03-Casey-the-Continuer.md](03-Casey-the-Continuer.md)** - Secondary persona
- **[06-Feature-Impact.md](06-Feature-Impact.md)** - Prioritized features with impact scores

---

_Back to [Trigger Map](00-trigger-map.md)_
