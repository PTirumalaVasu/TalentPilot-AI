---
title: "PRFAQ: TalentPilot-AI"
status: "complete"
created: "2026-07-08"
updated: "2026-07-08"
stage: 5
inputs:
  - "_bmad-output/planning-artifacts/briefs/brief-TalentPilot-AI-2026-07-08/brief.md"
  - "_bmad-output/brainstorming/brainstorm-talent-pool-management-capabilities-2026-07-07/brainstorm-intent.md"
  - "_bmad-output/design-thinking-2026-07-07.md"
  - "_bmad-output/innovation-strategy-2026-07-07.md"
  - "_bmad-output/planning-artifacts/research/domain-corporate-skill-tracking-ai-video-learning-platforms-research-2026-07-07.md"
  - "_bmad-output/planning-artifacts/research/market-ai-talent-pool-management-platform-research-2026-07-07.md"
  - "_bmad-output/planning-artifacts/research/technical-rag-and-vector-database-approach-for-matching-hr-assigned-skills-to-tutorials-research-2026-07-08.md"
  - "_bmad-output/planning-artifacts/research/technical-third-party-video-embeds-youtubevimeo-with-custom-watch-progress-tracking-research-2026-07-07.md"
  - "_bmad-output/project-context.md"
  - "web research: HR/LMS build-vs-buy landscape, 2026-07-08"
---

# TalentPilot Automatically Tracks Employee Progress on Video Training — No More Status-Chasing for It

## HR's dashboard now blends automatically-verified video progress with employee-reported updates for everything else — replacing a spreadsheet built entirely on the honor system with one HR can start to trust.

**13 July 2026** — TalentPilot AI launches today, replacing the shared spreadsheet HR uses to track employee skill development. It gives HR a live view of who's on track — and, just as important, tells HR which parts of that view it can actually vouch for. For employees, assigned video training now tracks itself: watch the video, and progress shows up on HR's dashboard without typing a status update.

Today, HR tracks employee skill development in a spreadsheet that only works if everyone keeps it updated. Every week, HR chases employees and managers for status: *Did you finish that course? What percentage are you through? Is this row accurate, or just stale?* Employees, in turn, interrupt their actual work to fill in a cell that gives them nothing back — a chore performed for someone else's visibility. The result: nearly nine in ten HR spreadsheets contain errors, and only one in five HR leaders trust the skill data in front of them. When someone asks "is this person ready?", HR is often answering off a grid that hasn't been touched in weeks, with no way to tell if the silence means *done* or *forgotten*.

With TalentPilot AI, that changes for video-based training. Employees watch their assigned videos — no status field, no checkbox, no monthly nudge to log progress. The moment they watch, HR's dashboard reflects it, automatically, tagged as verified. Everything else on the roadmap — documents, external resources — still relies on the employee to report progress, exactly as it does today, but now that self-reported status is visibly labeled as such instead of blending invisibly into the same grid as real activity. HR stops guessing which rows are current and which are guesses; the dashboard tells them outright, and flags the ones that need a second look.

> "We didn't build this to catch people falling behind. We built it so HR can finally stop guessing and start trusting the data enough to make a call — and so employees can stop performing progress updates for a system that never gave anything back."
> — Sesha, HR

### How It Works

**For HR:** Assigning training takes one step — pick an employee, pick the skill they need, done. TalentPilot AI takes it from there: employees see the assignment show up in their queue, matched with a handful of relevant videos and resources to get them started. HR doesn't chase, doesn't remind, doesn't check in — they open the dashboard whenever they need an answer. Each row shows the skill, the employee's progress, and a freshness tag: verified (auto-captured from actual video activity), self-reported (employee-entered, for non-video content), or needs attention (stale, inconsistent, or unclear). A "Needs Attention" filter surfaces exactly the rows worth a second look, with a drill-down explaining why — so HR spends time on the handful of cases that actually need it, not re-reading the whole grid.

**For Employees:** Assigned training shows up in one place. Pick a video, start watching — that's the entire interaction. There's nothing to check off, no field to update, no reminder email asking for a status. Close the tab mid-video and come back tomorrow: it picks up exactly where you left off, the same way a streaming show does. Progress on the dashboard updates itself in the background. For assigned documents or external resources, the employee still marks their own progress — same as today — but it's now clearly labeled as self-reported rather than mixed in as if it were verified.

