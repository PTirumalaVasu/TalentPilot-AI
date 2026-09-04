# Story HR-Dashboard.12: API Keys View + Add Skill Gate

**View**: HR Dashboard — new fourth view (Dashboard / Skills / API Keys), reached from the Skills tab
**Implements**: `_bmad-output/planning-artifacts/epics/epic-automated-content-discovery.md` — Story 1 (Configure API Keys Before Content Search Is Available)

---

## ⚠️ Mockup, Not a Real Security Pattern

This screen exists so the "gate the Add Skill button until keys are configured" UX can be reviewed. **A real implementation must never hold API keys in a browser-editable form** — visible red banner on the screen itself says so, and the epic's Story 1 Notes explain why (keys are operational secrets; belong server-side, same as this codebase's existing `YOUTUBE_API_KEY` pattern). `apiKeys` here is a plain in-memory object, lost on refresh, never sent anywhere.

---

## 📋 What Was Built

**Gate on "+ Add Skill"**: button now starts `disabled` in the static HTML. A status line next to the Add Skill heading (`⚠ API keys not configured` / `✓ API keys configured`) and a disabled-reason caption next to the button itself explain why, plus a "Configure API Keys →" link to the new screen.

**API Keys screen**: two password-type inputs (YouTube, Udemy), each with a live status label (Not configured / Configured — never re-displays the value), a Save button, and "← Back to Skills". Reachable only from the Skills view (no dedicated top-level nav item) — `switchMainView('api-keys')` keeps "Skills" highlighted in the header since this is a sub-screen of it.

**Gate logic**: `apiKeysConfigured()` requires **both** keys non-empty (plural "api keys" in the user's request read as both, not either). `updateAddSkillGate()` re-evaluates and updates the button/status/reason every time keys are saved. `addNewSkill()` also checks `apiKeysConfigured()` defensively, even though a native `disabled` button already blocks clicks.

**Clearing keys re-disables**: since the gate reads live `apiKeys` state (not "was ever configured"), saving an empty value back over a previously-set key disables Add Skill again — matches the epic's explicit AC on this point.

---

## ✅ Acceptance Criteria (traced to the epic's Story 1)

| # | Criterion | Result |
|---|---|---|
| 1 | Add Skill disabled by default, with visible reason + link | ✓ |
| 2 | API Keys screen shows one input + status per integration | ✓ |
| 3 | Saving both non-empty keys enables Add Skill | ✓ `updateAddSkillGate()` |
| 4 | Clearing a key back to empty re-disables | ✓ status read live each time |
| 5 | Key values never re-displayed once saved | ✓ inputs show status text only, not the value |
| 6 | No `hidden`+`flex` bug, no duplicate IDs, no syntax errors | ✓ full-file scan clean |

### User-Evaluable (Qualitative)

- [ ] Confirm "+ Add Skill" is genuinely disabled (not just styled to look disabled) on first load
- [ ] Configure both keys, confirm the button enables and the status flips to green
- [ ] Clear one key and re-save, confirm the button disables again

---

## 📊 Status

**Status**: ✅ Built, pending user review
**Started / Completed**: 2026-09-03

## 🔄 Update: per-key status notification banner

User asked for a notification at the top listing each key's status individually — green if configured, red if not — rather than only a single combined status line. Added `apiKeysStatusBannerHtml()` / `renderApiKeysStatusBanners()`: a banner (green-bordered "✓ All API keys configured" or red-bordered "⚠ Some API keys are not configured") containing one pill per provider (`✓ YouTube configured` in green / `✗ YouTube not configured` in red, same for Udemy). Rendered at the top of **both** the Skills tab and the API Keys screen — updates live via the same `updateAddSkillGate()` call already triggered on init and after every save, no new event wiring needed.

## 🔄 Update: per-admin key storage (requirements only, no prototype change)

User requested the real design store keys in a new database table, scoped per logged-in admin user (not one shared key). Epic's Story 1 rewritten with the actual table design (`admin_api_keys`, FK to `employees.id`, encrypted at rest, per-admin gate) — see `epic-automated-content-discovery.md`.

**Not reflected in this prototype's code**, and deliberately so: this is a static HTML mockup with exactly one logged-in user per scenario (no login-switching), so "per-admin" has nothing to demo against — the existing single in-memory `apiKeys` object already behaves as "the current session's admin's keys" trivially, since there's only ever one session. Flagged in the epic's Notes as a prototype tooling limitation, not a sign the requirement was dropped.
