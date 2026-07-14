# TalentPilot-AI — Project Documentation (Plain-Language Overview)

*Compiled from the BMAD planning artifacts in `_bmad-output/` — Product Brief, PRD, Architecture Spine, Solution Design, and Epics. Last compiled: 2026-07-13.*

---

## 1. The Problem Statement

HR at SAILS Software tracks employee skill development using a **shared spreadsheet**. HR assigns "must-do" skills to employees, employees are supposed to update their own progress in the sheet, and HR periodically scans the grid to decide who is ready to be staffed on a project.

This breaks down in practice, for one simple reason: **spreadsheets only work if people remember to update them.**

- **The data can't be trusted.** 88% of HR spreadsheets contain errors, and only 20% of HR leaders feel confident their skill data is accurate.
- **Nobody has a real-time picture.** Pulling together status across dozens of employees eats up admin time, and by the time HR needs an answer, the sheet is already stale.
- **Employees have no reason to update it.** Self-reporting progress is a chore with zero personal payoff, so it's the first thing people skip — leaving HR chasing people instead of managing skills.
- **When HR is asked "who can we staff on this?", they can't answer with confidence** — they end up asking around anyway, which defeats the purpose of having a tracking sheet at all.

The result, industry-wide: **87% of companies say lack of visibility into workforce skills is their #1 barrier to growth.**

The important insight behind this project: **it isn't the spreadsheet that's broken — it's the self-reporting step.** Any tool that still asks employees to manually type in "I'm 40% done" inherits the same trust problem. The only real fix is to stop asking employees to report progress at all, wherever that's technically possible.

---

## 2. The Solution

**TalentPilot-AI removes the self-reporting step for video-based learning — the one content type where progress can be captured automatically, from actual behavior instead of a manual entry.**

The idea in one sentence: *the same signal that lets an employee "resume where they left off" is the signal that tells HR how far along they are* — one write, two payoffs, no separate status update.

How it works, end to end:

1. **HR assigns a skill to an employee.** This sets the learning roadmap — HR still decides what people should learn (the system never guesses this).
2. **The system recommends learning content** (a video, document, or website) that matches the assigned skill, using AI-based semantic matching — no manual content-hunting by HR or the employee.
3. **The employee watches the video.** As they watch, the system silently records their exact playback position in the background — no button to click, no field to fill in.
4. **The employee can return any time and resume exactly where they left off** — Netflix/Spotify-style — with zero manual bookkeeping.
5. **HR's dashboard updates itself automatically**, in near real time, from that same watch data. No re-typing, no chasing, no separate sync step.
6. **HR can drill into any row to see *why* it says what it says** — the raw watch percentage, when it was last updated, and whether the number is machine-verified or still self-reported — so a readiness call can be defended, not just guessed at.

Two roles use the product:

- **HR Admin ("Rita")** — assigns skills, watches the dashboard, makes staffing/readiness calls, and can manually mark someone "ready" when she has other grounds for confidence (a conversation, an offline assessment) even if the auto-captured data hasn't caught up.
- **Employee ("Casey")** — receives assigned skills, sees a simple list of recommended content, watches videos, and resumes exactly where they stopped. Never types a status update.

This is deliberately **narrow**. It is not a full learning platform (no course catalog, no certifications, no learning paths) and it does not try to guess what someone *should* learn — HR always makes that call explicitly. Being narrow and fast to build is treated as a competitive advantage, not a limitation: none of the existing tools in this space (heavyweight talent-intelligence suites, LMS/LXP platforms, or newer AI gap-analysis tools) combine HR-driven assignment + AI content discovery + fully automatic video-progress capture + a consumer-grade resume experience in one lightweight product.

### What success looks like