> "I stopped getting the 'please update your training status' email. I didn't do anything — I just watched the video like I was supposed to, and apparently that was the update."
> — Employee, early pilot user

### Getting Started

TalentPilot AI launches internally on 13 July 2026. HR admins get access automatically and can start assigning skills immediately. Employees see their first assignment appear in their queue as soon as HR assigns one — no separate signup, no onboarding step, just their existing company login.

---

## Customer FAQ

### Q: Watching a video isn't the same as learning. What stops someone from just leaving it playing in the background without paying attention?

A: Nothing currently stops that. Watch-% measures exposure, not comprehension — the same "vanity metric" critique leveled at every completion-based LMS today, not unique to TalentPilot. What's different is the baseline it replaces: today's process makes an even weaker assumption — a self-reported checkbox anyone can click without watching a second of anything. Watch-% is a strictly stronger signal than a checkbox, even though it's imperfect. This is an accepted trade-off for MVP; comprehension verification (quizzes, checks) is explicitly out of scope for now, and will be watched via post-launch usage telemetry rather than solved upfront.

### Q: Who can see my watch data — is this being used to monitor or evaluate me personally?

A: HR sees it, the same as they'd see (or fail to see) your self-reported status today — except now it's real activity instead of a claim. Auto-captured progress data is explicitly coaching-only: it is never used in performance evaluations. That boundary has to hold in how the system is actually built (data access and reporting scope), not just in what this document says.

### Q: If most of the dashboard is still self-reported, how is this actually more trustworthy than the spreadsheet I have today?

A: It's not universally more trustworthy — it's selectively more trustworthy, and now labeled as such. Today's spreadsheet mixes everything into one indistinguishable grid; a stale self-reported cell looks identical to a fresh one. TalentPilot tells you which cells are verified, which are self-reported, and which need a second look. The claim isn't "trust the whole dataset" — it's "now you can tell which parts to trust."

### Q: Do I need to do anything to get started — does my old spreadsheet history carry over?

A: No migration. The dashboard starts clean on 13 July 2026; historical spreadsheet data does not import.

### Q: What happens to my progress if I switch devices, lose connection, or close the tab mid-video?

A: Progress is saved server-side via conditional writes (only a newer timestamp overwrites an older one) and flushed via a beacon when you close the tab, so you lose at most a few seconds. Switching devices resumes correctly because progress lives on the server, not the device.

### Q: What if the AI recommends a video that's wrong, outdated, or irrelevant to the skill I actually need?

A: Matching is semantic/approximate by design, not exact — loose matches are accepted so relevant-but-differently-worded content still surfaces. The real risk is content quality: YouTube has no built-in quality assurance, and "AI slop" is a documented problem. A human-approval checkpoint exists before content reaches employees. Content curation is a manual admin step in MVP, not fully automated — a real, ongoing operational cost, not a one-time build cost.

### Q: I already know this skill — do I have to sit through the video anyway to show as "ready" on the dashboard?

A: Currently, yes — there's no test-out or skip-with-proof-of-competency path. You watch anyway, or tell HR directly and they manually override the record, since HR retains manual readiness judgment regardless of what the automated signal shows.

### Q: Why not just get people to fill out the spreadsheet properly instead of building a new tool?

A: Because it isn't a communication problem, it's a structural one — self-reporting has zero personal benefit to the person doing it, so it's always the first thing deprioritized under load, no matter how clearly you ask. For video, TalentPilot doesn't ask harder; it doesn't ask at all. No amount of policy enforcement fixes an incentive-free chore.

### Q: What happens to my training history if this tool gets discontinued or replaced next year?

A: Honestly: this launches as an internal pilot, not a system with a guaranteed multi-year commitment. If the pilot's own success criteria (staleness %, dashboard adoption) don't hold up, it could be dropped or replaced. No promise of permanence — over-promising stability for a pilot isn't credible.

---

## Internal FAQ

