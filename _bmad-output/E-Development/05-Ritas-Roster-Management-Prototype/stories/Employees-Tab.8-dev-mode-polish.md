# Story: Employees-Tab.8 — Dev Mode Integration + Polish

**Status:** Implemented
**Spec reference:** `work/Employees-Tab-Work.yaml` → section-8

**Purpose:** Match the dev-mode tooling already present on 01.1/04.1, and do a final console/error pass.

**Implementation:**
- `components/dev-mode.css`/`dev-mode.js` copied from the sibling prototype folder and included identically
- Every interactive element carries a `data-object-id` matching the spec (verified against `work/Employees-Tab-Work.yaml`'s object_ids list)

**Acceptance criteria:**
- [ ] Shift+Click any `data-object-id` element copies its ID (dev mode) — **needs live Puppeteer/manual verification, not yet run**
- [ ] No console errors through the full path: Create → Password Reveal → Edit → Regenerate → Delete/Archive — **needs live verification, not yet run**

**Note:** This story's acceptance criteria are implemented in code but not yet exercised in a live browser session — see Step 4d (Present for Testing) / Step 5 (Finalization) for the verification pass.
