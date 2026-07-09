# Adversarial Review (General) — TalentPilot-AI PRD

**Reviewed:** `prd.md` (v draft, created 2026-07-09), cross-referenced against `addendum.md`
**Review date:** 2026-07-09
**Reviewer stance:** Cynical, jaded, assumes problems exist until proven otherwise.

---

## Findings

- **The "replace spreadsheet self-reporting" vision has no self-report mechanism to replace it with.** The Provenance Label glossary defines "Self-reported" as a first-class dashboard state, and the Vision explicitly says non-video content "stays self-reported." But no FR anywhere describes *how* an Employee submits self-reported status for documents/websites or sub-skills. FR-5 goes out of its way to say video has *no* manual input field — but nothing fills that role for the non-video case either. Either the legacy spreadsheet (or some other unspecified tool) has to keep existing in parallel to produce this data, which directly undercuts the core pitch and SM-2 ("dashboard as primary reference, not the spreadsheet"), or there's a missing feature.

- **The launch date reads as already unrealistic, not merely "at risk."** The PRD is dated 2026-07-09 and commits to a clean launch on 2026-07-13 — four days later. In that window: deployment/hosting target is still explicitly undecided (Open Question 7), FR-12 (HR Override) has zero UX design ("no existing scenario or prototype covers this interaction"), and a full-stack build (auth, dashboard, video capture pipeline, embeddings ingestion) plus 24 defined test cases remain to be executed. Open Question 7 frames this as "a risk to the date holding" — it reads more like a near-certainty of slippage.

- **No FR covers authentication, account provisioning, or role assignment**, despite every one of the three key user journeys opening with "Entry state: Authenticated," and despite the addendum locking in a specific auth mechanism (JWT in an HTTP-only cookie). How an HR Admin or Employee account comes to exist, and how the HR-Admin-vs-Employee role gets assigned, is unanswered.

- **No FR describes where the Employee roster comes from.** UJ-3 has Rita "select employee" during assignment, implying a maintained list of employees — but HRIS integration is explicitly declared out of scope (Open Question 5), and nothing else in the FR set describes employee data provisioning or maintenance.

- **The "coaching-only" guarantee is asserted, not engineered.** It's called a "launch-blocking requirement... enforced structurally at the data-access/service layer" in the Constraints section, but no FR operationalizes it — no access-control requirement, no audit-logging requirement, no described mechanism a reviewer could actually test against. It's a strong claim resting on zero testable consequences.

- **The coaching-only guarantee is also conceptually thin.** The dashboard's entire reason to exist is letting Rita make staffing calls ("who can we staff on this?") off the same Watch Progress signal the PRD insists is never used for evaluation. Being staffed or passed over on a visible project is a real career consequence flowing directly from this data. The guarantee fences off one narrow downstream use (formal performance review) while leaving the signal's more immediate use — staffing decisions — completely untouched by the same protection.

- **FR-6 and FR-5 contradict each other on precision.** FR-6 calls an inexact resume position a "launch-blocking defect," requiring the resume point to match "exactly." FR-5 samples playback position only every 5–10 seconds. By the architecture's own design, the best available data point can be up to ~10 seconds stale — "exactly" as a literal bar is inconsistent with the sampling cadence specified one requirement earlier.

- **FR-7's "never regress" guarantee doesn't address cross-device clock skew.** The testable consequences only cover the same-employee, two-tab, same-client scenario. If watch-progress timestamps are client-supplied (the addendum doesn't say they're server-assigned), ordinary clock drift between an employee's two different devices could cause a genuinely later watch session to lose to a clock-skewed "earlier" one — a plausible real-world case the FR never considers.

- **Nothing defends against a trivially spoofed "Verified" signal.** The entire pitch is that auto-captured watch data can be trusted where self-report couldn't — but nothing in the FRs or addendum describes server-side plausibility checks, rate limits, or anomaly detection on incoming watch-position writes. An employee opening dev tools and posting a fabricated 100%-watched update appears to be exactly as easy as the self-reporting this product was built to replace, just with an extra layer of technical friction.

- **FR-12 (HR Override) is an unmonitored lever that can quietly inflate the very metrics it's supposed to be measured against.** Override has an audit trail (timestamp + attributor) but no described review, approval threshold, or usage monitoring. SM-1/SM-2 measure staleness and dashboard-trust; nothing stops an HR Admin from marking everything "ready" via override to make those numbers look good without changing underlying behavior. SM-C1 names spreadsheet-reversion as a counter-metric to watch for; no equivalent counter-metric exists for override overuse.

- **The "zero budget" constraint isn't reconciled against the locked stack's paid API dependency.** Cost constraints say "no new paid infrastructure," and the addendum carefully reconciles the YouTube Data API's free-tier daily quota against the ingestion-cadence NFR — but never mentions that `text-embedding-3-small` (OpenAI) is a metered, paid API called at ingestion time and presumably at match/query time too. That gap is quietly unaddressed.

- **FR-4's single-recommendation, no-search design has no failure path for a bad match.** Content-approval is explicitly out of scope, so nothing is vetting what the embedding model surfaces before an Employee sees it. If that one recommendation is irrelevant or low quality, there's no in-product way to reject it, ask for an alternative, or flag it — the Employee is stuck with whatever came back, or with doing nothing.

- **No handling for content rot.** Once a YouTube video is ingested and assigned, nothing describes what happens if the uploader deletes it, makes it private, or region-locks it later. FR-5's "clear error state" covers the Employee's viewing moment, but no requirement notifies HR that an active Assignment now points at dead content — the row could sit indefinitely showing stale or broken status with no signal to anyone that it needs re-assignment.

- **Sub-skills are named as a permanent (not just MVP-deferred) gap, with no described home.** The Glossary defines sub-skill status as "out of MVP auto-capture scope" and Open Question 4 confirms it "remains self-reported indefinitely post-launch" — but, per the first finding above, there's no FR describing where that self-reporting actually happens. It's unclear whether this data lives in the product at all or whether HR is quietly expected to keep a side channel (possibly the very spreadsheet being replaced) alive forever for it.

- **SM-2 depends on "usage analytics" that no FR, NFR, or addendum stack item ever specifies building.** There's no instrumentation requirement anywhere in the document to actually produce the telemetry this success metric is supposed to be measured against. Separately, with what appears to be a single-digit number of HR Admin users in an internal pilot, "usage analytics" is a statistically thin instrument for validating a behavior-change hypothesis.

---

## Overall Read

The PRD is well-organized and unusually honest about its own open questions and assumptions — that's to its credit, and better than most. But several of its strongest claims (coaching-only as a structural guarantee, "Verified" as a trustworthy signal, dashboard as the spreadsheet's full replacement) are asserted at the vision/constraint level without corresponding testable FRs to back them, and the self-reported half of the product — the half that's supposed to coexist with auto-capture rather than disappear — has no described mechanism at all. Combined with a launch date that is four calendar days out with hosting undecided and one FR entirely undesigned, the schedule risk is at least as real as the requirements gaps.