### Q: The whole concept rests on an unvalidated hypothesis. What if it's wrong?

A: The team already made this trade-off on the record (2026-07-07): skip HR interviews, bet on "self-reporting, not spreadsheet format, is the real pain," validate via live telemetry instead. Legitimate strategy for a fast pilot — but it means this entire document rests on an assumption never tested in a single real conversation. If it's wrong — if the actual pain is HR not knowing *what* to assign, not tracking difficulty — this build solves the wrong problem elegantly. The team won't know if the bet was right until after the 5 weeks are spent, not before. This is the single biggest risk in the whole concept, and it's a deliberate, already-made choice, not something to re-litigate.

### Q: What's the hardest technical problem here — do we actually know how to build it?

A: No individual piece is novel. Video watch-% polling, resume via conditional writes, and semantic content matching via pgvector are each proven, off-the-shelf-category tech, per existing technical research. The real risk is integration: gluing three separately-proven pieces into one coherent pipeline in roughly five weeks. What it would take to know for sure: a working spike of polling → persist → dashboard in week one, before committing the rest of the timeline to it.

### Q: Who maintains this after the pilot?

A: Not currently named — a real gap, not yet resolved. Acceptable for now: owner assignment is deferred until before the pilot phase begins, not required before the 13 July build start. This has to actually happen before Phase 3 (Pilot & Validation), or the maintenance-decay failure mode (content curation goes stale, nobody watches the success metrics) applies regardless of build quality.

### Q: What team, and is the 5-week timeline realistic?

A: Still aspirational — no committed team size, roles, or timeline lock exists yet. Acceptable for now, on the same deadline: finalized before the pilot phase begins, not before 13 July. Until then, the 5-week phased plan in the brief is a target, not a commitment.

### Q: What's the legal/compliance exposure of tracking employee video-watch behavior?

A: No formal legal/compliance review has happened. The team made an explicit, informed decision that this isn't needed for the current scope (internal pilot, coaching-only data use, no external customers) — recorded as a consciously accepted risk, not an oversight. If the tool's scope or audience changes later — more departments, a shift in how the data is used — this decision should be revisited, not assumed to still hold.

### Q: What's the worst case if we ship and it doesn't work?

A: Not "nobody uses it" — that's cheap and recoverable, just a failed pilot. Worse: HR partially trusts a mixed-signal dashboard, misreads a stale self-reported cell as verified because the labeling isn't clear enough in practice, and makes a real staffing call on bad data — the exact failure the tool exists to prevent, now laundered through something that *looks* more trustworthy than the spreadsheet it replaced. That is worse than the status quo. The freshness/labeling UI needs a real usability check before pilot, not just build-and-ship.

### Q: Why build this instead of buying Cornerstone, Degreed, or LinkedIn Learning?

A: No reviewed vendor does granular auto-polled watch-% as its core trust signal — Degreed's "skill signals" are still self-assessment/peer-endorsed, still self-reported. Heavyweight platforms also commonly cost 20–50% of license again in implementation — disproportionate for testing one narrow hypothesis. Building lean is a smaller, faster, honestly-scoped bet before committing bigger spend in either direction.

### Q: If the pilot succeeds, what does that actually unlock?

A: Undecided. Reasonable for a five-week pilot, but "success" currently has no defined next action attached to it — expand to other departments, ship the fast-follows (nudges, transcript search), or something else. Worth naming before the pilot phase ends, not scrambling to answer it afterward.

### Q: Will HR actually drop the spreadsheet, or run both in parallel indefinitely?

A: Real risk, already measured by the existing success criteria ("no shadow spreadsheet" within 60 days), not ignored. A parallel spreadsheet in month one is expected; a permanent one is a failed pilot regardless of build quality.

---

## The Verdict

**Concept strength: Forged, with two structural cracks that need active tending — ready for a PRD, not ready to skip straight to build without carrying these forward as first-class requirements.**

The thinking is sharpest exactly where it matters most: the reframe from "replace the spreadsheet" to "remove the incentive-free chore of self-reporting" survived every adversarial question without needing to be walked back, and the "mixed trust, clearly labeled" positioning — a narrower, more honest claim than "the dashboard is trustworthy" — held up under direct attack in both FAQs. The soft spots are organizational, not conceptual: nobody owns this after week five, and the root-cause bet the whole thing rests on has never been tested against a real conversation.

