# Page Specification: Login

## Overview
- **Purpose:** Authenticate a user (HR Admin or Employee) and route them to their role's home page.
- **URL:** `/login`
- **Type:** Auth / standalone form
- **Source:** `frontend/src/pages/Login.tsx`

## Layout Structure (Desktop)
Single centered card on a plain `bg-gray-50` background, no header/nav/footer.

1. Card (`max-w-sm`, centered vertically and horizontally)
   - Header block: "TalentPilot-AI" wordmark (bold) + "Sign in to continue" subtitle
   - Generic error banner (conditional — red bordered box)
   - Form (`space-y-4`)
     - Email field: Label + Input + inline field error
     - Password field: Label + Input (masked) + inline field error
     - Submit button (full width, disabled while submitting, label swaps to "Signing in…")

## Component List

| Component | Location | Variant | Notes |
|---|---|---|---|
| `Card` / `CardContent` | Page wrapper | — | `max-w-sm`, `p-8` |
| `Label` | Above each field | — | |
| `Input` | Email, password | `type="email"`, `type="password"` | `aria-invalid` set from validation state |
| `FormErrorText` | Below each field + generic banner | — | `role="alert"` |
| `Button` | Submit | `default`, full width | `disabled` while `isSubmitting` |

## Content Strategy
- Wordmark: "TalentPilot-AI"
- Subtitle: "Sign in to continue"
- Field labels: "Email", "Password"
- Validation copy: "Email is required" / "Enter a valid email address" / "Password is required" (zod schema)
- Generic failure copy: "Something went wrong, please try again." (non-401 errors)
- 401 copy: server-provided `message`, falls back to the generic string
- Submit label: "Sign In" → "Signing in…"

## Responsive Behavior
No explicit breakpoints in this page — card is intrinsically narrow (`max-w-sm`) and centers on any viewport via flex; `p-4` outer padding prevents edge-to-edge collision on small screens.

## Interactions
- Client-side validation via `react-hook-form` + `zod`, `noValidate` on the form (no native browser bubbles)
- On submit: calls `login()`, then routes by role — `HR_ADMIN` → `/hr/dashboard`, else → `/employee/content` (`replace: true`, no back-button return to Login)
- 401 response surfaces the server's message inline; any other error (network, 5xx) shows the generic fallback
- Focus ring: `focus-visible:ring-2 ring-talentpilot-500` on interactive elements
