# Story HR-Dashboard.1: HR Dashboard - Page Shell & Header

**View**: HR Dashboard (Grid)
**Section**: 1 of 7
**Complexity**: Simple
**Estimated Time**: 15 minutes

---

## 🎯 Goal

Build the page skeleton and header bar: logo/wordmark, primary nav (Dashboard active / Skills dead link), and a user-menu dropdown with Sign Out. This is the foundation every later section renders inside.

---

## 📋 What to Build

### HTML Elements

```html
<body class="bg-gray-50 font-sans min-h-screen">
  <header class="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
    <div class="flex items-center gap-8">
      <div id="hr-dashboard-logo" class="font-bold text-lg text-gray-900">TalentPilot-AI</div>
      <nav class="flex gap-6 text-sm">
        <a id="hr-dashboard-nav-dashboard" href="#"
           class="text-talentpilot-600 font-medium border-b-2 border-talentpilot-600 pb-3 -mb-3">Dashboard</a>
        <a id="hr-dashboard-nav-skills" href="#"
           class="text-gray-600 hover:text-gray-900 pb-3 -mb-3 transition-colors">Skills</a>
      </nav>
    </div>
    <div class="relative">
      <button id="hr-dashboard-user-menu-trigger" onclick="toggleUserMenu()"
              class="flex items-center gap-2 text-sm text-gray-700">
        <span class="w-8 h-8 rounded-full bg-talentpilot-100 flex items-center justify-center text-talentpilot-700 font-medium">R</span>
        Rita
      </button>
      <div id="hr-dashboard-user-menu-dropdown" hidden
           class="absolute right-0 mt-2 w-40 bg-white border border-gray-200 rounded-lg shadow-lg z-10">
        <button id="hr-dashboard-user-menu-signout" onclick="handleSignOut()"
                class="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 rounded-lg">
          Sign Out
        </button>
      </div>
    </div>
  </header>

  <main id="hr-dashboard-main" class="px-6 pb-12">
    <!-- Sections 2-7 render here -->
  </main>
</body>
```

### JavaScript

```javascript
// Toggles the user-menu dropdown; closes it on outside click.
function toggleUserMenu() {
  const dropdown = document.getElementById('hr-dashboard-user-menu-dropdown');
  dropdown.hidden = !dropdown.hidden;
}

document.addEventListener('click', (event) => {
  const trigger = document.getElementById('hr-dashboard-user-menu-trigger');
  const dropdown = document.getElementById('hr-dashboard-user-menu-dropdown');
  if (!dropdown.hidden && !trigger.contains(event.target) && !dropdown.contains(event.target)) {
    dropdown.hidden = true;
  }
});

// Prototype-only stand-in for real sign-out (no live auth session to tear down).
function handleSignOut() {
  console.log('[prototype] Sign out clicked — would clear session and redirect to /login');
  document.getElementById('hr-dashboard-user-menu-dropdown').hidden = true;
}
```

### Tailwind Classes to Use

**Key classes for this section**:
- Header bar: `bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between`
- Active nav item: `text-talentpilot-600 font-medium border-b-2 border-talentpilot-600 pb-3 -mb-3`
- Inactive nav item: `text-gray-600 hover:text-gray-900 pb-3 -mb-3 transition-colors`
- Avatar circle: `w-8 h-8 rounded-full bg-talentpilot-100 flex items-center justify-center text-talentpilot-700 font-medium`
- Dropdown panel: `absolute right-0 mt-2 w-40 bg-white border border-gray-200 rounded-lg shadow-lg z-10`

---

## 🔗 Dependencies

**Shared code**:
- ✅ `shared/init.js` (loads `data/demo-data.json`, resolves `currentUser` for "Rita" + avatar initial)

**Components**: none required for this section.

---

## 📸 Baseline State

New section — no prior implementation to diff against. (Note: production already has this exact header in `frontend/src/pages/hr/Dashboard.tsx` — this prototype is a from-scratch rebuild for iteration purposes, not a modification of the live app.)

---

## 📝 Implementation Steps

### Step 1: HTML skeleton + header markup
Build the `<body>`/`<header>`/`<main>` structure above with real values from `data/demo-data.json`'s `currentUser` (Rita the Recommender → avatar initial "R", first name "Rita").

### Step 2: User-menu dropdown behavior
Wire `toggleUserMenu()` and the outside-click-closes handler.

### Step 3: Sign-out placeholder
Wire `handleSignOut()` as a console-logged placeholder (no real session in a static prototype).

---

## ✅ Acceptance Criteria

### Agent-Verifiable (Puppeteer)

