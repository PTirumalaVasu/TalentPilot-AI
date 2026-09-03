/**
 * Shared prototype initialization (used by every page in this scenario).
 * Loads data/demo-data.json, exposes it as window.DEMO_DATA, then calls
 * window.initPage() if the current page defines one.
 */
(async function () {
  try {
    const response = await fetch('data/demo-data.json');
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    window.DEMO_DATA = await response.json();
    console.log('📦 Demo data loaded (real backend seed data):', window.DEMO_DATA);
  } catch (error) {
    console.error(
      "❌ Could not load data/demo-data.json. If you opened this file directly " +
      "(file://...), Chromium-based browsers block local fetch() under CORS. " +
      "Serve this folder with a local static server instead — e.g. `npx serve .` " +
      "or VS Code's Live Server extension — then reload.",
      error
    );
    window.DEMO_DATA = null;
    if (typeof window.onDemoDataLoadFailure === 'function') {
      window.onDemoDataLoadFailure(error);
    }
  }

  if (typeof window.initPage === 'function') {
    window.initPage();
  }
})();
