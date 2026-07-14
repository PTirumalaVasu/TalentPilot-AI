---
project_name: 'TalentPilot-AI'
date: '2026-07-14'
trigger_story: '1-8-login-screen-ui'
change_type: 'Reversal of a prior explicit non-goal (Story 1.8 AC7)'
scope_classification: 'Minor'
status: 'proposed'
---

# Sprint Change Proposal — Persist Authentication Across Browser Refresh

## 1. Issue Summary

**Problem statement:** Refreshing the browser on a protected route logs the user out, even when their session cookie is still valid server-side.

**Discovery context:** Reported directly by TalentPilot (acting as product owner) on 2026-07-14, after Epic 1 (Authentication & Session Gate) had already shipped and closed (`epic-1: done`, retro completed 2026-07-10). This was **not a regression** — it was the documented, intended behavior of Story 1.8.

**Evidence:**
- Story 1.8's own AC7 ("Explicit non-goals"): *"Do not add a 'remember me' / persistent-login feature... none are in scope for any epic."*
- Story 1.8's Dev Notes, written at implementation time, name this exact symptom and classify it as intentional: *"Known, accepted limitation, not a bug: ...A refresh on any protected route always bounces to `/login`, even if the cookie is technically still valid server-side. No AC/story requires persisting login across a refresh (AC7 explicitly excludes 'remember me'), so this is the safe, honest behavior..."*
- `frontend/src/lib/auth/AuthContext.tsx`'s pre-fix docstring repeated the same reasoning in code.

**Fix already implemented and shipped**, ahead of this course-correction: `GET /api/auth/me` (backend) + an `AuthContext` mount-time check (frontend) that silently restores session state from the existing HttpOnly cookie. Branch `fix/refresh-auth-persistence`, PR #83. Adversarially code-reviewed (Blind Hunter + Edge Case Hunter, `no-spec` mode) — 4 patches applied (login-vs-mount-check race guard, request timeout, 2 new tests for the refresh-persistence happy path and loading state, a type dedup), 3 items deferred, 3 dismissed as noise.

This proposal exists to reconcile the planning artifacts with what was actually built and reviewed, per this project's own "Project Context Maintenance" rule and its established pattern of formally superseding earlier decisions rather than leaving stale documentation standing.

## 2. Impact Analysis

### Epic Impact

- **Epic 1 (Authentication & Session Gate)** — already `done`, all 8 stories + retrospective complete. This is a post-closure amendment, not a re-opening of in-flight work.
- **Story 1.8 (Login Screen UI)** — its AC7 bullet on persistent login is now false as written and needs a superseded annotation, in the style already established elsewhere in this project's docs (e.g. `~~Still-open technical constraint~~ — Resolved 2026-07-07`). Its Dev Notes' "Known, accepted limitation, not a bug" paragraph needs the same treatment — it currently reads as still-true.
- **No other epic (2-5) impacted.** Checked all epic/story text for `1.8`, `remember me`, `persist` references relevant to session behavior — Epic 2-5 stories reference Story 1.8 only for its routing/redirect behavior (`/employee/content`, etc.), never for the refresh-logout behavior itself. No dependency chain touches this.
- No epic resequencing, no new epic, no epic invalidated.

### Artifact Conflicts

| Artifact | Conflict? | Action |
|---|---|---|
| **PRD** (`prd.md` §4.5, FR-13/FR-14, Session glossary) | **None.** FR-13/FR-14 require a valid, role-scoped session before data access — this fix doesn't weaken that gate, it only changes how the *frontend* re-establishes UI state from an already-valid cookie. The Session glossary entry doesn't currently state a position on refresh behavior either way. | No required change. Optional: could add one clause to the Session glossary entry noting session state survives a refresh, for future-reader clarity. |
| **Architecture** (`ARCHITECTURE-SPINE.md`, AD-6) | **None.** AD-6 ("server-side session/role/identity gate on every request") is unchanged — `GET /api/auth/me` reuses the existing `get_current_user` dependency, adding no new trust boundary. | No change needed. |
| **UI/UX specs** | **None found.** No wireframe/flow doc specs the post-refresh loading state; the only user-visible addition is a brief blank/loading render before redirect-or-restore, which isn't significant enough to require a spec update. | No change needed. |
| **`epics.md`** | **None.** Story 1.8's AC list in `epics.md` itself doesn't restate the "no remember me" exclusion — that language only exists in the elaborated story file. | No change needed. |
| **Story file** (`1-8-login-screen-ui.md`) | **Yes** — AC7 and Dev Notes directly contradict shipped behavior. | Amend both (see Section 4). |
| **`project-context.md`** | **Yes** — mandatory per its own maintenance rule; no entry exists yet for this fix or the code review that followed it. | Append entry (see Section 4). |
| **`sprint-status.yaml`** | **Yes** — its comment log narrates Story 1.8's full history including the AC7 exclusion (lines 73-78); leaving it un-appended makes the log inconsistent with reality. | Append dated comment line (see Section 4). No `development_status` entries change — Story 1.8 stays `done`, no epic/story added or removed. |
| **`deferred-work.md`** | **Yes** — the code review that hardened this fix deferred 3 items (non-401 error handling ambiguity, revoked-token-set growth rate, no rate limiting on `/me`) but had no story file to log them against (review ran in `no-spec` mode) and they were never written to this file. | Append entry (see Section 4). |