### Forged in Steel

- **The root-cause reframe.** "Self-reporting is the disease, Excel is just where it lives" is a genuinely sharp insight, confirmed by you and never contradicted anywhere in the FAQs. It gives the whole document a consistent spine.
- **"Mixed trust, clearly labeled."** Dropping the tempting-but-dishonest "fully trustworthy dashboard" claim in favor of "you can now tell which cells to trust" is the single best decision made in this session. It's narrower, true, and it's the actual differentiator — not a feature list.
- **The privacy boundary.** "Coaching-only, never performance evaluation" isn't a marketing line — it's now a recorded implementation constraint. Resolving this before build, rather than discovering it after launch, is exactly what this process is for.
- **Build-vs-buy reasoning.** Backed by real evidence (no vendor auto-polls watch-% as a trust signal; heavyweight implementation costs 20–50% of license again), not a vague "we can do it better."
- **Technical feasibility.** Every component is proven, off-the-shelf-category tech per your own prior research. The risk is integration timing, not invention — a much more tractable problem.

### Needs More Heat

- **The freshness/labeling UI itself.** The whole trust story depends on "verified" vs. "self-reported" being visually unmistakable — but that UI doesn't exist yet, even as a mockup, and hasn't been tested on a real HR person. This needs actual design work and a usability check before it's ready to hand to a PRD as a solved problem.
- **The post-pilot success path.** "Expand to more departments" vs. "ship the fast-follows" vs. something else is genuinely undecided. Fine to leave open now, but it should be named before the pilot phase ends — not discovered in a scramble.
- **Operationalizing the content-approval step.** You've accepted a human-approval gate on AI-matched video content as an ongoing cost — but with no named owner, there's currently nobody positioned to actually do that work.

### Cracks in the Foundation

- **The unvalidated root-cause hypothesis.** This is the one crack underneath everything else. You made a deliberate, informed choice to skip HR interviews and bet the entire concept on "self-reporting is the real pain" — validated only after the fact, via telemetry. That's a legitimate strategy, but it means every other claim in this document inherits that risk. *What would close this crack:* define, in writing, the specific telemetry thresholds (e.g., staleness % drop, dashboard adoption rate) that will count as confirming or refuting the hypothesis — and decide that now, not after seeing favorable-looking numbers.
- **No owner, no committed team or timeline.** Both explicitly deferred to "before the pilot phase," which is a reasonable call — but it's a real organizational gap, not a technical one, and the pilot's own success depends on someone actually closing it by that deadline. *What would close this crack:* treat "name an owner" and "lock the team" as an actual gate before Phase 3 starts, tracked as visibly as any technical milestone — not left to happen informally.
- **The legal/compliance waiver.** A consciously accepted risk, which is your call to make — but it currently has no tripwire. *What would close this crack:* write down the specific condition that would make this revisit mandatory (e.g., "if this expands beyond this pilot team, or if progress data is ever used in a review, legal review becomes required before that happens") so the decision doesn't silently persist past the point where it was valid.

None of these are reasons to stop. They're the three things a PRD and architecture pass need to treat as real requirements — a tested-not-assumed UI, a named accountable owner, and an explicit revisit condition on the legal decision — rather than narrative footnotes that quietly get dropped.

<!-- coaching-notes-stage-2 -->
## Coaching Notes — Stage 2: The Press Release

**Rejected headline framings:**
- "Nobody Has to Report Their Own Progress Anymore — TalentPilot Tracks It For Them" — dropped as dishonest overclaim; non-video content still requires employee self-report.
- Dual-audience-equal headline (trying to serve HR and employee framing at once) — user explicitly redirected: since this is an internal HR tool, headline should lead HR, employee benefit demoted to subheadline/body.
- "TalentPilot Automatically Tracks Employee Training Progress — No More Chasing Status Updates" (unscoped) — dropped after user corrected the underlying assumption: employees CAN still manually update progress for non-video content, so "no more chasing" cannot be claimed unscoped. Final headline scopes the claim explicitly to video training.

