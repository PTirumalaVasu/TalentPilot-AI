---
status: proposed
source: User request during Phase 5 Prototyping (2026-09-03) — "When we click on Add skill button we need to sign up into those sites then we need to get all the links related to the skill name from the youtube/udemy and other sites"; extended same day — "Add button should be disabled till the api keys are configured in to the Skill tab... provide a new screen to add API keys"; extended again — "add a new table in the database to store the API keys against the admin user which admin user is login to the system those api keys should use" (later reversed — see Correct Course change log below); revised via /bmad-correct-course (2026-09-03) — (1) API keys changed from per-admin back to a single shared/org-level key, and (2) content review is now a PREREQUISITE for skill creation — "while adding the skill should show all the links from Udemy/youtube and Admin can approve at least one of the link then only admin can add the skill, not from the below cards"
relatedPrototype: design-artifacts/E-Development/01-Assign-New-Skill-Prototype/hr-dashboard.html (simulated mockup only — see Story implementation note)
implementationStory: design-artifacts/E-Development/01-Assign-New-Skill-Prototype/stories/HR-Dashboard.12-api-keys-view.md (Story 1); HR-Dashboard.13-inline-content-approval.md (Stories 2-3, current); HR-Dashboard.11-content-discovery-mockup.md (superseded)
---

# Epic: Automated Content Discovery for New Skills

## Change Log (Correct Course, 2026-09-03)

Two scope changes were made to this epic via the `/bmad-correct-course` workflow, bundled into one Sprint Change Proposal since both touch the same feature:

1. **API keys reverted from per-admin to shared/org-level.** Story 1 previously specified a per-`employee_id` `admin_api_keys` table (added the same day, at explicit request). On reflection this was over-engineered relative to actual need — reverted to a single organization-wide key per provider. Story 1 below reflects the new (shared) design; the per-admin design it replaces is preserved in this file's git history, not repeated here.
2. **Content approval is now a prerequisite for skill creation, not a follow-up.** Previously: Add Skill saved the skill immediately, then a search ran and candidates could be reviewed afterward, asynchronously, from each skill's card in the list — a skill existed whether or not anything was ever approved. Now: entering a skill triggers the search first, candidates are reviewed **inline in the Add-Skill flow itself** (not "the below cards" — the per-card review panel is removed), and the skill is only actually created once the admin approves **at least one** candidate. Stories 2 and 3 below are rewritten for this new sequencing.

## Overview

When an HR Admin adds a new skill, the system searches external platforms (YouTube, and Udemy once Story 4 is resolved) for relevant training content **before the skill is saved**, and the admin must approve at least one candidate as part of creating the skill — content review is no longer optional or deferrable. This still extends the existing HR-curated-content model rather than replacing it (a human always approves before anything is assignable) — what changed is *when* that approval happens relative to the skill existing at all.

**This is a real backend feature, not something a static HTML prototype can perform.** API keys cannot live in client-side JavaScript, and browsers can't call most third-party search APIs directly (CORS). The prototype gets a **clearly-labeled simulated mockup** of the flow (fake results, no real network calls) so the UX can be reviewed — see `HR-Dashboard.11-content-discovery-mockup.md`.

## Important Scoping Notes (from the real codebase, not assumptions)

- **YouTube already has partial backend support.** `backend/app/content/` has an `ingest` CLI (`app.content.cli ingest`), `find_best_matching_content()` (pgvector cosine similarity, `SIMILARITY_THRESHOLD = 0.4`), and a `ContentCatalog` model with `source: YOUTUBE | MANUAL` + a stored `embedding`. Real seed content (`backend/app/core/seeds.py`) was originally pulled this way, per its own comment: "pulled live from YouTube via `app.content.cli ingest`... during manual verification on one machine" — meaning today this is a manual, one-off CLI operation, not an automated on-skill-creation trigger.
- **YouTube Data API v3 has a strict free quota**: 10,000 units/day, and `search.list` costs 100 units per call — 100 searches/day on the free tier, zero margin for retries or multiple skills created in a burst. A real "search on every skill creation" feature needs quota planning (batching, caching, or a paid tier) before it can run unattended.
- **Udemy has no existing integration in this codebase at all.** It would need new credentials (Udemy's Affiliate API and Instructor API have different auth models and different data access — which one depends on the partnership TalentPilot-AI would actually have with Udemy), a new ingestion module mirroring the YouTube one, and a **licensing decision**: Udemy courses are paid — "links related to the skill" for an employee to actually watch either requires purchased seats per employee or restricting suggestions to public preview clips / course descriptions only (not full course access).
- **"Sign up into those sites"** — read here as "the service needs API/developer credentials," not that the app creates individual user logins on YouTube/Udemy on HR's behalf. Flagging the literal phrasing in case something narrower (e.g., an admin's own YouTube account, SSO) was actually meant — worth confirming before real implementation.
- **⚠️ Security warning on Story 1 below, read before implementing**: entering raw API keys into a web form (even an admin-only one) and having the browser hold or transmit them is a real anti-pattern for production — see that story's Notes.