### Technical Impact

None beyond what's already shipped in PR #83 — this proposal is documentation-only. No further code changes are proposed here.

## 3. Recommended Approach

**Selected: Option 1 — Direct Adjustment (Minor scope).**

- **Option 1 (Direct Adjustment):** Viable and recommended. The code is already built, reviewed, and merged; the only remaining work is amending 4 documentation artifacts to match. Effort: **Low**. Risk: **Low**.
- **Option 2 (Rollback):** Not viable. Reverting would reintroduce the exact bug the user asked to fix, for no benefit — rejected.
- **Option 3 (MVP Review):** Not applicable. This doesn't change MVP scope, goals, or any FR — it reverses one exclusion bullet inside an already-closed epic. Rejected as unnecessary ceremony for a narrow, already-implemented change.

**Rationale:** The engineering work is done and already passed adversarial review. What's missing is purely the paper trail — bringing Story 1.8, `project-context.md`, `sprint-status.yaml`, and `deferred-work.md` back into sync with reality, following this project's own established pattern for superseding earlier decisions (strikethrough + dated "Superseded" note, never silently deleting the original text).

## 4. Detailed Change Proposals

### Story: `1-8-login-screen-ui.md`

**Section: AC7 — Explicit non-goals**

```
OLD:
- Do **not** add a "remember me" / persistent-login feature, password reset, or
  account registration — none of these exist in the backend (Story 1.4's mock
  credential store is fixed, five hardcoded demo accounts) and none are in
  scope for any epic.

NEW:
- ~~Do **not** add a "remember me" / persistent-login feature~~ — **Superseded
  2026-07-14**: user-requested fix for "refresh logs the user out" reversed
  this exclusion. Implemented via a new `GET /api/auth/me` endpoint +
  an `AuthContext` mount-time check (branch `fix/refresh-auth-persistence`,
  PR #83), outside the normal `bmad-create-story` pipeline — see
  `project-context.md`'s corresponding entry and this Sprint Change
  Proposal for full rationale and code-review findings. Password reset and
  account registration remain out of scope — only the persistent-session
  clause of this bullet was reversed.
```

**Rationale:** AC7 is the artifact of record that excluded this behavior; leaving it unedited means the story file actively contradicts shipped code.

**Section: Dev Notes — "Known, accepted limitation, not a bug"**

```
OLD:
- **Known, accepted limitation, not a bug**: there is no `GET /api/auth/me`
  (or equivalent) endpoint on the fixed backend contract, so the frontend's
  auth state is purely in-memory (`AuthContext`) with no way to silently
  verify an existing cookie on a hard page refresh. A refresh on any
  protected route always bounces to `/login`, even if the cookie is
  technically still valid server-side. No AC/story requires persisting
  login across a refresh (AC7 explicitly excludes "remember me"), so this
  is the safe, honest behavior rather than inventing a fake client-side
  session check — documented directly in `AuthContext.tsx`'s own docstring
  for the next person who touches it.

NEW:
- ~~Known, accepted limitation, not a bug~~ — **Superseded 2026-07-14**: a
  `GET /api/auth/me` endpoint now exists (reusing the existing
  `get_current_user` dependency), and `AuthContext` calls it on mount to
  restore session state from the cookie. `AuthContext.tsx`'s docstring was
  updated accordingly as part of the fix. See AC7's superseded note above
  and `project-context.md` for the full change record.
```

**Rationale:** This paragraph is the most detailed articulation of the old decision and the first place a future reader would look — it must not be left stating something now false.

### Project Context: `_bmad-output/project-context.md`

