# Authentication Login Gate — Update Specification

## Change Summary

Add a prototype-level login gate to all 3 existing TalentPilot-AI prototypes. Each folder gets its own `login.html` (same shared design, replicated per folder like the rest of the shared/ layer) plus a `shared/auth.js` mock credential store. Existing protected pages gain a two-line session guard at the very top of `<head>` and a working `logout()` — nothing else about them changes. One data gap is closed (Morgan/Jordan get their own `employeeAssignments` entries) so "logs in as themselves" is true for all 4 demo employees, not just Casey/Sam.

## Before

- No identity check anywhere. Any of the 4 entry HTML files renders full content immediately for anyone who opens it.
- Scenario 02 hardcodes "Casey" in the header regardless of which employee's data is actually being viewed (`selected_employee_id` defaults silently to `emp-casey`).
- "Sign Out" is a `console.log` no-op in all 4 pages.

## After

### 1. `shared/auth.js` (new — identical content in all 3 folders)

```js
const DEMO_ACCOUNTS = [
  { email: 'rita@sailssoftware.com',   password: 'demo123', role: 'HR',       firstName: 'Rita',   lastName: 'the Referee' },
  { email: 'casey@sailssoftware.com',  password: 'demo123', role: 'Employee', employeeId: 'emp-casey',  firstName: 'Casey',  lastName: 'the Continuer' },
  { email: 'morgan@sailssoftware.com', password: 'demo123', role: 'Employee', employeeId: 'emp-morgan', firstName: 'Morgan', lastName: '' },
  { email: 'jordan@sailssoftware.com', password: 'demo123', role: 'Employee', employeeId: 'emp-jordan', firstName: 'Jordan', lastName: '' },
  { email: 'sam@sailssoftware.com',    password: 'demo123', role: 'Employee', employeeId: 'emp-sam',    firstName: 'Sam',    lastName: '' },
];

const TalentPilotAuth = {
  SESSION_KEY: 'talentpilot_auth_session',
  login(email, password) { /* looks up DEMO_ACCOUNTS, writes session to sessionStorage; if session.employeeId is set, also writes sessionStorage 'selected_employee_id' directly (not via PrototypeAPI, which isn't loaded on login.html); returns session or null */ },
  getSession() { /* reads + parses session from sessionStorage, or null */ },
  logout() { /* clears session, navigates to login.html */ },
  requireRole(role) { /* getSession(); if missing or role mismatch -> location.replace('login.html'); returns session */ },
};
window.TalentPilotAuth = TalentPilotAuth;
```

Session shape: `{ email, role, firstName, lastName, employeeId }`. Stored in `sessionStorage` (matches the existing `PrototypeAPI` pattern — session-scoped, no persistence beyond the browser tab, no backend).

### 2. `login.html` (new — one shared design, ×3 folders, only `HR_HOME`/`EMPLOYEE_HOME` differ)

- Same Tailwind CDN setup, same `talentpilot` color tokens and Inter font as every existing page — visually part of the same product, not a new design language.
- Centered card: "TalentPilot-AI" wordmark, email + password fields, Sign In button.
- Below the form, a visible "Demo accounts (password: demo123)" hint list — intentional for a mock/prototype gate, not a security decision that would apply in production.
- Two inline notice slots (hidden by default): wrong-credentials error, wrong-role-for-this-folder notice.
- Inline script: reads `?error=wrong_role` query param to show the notice on redirect-back; auto-continues past the form if a valid same-folder-role session already exists; on submit, calls `TalentPilotAuth.login()` and routes by `session.role` to `HR_HOME` or `EMPLOYEE_HOME` (whichever is defined for this folder), or shows the wrong-role notice if neither applies.

Per-folder destination config:
| Folder | HR_HOME | EMPLOYEE_HOME |
|---|---|---|
| 01-Ritas-Trust-Call-Prototype | `01.1-Skills-Dashboard.html` | *(none — notice shown)* |
| 02-Caseys-Resume-and-Watch-Prototype | *(none — notice shown)* | `02.1-Content-Discovery.html` |
| 03-Ritas-Assignment-and-Track-Prototype | `03-Skills-Dashboard.html` | *(none — notice shown)* |

### 3. Guard on existing protected pages (2 lines added at the top of `<head>`, nothing else touched)