---

## Story 1: Configure a Shared API Key Per Integration Before Content Search Is Available

As an **HR Admin**,
I want **one shared YouTube key and one shared Udemy key configured for the whole organization**,
So that **any HR Admin can search for content without every admin needing to obtain and manage their own credentials**.

**Design decision (revised via Correct Course, 2026-09-03): one key per provider, organization-wide — not per-admin.** Any HR Admin can view configuration status and update either key; whoever last saved a key is recorded for audit purposes, but the key itself is not scoped to them. The "is content search available" gate is evaluated **globally**: once any admin configures both keys, search is available to every HR Admin.

### Data Model

```sql
CREATE TABLE integration_api_keys (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider       VARCHAR(20) NOT NULL UNIQUE,  -- 'YOUTUBE' | 'UDEMY'
    encrypted_key  TEXT NOT NULL,                -- see Security Notes below — never plaintext
    updated_by     UUID NOT NULL REFERENCES employees(id),  -- audit trail: which admin last set it
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

One row per provider, full stop — `UNIQUE (provider)`. `updated_by` keeps an audit trail of who last changed a shared key without scoping access to them. Only `employees.role = 'HR_ADMIN'` may read status or write keys (enforce via this codebase's existing `require_hr_admin()` pattern, `backend/app/assignments/service.py`).

**Real implementation story for just this table**: `_bmad-output/implementation-artifacts/stories/2-1a-create-integration-api-keys-table.md` (sprint-status.yaml: `2-1a-create-integration-api-keys-table`) — a real Alembic migration + SQLAlchemy model, verified against this codebase's actual migration tooling and model conventions (not assumed), split out so a backend developer can implement the table independently of the UI/gate work described below in this same Story 1.

**Acceptance Criteria:**

**Given** the organization has not configured both the YouTube and Udemy keys
**When** any HR Admin views the Skills tab
**Then** the "+ Add Skill" flow's search step is disabled, with a visible reason and a link to the API Keys screen

**Given** I open the API Keys screen
**When** it renders
**Then** I see one input per integration, a Save action, and each key's organization-wide status (configured / not configured) — never the key's actual value once saved

**Given** I save both keys with non-empty values
**When** the save completes
**Then** a row is upserted into `integration_api_keys` per provider (encrypted before storage — see Security Notes), and content search becomes available to **every** HR Admin, not just me

**Given** a key is cleared back to empty and saved
**When** that completes
**Then** that provider's row is deleted (or nulled) and search becomes unavailable again for everyone, until reconfigured

**Security Notes for real implementation (do not build this literally as a browser form holding real keys):**
- `encrypted_key` must be encrypted at rest — application-level AES-256-GCM with a data-encryption key sourced from a KMS/secrets manager (not a key stored in the same database), or `pgcrypto` if the DB-native approach is preferred. Never a plaintext column.
- The API layer must be **write-only** from the browser's perspective: a save endpoint accepts a new key value; a read/status endpoint returns only a boolean ("configured: true/false") plus maybe a masked hint (e.g. last 4 characters) — it must never return the decrypted key back to the browser.
- A shared key is higher blast-radius than a per-admin key (any HR Admin can rotate/break it for everyone) — worth deciding whether write access should be restricted further (e.g. a separate "org settings" permission beyond plain `HR_ADMIN`), even though this epic doesn't require that distinction today.
- Audit who changed a key and when (`updated_by`/`updated_at` here are a start; a real implementation likely wants a separate append-only audit log if key changes need to be traceable after the fact, not just the most recent change).
- This remains additive to, not a replacement for, this codebase's existing `YOUTUBE_API_KEY` env-var pattern if that's still used elsewhere — clarify with real stakeholders whether this DB-backed key fully replaces that or the env var remains a deploy-time fallback.

---

## Story 2: Search for Content When Adding a New Skill (Before the Skill Is Saved)

As an **HR Admin**,
I want **the system to search YouTube and Udemy for relevant content as soon as I enter a skill's name, before the skill is actually created**,
So that **I can see what's available and choose good content as part of creating the skill, not as a disconnected follow-up task**.

**Revised via Correct Course, 2026-09-03**: previously the skill was saved immediately and search happened afterward, asynchronously. Now the search is a **step within** skill creation, not a background process that follows it — see Story 3 for what happens with the results.

**Acceptance Criteria:**

**Given** both API keys are configured (Story 1) and I enter a skill name (and optional description) in the Add-Skill flow
**When** I trigger the search
**Then** the system searches YouTube (Data API v3 `search.list`) and Udemy (once Story 4 is resolved — see that story) using the entered name/description as the query, using the shared keys from Story 1 — **the skill itself is not created yet**

**Given** the search returns results
**When** they're processed
**Then** each candidate gets an embedding generated and is filtered by relevance — reusing the existing `find_best_matching_content()` cosine-similarity approach — before being shown to HR, rather than showing every raw search result

**Given** the search fails (API error, quota exhausted, or zero candidates clear the relevance threshold)
**When** that happens
**Then** HR sees a clear failure message and the skill is **not** created — unlike the previous design, a search failure now blocks skill creation, since Story 3 makes at least one approved candidate a prerequisite. (If "let HR proceed with zero content, to be added manually later" is actually wanted for this failure case specifically, that's a product decision to confirm — flagged here rather than assumed.)

---

## Story 3: Approve At Least One Candidate Before the Skill Is Created

As an **HR Admin**,
I want **to review every candidate found for a new skill and approve at least one before the skill can be saved**,
So that **no skill ever enters the catalog without at least one piece of vetted, assignable content already attached**.

**Revised via Correct Course, 2026-09-03**: this is the epic's central sequencing change. Content review used to be optional and happen after the skill already existed, shown per-skill in the skills list ("the below cards"). Now it's a **gate on creation itself**, shown inline in the Add-Skill flow, and the per-card review UI is removed.

**Acceptance Criteria:**

**Given** Story 2's search returned candidates
**When** they're shown to me
**Then** they render **inline within the Add-Skill flow** (not in a panel under the skill's card in the skills list — that UI is removed), each with title, thumbnail, duration, source (YouTube/Udemy), and **the actual link/URL** so I can see (not just infer) what I'm reviewing before approving it

**Given** I click a candidate's link
**When** it opens
**Then** it opens **as a popup over the current page, not a navigation to another page or tab** — I can view/preview the candidate and approve or reject it from within that popup without losing my place in the Add-Skill flow

**Given** I am reviewing candidates
**When** I click Approve on one
**Then** it's marked approved locally; **"Add Skill" stays disabled until at least one candidate is approved**

**Given** I click Reject on a candidate
**When** that happens
**Then** it's discarded and won't be shown again for this skill-creation attempt

**Given** I have approved at least one candidate
**When** I click "Add Skill"
**Then** the skill is created AND the approved candidate(s) are written to `content_catalog` in the same operation — a skill and its first approved content always come into existence together, never a skill with zero content

**Given** I have approved zero candidates (rejected all, or none reviewed yet)
**When** I look at "Add Skill"
**Then** it remains disabled — there is no path to creating a skill with no approved content through this flow

**Given** I want to abandon this skill entirely
**When** I click Cancel
**Then** the name/description and any approved/pending candidates are discarded — nothing is saved (no draft-saving in this flow)

**Note — no longer applicable as previously written**: the old Story 3 AC "no candidates approved → assigning shows 'No approved content found yet'" described a state (skill exists, zero content) that this revision makes unreachable through skill creation. That empty-content message may still be reachable through some *other* path (e.g. if content is later deleted from the catalog) — worth a separate check, not assumed here.

---

## Story 4: Udemy Integration (flagged, not detailed)

Deliberately **not** broken down to acceptance-criteria level yet. Before writing implementation stories, this needs a discovery spike to resolve: which Udemy API/partnership TalentPilot-AI would actually use, what data it grants access to, and the licensing question above (purchased seats vs. preview-only links). Recommend scoping as a separate epic once those are answered, rather than guessing terms into acceptance criteria now.

**Note**: the prototype's simulated mockup (Story 2/3's implementation) shows fabricated Udemy candidates alongside YouTube ones for UX-review purposes, even though this story remains unresolved for real backend work — the mockup demonstrates the intended *experience*, not a claim that Udemy is actually integrated.

---

## Out of Scope / Notes

- Rate limiting, retry/backoff strategy, and cost monitoring for the YouTube API are real implementation concerns not detailed here — flagged so they aren't discovered for the first time in production. With a shared key (Story 1), the whole organization now shares one quota (10,000 units/day) — worth modeling expected skill-creation volume against that before this goes live, since a burst of skill creation could exhaust it for everyone.
- API keys must be encrypted at rest in the `integration_api_keys` table (Story 1) and never exposed to the browser after being saved — see that story's Security Notes.
- No embedding/search cost estimate included — worth modeling before committing to "search on every skill creation" vs. a batched/on-demand trigger.
- **Prototype limitation, not a real gap**: this static HTML prototype only ever represents one logged-in user per scenario — there's no multi-admin login-switching, but that's now moot for Story 1 anyway since the key is shared, not per-admin. The mockup's single in-memory `apiKeys` object now directly matches the real design (one org-wide value), unlike the earlier per-admin revision where it was a simplification.
