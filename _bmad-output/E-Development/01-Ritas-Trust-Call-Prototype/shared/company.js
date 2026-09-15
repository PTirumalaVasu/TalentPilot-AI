/**
 * Company name label — added 2026-09-15, direct request ("add one setting
 * under the logout button to configure the Company name to show just right
 * beside the collapse and open menu"). A small, per-browser, client-only
 * setting (no backend — same localStorage-only persistence model as
 * shared/theme.js / shared/nav.js) letting the HR Admin label the shell with
 * their own org's name, distinct from the "TalentPilot-AI" product name in
 * the logo. Rendered into every `.app-nav-company-name` element (there's one
 * per page, in the top header just before the dark/light mode toggle) and kept in sync with the
 * "Company Settings" modal's input field.
 *
 * Markup contract:
 * - `.app-nav-company-name` lives in the top `<header>`, not the sidebar —
 *   it does not carry `.app-nav-label` and is unaffected by the nav
 *   collapse/expand state (shared/nav.js).
 * - `#company-settings-input` is the modal's text input, kept in sync with
 *   the stored value whenever it changes.
 */
(function () {
  const STORAGE_KEY = 'talentpilot_company_name';

  function getCompanyName() {
    try {
      return localStorage.getItem(STORAGE_KEY) || '';
    } catch (e) {
      return ''; // localStorage can throw in locked-down/private contexts
    }
  }

  function render() {
    const name = getCompanyName();
    document.querySelectorAll('.app-nav-company-name').forEach((el) => {
      el.textContent = name;
      el.title = name;
    });
    const input = document.getElementById('company-settings-input');
    if (input) input.value = name;
  }

  window.TalentPilotCompany = {
    init: function () {
      render();
    },
    save: function (name) {
      const trimmed = (name || '').trim();
      try {
        localStorage.setItem(STORAGE_KEY, trimmed);
      } catch (e) {
        // Persistence is a nicety, not a requirement — still applies for this view.
      }
      render();
    },
  };

  // Kept as a DOMContentLoaded fallback (mirrors shared/nav.js) — the primary
  // call is the inline <script> at the end of each page's <aside>, right
  // after TalentPilotNav.init(), so the label is correct before first paint
  // rather than only after the whole page finishes loading.
  document.addEventListener('DOMContentLoaded', function () {
    window.TalentPilotCompany.init();
  });
})();
