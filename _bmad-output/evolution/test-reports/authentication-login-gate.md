# Test Report: Authentication Login Gate

## Summary

9/9 acceptance criteria passed after one real bug found-and-fixed during testing. Verified by actually driving all 3 prototype folders in a real browser (Playwright/Chromium against the `file://` HTML, no server), not by reading the code.

## Method

Fresh browser context per folder (no cross-folder session bleed). Each flow was driven through real form fills/clicks against the rendered page; screenshots captured at each major state.

## Results

| # | Criterion | Steps | Expected | Actual | Pass? |
|---|-----------|-------|----------|--------|-------|
| 1 | No-session redirect | Open `01.1-Skills-Dashboard.html` / `02.1-Content-Discovery.html` / `03-Skills-Dashboard.html` directly, no session | Redirect to that folder's `login.html` before content paints | All 3 redirected correctly | Y |
| 2 | HR login unchanged rendering | Log in `rita@sailssoftware.com`/`demo123` on folders 01 & 03 | Dashboard renders exactly as before (6 rows on 01, header, table) | Confirmed — 6 rows, all data/labels match pre-auth `demo-data.js`; screenshot attached | Y |
| 3 | Employee login → own data | Log in `morgan@sailssoftware.com`/`demo123` on folder 02 | Content Discovery shows Morgan's own 1 assignment (Python Basics, 100%), header "Morgan"/"M" | **Initially FAILED** — see Issues Found #1. After fix: employee-name card = "Morgan", skills count = 1, header = "Morgan"/"M" | Y (after fix) |
| 4 | Casey unaffected | Log in `casey@sailssoftware.com`/`demo123` on folder 02 | Casey's original 3 assignments, header "Casey"/"C", unchanged from pre-auth | Confirmed — skills count 3, employee-name card "Casey the Continuer" | Y |
| 5 | Wrong-role notice | Log in `casey@...` on folder 01 (HR-only); log in `rita@...` on folder 02 (Employee-only) | Login succeeds but shows wrong-role notice, no dashboard access | Both directions confirmed — stayed on `login.html`, notice visible | Y |
| 6 | Invalid credentials | Submit wrong password on folder 01's login | Inline "Incorrect email or password" notice, no navigation | Confirmed — notice visible, URL still `login.html` | Y |
| 7 | Sign Out clears session | Sign out from folder 01 and folder 02 (via `02.2` page) | Returns to `login.html`; reopening the protected page afterward redirects to login again | Confirmed both folders; reopening `01.1` after sign-out redirected to login again (no stale access) | Y |
| 8 | Zero regression on existing flows | Folder 03's 3-step "+ New Assignment" flow; folder 01's `?demo_state=modal-loading` query-param path | Both still work exactly as before, guard doesn't interfere | Confirmed — assignment created, toast "✓ Skill assigned to Casey — Advanced SQL" shown, row added; demo-state modal still opens | Y |
| 9 | No new HR-visible surface | Compare folder 01/03 dashboard content before/after | No new field, label, or score added | Confirmed — same 4 columns, same status/progress rendering, nothing added | Y |

## Issues Found

1. **[Fixed during this session] Employee login silently showed the wrong employee's data.** Root cause: `TalentPilotAuth.login()` originally tried to sync the selected employee via `window.PrototypeAPI.setSelectedEmployee(...)`, but `login.html` never loads `shared/prototype-api.js` — so that call silently no-op'd (`window.PrototypeAPI` was `undefined`), and `PrototypeAPI.getSelectedEmployeeId()`'s hardcoded `'emp-casey'` fallback won every time. Logging in as Morgan showed Casey's employee-info-card and Casey's 3 videos, while only the header (which reads the auth session directly, not `PrototypeAPI`) correctly said "Morgan" — a visible inconsistency within the same page. **Fix:** `login()` now writes the `selected_employee_id` sessionStorage key directly (the same key `PrototypeAPI` reads), removing the cross-script dependency entirely. Re-verified after the fix — Morgan now correctly sees her own 1 assignment throughout.

## Findings unrelated to this change (pre-existing, not introduced by the auth gate)

- ⚠️ The app's own floating "Dev Mode" toggle button (`position: fixed; top:20px; right:20px; z-index:9999`) visually overlaps the header's user-menu button in the top-right corner at the default viewport (see screenshot `01-02-dashboard-after-login.png` — only a sliver of the avatar circle peeks out from behind it). A literal mouse click there hits Dev Mode instead of opening the Sign Out menu. This predates the auth work and isn't something this change touches, but it's more consequential now that Sign Out is a real, load-bearing action rather than a no-op — worth a follow-up fix (raise the user-menu's z-index or reposition the dev-mode button).
- 🔍 The Provenance Drill-Down modal (01.2, folders 01 & 03) has no click handler wired to open it from a normal loaded-state row — it's only reachable via the `?demo_state=modal-loading`/`?demo_state=modal-error` query-param paths used for spec/demo review. Confirmed this still works unchanged after adding the guard, but the "click a row to drill down" path itself doesn't exist in the shipped code, guard or no guard.

## Recommendation

**Pass.** All 9 acceptance criteria hold; the one real defect found during testing was fixed and re-verified in the same session. The two unrelated findings above are pre-existing and out of this scenario's scope — logged here for visibility, not blocking.

---
*Acceptance Test report — `wds-8-product-evolution` pipeline, Step [T].*
