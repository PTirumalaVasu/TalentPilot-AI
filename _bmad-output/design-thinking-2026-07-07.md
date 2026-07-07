# Design Thinking Session: TalentPilot-AI

**Date:** 2026-07-07
**Facilitator:** TalentPilot
**Design Challenge:** Eliminate manual, spreadsheet-driven skill tracking so HR gains real-time org-wide skill-readiness visibility while employees learn without any administrative overhead.

---

## 🎯 Design Challenge

Today, HR manages employee skill development through Excel — manually assigning courses, chasing status updates, and eyeballing spreadsheets to judge who's ready for what. This is slow, error-prone, and gives HR no live picture of org-wide readiness. Employees, meanwhile, have no clear system telling them what to learn or where they left off. TalentPilot-AI's opportunity is to replace that spreadsheet choreography with a platform where HR sets the learning roadmap (must-do skills/courses per employee), an AI assistant surfaces relevant content (video/doc/web) for employees to consume, and the system *automatically* captures progress from real video-watch behavior — so the HR dashboard reflects reality without anyone re-typing it in.

Two roles are in scope — **HR** (assigns, monitors, judges project-readiness manually) and **Employee** (learns, resumes where they left off, zero manual logging). No Manager/Team Lead role, no automated gap-matching — HR's judgment stays human; only the *tracking* becomes automatic.

**Constraints:** Not yet defined (open — tech stack, integration requirements, timeline, budget).

**Success looks like:** HR stops maintaining the tracking spreadsheet entirely; the dashboard becomes the single source of truth for skill readiness; employees always know what's next and never lose their place.

**Existing research:** The 2026-07-07 brainstorming session (`_bmad-output/brainstorming/brainstorm-talent-pool-management-capabilities-2026-07-07/`) is the only grounding so far — no HR interviews, tickets, or competitive benchmarking yet.

---

## 👥 EMPATHIZE: Understanding Users

### User Insights

_Source: brainstorm-intent.md + TalentPilot's direct knowledge of the current process. No formal interviews or live shadowing conducted yet — flagged below where content is inferred rather than confirmed._

- **HR Admin's primary action is entry, not review.** Opening the shared Excel sheet, the HR admin's core recurring task is adding/updating must-do skills and courses against each employee — confirmed directly, and consistent with the MVP's "HR Assignment Flow" scope item. Readiness-judgment is a separate, secondary act, not the main day-to-day interaction.
- **The sheet is bidirectional, and that's the weak link.** HR writes assignments in; employees self-report their own progress/status back into the *same shared sheet*. This self-reported flow is exactly the piece the new system eliminates by auto-capturing video-watch signals instead — the redesign is already targeting the right failure point.
- **No hidden complexity layer.** There are no extra tabs, color flags, or personal workarounds bolted onto the sheet. The pain isn't "the spreadsheet got too complicated" — it's structural: a plain shared file depending on people remembering to update it, with HR left to chase whoever didn't.
- **"Chasing" is the dread, and it now has a clear cause.** The phrase "without chasing spreadsheets" in the intent doc isn't decorative — it's the direct consequence of relying on self-reported status. HR isn't chasing data errors, they're chasing *people* to go type something in.

### Key Observations

