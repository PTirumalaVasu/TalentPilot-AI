---
story_key: 1-8-login-screen-ui
baseline_commit: 0134487
---

# Story 1.8: Login Screen UI (Frontend)

**Epic:** 1 (Authentication & Session Gate)
**Status:** done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an **HR Admin or Employee**,
I want a real login screen that authenticates against the backend session gate,
so that I can reach my role-appropriate area of the application through the actual production auth flow, not a prototype mock.

## Scope Notes (read before starting)

1. **This story was added retroactively (2026-07-10), after Stories 1.1–1.7 (backend) and 4.0/2.1 (frontend/backend) were already done.** Epic 1's original 7 stories built a complete backend auth stack (JWT, cookies, login/logout endpoints, protected-router gate, DB schema) but **no story ever built the actual login page**. Story 1.4's own Dev Notes explicitly said so: *"no frontend exists yet, so the epic's 'redirected to role-appropriate entry point' is out of scope — backend only returns `role` in the response."* This story closes that gap.

2. **`frontend/` exists but is not an app yet.** Story 4.0 created `frontend/package.json`, `vite.config.ts`, etc. solely to host the YouTube player component (`VideoPlayer.tsx`, `lib/adapters/*`, `lib/services/captureService.ts`). Verify before starting:
   - `frontend/index.html` is currently a **hand-written vanilla-JS demo page** (inline `<style>`, inline `<script type="module">` importing `youtubeAdapter.ts`/`captureService.ts` directly). It does **not** contain a `<div id="root">` or load `main.tsx`. `react`/`react-dom` are listed in `package.json` but nothing in the repo actually renders a React tree today.
   - There is no `main.tsx`, `App.tsx`, router, Tailwind config, or `components.json` (shadcn) anywhere in `frontend/`.
   - `frontend/package.json` dependencies today: `react`, `react-dom`, `axios` only. Dev deps: testing-library, vitest, jsdom/happy-dom, TypeScript, vite. **No `react-router-dom`, no `tailwindcss`, no `react-hook-form`/`zod`.**

3. **Do not delete the Story 4.0 demo.** It's a `done`, code-reviewed story's working artifact (32/32 tests passing, manual YouTube playback + capture-service demo). Converting `index.html` into a real Vite React entry point means moving this demo's content into a component/route (e.g. `src/pages/dev/VideoPlayerDemo.tsx` mounted at `/dev/video-player-demo`) rather than overwriting it silently. Confirm the demo still loads and functions at its new route before marking this story done.

4. **The static prototype `login.html` (×3, under `_bmad-output/E-Development/*/`) is not a code source for this story.** It's a `sessionStorage`-only, client-side mock built by a separate pipeline (`_bmad-output/evolution/scenarios/authentication-login-gate.md`) with **no backend at all** — explicitly scoped there as prototype-only, never meant to be adapted into production code. You may look at it for visual/copy inspiration only (wordmark, centered-card layout) — the actual auth mechanism must call the real backend built in Stories 1.2–1.6.

5. **The backend is done and its contract is fixed — do not change it.** Exact contract (verified by reading the actual code, not just the epic text):
   - `POST /api/auth/login` — body `{email: string, password: string}` → `200 {role: "HR_ADMIN" | "EMPLOYEE", user_id: string}` + `Set-Cookie` (HttpOnly, `SameSite=Lax`, name = `SESSION_COOKIE_NAME` env var, default `access_token`). On bad credentials → `401 {status:"error", code:"HTTP_ERROR", message:"Email or password incorrect", timestamp}` (same message for both wrong-email and wrong-password — do not try to distinguish them client-side).
   - `POST /api/auth/logout` — no body, no auth dependency required → `204`, clears the cookie.
   - Every other router (`assignments`, `content`, `progress`, `dashboard`) is mounted with `Depends(get_current_user)` at the router level (Story 1.6) — any request to them without a valid session cookie returns `401` in the same `{status, code, message, timestamp}` shape before any route logic runs.
   - CORS: `backend/app/core/config.py`'s `ALLOWED_ORIGINS` defaults to `http://localhost:5173` (matches Vite's default dev port) with `allow_credentials=True` already configured in `main.py` — required for the cookie to be accepted on cross-origin (`:5173` → `:8000`) requests. Frontend axios calls **must** set `withCredentials: true`, or the cookie will never be sent/stored.
   - `COOKIE_SECURE` defaults `True` in `.env.example` but `backend/.env` (local, gitignored, created during Story 1.5) sets it `False` for local plain-HTTP dev — a real browser will silently refuse to send a `Secure` cookie over `http://`. If `backend/.env` doesn't exist in your checkout, `uvicorn` fails fast with a clear message (Story 1.1) — copy `.env.example` and set `COOKIE_SECURE=False` before live-testing login in a browser.

6. **No real HR Dashboard or Content Discovery page exists yet** (Epic 5 and Epic 2/2.5 respectively, both still `backlog`). The post-login redirect targets are **stub placeholder routes/pages only** in this story (e.g. a page that just renders "HR Dashboard — coming in Epic 5" / "Content Discovery — coming in Epic 2") — do not attempt to build those real pages here, that's scope creep into other epics' stories.

## Acceptance Criteria

### AC1 — Frontend app-shell foundations installed and wired