**New entry, appended to the running log** (following this file's existing per-decision bullet format):

```
- **Story 1.8 AC7's "no persistent session" exclusion reversed** (2026-07-14, user-requested, ad hoc fix outside the normal story pipeline). Root cause: Story 1.8 had deliberately excluded "remember me" as a non-goal, and its own Dev Notes named the resulting "refresh logs you out" behavior as an accepted limitation, not a bug — see that story's AC7/Dev Notes (now annotated as superseded). Fix: added `GET /api/auth/me` (reuses the existing `get_current_user` dependency, no new trust boundary — AD-6 unaffected) and an `AuthContext` mount-time check that restores session from the existing HttpOnly cookie; `RequireAuth` now waits on a `loading` status instead of assuming logged-out. Branch `fix/refresh-auth-persistence`, PR #83, merged after a `bmad-code-review` pass (no spec file — the fix predated this course-correction) that found and fixed a real race condition (a slow mount-time `/me` check could overwrite a just-completed login with a stale 401), added a request timeout to prevent an indefinite blank screen on a hung request, and added test coverage for the actual refresh-persistence happy path (previously untested — only the unauthenticated path had a test). 3 items deferred to `deferred-work.md` (non-401 errors from `/me` are treated identically to logged-out — a UX question, not a bug; `_revoked_tokens`' in-memory growth rate increases since `/me` now polls it on every page load; `/me` has no rate limiting, consistent with every other endpoint in this codebase). **Process note:** this fix shipped before a formal course-correction was run — `bmad-correct-course` was invoked after the fact (this Sprint Change Proposal) specifically to reconcile Story 1.8's text with the now-superseded AC7, since no new story was created for the fix itself.
```

**Rationale:** Mandatory per this file's own maintenance rule; also the only place that captures the full fix + review narrative in one spot, matching how every other decision in this log is recorded.

### Sprint Status: `_bmad-output/implementation-artifacts/sprint-status.yaml`

**New comment line**, appended after the existing Story 1.8 comment block (after line 78, the epic-1 retrospective entry), preserving the existing narrative-comment-log convention:

```
# Story 1.8 AC7 ("no persistent session") reversed 2026-07-14 (user-requested, post-closure) -- refreshing a protected route was logging users out by design (documented as an accepted limitation in 1.8's own Dev Notes), and TalentPilot asked for it fixed. Implemented via GET /api/auth/me + AuthContext mount-time restore (branch fix/refresh-auth-persistence, PR #83), code-reviewed and merged, then formally reconciled via bmad-correct-course (this proposal) since no new story was created for the fix. Story 1-8-login-screen-ui stays "done" -- no development_status change, no epic/story added or removed. Full detail: sprint-change-proposal-2026-07-14.md, project-context.md.
```

**Rationale:** No `development_status` values change (Story 1.8 remains `done`; no new story/epic exists), but the comment log is this file's mechanism for recording exactly this kind of post-hoc amendment, and every prior Story 1.8 event is already recorded there.

### Deferred Work: `_bmad-output/implementation-artifacts/deferred-work.md`

**New section, appended at the end of the file:**

```
## Deferred from: code review of fix/refresh-auth-persistence (2026-07-14)

- **Non-401 errors from `GET /api/auth/me` (network failure, 5xx) are treated identically to "not logged in"** [frontend/src/lib/auth/AuthContext.tsx] — the mount-time check's `.catch` sets `unauthenticated` regardless of *why* the request failed, silently bouncing a user with a perfectly valid session to `/login` on a transient backend blip or network error. The "correct" UX (retry? distinct error state? stay on a neutral loading screen?) is a product decision, not an unambiguous code fix, and matches this project's existing minimal-error-handling pattern elsewhere (no other endpoint in the app distinguishes transient failures from auth failures either). **How to apply:** if this becomes a real complaint (e.g. flaky networks bouncing legitimately-logged-in users), revisit with explicit product input on the desired fallback UX.
- **`_revoked_tokens`' in-memory growth/lookup volume increases** [backend/app/auth/service.py] — already a documented, accepted MVP limitation (unbounded set, wiped on restart, no pruning — see Story 1.5's original deferred item), but `GET /api/auth/me` now calls into the same lookup path on every page load/refresh for every open tab, increasing call volume against it. Correctness is unaffected; only the traffic profile against an already-accepted limitation changed. **How to apply:** revisit only if this limitation is ever revisited generally (e.g. moving to Redis-backed revocation) — no action needed on its own.
- **No rate limiting on `GET /api/auth/me`** [backend/app/auth/router.py] — consistent with every other endpoint in this codebase (none has rate limiting), so not a regression specific to this fix, but worth naming since `/me` will now fire automatically and unauthenticated-reachable on every hard refresh/tab open, unlike most existing endpoints which require an authenticated action to trigger. **How to apply:** if rate limiting is ever added project-wide, include `/me` in that pass — no standalone action needed.
```

**Rationale:** These 3 findings were triaged as `defer` during the `bmad-code-review` pass on PR #83, but that review ran in `no-spec` mode (the fix predated this course-correction, so no story file existed to log them against) and they were never persisted to this file, breaking the project's pattern of every deferred finding having a durable record.

## 5. Implementation Handoff

**Scope classification: Minor.** All proposed changes are documentation/artifact amendments to bring planning docs in line with already-shipped, already-reviewed code. No further application code changes are proposed.

**Handoff: Developer agent (direct implementation)** — apply the 4 file edits above (Story 1.8, `project-context.md`, `sprint-status.yaml`, `deferred-work.md`) directly; no PO/DEV backlog reorganization or PM/Architect replanning is needed.

**Success criteria:**
- Story 1.8's AC7 and Dev Notes no longer contradict actual shipped behavior — both carry a dated "Superseded" annotation pointing to this proposal.
- `project-context.md` reflects the fix and its review findings, satisfying this project's own mandatory-update rule.
- `sprint-status.yaml`'s comment log and `deferred-work.md` are consistent with what actually happened during the `bmad-code-review` pass on PR #83.
- No `development_status` values change; Epic 1 / Story 1.8 remain `done`.