- Two distinct HR actions live in one sheet: writing assignments (frequent, low-friction) and judging readiness (occasional, high-stakes). The MVP's split into "HR Assignment Flow" and "HR Dashboard" already reflects this real split correctly.
- Employee self-reporting is the single point of failure driving HR's core frustration — replacing it with auto-captured signals (video watch %) doesn't just modernize the tool, it removes the exact behavior nobody wants to do (updating a spreadsheet about your own progress).
- Absence of workarounds is itself a signal: this isn't a power-user tool with entrenched habits to migrate away from. It's a bare-minimum shared artifact — lower switching cost, but also less tolerance for a new tool that adds friction back in.
- Open question carried forward: how *often* HR actually opens the sheet to judge readiness (weekly ritual vs. ad hoc pull) — still unknown; matters for how "live" the dashboard truly needs to feel.
- **Root-cause hypothesis (inferred, not confirmed):** the real pain is the self-reporting *compliance step* itself, not the spreadsheet format — auto-capturing video-watch signal doesn't just modernize the tool, it removes the exact behavior people were failing at. Treat as a hypothesis to test in real interviews, not a settled finding.
- **Interpretive risk — "no workarounds" is ambiguous.** It could mean the plain sheet already meets everyone's needs (unlikely, given the "chasing" pain), or that people gave up trying to make it work at all (learned helplessness). These two readings point to opposite design responses, so this should become a direct question in any future HR/employee interview rather than an assumption we design around.
- **Auto-capture only closes the trust gap for video.** The "sub-skills" and "status" columns on the dashboard aren't video-shaped — they may still depend on some other self-reported or HR-judged input even after launch, so the underlying data-trust problem isn't fully solved MVP-wide, only for the video-consumption slice.
- **Design principle for Ideate:** the same watch-% signal can do double duty — eliminating the dreaded self-report *and* powering the "continue watching" resume feature. One data stream, two wins; worth carrying forward as a guiding principle rather than two separate features.
- **Still-open infrastructure constraint:** self-hosted vs. third-party video embeds changes what "auto-captured watch %" can technically mean — unresolved across two rounds of discussion, and blocks a full feasibility answer.
- **Candidate success metric surfaced (carry to Step 7):** % of assignment rows with a self-reported status stale beyond 7 days, as a baseline — expected to approach zero once auto-capture replaces self-reporting for video content.

### Empathy Map Summary

**HR Admin**
- **Does** (confirmed): Adds/updates must-do skills and courses per employee in the shared sheet; periodically reviews the status column to judge project-readiness; chases employees who haven't self-reported.
- **Says** (inferred): "Has anyone actually filled this in?" / "I need to know who's ready by [deadline]."
- **Thinks** (inferred): Doesn't fully trust the status column because it depends on someone else remembering to update it.
- **Feels** (inferred): Worn down by the chasing; a little anxious making real staffing calls on data they suspect is stale.

**Employee**
- **Does** (confirmed): Self-reports their own progress/status into the shared sheet.
- **Says/Thinks** (inferred): Updating the sheet isn't part of "real work" — easy to deprioritize or forget.
- **Feels** (inferred): Mild guilt or avoidance about not updating; no personal payoff for keeping it current, unlike a "continue watching" nudge that serves them directly.

_Confirmed = stated directly by TalentPilot or the intent doc. Inferred = reasonable hypothesis pending real interviews/shadowing — carried forward as a validation target, not settled fact._

---

## 🎨 DEFINE: Frame the Problem

### Point of View Statement

- **HR Admin:** *HR Admin needs a way to judge project-readiness that doesn't depend on unreliable, self-reported data, because chasing employees for spreadsheet updates wastes their time and quietly undermines confidence in the staffing calls they're making off it.*
- **Employee:** *Employees need to make progress visible without doing any extra reporting work, because manually updating a shared sheet about their own status is an easy-to-deprioritize chore with zero personal payoff — and it's the exact behavior HR can't rely on.*

### How Might We Questions

1. How might we replace self-reported progress with signals HR can actually trust — starting with video, where we already know it's possible?
2. How might we design the "auto-capture + resume" mechanic as one unified experience rather than two bolted-together features, since it's simultaneously killing the dread *and* creating the delight?
3. How might we close the trust gap for the dashboard fields that auto-capture doesn't reach — sub-skills and status — without reintroducing a manual-entry chore?
4. How might we design the dashboard so HR trusts the data enough to act on it quickly, given they currently have reason to doubt it?
5. How might we find out — cheaply, before committing further — whether "no workarounds" means the old process was tolerable or that people had simply stopped trying?
6. How might we make any *remaining* human-input fields feel worth doing, instead of unpaid administrative work with no reward loop?

### Key Insights