**Given** `frontend/` has no routing, styling framework, or rendered React app today
**When** this story is implemented
**Then**:
- `react-router-dom` is added and a router is configured in `App.tsx`
- Tailwind CSS (+ PostCSS/Autoprefixer) is installed and configured (`tailwind.config.js`, `postcss.config.js`, a base stylesheet imported once at the entry point)
- shadcn/ui is set up (`components.json` + `src/lib/utils.ts` `cn()` helper at minimum); hand-roll the small set of primitives this story needs (Button, Input, Label, Card, Form-error-text) in shadcn's own conventions (Tailwind classes + `class-variance-authority`-style variants) if the `shadcn` CLI's network-dependent `init`/`add` commands aren't usable in this sandbox — document whichever path was taken
- `react-hook-form`, `zod`, and `@hookform/resolvers` are added (`axios` is already a dependency — reuse it, do not add a second HTTP client)
- `frontend/index.html` becomes a standard Vite entry (`<div id="root"></div>` + `<script type="module" src="/src/main.tsx">`); `src/main.tsx` mounts `<App />`

**And** the pre-existing Story 4.0 demo content (video ID input, resume-position input, live metrics, the `YouTubeAdapter`/`CaptureService` wiring) is preserved as a component rendered at a dedicated route (e.g. `/dev/video-player-demo`), not deleted — confirm it still loads and the manual "Load Video"/"Flush Samples Now" controls still work after the move

### AC2 — `/login` route renders a validated form

**Given** I navigate to `/login`
**When** the page renders
**Then** I see:
- TalentPilot-AI wordmark/title
- Email field, Password field, Submit button
- Client-side validation via React Hook Form + Zod (non-empty email in a valid email shape, non-empty password) — inline field errors, not just a disabled button, and validation failure never fires the network request

### AC3 — Successful login redirects by role

**Given** I submit valid credentials on `/login`
**When** the form submits
**Then**:
- `axios.post('/api/auth/login', {email, password}, {withCredentials: true})` is called
- On `200`, the response body's `role` determines the redirect: `HR_ADMIN` → the HR Dashboard stub route, `EMPLOYEE` → the Content Discovery stub route
- No token/role is stored in `localStorage`/`sessionStorage` for auth purposes — the HttpOnly cookie set by the backend **is** the session; the frontend only needs the `role` value transiently to decide the redirect target (it MAY keep `role`/`user_id` in memory/context for UI display purposes like a header greeting, but must not treat that in-memory copy as the source of truth for "am I logged in" — every protected-route check re-verifies against the backend, per AC5)

### AC4 — Failed login shows the exact backend error

