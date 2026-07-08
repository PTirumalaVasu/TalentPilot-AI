/**
 * Auto-initialization — loads demo data (via PrototypeAPI) and calls
 * window.initPage() if the page defines one. Runs on every page load.
 */

document.addEventListener('DOMContentLoaded', async () => {
  console.log('🚀 TalentPilot-AI Prototype — Scenario 03: Rita\'s Assignment & Track');

  try {
    const data = await window.PrototypeAPI._load();
    console.log('📦 Demo data loaded:', data);
  } catch (error) {
    console.error('❌ Failed to load demo data:', error);
  }

  if (typeof window.initPage === 'function') {
    window.initPage();
  }

  if (typeof window.initDevMode === 'function') {
    window.initDevMode();
  }
});