- The core lever isn't a better-looking dashboard — it's trustworthy, low-friction data capture. UI polish can't fix data nobody believes.
- The resume/continue-watching mechanic isn't a nice-to-have layered on top; it's the same signal that solves HR's trust problem. Building it as core infrastructure, not a bolt-on feature, is the opportunity.
- Real risk: the MVP scope solves this cleanly for video, but sub-skills/status fields are still exposed to the same self-report unreliability — an uneven trust story across one dashboard is itself a UX problem.
- Biggest open assumption blocking confident design: we don't know if the current process's silence means adequacy or resignation. That's worth resolving with real users before Ideate locks in a direction.

---

## 💡 IDEATE: Generate Solutions

### Selected Methods

- **Brainstorming** — the default engine for raw volume across all six HMWs; low overhead, works solo just as well as in a group.
- **SCAMPER Design** — an existing MVP scope already exists to riff on, so applying Substitute/Combine/Eliminate/Reverse lenses to it is higher-leverage than starting from a blank page.
- **Analogous Inspiration** — the Netflix/Spotify "continue watching" instinct was already this method in disguise; applied deliberately across the other HMWs too (Duolingo, Fitbit, GitHub, etc.).

### Generated Ideas

*Closing the trust gap beyond video (HMW1, HMW3)*
1. Proxy-signal tracking for docs/websites via scroll-depth and time-on-page.
2. Lightweight end-of-content checkpoint quiz; passing = trust signal (flag: expands current MVP scope).
3. "Opened the link at all" as a weak-but-real, zero-effort engagement signal for non-video content.
4. Replace free-text "status" with system-derived states (Not Started / In Progress / Ready) computed from video %, defaulting to explicit "Unknown" rather than a guess when no signal exists.
5. AI content-discovery assistant auto-suggests "mark as attempted" nudges when it detects related searches/opens.
6. HR can flag a sub-skill "assessed live" (e.g., in a 1:1) with a timestamp — manual judgment leaves an audit trail instead of a silent cell.
7. Substitute "time-to-complete vs. estimate" as an alternate trust signal for non-video content types.

*Making auto-capture + resume one mechanic (HMW2, HMW6)*
8. Ship tracking and resume as a single atomic feature/API/UI card — you can't get one without the other, so stop designing them separately.
9. Progress ring on the "continue watching" thumbnail doing double duty: visual resume cue *and* the trust signal, rendered once.
10. Auto-generated "your week in learning" recap for employees, reusing the same watch-position log for a third purpose: motivation.
11. Duolingo-style streak/momentum visual tied to actual learning engagement — rewarding the behavior we want, not the chore we're removing.
12. Auto-unlocked, team-visible skill badges on video completion — social payoff, zero manual claiming.

*Building dashboard confidence (HMW4)*
13. Per-data-point freshness indicator: green (auto-captured today) / yellow (self-reported, aging) / red (no signal) — makes the trust gap visible instead of hiding it behind a uniform grid.
14. "Needs attention" as a first-class dashboard view (stale/missing data), not just alphabetical-by-employee — serves the actual readiness-judgment moment directly.
15. One-click "why is this employee marked ready" drill-down exposing underlying signals — trust through transparency, not a black-box cell.
16. Reverse the flow entirely: employees self-trigger a "readiness certificate" once signals cross a threshold; HR becomes an exception-handler, not a full-grid reviewer.

*Provocations (SCAMPER: Eliminate/Combine/Reverse)*
17. Eliminate the "status" column outright — show only what's provably true from signals; a blank cell beats a guessed one.
18. Combine assignment + content-discovery into one screen: HR assigns a skill, AI-suggested content appears inline immediately — collapses the "two-layer model" into a single action.
19. Merge the HR Dashboard and HR Assignment Flow into one continuously-updating view instead of two separate flows.

*De-risking the biggest open assumption (HMW5)*
20. Run a 15-minute structured interview with 2–3 real HR admins using the Empathy Map's Does/Says/Thinks/Feels prompts — cheapest path to resolving "tolerable vs. resigned."
21. Anonymous one-question employee pulse: "How do you feel about updating your progress sheet today?" — a lighter proxy if full interviews aren't available yet.

### Top Concepts

