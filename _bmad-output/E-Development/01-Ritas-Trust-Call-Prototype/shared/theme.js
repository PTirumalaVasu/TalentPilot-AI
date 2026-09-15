/**
 * Theme toggle (Light/Dark mode) — FR-30, App-Wide Theming (Epic 8, Story
 * 8.1, real app: done). These prototype mockups never got a dark-mode
 * toggle at all — added 2026-09-15, per direct request, to close that gap.
 *
 * Matches FR-30's consequences: defaults to prefers-color-scheme on first
 * visit, a manual pick persists (here: localStorage, per-browser — same
 * "no backend change, zero-budget-consistent" persistence FR-30 specifies
 * for the real app), and switching takes effect immediately, no reload.
 *
 * Include this script BEFORE Tailwind's CDN <script> tag's config block
 * runs, or at least before body paint, to avoid a flash of the wrong theme.
 * Requires `darkMode: 'class'` in each page's tailwind.config.
 */
(function () {
  const STORAGE_KEY = 'talentpilot_theme';

  function getStoredTheme() {
    try {
      return localStorage.getItem(STORAGE_KEY);
    } catch (e) {
      return null; // localStorage can throw in locked-down/private contexts
    }
  }

  function getPreferredTheme() {
    const stored = getStoredTheme();
    if (stored === 'light' || stored === 'dark') return stored;
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }

  function applyTheme(theme) {
    document.documentElement.classList.toggle('dark', theme === 'dark');
    const toggleBtn = document.getElementById('app-theme-toggle');
    if (toggleBtn) {
      toggleBtn.textContent = theme === 'dark' ? '☀️' : '🌙';
      toggleBtn.setAttribute('aria-label', theme === 'dark' ? 'Switch to Light mode' : 'Switch to Dark mode');
    }
  }

  window.TalentPilotTheme = {
    init: function () {
      applyTheme(getPreferredTheme());
    },
    toggle: function () {
      const next = document.documentElement.classList.contains('dark') ? 'light' : 'dark';
      try {
        localStorage.setItem(STORAGE_KEY, next);
      } catch (e) {
        // Persistence is a nicety, not a requirement — theme still applies for this view.
      }
      applyTheme(next);
    },
  };

  // Applied immediately (not on DOMContentLoaded) to avoid a flash of the
  // wrong theme on load — safe since this only touches <html>'s class list,
  // not any element that must exist yet.
  window.TalentPilotTheme.init();
})();
