/**
 * Left-pane nav collapse/expand toggle — added 2026-09-15, direct request.
 * Persists the collapsed/expanded state per browser (localStorage), same
 * pattern as shared/theme.js, so the choice survives navigating between
 * pages (each a separate full page load, not an SPA).
 *
 * Markup contract (see each page's <aside id="app-nav-sidebar">):
 * - The sidebar itself toggles between `.app-nav-expanded`/`.app-nav-collapsed`
 *   width classes (applied here, not hardcoded in each page's own class list).
 * - Each nav link and the logo contain two spans: `.app-nav-label` (full text,
 *   shown when expanded) and `.app-nav-icon` (2-letter badge, shown when
 *   collapsed) — both always in the DOM, visibility toggled here.
 */
(function () {
  const STORAGE_KEY = 'talentpilot_nav_collapsed';

  function isCollapsed() {
    try {
      return localStorage.getItem(STORAGE_KEY) === '1';
    } catch (e) {
      return false;
    }
  }

  function applyState(collapsed) {
    const aside = document.getElementById('app-nav-sidebar');
    if (!aside) return;

    aside.classList.toggle('w-56', !collapsed);
    aside.classList.toggle('w-16', collapsed);

    document.querySelectorAll('.app-nav-label').forEach((el) => el.classList.toggle('hidden', collapsed));
    document.querySelectorAll('.app-nav-icon').forEach((el) => el.classList.toggle('hidden', !collapsed));
    document.querySelectorAll('.app-nav-link-row').forEach((el) => el.classList.toggle('justify-center', collapsed));

    const toggleBtn = document.getElementById('app-nav-collapse-toggle');
    if (toggleBtn) {
      toggleBtn.textContent = collapsed ? '»' : '«';
      toggleBtn.setAttribute('aria-label', collapsed ? 'Expand navigation' : 'Collapse navigation');
      toggleBtn.setAttribute('title', collapsed ? 'Expand navigation' : 'Collapse navigation');
    }
  }

  window.TalentPilotNav = {
    init: function () {
      applyState(isCollapsed());
    },
    toggle: function () {
      const next = !isCollapsed();
      try {
        localStorage.setItem(STORAGE_KEY, next ? '1' : '0');
      } catch (e) {
        // Persistence is a nicety, not a requirement — state still applies for this view.
      }
      applyState(next);
    },
  };

  document.addEventListener('DOMContentLoaded', function () {
    window.TalentPilotNav.init();
  });
})();