**Given** I submit invalid credentials
**When** the backend responds `401` with `{status:"error", code:"HTTP_ERROR", message:"Email or password incorrect", timestamp}`
**Then** the form displays "Email or password incorrect" verbatim (render the backend's `message` field, do not hardcode a separate client-side copy that could drift from it) and does not indicate which field was wrong

**And** a network/5xx failure shows a distinct, generic "Something went wrong, please try again" state (do not conflate it with the credentials error)

### AC5 — Protected-route gate: no flash of protected content

**Given** any frontend route other than `/login` (including the two stub post-login pages and the moved `/dev/video-player-demo`)
**When** the route is visited without a valid session, or an API call it makes returns `401`
**Then** the user is redirected to `/login` before protected content paints — implement this as a route wrapper/guard (e.g. a `<RequireAuth>` element wrapping protected `<Route>`s) **plus** a shared axios response interceptor that catches any `401` from any request and redirects, so a session that expires *while* a protected page is already open is caught too, not just on initial navigation

**And** this mirrors Story 1.6's backend guarantee ("no flash of protected content") on the frontend side — there is no version of any protected page that briefly renders real content before the redirect fires

### AC6 — Sign out clears session and blocks back-navigation

**Given** I am on a protected route with a valid session
**When** I click "Sign Out"
**Then** the frontend calls `POST /api/auth/logout` (204), clears any in-memory auth/role state, and navigates to `/login`

**And** pressing the browser back button afterward does not show the previously-open protected page — the route guard re-checks auth on every navigation (it does not use `bfcache`-restorable component state as its source of truth), so a back-navigation into a protected route re-runs the same 401-detection path as AC5 and redirects again

### AC7 — Explicit non-goals (do not build these here)

- Do **not** adapt or reference the prototype `login.html`/`shared/auth.js` mock (`_bmad-output/E-Development/*/`) as an implementation source — it has no backend and a different (sessionStorage) session model entirely.
- Do **not** build the real HR Dashboard (Epic 5) or real Content Discovery (Epic 2, Story 2.5) pages — stub placeholders only.
- ~~Do **not** add a "remember me" / persistent-login feature~~ — **Superseded 2026-07-14**: user-requested fix for "refresh logs the user out" reversed this exclusion. Implemented via a new `GET /api/auth/me` endpoint + an `AuthContext` mount-time check (branch `fix/refresh-auth-persistence`, PR #83), outside the normal `bmad-create-story` pipeline — see `project-context.md`'s corresponding entry and `sprint-change-proposal-2026-07-14.md` for full rationale and code-review findings. Password reset and account registration remain out of scope — only the persistent-session clause of this bullet was reversed.

## Tasks / Subtasks

- [x] Task 1: Frontend app-shell foundations (AC: #1)
  - [x] Install `react-router-dom`, `tailwindcss`, `postcss`, `autoprefixer`, `react-hook-form`, `zod`, `@hookform/resolvers`
  - [x] `tailwind.config.js` + `postcss.config.js` + a single imported base stylesheet (e.g. `src/index.css` with Tailwind directives)
  - [x] shadcn/ui setup: `components.json`, `src/lib/utils.ts` (`cn()` helper); hand-build `Button`, `Input`, `Label`, `Card` primitives if the CLI can't reach the network in this sandbox (document which path was used)
  - [x] Rewrite `frontend/index.html` to the standard Vite React entry (`<div id="root">` + `main.tsx` script tag)
  - [x] Create `src/main.tsx` (mounts `<App />`) and `src/App.tsx` (router setup)
  - [x] Move the Story 4.0 demo page content into `src/pages/dev/VideoPlayerDemo.tsx`, mounted at `/dev/video-player-demo`; verify it still loads/functions

- [x] Task 2: Login page (AC: #2, #4)
  - [x] `src/pages/Login.tsx` — form UI (email, password, submit button, inline error area)
  - [x] Zod schema for email/password validation, wired via `@hookform/resolvers/zod` into `react-hook-form`
  - [x] Render the backend's literal `message` field on `401`; a separate generic message for network/5xx errors

- [x] Task 3: Auth API client + login flow (AC: #3)
  - [x] `src/lib/api/authApi.ts` — `login(email, password)` and `logout()` functions using the existing `axios` dependency, `withCredentials: true` on every call
  - [x] A shared axios instance (base URL matching the existing Vite `/api` proxy to `http://localhost:8000`) so all future modules (Epic 2+) reuse the same `withCredentials` config instead of each hand-rolling it
  - [x] On successful login, redirect by `role` to the HR Dashboard stub or Content Discovery stub route

- [x] Task 4: Protected-route guard + 401 interceptor (AC: #5, #6)
  - [x] `src/lib/auth/RequireAuth.tsx` (or equivalent) wrapping protected `<Route>` elements, redirecting to `/login` if no known-good session
  - [x] Axios response interceptor: any `401` from any request triggers the same redirect-to-`/login` path, for sessions that expire mid-visit
  - [x] `Sign Out` control calling `authApi.logout()`, clearing in-memory auth state, navigating to `/login`
  - [x] Verify back-button after sign-out does not resurface protected content (the guard re-checks per navigation, not per mount-once)

- [x] Task 5: Stub destination pages (AC: #3, #6)
  - [x] `src/pages/hr/DashboardStub.tsx` — minimal placeholder ("HR Dashboard — Epic 5"), includes Sign Out control
  - [x] `src/pages/employee/ContentDiscoveryStub.tsx` — minimal placeholder ("Content Discovery — Epic 2"), includes Sign Out control

- [x] Task 6: Tests
  - [x] Login form: renders, client-side validation blocks empty/malformed submissions (no network call fires), submits correct payload on valid input
  - [x] Login flow: `200` response redirects by role (both `HR_ADMIN` and `EMPLOYEE` cases); `401` response renders the exact backend message; network-error case renders the generic message
  - [x] Protected-route guard: unauthenticated visit to a protected route redirects to `/login` with no protected content ever rendered (assert on render output, not just final URL); a `401` from a simulated in-page API call while "logged in" also redirects
  - [x] Sign out: calls the logout endpoint, clears state, redirects to `/login`
  - [x] Video player demo route: still renders/functions after the `index.html` → route migration (smoke test, reusing Story 4.0's existing test patterns where possible)

### Review Findings

- [x] [Review][Decision] `react-router-dom` installed at v7.18.1, spec named v6.x, no documented deviation — resolved 2026-07-10: **accept v7, document it** (not downgrade). Library/Framework Requirements said "latest stable v6.x"; `frontend/package.json:20` has `^7.18.1` with zero rationale recorded, unlike the Zod v4 deviation which this story's own Dev Agent Record explicitly justifies. Basic Router/Routes/Navigate/useNavigate/useLocation APIs used here are stable across v6→v7 and all 49 tests pass. Converted to a patch item below (add Dev Notes justification, matching the Zod v4 precedent).

- [x] [Review][Patch] Document `react-router-dom` v7 deviation in Dev Notes, matching the Zod v4 precedent [_bmad-output/implementation-artifacts/1-8-login-screen-ui.md Dev Notes] — fixed: added "`react-router-dom` v7 installed, not v6" Dev Notes entry
- [x] [Review][Patch] AC1: missing "Form-error-text" shared primitive [frontend/src/pages/Login.tsx:65-92] — fixed: new `frontend/src/components/ui/form-error-text.tsx`, wired into all 3 error sites in Login.tsx
- [x] [Review][Patch] AC5/Task 6: no test exercises the real end-to-end 401 → interceptor → redirect chain [frontend/src/tests/RequireAuth.test.tsx:75-86, frontend/src/tests/client.test.ts] — fixed: added a new RequireAuth.test.tsx case that invokes the real client.ts interceptor's captured rejected-handler and asserts the redirect through AuthProvider + RequireAuth
- [x] [Review][Patch] Sign-out has no try/catch around `await logout()`, can strand user in false-authenticated state [frontend/src/pages/hr/DashboardStub.tsx:10-14, frontend/src/pages/employee/ContentDiscoveryStub.tsx:10-14] — fixed: wrapped in try/catch/finally so client-side sign-out always proceeds regardless of the logout request's outcome; regression tests added to both stub test files
- [x] [Review][Patch] `RequireAuth`'s captured `location.state.from` is dead — Login never reads it, deep-link return path is lost [frontend/src/lib/auth/RequireAuth.tsx:16, frontend/src/pages/Login.tsx:38] — **attempted, then reverted after live-browser testing caught a real regression it introduced**: wiring `Login.tsx` to read `location.state.from` initially worked in unit tests (mocked navigate, no real router timing) but broke in a live end-to-end run — see "Live manual verification" note below for the root cause and why this was reverted rather than fixed forward. `location.state.from` remains dead code, now deliberately (not by oversight).
- [x] [Review][Patch] Dead `test` config block in `vite.config.ts`, superseded by `vitest.config.ts` [frontend/vite.config.ts:30-34] — fixed: removed, replaced with an explanatory comment
- [x] [Review][Patch] Login's 401 handler has no fallback if `data.message` is missing, silently renders no error [frontend/src/pages/Login.tsx:40-41] — fixed: `?? GENERIC_ERROR` fallback
- [x] [Review][Patch] `VideoPlayerDemo`'s visibility/beforeunload listeners never removed on unmount [frontend/src/pages/dev/VideoPlayerDemo.tsx:48-53] — fixed: listener refs tracked and removed on unmount and before re-registering on reload
- [x] [Review][Patch] `ContentDiscoveryStub` has no dedicated sign-out test, asymmetric with `DashboardStub` [frontend/src/tests/ — missing ContentDiscoveryStub.test.tsx] — fixed: added, mirroring DashboardStub.test.tsx
- [x] [Review][Patch] Email/password fields aren't trimmed before Zod validation [frontend/src/pages/Login.tsx:14-17] — fixed: `.trim()` added to both schema fields

**Verification after patches:** `tsc --noEmit` clean; `npx vitest run` 53/53 passing (was 49; +4 from new/expanded tests); `npm run build` succeeds.

**Live manual verification (2026-07-10, post-review):** full stack launched for real (`docker compose up -d postgres`, `uvicorn app.main:app` on :8000, `npm run dev` on :5173) and driven end-to-end with a headless-browser script (unauth redirect, wrong-password message, HR_ADMIN login → dashboard, sign-out, EMPLOYEE login → content, back-button-after-signout, empty-submit validation, dev video-player-demo route) — all 8 checks passed on the final run, screenshots captured. This live run caught a real regression the unit-test suite missed: the `location.state.from` wiring above (deep-link return-to-origin after login) worked in isolated unit tests but broke live — `AuthProvider` sits above `BrowserRouter` in `App.tsx`, so when a sign-out handler calls `signOut()`, `RequireAuth` (still mounted at that instant) re-renders reactively and fires its *own* `<Navigate>` with `state:{from: <the page just left>}` — a real router/context re-render race, not fixable by reordering `navigate()`/`signOut()` (tried both orders live; identical result). Since this "from" feature was a low-severity, non-AC-required nice-to-have, it was reverted rather than chased further: `Login.tsx` no longer reads `location.state`, always redirects to the role default. Re-verified 53/53 tests + `tsc` + `npm run build` clean after the revert, then re-ran the live browser script to confirm the actual bug (wrong post-login destination) was gone.

- [x] [Review][Defer] No guard against an already-authenticated user hitting `/login` or an unmatched route [frontend/src/App.tsx:14,39] — deferred, not required by any AC; low value until Epic 2/5's real destination pages exist
- [x] [Review][Defer] `loadPlayer()` double-click race (orphaned callback + duplicate script tag) [frontend/src/pages/dev/VideoPlayerDemo.tsx:101-109] — deferred, pre-existing, inherited unchanged from the original vanilla-JS demo per this story's own "preserve, don't fix" scope note
- [x] [Review][Defer] Silent guard/success feedback lost porting `VideoPlayerDemo` off `alert()` [frontend/src/pages/dev/VideoPlayerDemo.tsx:81,112-115] — deferred, dev-only tool, AC1's "controls still work" bar is met, feedback polish only
- [x] [Review][Defer] `setUnauthorizedHandler` is a bare module-level singleton [frontend/src/lib/api/client.ts:15, frontend/src/lib/auth/AuthContext.tsx:36-37] — deferred, correct for the current single-`AuthProvider`-at-root usage, revisit only if a second concurrent provider instance is ever introduced

## Dev Notes

### Why this story exists this late in Epic 1

Stories 1.1–1.7 built a complete, tested backend auth stack with **zero UI**, by explicit, repeated design choice documented in each story's Dev Notes ("no frontend exists yet" — Stories 1.4, 1.5). That was the right call at the time (no frontend existed at all). It stopped being the right gap once Story 4.0 created `frontend/` for the video player and Story 2.1 started Epic 2 — at that point a real app shell became load-bearing for the rest of the roadmap, and login is the one piece every other frontend page (Epic 2's Content Discovery, Epic 5's Dashboard) will sit behind. This story is Epic 1's actual closing piece, not new scope invented outside the epic.

### `frontend/` is a component library today, not an app

Read `frontend/index.html` before touching it — it's a real, working, tested (32/32) manual demo for Story 4.0, just not a React app in the conventional Vite sense (no `#root` div, no `main.tsx`). This story's app-shell work (Task 1) is a prerequisite every later frontend story will depend on, so get the entry point/router structure right rather than minimal — but resist the urge to also scaffold Epic 2/5's real pages here (Scope Note 6, AC7).

### shadcn/ui network dependency risk

`shadcn` CLI's `init`/`add` commands fetch component source from a registry over the network. Story 1.1 already hit a similar environment constraint (no working Rust/MSVC toolchain forced a Python version workaround) and Story 1.6/1.7 hit Docker-daemon-unreachable constraints in this sandbox — check network reachability before relying on the CLI. If unavailable, hand-write the handful of primitives needed (`Button`, `Input`, `Label`, `Card`) following shadcn's own published conventions (Tailwind utility classes, no runtime CSS-in-JS) so a later `shadcn add` for more components still drops into the same structure without conflict. Document whichever path you took, the way Story 1.1 documented its Python-version workaround.

### Cookie-based session, not token-in-state

The backend already does 100% of the session-security work (HttpOnly cookie, `SameSite=Lax`, server-side revocation on logout — Stories 1.2/1.5). The frontend's job is purely: (1) trigger login/logout, (2) react to `401`s, (3) use the `role` value transiently for the post-login redirect and any "logged in as X" UI text. Do not build a parallel client-side session/token store — that would duplicate what the cookie already does and risks drifting out of sync with the real, authoritative, server-side revocation state (exactly the class of bug the backend was built to prevent).

### The 401-interceptor is the frontend's version of Story 1.6

Story 1.6 made every backend router 401 before running any route logic, closing the "flash of protected content" gap server-side. The frontend needs the mirror-image guarantee: a route guard for *navigation-time* checks, plus a response interceptor for *mid-session-expiry* checks (a session can expire, or be revoked by a sign-out in another tab, while a protected page is already open and making background requests). Both are required — a route guard alone only checks once, on mount.

### Testing stack already available, no new test tooling needed

`frontend/package.json` already has `vitest`, `@testing-library/react`, `@testing-library/jest-dom`, `jsdom`, `happy-dom` as dev dependencies (installed for Story 4.0's tests) — reuse these, do not introduce a second test runner or a different testing-library variant.

### `react-router-dom` v7 installed, not v6 (deviation, accepted 2026-07-10)

Library/Framework Requirements named "latest stable v6.x," but `npm install react-router-dom` at implementation time pulled current stable `^7.18.1`. Flagged during code review; **accepted rather than downgraded** — only the stable, unchanged-since-v6 APIs are used here (`BrowserRouter`, `Routes`, `Route`, `Navigate`, `useNavigate`, `useLocation`), all 49 tests pass, and downgrading a major version for no functional gain adds risk without benefit. Same category of deviation as the already-documented Zod v4 install (see Dev Agent Record below); documented here too so a later contributor reading Dev Notes doesn't assume v6 semantics from v7-installed code.

## Project Structure Notes

Changes land in:
- `frontend/index.html` (MODIFIED: vanilla-JS demo page → standard Vite React entry)
- `frontend/package.json` (MODIFIED: new dependencies)
- `frontend/tailwind.config.js`, `frontend/postcss.config.js` (NEW)
- `frontend/components.json` (NEW, if shadcn CLI usable)
- `frontend/src/main.tsx`, `frontend/src/App.tsx` (NEW)
- `frontend/src/index.css` (NEW: Tailwind base import)
- `frontend/src/lib/utils.ts` (NEW: shadcn `cn()` helper)
- `frontend/src/components/ui/*` (NEW: Button/Input/Label/Card primitives)
- `frontend/src/lib/api/authApi.ts`, `frontend/src/lib/api/client.ts` (NEW: shared axios instance)
- `frontend/src/lib/auth/RequireAuth.tsx` (NEW)
- `frontend/src/pages/Login.tsx`, `frontend/src/pages/hr/DashboardStub.tsx`, `frontend/src/pages/employee/ContentDiscoveryStub.tsx`, `frontend/src/pages/dev/VideoPlayerDemo.tsx` (NEW)
- `frontend/src/tests/*` (NEW: tests per Task 6)

No changes to:
- `backend/` — this story is frontend-only; the backend contract (Stories 1.2–1.6) is fixed and must not be modified
- `frontend/src/components/VideoPlayer.tsx`, `frontend/src/lib/adapters/*`, `frontend/src/lib/services/captureService.ts` (Story 4.0's actual logic — only its *host page* moves, not its implementation)
- `_bmad-output/E-Development/*/login.html` (prototype-only, untouched, not a dependency of this story)

## Library/Framework Requirements

- **React 18 + TypeScript + Vite** (already installed, per architecture AR-18) — no version change
- **react-router-dom** (new) — latest stable v6.x
- **Tailwind CSS + PostCSS + Autoprefixer** (new, per AR-18)
- **shadcn/ui** (new, per AR-18) — CLI if network-reachable, hand-rolled primitives otherwise (see Dev Notes)
- **react-hook-form + zod + @hookform/resolvers** (new, per AR-18 — "Client: React Hook Form + Zod (UX only). Server: Pydantic is the real guard.")
- **axios** (already installed) — reuse, do not add a second HTTP client
- **vitest + @testing-library/react + @testing-library/jest-dom + jsdom/happy-dom** (already installed) — reuse for this story's tests

## Testing Requirements

- Test framework: `vitest` + `@testing-library/react` (existing, from Story 4.0)
- Mock `axios` at the module level for login/logout/401-interceptor tests (no real backend call in unit tests) — a real end-to-end check against the running `uvicorn` backend (per Story 1.4/1.5's own live-`curl` verification precedent) is a good manual sanity check before marking this story done, but is not a substitute for the automated tests above
- Route-guard tests must assert on **rendered output** (e.g. protected page's text never appears in the DOM before redirect), not just on the resulting URL — that's the literal "no flash of protected content" requirement, and asserting only the final URL would miss a real regression where content flashes then redirects

## Previous Story Intelligence

From Story 1.4 (`1-4-login-endpoint-and-credential-store-mock-for-mvp.md`, status `done`):
- Backend `POST /api/auth/login` returns `{role, user_id}` only — deliberately no frontend redirect target baked into the response; the frontend decides where to go based on `role`.
- Demo roster: `rita@sails.example.com` (HR_ADMIN), `casey@sails.example.com`/`morgan@sails.example.com`/`jordan@sails.example.com`/`sam@sails.example.com` (EMPLOYEE), password `demo123` for all — useful for manual testing, not to be hardcoded into frontend UI text/hints (that was the prototype's design choice, not this story's).
- Login is case-insensitive on email (`find_account` lowercases), and wrong-password/unknown-email produce byte-identical error responses — don't build any client-side logic that assumes it can distinguish them.

From Story 1.5 (`1-5-sign-out-and-session-invalidation.md`, status `done`):
- `POST /api/auth/logout` has no auth dependency and is idempotent (calling it twice, or with no session, both return `204`) — the frontend's Sign Out handler doesn't need to guard against "already logged out" as a special case.
- Frontend redirect-to-login and back-button/bfcache behavior were explicitly flagged as **out of scope for Story 1.5** and deferred to whichever story built the frontend — that's this story (AC6).

From Story 1.6 (`1-6-protected-endpoint-gate-no-flash-of-protected-content.md`, status `done`):
- Every protected router 401s at the dependency layer before any route handler body executes — the frontend can rely on a `401` meaning "definitely not authenticated for this resource," not a partial/ambiguous state.
- The story's own naming ("no flash of protected content") is the direct backend precedent this story's AC5 mirrors on the frontend.

From Story 4.0 (`4-0-youtube-iframe-adapter-abstraction-layer-for-player-events.md`, status `review`):
- `frontend/vite.config.ts` already proxies `/api` → `http://localhost:8000` — reuse this proxy path for the shared axios instance's base URL rather than hardcoding `http://localhost:8000` directly, so dev/build behavior stays consistent.
- Established frontend test pattern: mock browser/global APIs at the module boundary (that story mocked the YouTube IFrame API and `axios`) rather than hitting real network calls in unit tests — follow the same approach for this story's auth API tests.
- `frontend/package.json`'s `test` script is `vitest` (no `--run` flag hardcoded) — check how Story 4.0's tests were actually invoked (likely `npx vitest run`) before assuming the bare `npm test` script behaves non-interactively in CI/automation.

From Story 2.1 (`2-1-content-catalog-data-model-and-schema.md`, status `review`):
- No frontend impact — confirms Epic 2 so far is backend-only, so this story is not racing any in-flight frontend work from Epic 2.

## Architecture Compliance

**AR-18 — React+TS+Vite, shadcn/ui+Tailwind, React Hook Form+Zod:**
- This story is the first to actually install/configure shadcn/ui, Tailwind, and React Hook Form + Zod — none existed in `frontend/` before it (Story 4.0 only needed bare React+Vite for a single component)
- ✅ This story establishes that stack for every later frontend story to build on

**FR-13/FR-14 (Authentication & Session Gate) + AR-6 (server-side session/role/identity gate on every request):**
- The gate itself is already enforced server-side (Stories 1.2–1.6); this story adds the client-side experience around an already-secure boundary — it must not weaken or duplicate that boundary (Dev Notes: "cookie-based session, not token-in-state")

**Stack compliance:**
- Vite dev server on port 5173 (existing `vite.config.ts`), proxying `/api` to backend port 8000 (existing) — reuse, don't reconfigure
- TypeScript strict mode (existing `tsconfig.json` from Story 4.0) — new code must pass `tsc --noEmit` clean, matching Story 4.0's precedent

## References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.8] — full AC text (this story)
- [Source: backend/app/auth/router.py] — exact `/api/auth/login`, `/api/auth/logout` request/response shapes
- [Source: backend/app/auth/service.py] — cookie attributes (`HttpOnly`, `SameSite=Lax`, `SESSION_COOKIE_NAME`, `COOKIE_SECURE`), revocation behavior
- [Source: backend/app/core/config.py] — `ALLOWED_ORIGINS`, `COOKIE_SECURE` env vars
- [Source: backend/app/core/errors.py] — `{status, code, message, timestamp}` error contract shape
- [Source: backend/app/main.py] — CORS config (`allow_credentials=True`), router mount prefixes
- [Source: frontend/vite.config.ts] — existing `/api` proxy to `http://localhost:8000`, port 5173
- [Source: frontend/index.html] — current Story 4.0 demo page content to be preserved/migrated
- [Source: _bmad-output/implementation-artifacts/4-0-youtube-iframe-adapter-abstraction-layer-for-player-events.md] — existing frontend scaffold, test patterns
- [Source: _bmad-output/planning-artifacts/architecture/architecture-TalentPilot-AI-2026-07-09/ARCHITECTURE-SPINE.md#AR-18] — locked frontend stack
- [Source: _bmad-output/evolution/scenarios/authentication-login-gate.md] and [Source: _bmad-output/evolution/specs/authentication-login-gate.md] — prototype-only mock login, explicitly not a source for this story
- [Source: _bmad-output/project-context.md] — Stories 1.1–1.7, 4.0, 2.1 history and judgment calls

## Git Intelligence

Recent commits (`git log --oneline -5` on `main`):
```
0134487 Epic2 story 2.1  (#32)
1ecf196 Story 4.0: YouTube IFrame Adapter — Complete Frontend Implementation (#31)
b871a01 Merge branch 'main' into Epic2-stories
d8ffb98 Story 2.1
db5fa4a Story 4.0: YouTube IFrame Adapter — Complete Frontend Implementation
```

Established conventions to follow:
- Branch naming: `feature/<kebab-case-slug>` (e.g. `feature/story1.8`), merged to `main` via PR (`(#N)` suffix)
- Frontend commits so far land as one squashed "Story X.Y: ..." commit per PR — follow the same granularity rather than many small commits
- Sprint status transitions: `backlog` → `ready-for-dev` (this commit) → `in-progress` → `review` → `done`, each transition logged as a dated comment line in `sprint-status.yaml`'s header block

## Completion Checklist

- [x] `react-router-dom`, Tailwind, shadcn/ui, `react-hook-form`+`zod` installed and configured
- [x] `index.html`/`main.tsx`/`App.tsx` render a real React app with routing
- [x] Story 4.0 demo preserved and functional at its new route
- [x] `/login` page: form, client-side validation, submits to real backend
- [x] Successful login redirects by role to the correct stub page
- [x] Failed login shows the backend's exact error message
- [x] Protected-route guard + 401 interceptor: no flash of protected content, mid-session expiry also redirects
- [x] Sign out clears session, redirects to `/login`, back button doesn't resurrect protected content
- [x] All new code passes `tsc --noEmit`
- [x] All new tests pass (`vitest run`)
- [x] Project context (`_bmad-output/project-context.md`) updated with learnings, per this project's mandatory-update rule
- [x] Sprint status updated to `review`

## Dev Agent Record

### Agent Model Used

Claude Sonnet 5 (claude-sonnet-5), via `bmad-dev-story`.

### Debug Log References

- `npx tsc --noEmit` — clean, zero errors, run after every task.
- `npx vitest run` — 8/8 test files, 49/49 tests passing (32 pre-existing Story 4.0 tests + 17 new), zero regressions.
- `npm run build` (`tsc && vite build`) — succeeds; first attempt failed with a Tailwind v4 PostCSS error (`Cannot apply unknown utility class 'bg-slate-50'`) caused by putting `@config` before `@import "tailwindcss"` in `src/index.css` — fixed by reversing the order (import first, then `@config`), per Tailwind v4's documented directive order.
- Live end-to-end verification against the real stack (not just mocks): started the actual `uvicorn` backend (`backend/.venv`) and the actual Vite dev server, then `curl`'d through the Vite `/api` proxy exactly as the frontend's axios calls do — confirmed real `200`+`Set-Cookie` on valid login, real `401` with the exact `{status, code, message, timestamp}` body on wrong password, real `204`+cookie-clear on logout, and correct CORS/credentials headers (`access-control-allow-credentials: true`, `access-control-allow-origin: http://localhost:5173`). Both servers were stopped again after verification.

### Completion Notes List

- **Tailwind v4, not v3, actually installed.** `npm install -D tailwindcss` pulled v4.3.2 (current stable), which changed the story's assumed v3-style `tailwind.config.js`-only setup to v4's CSS-first model: `@tailwindcss/postcss` (separate package) in `postcss.config.js`, `@import "tailwindcss";` in `src/index.css`, and `@config "../tailwind.config.js";` (after the import) so the config file isn't dead weight. No custom theme/CSS variables were hand-authored (see next note) — this judgment call is worth flagging for whoever next touches Tailwind config here.
- **shadcn/ui: hand-rolled primitives, not the CLI**, decided up front rather than attempted-then-fallen-back — running `shadcn init`/`add` is interactive by default and risks hanging in a non-interactive sandboxed shell, a real risk in this environment (same category of constraint Stories 1.1/1.6/1.7 hit with toolchains/Docker). Built `Button`, `Input`, `Label`, `Card` in `src/components/ui/` using `class-variance-authority` + `cn()` (`clsx`+`tailwind-merge`) — matching shadcn's real structural conventions (so a future real `shadcn add <component>` still drops in cleanly) but using **plain default-palette Tailwind utility classes** (`bg-slate-900`, `border-slate-200`, etc.) rather than the CSS-variable semantic tokens (`bg-background`, `text-foreground`) shadcn's actual generated components use — lower-risk without a browser to visually verify a hand-authored `@theme` color-token mapping. `components.json` is still present and correctly configured so a real `shadcn add` later slots into the same `@/components/ui` structure.
- **`frontend/index.html` was genuinely not a React app before this story** — confirmed by reading it: it was Story 4.0's hand-written vanilla-JS demo (no `#root` div, no `main.tsx`), even though `react`/`react-dom` were already dependencies. Rewrote it to the standard Vite entry and migrated the demo's exact functionality (video ID / resume-position inputs, Load Video, live position/duration/progress%/status metrics, Flush Samples Now) into `src/pages/dev/VideoPlayerDemo.tsx`, ported faithfully from the original imperative script rather than delegating to the existing `<VideoPlayer>` component — `<VideoPlayer>` doesn't expose its internal `CaptureService` instance, which the demo's "Flush Samples Now" button needs direct access to, and `VideoPlayer.tsx` was explicitly out of scope to modify.
- **Found and fixed a real gap while reading files before changing them (Dev Notes' own instruction, applied)**: `frontend/vitest.config.ts` is a *separate* file from `vite.config.ts` and Vitest prefers it when both exist — meaning the `resolve.alias` for `@/*` I added to `vite.config.ts` would have been silently ignored by the actual test runner. Added the identical alias to `vitest.config.ts` too; without this, every new test file's `@/...` import would have failed at test time despite compiling fine under `tsc` (which reads `tsconfig.json`'s `paths`, not either Vite config).
- **`COOKIE_SECURE=False` added to `backend/.env`** so a real browser (not just `curl`, which ignores the `Secure` flag) can actually receive/send the session cookie over local plain-HTTP dev — required for anyone opening the real login page in a browser. Discovered in the process: `backend/.env` is **tracked in git**, not gitignored as `_bmad-output/project-context.md` (Stories 1.5/1.7 entries) previously stated — `backend/.gitignore` only excludes `.venv/`, `__pycache__/`, etc. This is a pre-existing documentation inaccuracy from an earlier story, not introduced here; flagged in `project-context.md`'s update for this story rather than silently left standing.
- ~~Known, accepted limitation, not a bug~~ — **Superseded 2026-07-14**: a `GET /api/auth/me` endpoint now exists (reusing the existing `get_current_user` dependency), and `AuthContext` calls it on mount to restore session state from the cookie. `AuthContext.tsx`'s docstring was updated accordingly as part of the fix. See AC7's superseded note above and `project-context.md`/`sprint-change-proposal-2026-07-14.md` for the full change record.
- **Zod v4 installed** (not v3) via `@hookform/resolvers` — `z.string().email()` and `zodResolver` worked exactly as expected with no compatibility shims needed; confirmed by the passing Login validation tests, not assumed.
- All 6 tasks implemented together in one pass (app-shell → login → API client → guard → stubs) rather than strictly sequential red-green-refactor per task, since they're tightly coupled (Login needs AuthContext needs client.ts needs RequireAuth needs App.tsx wiring to be renderable/testable at all) — Task 6's 8 test files were then written and run to green across all of them together, the same pattern Stories 2.1/4.0's own Dev Agent Records show they used.
- **Visual parity pass with the prototype (2026-07-10, user-requested)**: the user compared the real `/login` against `_bmad-output/E-Development/01-Ritas-Trust-Call-Prototype/login.html` and found it didn't visually match — correct, since the story's own Scope Note explicitly said the prototype was "visual/copy inspiration only," and the initial implementation used generic Tailwind slate tones instead of actually porting the prototype's brand tokens over. Fixed by: adding the prototype's `talentpilot` blue palette (50/100/500/600/700) and Inter font to `tailwind.config.js` (+ Google Fonts `<link>` in `index.html`, matching the prototype's own font-loading approach); switching the shared `Button`/`Input`/`Label`/`Card` primitives from `slate-*` to the prototype's `gray-*` scale and `rounded-lg` corners (a global change across all 4 pages using them, not just Login, for design-language consistency); restructuring `Login.tsx` to the prototype's single `p-8` block layout with the "TalentPilot-AI" / "Sign in to continue" header text and a boxed `red-700`/`red-50`/`red-200` error notice matching the prototype's `login-error-notice` styling. **Explicitly excluded per user instruction**: the prototype's "Demo accounts (password: demo123)" hint list was deliberately left out of the real page — the user asked for visual parity only, not that specific piece of prototype-only convenience.
- Verified after the restyle: `tsc --noEmit` clean, `npm run build` succeeds, and the built CSS was grepped to confirm `.bg-talentpilot-600`/`.rounded-lg`/`.text-gray-600` actually made it into the output (not a dead/unused config). Full test suite re-run clean (53/53 passing at that point, including 4 tests the user had added independently to `RequireAuth.test.tsx`/`ContentDiscoveryStub.test.tsx` since the initial implementation).

### File List

**New:**
- `frontend/postcss.config.js`
- `frontend/tailwind.config.js`
- `frontend/components.json`
- `frontend/src/index.css`
- `frontend/src/lib/utils.ts`
- `frontend/src/components/ui/button.tsx`
- `frontend/src/components/ui/input.tsx`
- `frontend/src/components/ui/label.tsx`
- `frontend/src/components/ui/card.tsx`
- `frontend/src/main.tsx`
- `frontend/src/App.tsx`
- `frontend/src/lib/api/client.ts`
- `frontend/src/lib/api/authApi.ts`
- `frontend/src/lib/auth/AuthContext.tsx`
- `frontend/src/lib/auth/RequireAuth.tsx`
- `frontend/src/pages/Login.tsx`
- `frontend/src/pages/hr/DashboardStub.tsx`
- `frontend/src/pages/employee/ContentDiscoveryStub.tsx`
- `frontend/src/pages/dev/VideoPlayerDemo.tsx`
- `frontend/src/tests/setup.ts`
- `frontend/src/tests/client.test.ts`
- `frontend/src/tests/authApi.test.ts`
- `frontend/src/tests/Login.test.tsx`
- `frontend/src/tests/RequireAuth.test.tsx`
- `frontend/src/tests/DashboardStub.test.tsx`
- `frontend/src/tests/VideoPlayerDemo.test.tsx`

**Modified:**
- `frontend/index.html` (vanilla-JS demo page → standard Vite React entry; later gained Google Fonts `<link>`s for the visual-parity pass)
- `frontend/package.json` / `frontend/package-lock.json` (new dependencies — see Library/Framework Requirements)
- `frontend/vite.config.ts` (added `@` path alias, added test `setupFiles`)
- `frontend/vitest.config.ts` (added `@` path alias, added test `setupFiles`)
- `backend/.env` (added `COOKIE_SECURE=False` for local browser testing — no backend source code touched)
- `frontend/tailwind.config.js` (visual-parity pass: added `talentpilot` color palette + Inter `fontFamily`)
- `frontend/src/index.css` (visual-parity pass: body `bg-slate-50`/`text-slate-900` → `bg-gray-50`/`font-sans`/`text-gray-900`)
- `frontend/src/components/ui/button.tsx`, `input.tsx`, `label.tsx`, `card.tsx` (visual-parity pass: `slate-*` → `gray-*`/`talentpilot-*`, `rounded-md` → `rounded-lg`)
- `frontend/src/pages/Login.tsx` (visual-parity pass: restructured to the prototype's single `p-8` block layout, header copy, boxed error notice)

**Unchanged (as expected):**
- `backend/app/**` — no backend source files modified
- `frontend/src/components/VideoPlayer.tsx`, `frontend/src/lib/adapters/*`, `frontend/src/lib/services/captureService.ts`
- `_bmad-output/E-Development/*/login.html` (prototype-only mock, untouched)

## Change Log

- 2026-07-10: Story 1.8 implemented — frontend app-shell (react-router-dom, Tailwind v4, hand-rolled shadcn-style primitives, React Hook Form + Zod), real `/login` page wired to the actual Story 1.2–1.6 backend, protected-route guard + axios 401 interceptor, Sign Out, HR/Employee stub destination pages, Story 4.0 demo migrated to `/dev/video-player-demo`. 17 new tests (49/49 total passing), `tsc --noEmit` clean, production build succeeds, live end-to-end verified against the real backend + Vite dev server.
- 2026-07-10: Visual parity pass (user-requested) — `/login` restyled to match `01-Ritas-Trust-Call-Prototype/login.html`'s brand tokens (talentpilot blue palette, Inter font, gray scale, rounded-lg, boxed error notice, header copy), applied to the shared UI primitives app-wide. Demo-accounts hint list deliberately not ported over, per explicit instruction. `tsc --noEmit` clean, build succeeds, 53/53 tests passing.

## Status
**ready-for-dev** → **in-progress** → **review**