- HR stops keeping a shadow spreadsheet within 60 days of go-live and uses the dashboard as the real source of truth.
- The percentage of stale, self-reported video-progress rows drops from effectively 100% (today's baseline) to near-zero.
- Employees actually finish videos and use the resume feature, without ever being asked to "log" anything.
- **Watch on this:** if HR is still privately checking the old spreadsheet after go-live, that's a red flag even if the backend numbers look good — behavior change is the real proof, not the metric alone.

---

## 3. Who This Is For — and Who It Isn't

| | |
|---|---|
| **HR Admin (primary user)** | Assigns skills, reads the dashboard, makes readiness calls, can manually override a status. |
| **Employee (secondary user)** | Receives assignments, watches recommended content, resumes videos. Never manually reports progress. |
| **Manager / Team Lead** | **Not a role in this product at all.** Considered and explicitly dropped for v1 — revisit only if a real pilot demands it. |

**Explicitly out of scope**, on purpose (not oversights):
- Not a full LMS/LXP — no course catalog browsing, no learning paths, no certifications.
- Not a skill-gap detector — the system never decides what someone *should* learn; HR always assigns explicitly.
- Not a performance-evaluation input — auto-captured watch data is "coaching-only" by design and is structurally blocked from feeding into performance reviews.
- Not tracking progress on documents or websites — only video watch behavior can be captured automatically; other content types stay self-reported and are visibly labeled as less trustworthy, not silently blended in.
- No content-approval workflow — AI-recommended content reaches employees without a human quality check in this version (an accepted risk, not an oversight).
- Not a commercial product — this is an internal pilot for SAILS Software's own HR team.

---

## 4. Project Requirements (in plain language)

The PRD defines 14 core capabilities ("Functional Requirements," FR-1 through FR-14), grouped into five features. Below is what each one means in practice.

### 4.1 Skill Assignment Flow
- **HR can assign a skill to an employee** in a simple three-step flow (pick employee → pick skill → review the AI-suggested content → confirm), completing in under two minutes.
- **HR sees what content the employee will get**, before confirming — this is just visibility, not an approval gate. If nothing to assign a skill without content rather than getting stuck.
- If HR tries to assign a skill the employee already has, the system surfaces the existing assignment instead of silently creating a duplicate.
- Canceling the flow at any point leaves nothing behind — a true no-op.

### 4.2 AI-Assisted Content Discovery
- For every assigned skill, the system suggests **one** relevant piece of content (video, document, or website) using approximate/semantic matching — it doesn't need exact keyword overlap to find a good match.
- If nothing good enough is found, the system shows **no** recommendation rather than a poor guess — an honest blank beats a misleading match.
- The employee sees **all** their assigned content in one simple list (grouped "In Progress" / "To Start") — there is no search box and no browsable catalog, because the employee isn't meant to go hunting; HR already decided what they need.
- Content is refreshed via a scheduled batch job (not searched live) because the underlying video-search service has a strict daily usage limit.

### 4.3 Automatic Video Progress Capture & Resume
- While a video plays, the system **automatically records the playback position** every 5–10 seconds — no manual input field exists anywhere for this.
- If the tab is closed abruptly, the last known position is still reliably saved.
- The employee can resume a video at the **exact** position they left off — getting this wrong on a first use is treated as a launch-blocking bug, not a minor annoyance.
- If the same video is open in two tabs at once, the system keeps whichever update happened **most recently in time** — never just "whichever number is higher" — so a legitimate rewind (someone scrubbing back on purpose) is respected instead of accidentally blocked.

### 4.4 Readiness Dashboard
- HR's main screen: one row per employee-and-skill assignment, showing a simple **Status** badge — *Not Started*, *In Progress*, or *Completed* — as the at-a-glance answer.
- Clicking into any row reveals the deeper trust detail — the **Provenance Label**: *Verified* (machine-captured from real video watching), *Self-reported* (typed in by someone, less trustworthy), *Needs Attention* (data hasn't been updated in 7+ days), or *HR Override* (a human manually confirmed it).
- Rows **update themselves automatically** as new watch data comes in — HR never has to refresh or re-type anything, and updates show up within 30 seconds.
- **HR can manually mark someone as ready**, independent of the automatic data — useful when HR has other grounds for confidence (a conversation, an offline test). This manual override is always kept clearly separate from "machine-verified" — it's never disguised as auto-captured data, and HR can reverse it later.
- Status badges never rely on color alone — they always include text or an icon, so the dashboard is usable by everyone (accessibility requirement).

### 4.5 Authentication & Login
- Nobody can see any assignment, content, or watch-progress data without logging in first — and there's never a flash of protected content before a redirect to login.
- Each login session is locked to exactly one role: an HR Admin can see everything org-wide (through safe, coaching-only views); an Employee can only ever see their **own** data, no matter how a request is crafted.
- Logging out immediately kills the session — no lingering access via the browser back button.

### Non-Functional Requirements (the "quality bar," in plain terms)
- **Speed:** dashboard loads in under 2 seconds; video player loads in under 3 seconds; a new assignment appears within 1 second of confirming it.
- **Data safety:** a failed dashboard refresh never means a lost assignment — it's shown as a distinct, recoverable error.
- **Anti-cheating:** the server double-checks that watch-progress updates look like real playback (not an instant jump to 100%) before treating them as "Verified" — trust in the Verified label can't rest on data the client could fake.
- **Privacy ("coaching-only"):** raw watch data can never be exported or shaped into a performance-review report — this is enforced in the code itself, not just as a policy statement.
- **Accessibility:** WCAG 2.1 AA compliant — keyboard-operable throughout, screen-reader announcements for live updates, no color-only signals.
- **No paid infrastructure** — the whole build runs on a zero budget, using free/local tools wherever possible.

---

## 5. Architecture (in plain language)

### The big picture

TalentPilot-AI is built as a **modular monolith** — one single application (not a tangle of microservices), but internally organized into clean, self-contained sections ("modules") so that each feature can be understood by opening one folder, not by chasing logic across the whole codebase. For a small internal pilot, microservices would be unnecessary overhead — this keeps things simple without losing structure.

**The three moving pieces:**
- A **React** website (what HR and employees actually see and click).
- One **FastAPI** (Python) backend application that handles all the logic.
- One **PostgreSQL** database (with a special add-on called `pgvector` that lets it do AI-style "similarity" matching for content recommendations).

Everything runs locally for this pilot (via Docker) — there is no live production deployment yet; that's a deliberate, explicit decision to keep the pilot scoped and cheap.

### The five building blocks (modules)

| Module | What it's responsible for |
|---|---|
| **auth/** | Logging in, sessions, and making sure people can only see what they're allowed to see. |
| **assignments/** | Creating and storing "HR assigned Skill X to Employee Y" records. |
| **content/** | The library of recommended videos/docs/sites, and the AI matching that connects them to skills. |
| **progress/** | The single source of truth for "how far along is this, and how much do we trust it" — owns all watch data, staleness detection, and HR overrides. |
| **dashboard** | Doesn't own any data itself — it just reads from `assignments` and `progress` and composes the HR's view. |

### The most important design decision

**One module (`progress/`) is the *only* place allowed to decide what a dashboard row's Status and trust level actually are.** No other part of the system is allowed to compute or guess this independently.

Why this matters, explained simply: if the dashboard, the assignment screen, and some future export feature each calculated "is this person ready?" using their own logic, they could disagree with each other — and that's exactly the trust problem this whole product exists to solve. By funneling every read through one authority, the system guarantees the answer is always consistent, and makes the "coaching-only" privacy rule (watch data must never leak into a performance review) enforceable in exactly one place instead of scattered — and easily forgotten — throughout the code.

### Other key engineering decisions, explained

- **Watch-progress updates are ordered by *when they happened*, not by the number itself.** If someone rewinds a video on purpose, that's a real, newer action that should count — even though the position number goes down. The system tells "someone rewound on purpose" apart from "an old, out-of-date update arrived late" by comparing timestamps, not positions.
- **The server double-checks watch data before trusting it ("Verified").** A position that jumps instantly toward 100% isn't real playback — the server rejects unrealistic updates so the "Verified" label actually means something.
- **An HR Override is stored as a separate record, not written over the real data.** This way, if HR manually marks someone "ready" and then real watch data comes in later, both pieces of information stay visible — nothing gets silently erased, and a manual override is never disguised as machine-verified.
- **Content isn't searched live — it's fetched in scheduled batches.** The video-search service (YouTube's API) only allows about 100 searches per day, nowhere near enough to search fresh every time someone loads a page. So the system pre-builds its content library ahead of time and matches against what's already been collected.
- **Content matching uses AI "embeddings," not exact keyword matching.** Skill names and video descriptions are converted into numeric representations ("vectors") using a free, offline AI model, and the system finds videos that are *semantically* close to a skill — even if the exact words don't match. If nothing is close enough, it shows nothing rather than a bad guess.
- **The video player is built behind a swappable "adapter."** The core progress-tracking logic doesn't know or care whether the video comes from YouTube or (later) Vimeo — it just talks to a generic interface. This means the video provider could be swapped later without rewriting the trust/progress logic.
- **Every request is checked for permission on the server, every single time** — not just when someone logs in. An employee session is hard-locked to that one employee's own data no matter how a request is phrased, and this is enforced in the actual data-fetching code, not just hidden by the login screen.
- **The dashboard refreshes itself by asking the server every 30 seconds or less** ("polling") rather than using more complex real-time technology — simple, reliable, and good enough for this scale.

### How the pieces connect

```
Browser (React website)
      │  (secure login cookie)
      ▼
FastAPI backend  ──────►  PostgreSQL + pgvector database
      ▲
      │ (limited daily calls)
Scheduled job  ──────►  YouTube (content search)
```

Everything above runs together locally via Docker Compose for this pilot phase.

### Tech stack, at a glance

| Layer | Tool | Why |
|---|---|---|
| Frontend | React + TypeScript + Vite, shadcn/ui + Tailwind | Modern, fast, well-supported UI toolkit |
| Backend | Python 3.12+, FastAPI | Fast to build with, good async support |
| Database | PostgreSQL + pgvector | Reliable relational storage plus AI-style similarity search in one place |
| AI matching | A free, local `sentence-transformers` model | No API costs, works offline, fits the zero-budget constraint |
| Video | YouTube IFrame Player (behind a swappable adapter) | Free, well-documented, and not locked in long-term |
| Hosting | Docker Compose, local only for this pilot | Keeps the pilot cheap and simple; production hosting is a later decision |

---

## 6. Known Open Questions & Risks (carried forward honestly, not hidden)

These are documented gaps the planning process surfaced — none of them block building the pilot, but they matter for what comes after:

- **Where do login accounts and the employee list actually come from in production?** For now, accounts are seeded locally by hand; a real company login system (SSO) and employee roster (HRIS) integration is a later decision.
- **How long should watch history be kept?** No retention period has been locked in yet.
- **Do HR Admins actually notice and correctly read the trust labels (Verified vs. Self-reported vs. Needs Attention)?** This hasn't been tested with a real HR person yet — it's flagged as something to check right after (or even before) launch, since the whole point of the product depends on HR actually using this signal instead of reverting to gut feel.
- **Documents and websites will always remain self-reported** in this version — only video can be automatically verified. This is a known, accepted limitation, not a bug.
- **No formal legal/compliance review of employee video-watch tracking has happened yet** — consciously deferred since this is an internal pilot, but would need revisiting if the product expanded beyond one internal team.
- **Nobody has been named yet as the long-term owner** of this product after the pilot — three possible futures were identified (stay standalone, feed into a future full LMS, or get folded into a bigger platform), but no decision has been made.

---

## 7. Quick Reference — Documents This Was Built From

| Document | What it covers |
|---|---|
| `_bmad-output/planning-artifacts/briefs/brief-TalentPilot-AI-2026-07-08/brief.md` | Original problem framing, opportunity, and business case |
| `_bmad-output/planning-artifacts/prds/prd-TalentPilot-AI-2026-07-09/prd.md` | Full detailed requirements (the 14 FRs, user journeys, non-goals, success metrics) |
| `_bmad-output/planning-artifacts/architecture/architecture-TalentPilot-AI-2026-07-09/ARCHITECTURE-SPINE.md` | The binding technical rules ("invariants") a builder must not violate |
| `_bmad-output/planning-artifacts/architecture/architecture-TalentPilot-AI-2026-07-09/SOLUTION-DESIGN.md` | The human-readable explanation of *why* those technical rules exist, plus data model and flows |
| `_bmad-output/planning-artifacts/epics.md` | The requirements broken down into buildable epics and stories |