```html
<meta charset="UTF-8">
<script src="shared/auth.js"></script>
<script>TalentPilotAuth.requireRole('HR');</script>
<!-- rest of <head> unchanged -->
```

(`'Employee'` for 02.1/02.2.) Runs before any body content paints — unauthorized visitors never see the dashboard, not even a flash of it.

### 4. Logout wiring (existing `handleSignOut()`, currently a no-op, in all 4 pages)

```js
function handleSignOut() {
  TalentPilotAuth.logout();
}
```

### 5. Scenario 02 header identity (01.1/03 need no change — only Rita/HR ever reaches them)

`02.1-Content-Discovery.html` and `02.2-Continue-Watching.html` currently hardcode the header avatar letter and name ("C" / "Casey") as static markup. Since Morgan/Jordan/Sam can now legitimately land here too, these two nodes get `id`s (`header-user-avatar`, `header-user-name`) so `initPage()` can set them from the session on load:

```js
const session = TalentPilotAuth.getSession();
document.getElementById('header-user-avatar').textContent = session.firstName[0];
document.getElementById('header-user-name').textContent = session.firstName;
```

No layout/style change — same element, same position, same look, just correct text.

### 6. Demo data gap closed — `02-.../data/demo-data.js`

`employeeAssignments` currently has entries only for `emp-casey` and `emp-sam`. Add matching-shape entries for `emp-morgan` and `emp-jordan` (reusing existing `content_catalog`/skills — no new skills/content invented) so every one of the 4 demo employees sees their own assignments post-login rather than silently falling back to Casey's list.

## Components

| Component | New/Changed | Behavior |
|---|---|---|
| `shared/auth.js` | New (×3) | Mock credential store + session helpers |
| `login.html` | New (×3) | Shared login UI; role-based redirect; wrong-role notice |
| Page `<head>` guard | Changed (×4 pages) | 2-line synchronous session/role check before paint |
| `handleSignOut()` | Changed (×4 pages) | Was no-op console.log → now clears session, returns to login |
| Header avatar/name (02.1, 02.2 only) | Changed | Static text → session-driven text, same visual output for Casey, correct for others |
| `demo-data.js` (folder 02) | Changed (additive) | New `employeeAssignments` entries for `emp-morgan`, `emp-jordan` |

## Responsive Behavior

`login.html` reuses the same `min-h-screen bg-gray-50 font-sans` body pattern and Tailwind utility classes as every other page in the prototype set; the centered card collapses to full-width on narrow viewports the same way existing cards do elsewhere in the product (no new breakpoint logic introduced). No responsive behavior changes on any existing page — guard/logout changes are invisible to layout.

## Acceptance Criteria

1. Opening `01.1-Skills-Dashboard.html`, `02.1-Content-Discovery.html`, `02.2-Continue-Watching.html`, or `03-Skills-Dashboard.html` directly with no session redirects to that folder's `login.html` before dashboard content renders.
2. Logging in as `rita@sailssoftware.com` / `demo123` on folder 01 or 03 lands on that folder's dashboard, unchanged from today's rendering.
3. Logging in as `casey@sailssoftware.com` / `demo123` on folder 02 lands on Content Discovery showing Casey's existing 3 assignments (unchanged).
4. Logging in as `morgan@sailssoftware.com` / `demo123` on folder 02 lands on Content Discovery showing **Morgan's own** assignments (not Casey's), and the header shows "Morgan" / "M", not "Casey" / "C".
5. Logging in as `casey@sailssoftware.com` on folder 01 (wrong role for this folder) succeeds as a login but shows the wrong-role notice instead of the dashboard; same for Rita on folder 02.
6. Wrong password/unknown email shows the credentials-error notice, no session written.
7. Clicking "Sign Out" on any protected page clears the session and returns to that folder's `login.html`; reopening the protected page afterward redirects to login again (no stale access).
8. No pixel/behavioral difference on any dashboard/content page for an already-authorized session, other than the header identity fix in 02.1/02.2 and the now-functional Sign Out.
9. HR's dashboard (01.1, 03) shows no new data field, label, or score beyond what exists today — the coaching-only/no-performance-evaluation boundary (`project-context.md`) holds because no new HR-visible surface was added.

---
*Design Solution spec — `wds-8-product-evolution` pipeline, Step [D]. Feeds Implement [I] and Acceptance Test [T].*