| # | Criterion | Element | Expected | How to Verify |
|---|-----------|---------|----------|----------------|
| 1 | Logo renders | `#hr-dashboard-logo` | Text = "TalentPilot-AI" | `textContent` equality |
| 2 | Dashboard nav shows active styling | `#hr-dashboard-nav-dashboard` | Has classes `text-talentpilot-600`, `border-b-2` | `classList.contains` |
| 3 | Skills nav is present but unstyled-active | `#hr-dashboard-nav-skills` | Does NOT have `text-talentpilot-600` | `classList.contains` (false) |
| 4 | User menu shows Rita's initial | `#hr-dashboard-user-menu-trigger` | Contains "R" and "Rita" | `textContent` includes both |
| 5 | Dropdown hidden by default | `#hr-dashboard-user-menu-dropdown` | `hidden` attribute present | `hasAttribute('hidden')` |
| 6 | Click trigger opens dropdown | `#hr-dashboard-user-menu-dropdown` | `hidden` removed after click | Click + re-check attribute |
| 7 | Click outside closes dropdown | `#hr-dashboard-user-menu-dropdown` | `hidden` re-added after outside click | Click body + re-check attribute |
| 8 | No console errors on load | — | 0 console errors | Puppeteer console listener |

### User-Evaluable (Qualitative)

- [ ] Header feels consistent with the real production Dashboard (side-by-side comparison, not just a passable approximation)
- [ ] Active/inactive nav distinction is visually clear at a glance
- [ ] Dropdown positioning looks correct (right-aligned under avatar, not clipped)
- [ ] Looks right at all 3 test viewports (390px / 768px / 1440px)

---

## 🧪 How to Test

### Puppeteer Self-Verification (Agent)

1. Open `hr-dashboard.html` in Puppeteer
2. Set viewport to 1440×900, then repeat at 768×1024 and 390×844
3. For each agent-verifiable criterion above: locate element, read actual value, compare to expected, narrate with ✓/✗
4. Fix any mismatches and re-verify until all pass
5. Check console for errors at each viewport

### User Qualitative Review

After Puppeteer verification passes:
- Report X/8 criteria passing
- Ask user to evaluate the qualitative checklist above
- Collect feedback before moving to Section 2

---

## 🐛 Common Issues & Fixes

### Issue: Dropdown doesn't close on outside click
**Symptom**: Dropdown stays open after clicking elsewhere on the page
**Cause**: Outside-click listener attached before the dropdown exists in the DOM, or event bubbling stopped elsewhere
**Fix**: Attach the `document.addEventListener('click', ...)` handler after DOM content is loaded; verify no other handler calls `stopPropagation()` on the header

### Issue: Avatar initial doesn't match demo data
**Symptom**: Avatar shows a hardcoded "R" even if demo data changes
**Cause**: Initial was hardcoded in HTML instead of derived from `currentUser.name` at init time
**Fix**: Derive `initial = currentUser.name.charAt(0).toUpperCase()` in `shared/init.js` and inject at render time, not hardcode in the template

---

## 🎨 Design Notes

**Visual requirements**:
- Match `design-system.md`'s recommendation of `talentpilot-*` throughout (not the mixed `blue-*`/`talentpilot-*` production uses) — this section is the first place that choice becomes visible
- Border-bottom "active tab" treatment on Dashboard nav must read clearly against the plain gray "Skills" link

**UX considerations**:
- "Skills" nav is intentionally a dead link (`href="#"`) — matches real production, not a bug to fix in this prototype
- Sign Out is a real-feeling interaction (closes menu, logs an action) even though there's no live session to end

---

## 💡 Tips

- Keep `<main id="hr-dashboard-main">` empty in this section — Sections 2-7 append into it, so getting its id right now avoids rework later
- `data/demo-data.json`'s `currentUser` block is the single source for the name/avatar shown here — don't hardcode "Rita" a second time anywhere else in the file

---

## ➡️ Next Section

After this section is approved: `HR-Dashboard.2-toolbar-title-row.md`

---

## 📊 Status Tracking

**Status**: ✅ Complete
**Started**: 2026-09-03
**Completed**: 2026-09-03
**Approved By**: Vasu
**Notes**: Implemented in `hr-dashboard.html`. 9/9 structural checks passed (no Puppeteer available in this environment — verified via grep + `node --check` instead of live browser automation). User confirmed qualitative review in-browser: approved.

---

## 🔄 Changes from Original Plan

- Avatar initial and display name are set dynamically in `initPage()` from `DEMO_DATA.currentUser` rather than hardcoded as static "R"/"Rita" text in the HTML — this directly follows this story's own Tips section ("don't hardcode Rita a second time"), not a deviation from intent. Two extra ids (`hr-dashboard-user-avatar`, `hr-dashboard-user-name`) were added to support this; the 5 object IDs from the work file are all still present unchanged.