**Differentiator explored but narrowed:** Originally leaned toward "a dashboard HR can finally trust" as an unqualified claim. Corrected to "mixed trust, clearly labeled" — the dashboard blends auto-verified (video) and self-reported (non-video) data in the same grid; the actual innovation is the labeling/freshness distinction, not full-dashboard trust. This is a narrower, more defensible, more honest differentiator and should carry through Customer/Internal FAQ and the Verdict.

**Confirmed launch specifics:** Launch date 13 July 2026; leader quote attributed to Sesha, HR.

**Still open, not yet resolved (raised, not answered by user — not blockers, but worth revisiting before final Verdict):**
- Whether historical spreadsheet data migrates into the dashboard at launch, or the dashboard starts empty on day one. Getting Started section deliberately makes no claim either way.
- Whether the illustrative employee quote tone ("apparently that was the update") is the right voice, or reads as too cute — user moved to Stage 3 without confirming or rejecting.

**Out-of-scope/timeline signals:** None beyond what MVP scope already establishes (video-only auto-capture; HR-only readiness judgment).

<!-- coaching-notes-stage-3 -->
## Coaching Notes — Stage 3: Customer FAQ

**Gaps revealed:**
- Comprehension-vs-exposure gap (watch-% doesn't prove learning) — accepted trade-off, explicitly deferred to post-launch telemetry, not solved for MVP.
- Content-quality risk (AI-matched YouTube content can be wrong/low-quality) — mitigated by a human-approval checkpoint, which is itself an accepted ongoing operational cost, not a one-time build item.
- No test-out/skip path for employees who already know a skill — accepted trade-off; HR's manual override authority is the current mitigation.

**Trade-off decisions made:**
- Privacy/monitoring policy — **resolved, not a trade-off**: auto-captured progress data is explicitly coaching-only, never used in performance evaluation. This is now also recorded in project memory (`project_talentpilot_mvp_scope.md`) since it constrains the actual implementation (data access/reporting boundaries), not just this document.
- Data migration — **resolved**: no migration; dashboard starts clean at the 13 July 2026 launch. Also recorded in project memory.
- Comprehension verification, content-quality automation, and skill test-out were each explicitly named as accepted trade-offs / fast-follow candidates rather than launch blockers — none block the pilot launch as currently scoped.

**Competitive intelligence surfaced:** None new in this stage — competitive/build-vs-buy questions were deliberately routed to the Internal FAQ instead, since the customer-facing questions here are about employee/HR trust in the mechanism, not about vendor alternatives.

**Scope/requirements signals:** The "mixed trust, clearly labeled" positioning from Stage 2 held up under adversarial questioning without needing to be walked back — the dashboard's real value claim (labeling, not universal trust) survived the hardest question asked.

<!-- coaching-notes-stage-4 -->
## Coaching Notes — Stage 4: Internal FAQ

**Feasibility risks identified:**
- No individual technical component is novel (video polling, conditional-write persistence, pgvector matching are all proven, off-the-shelf-category tech per existing research) — the real risk is integration under time pressure, not invention. Recommended de-risking move: a week-one spike of the polling → persist → dashboard pipeline before committing the rest of the timeline.
- Dashboard labeling-UI clarity identified as a genuine pre-launch risk, not a nice-to-have: if "self-reported" vs. "verified" isn't visually unambiguous, HR could misread a stale cell as trustworthy and make a bad readiness call — worse than the status quo, since it would happen through a system that looks more trustworthy than the spreadsheet it replaced. Worth a dedicated usability check before pilot.

**Resource/timeline reality (explicitly examined, not hand-waved):**
- No named owner exists for post-pilot maintenance (content-curation approval, bug fixes, watching success telemetry). User decision: acceptable to remain aspirational now, **must be finalized before the Pilot & Validation phase begins** (not before the 13 July build start).
- No committed team size, roles, or timeline lock exists behind the brief's 5-week phased plan. Same deadline as above: finalize before the pilot phase begins. Until then, the 5-week plan is a target, not a commitment.

**Unknowns flagged with "what would it take to find out":**
- Legal/compliance exposure of employee video-watch tracking — no formal review has occurred. **User explicitly decided this is not needed for current scope** (internal pilot, coaching-only, no external customers) — a consciously accepted risk, not an oversight, revisit only if scope/audience changes.

**Strategic positioning decisions:**
- Build-vs-buy case made explicitly: no existing vendor (Cornerstone, Degreed, LinkedIn Learning) does auto-polled watch-% as a core trust signal; their "skill signals" remain self-reported/peer-endorsed. Heavyweight platform implementation cost (20-50% of license again) makes buying disproportionate for testing one narrow hypothesis.
- Post-pilot-success path (expand to other departments vs. ship fast-follows vs. something else) is explicitly undecided — flagged as worth naming before the pilot ends, not a launch blocker now.

**Technical constraints/dependencies surfaced:** None new beyond what prior technical research already established (YouTube IFrame polling, pgvector + text-embedding-3-small, human-approval content gate). No new dependency risk found in this stage.

<!-- coaching-notes-stage-1 -->
## Coaching Notes — Stage 1: Ignition

**Concept type:** Internal tool (not commercial, for now). No unit economics / customer-acquisition framing — FAQs calibrated to stakeholder value, adoption path, and build-vs-buy justification instead.

**Essentials confirmed by user (2026-07-08):**
- Customer: HR admins (assign + judge readiness) and Employees (consume + resume), per existing MVP scope.
- Problem: user explicitly reframed the root cause — "the spreadsheet itself isn't the biggest problem, it's the manual self-reporting and constant updating required from employees and managers. Excel is just where that process happens." This is now a *confirmed* framing choice, not an open hypothesis, and should headline the press release.
- Stakes: 88% of HR spreadsheets contain errors (Hackett Group); only 20% of HR leaders trust their own skills data (Gartner); 87% of companies cite skills-visibility as their #1 growth barrier.
- Solution: HR assigns → AI recommends matched video content → watch % auto-captured (never self-reported) → trust/freshness dashboard → Netflix-style resume.
- No additional source documents beyond what was already discovered in the repo.

**Why this direction over alternatives:** User explicitly chose to center the PR on "reducing manual reporting through centralized tracking and automation" rather than "replacing spreadsheets" as the headline frame — the tool (Excel) is not the villain, the process is.

**Key subagent findings shaping framing going forward:**
- Root-cause hypothesis (self-reporting is the disease) remains *unvalidated by primary research* — team deliberately skipped HR interviews (2026-07-07 decision) and is validating via live post-launch usage data instead. This is a legitimate target for the hardest Internal FAQ question.
- New risk surfaced, not previously documented: auto-polling video watch behavior may read internally as employee surveillance/monitoring. Needs a direct answer in Internal FAQ, not deflection.
- Build-vs-buy is now the central internal-stakeholder tension (since this stays internal): Cornerstone/Degreed/LinkedIn Learning already ship skill dashboards, but (a) their "skill signals" are still self-reported/peer-endorsed, not behaviorally captured, and (b) heavyweight platform implementation commonly runs 20-50% of license cost on top — real ammunition for "why build," but must be argued specifically, not hand-waved.
- Directionally validated: 2026 industry analysis (Bersin) frames a market-wide shift from completion/self-reported tracking to behavioral/auto-inferred signals — TalentPilot's bet aligns with, not against, where the category is moving. "Completion is a vanity metric" is a widely shared practitioner complaint (supports problem statement).
- MVP dashboard's trust story is uneven even post-launch: only video watch-% is behaviorally verified; other dashboard fields (sub-skills, HR judgment) remain self-reported/manual. Accepted known gap, not yet resolved — worth a candid Internal FAQ answer rather than overselling "fully trustworthy dashboard."
- Correction applied: web/artifact research flagged YouTube-vs-Vimeo as still open, but project-context.md shows this was already resolved (YouTube IFrame API, decided 2026-07-07) — treated as settled going forward.

**User context not fitting elsewhere:** User confirmed via direct answers (not extended discovery) — fast-tracked through Ignition in one exchange since prior brainstorming/design-thinking/brief work already established the essentials.
