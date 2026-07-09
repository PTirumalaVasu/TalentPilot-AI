# Authentication Login Gate — Scenario

## Target

Backfill a login/session gate in front of all 3 built prototypes. Flagged retroactively (2026-07-09) as a gap missed during the original brainstorming/Design Thinking phases — the Trigger Map (`_bmad-output/B-Trigger-Map/00-trigger-map.md`) defines Rita (HR) and Casey (Employee) as the two personas with distinct driving forces, but never surfaced "who is allowed to open this and see it" as a want/fear, so no login gate was ever scoped. Today anyone who opens any of the 3 HTML files sees full dashboard/employee content with no identity check at all.

This matters for two of the already-locked driving forces, not just as new scope:
- **Rita's fear** (Trigger Map DF0): "A dashboard that looks trustworthy but isn't." An ungated dashboard anyone can open undermines that trust before she even reads a row.
- **Casey's fear** (Trigger Map DF1): "Feeling watched/surveilled." Combined with the PRFAQ's locked **coaching-only, never-performance-evaluation** privacy decision, an ungated Employee view means there's no boundary enforcing who can even see progress data in the first place — the policy exists in decisions but not in the product.

## Current State

- Double-click any of the 3 prototype HTML files → dashboard/content renders immediately, no identity check.
- Each prototype's `data/demo-data.js` hardcodes a single `currentUser` (Rita in 01 & 03, Casey in 02); Scenario 02's employee-switching (`selected_employee_id`) exists in `PrototypeAPI` but nothing in the UI lets a specific employee assert "this is me" — it silently defaults to `emp-casey`.
- No two-role distinction is enforced anywhere; HR and Employee views are only separated by which HTML file you happen to open.

## Desired State

- Opening any prototype's entry page with no active session redirects to that folder's `login.html` first.
- One shared login page design (same markup/behavior), replicated per folder like the rest of the shared/ layer (`demo-data.js`, `prototype-api.js` are already duplicated per folder — this follows the same accepted convention, see `PROTOTYPE-ROADMAP.md`).
- A small demo account list — Rita (HR) and Casey/Morgan/Jordan/Sam (Employee, matching the existing 4 demo employees) — each with mock email+password credentials.
- On successful login, the session's role determines the destination: HR → that folder's dashboard page; Employee → that folder's content-discovery page. Since each folder physically only contains ONE role's view (01/03 = HR only, 02 = Employee only), logging in with the "other" role succeeds (valid credentials) but surfaces an inline notice on the login page rather than a broken redirect, pointing to the right folder.
- Each employee's own name/ID drives what they see (Morgan sees Morgan's assignments, not Casey's) — not a single shared "Employee" demo identity.
- Existing dashboard/content pages render **exactly as they do today** once past the gate — zero visual/behavioral change to anything other than the "Sign Out" button (currently a no-op stub) becoming functional, which is inherent to shipping auth, not a redesign.
- HR's authorized view still shows only what it always showed (provenance-labeled, coaching-framed progress) — the auth boundary itself must not introduce any new surface that reads as performance evaluation.

## User Journey

**Entry point:** Someone opens a prototype folder's HTML file (double-click, `file://`) to demo a scenario.

**Proposed flow:**
1. Land on any protected page (e.g. `01.1-Skills-Dashboard.html`) → no session found → immediately redirected to `login.html` (same folder) before any dashboard content paints.
2. `login.html` shows the TalentPilot-AI login form (email + password) plus a visible demo-account/password hint list (this is a mock prototype gate, not a production credential store — visibility is intentional so anyone testing the prototype can self-serve).
3. Enter a valid demo account's credentials → session written (role, name, employeeId if applicable).
   - HR account in an HR folder (01 or 03) → redirected straight to that folder's dashboard.
   - Employee account in the Employee folder (02) → redirected to Content Discovery, seeing **that employee's own** assigned videos.
   - Wrong-role-for-this-folder (e.g. an Employee account on folder 01) → login succeeds but an inline message explains this folder's demo doesn't include that role's view, and names the folder that does.
4. Signing out clears the session and returns to `login.html`.
5. Re-opening a protected page directly (bookmark, refresh) with no session, or a session for the wrong role, bounces back to `login.html` the same way — no silent bypass.

## Success Criteria

- All 4 protected pages (01.1, 02.1, 02.2, 03) refuse to render without a valid session for the correct role.
- Each of the 4 demo employees can log in as themselves and see their own assigned content, not Casey's by default.
- No existing page's layout, copy, or interaction changes for an already-authorized user — a before/after screenshot of the dashboard content area should be pixel-identical.
- HR's dashboard still only shows coaching-framed provenance labels, nothing new that reads as a performance score/ranking.

## Scope

- **Pages affected:** `login.html` (new, ×3 folders), `01.1-Skills-Dashboard.html`, `02.1-Content-Discovery.html`, `02.2-Continue-Watching.html`, `03-Skills-Dashboard.html` (guard + logout wiring only).
- **Components touched:** New `shared/auth.js` (×3 folders, mock credential store + session helpers). Existing header user-menu in 02.1/02.2 becomes session-driven instead of hardcoded "Casey" (needed so a non-Casey employee login shows their own name — see Design spec).
- **Data changes:** `02-Caseys-Resume-and-Watch-Prototype/data/demo-data.js` gains `employeeAssignments` entries for `emp-morgan` and `emp-jordan` (currently only `emp-casey`/`emp-sam` exist, so those two would otherwise silently fall back to Casey's list post-login — contradicts "logs in as themselves"). Additive only, no existing entries touched.
- **Risk level:** Medium (behavior change: pages that used to render unconditionally now gate on session) but zero structural/visual change to authorized content.

## Out of Scope (Won't, per confirmed MVP boundary)

- No Manager/Team Lead role or any role beyond HR/Employee.
- No production auth stack (JWT, real database, password hashing, backend) — this is a prototype-level, client-side, mock-credential gate only, consistent with the rest of the prototype layer having no backend at all.
- No change to what data HR's dashboard displays or how progress is framed — the coaching-only/no-performance-evaluation boundary is enforced by not adding any new HR-visible surface, not by building a new permissions UI.

---
*Scope Improvement scenario — `wds-8-product-evolution` pipeline, Step [S]. Feeds `evolution/specs/authentication-login-gate.md`.*