1. **Trust/Freshness Dashboard** *(ideas #13, #14, #15)* — a per-cell freshness indicator, a "needs attention" filter, and a drill-down explaining *why* a status is what it is. Directly answers HR's core need (a readiness judgment they can actually trust) and is mostly UI/data-flagging logic — no new tracking infrastructure required, so it's buildable now regardless of how the video-hosting question resolves.
2. **Unified Auto-Capture + Resume Mechanic** *(ideas #8, #9, #10)* — one atomic feature instead of two bolted-together ones, reusing a single data pipe for tracking, resume, and a motivational recap. This *is* the MVP's core video flow, just designed deliberately as "one signal, three payoffs" rather than three separate asks.
3. **Cheap Validation Sprint** *(ideas #20, #21)* — not a UI concept, but the highest-leverage next action: a short real-HR-admin interview that resolves the single biggest assumption gating everything else (root-cause theory, "tolerable vs. resigned"). Flagged as a top concept anyway because building further without it means Prototype and Test would be validating against each other instead of against reality.

---

## 🛠️ PROTOTYPE: Make Ideas Tangible

### Prototype Approach

- **Storyboarding** — sequences the two design concepts (Trust Dashboard + Unified Auto-Capture/Resume) into one coherent HR + Employee journey, so the *flow* gets tested, not isolated screens.
- **Paper Prototyping** — a low-fi wireframe of just the Trust/Freshness Dashboard screen — the fastest way to get reactions to the freshness-indicator idea before any UI code is written.
- **Wizard of Oz** — fakes the auto-capture signal entirely by hand ("pretend the system just detected 73% watched") to test whether the resume card + freshness indicator *feel* right, without building any real video-tracking infrastructure yet.
- **Role Playing** — rehearses the Cheap Validation Sprint's interview script with a stand-in before it reaches a real HR admin, catching leading questions or dead air in advance.

### Prototype Description

- A **6-frame storyboard**: HR assigns a skill → Employee gets AI-surfaced content → Employee watches, leaves, returns to "Continue Watching" → system auto-captures % with zero self-report → HR dashboard shows that employee's row color-coded by freshness → HR filters to "Needs Attention" and drills into one flagged row.
- A **paper wireframe** of the dashboard alone: employee rows, green/yellow/red freshness-coded status cells, a "Needs Attention" filter toggle, and a drill-down panel sketch showing the "why is this employee ready" reasoning.
- A **Wizard-of-Oz walkthrough script**: manually narrate "the system just detected Employee X watched 73% of Video Y" and show, by hand, how the resume card and freshness cell would update — backend entirely faked, only the reaction is real.
- A **one-page interview guide** for the validation sprint, built directly from the Empathy Map's Does/Says/Thinks/Feels prompts, rehearsed once via role play before use on a real HR admin.

### Key Features to Test

- Does the freshness indicator actually change how *quickly and confidently* HR makes a readiness call, versus today's plain grid?
- Does "Needs Attention" get used naturally, or does everyone default back to scanning every row out of habit?
- Does the drill-down ("why is this employee ready") build trust, or is it noise nobody opens?
- Does the resume card feel like a genuine convenience to an employee, or a UI flourish they ignore?
- Does the interview guide actually surface "tolerable vs. resigned" cleanly — or does role-play reveal it needs sharper wording before the real interview?

---

## ✅ TEST: Validate with Users

### Testing Plan

*Methods:* Usability Testing (task-based sessions against the storyboard/wireframe/Wizard-of-Oz walkthrough), Assumption Testing (targeting the open assumptions carried since Empathize), Feedback Capture Grid (organizing results into likes / questions / ideas / changes).

*Who (aim 5–7):* 3–4 HR Admins, 3–4 Employees — same access caveat as Empathize: real participants vs. proxy-only changes this from "run" to "dry-run."

*Tasks:*
- **HR Admin:** (1) Find "who's NOT ready for Project X" on the dashboard wireframe — watch whether they reach for the Needs Attention filter or fall back to scanning every row. (2) React to a Wizard-of-Oz "system just detected 73% watched" narration and the freshness cell updating. (3) Open the drill-down and narrate what they think it's telling them.
- **Employee:** (1) React to the "Continue Watching" resume card — explain what it does, and whether they'd trust it to remember their spot. (2) React to the Wizard-of-Oz "the system detected you watched 73%" narration — accurate, creepy, neutral? (3) React to no longer needing to self-report status at all.
- **Validation-sprint interview** (separate, structured): the one-page guide with 2–3 real HR admins, aimed at resolving "tolerable vs. resigned" specifically.

*Questions:* "Walk me through how you'd figure out who's ready." / "What does this color mean to you?" / "What would make you trust this number enough to act on it?" / "What's missing that you'd want to check before making this call?"

*Capture:* Think-aloud during tasks, logged live into a Feedback Capture Grid per session, merged across all 5–7 for patterns.

### User Feedback

_Not yet collected — no real test sessions have run. Left honestly open rather than fabricated; the Feedback Capture Grid above is ready to receive it the moment sessions happen._

### Key Learnings

_Not yet available — pending real sessions. What this round of testing is specifically aimed at validating or killing: the root-cause hypothesis (self-reporting is the real pain, not the spreadsheet format), the "tolerable vs. resigned" ambiguity, whether the freshness indicator actually speeds up HR's confidence versus today's grid, and whether the resume card reads as genuine convenience or ignored flourish._

---

## 🚀 Next Steps

### Refinements Needed

- The two design concepts (Trust/Freshness Dashboard, Unified Auto-Capture + Resume) don't need visual rework yet — they haven't been touched by a real user, so there's nothing confirmed-broken to fix. The refinement that matters right now is informational: resolve the open questions before investing further in build-out.
- Once real feedback lands, likely refinement targets are specific, not sweeping: the exact staleness thresholds behind the freshness color bands, and how prominent "Needs Attention" needs to be to actually get used instead of ignored out of habit.

### Action Items

_Decision (2026-07-07): TalentPilot opted out of the pre-build validation sprint and HR admin interviews. The plan below proceeds straight to build, treating carried assumptions as working hypotheses to revisit only if real post-launch usage data contradicts them — not as a pre-build gate._

1. **Resolve the video-hosting constraint** (self-hosted vs. third-party embeds) — a technical decision, needed before the auto-capture mechanic can be built either way.
2. **Refine the two concepts directly into build-ready specs** — Trust/Freshness Dashboard and Unified Auto-Capture + Resume — using the empathy work already done (confirmed observations + explicitly-flagged assumptions), without an upfront interview gate.
3. **Build the MVP slice** per the existing scope: HR Assignment Flow, AI Content Discovery, Video Progress Tracking, Continue-Watching/Resume.
4. **Validate via real usage once live**, instead of upfront interviews — instrument the success metrics below directly from system data as the ongoing feedback loop.
5. **Treat carried assumptions as working hypotheses** — the root-cause theory (self-reporting is the real pain) and the "tolerable vs. resigned" question stay open, revisited only if live usage data suggests they were wrong (e.g., HR still doesn't trust the dashboard despite freshness indicators).

**Who's involved:** TalentPilot, driving build and refinement directly; no external interview participants required for this phase.

### Success Metrics

- **Primary:** % of assignment rows with self-reported status stale beyond 7 days — baseline at launch, target near-zero once auto-capture replaces self-reporting for video content.
- **Secondary:** HR's time-to-readiness-judgment ("who's ready for Project X") — measured from real usage post-launch (no pre-launch baseline interview).
- **Adoption proxy:** % of HR sessions using the "Needs Attention" filter vs. a full-grid scan — tests whether the feature changes behavior, not just whether it exists.
- **Lightweight qualitative signal:** informal feedback / support-channel sentiment once live, monitored as an ongoing signal rather than a pre-build interview gate.

**Next cycle:** Proceeding straight to build/refine by decision, skipping the pre-build validation sprint. Real usage data post-launch — not upfront interviews — is the mechanism that confirms or overturns the assumptions carried from Empathize.

---

_Generated using BMAD Creative Intelligence Suite - Design Thinking Workflow_
