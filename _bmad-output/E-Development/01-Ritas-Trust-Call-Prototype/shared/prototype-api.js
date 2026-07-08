/**
 * PrototypeAPI — simulates the real FastAPI backend using sessionStorage.
 * Mirrors the data shape from DD-001-poc-hypothesis-flows.yaml (assignments,
 * skill_progress) so migration notes stay meaningful. See PROTOTYPE-ROADMAP.md
 * "Production Migration Note" — this is throwaway, not the real backend.
 */

const STORAGE_KEY = 'talentpilot_prototype_data';

const PrototypeAPI = {
  async _load() {
    let raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw) {
      // Seeded from window.DEMO_DATA (data/demo-data.js), not fetch() —
      // fetch() of a local file is blocked by browsers under file://,
      // which breaks the "just double-click, no server" prototype promise.
      if (!window.DEMO_DATA) {
        throw new Error('window.DEMO_DATA not found — is data/demo-data.js included before this script?');
      }
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(window.DEMO_DATA));
      raw = JSON.stringify(window.DEMO_DATA);
    }
    return JSON.parse(raw);
  },

  async _save(data) {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  },

  async getUser() {
    const data = await this._load();
    return data.currentUser;
  },

  async getEmployees() {
    const data = await this._load();
    return data.employees;
  },

  async getSkills() {
    const data = await this._load();
    return data.skills;
  },

  async getAssignments() {
    const data = await this._load();
    return data.assignments.map((a) => ({
      ...a,
      employee: data.employees.find((e) => e.id === a.employeeId),
      skill: data.skills.find((s) => s.id === a.skillId),
    }));
  },

  async getAssignmentDetail(assignmentId) {
    const assignments = await this.getAssignments();
    const assignment = assignments.find((a) => a.id === assignmentId);
    if (!assignment) {
      throw new Error(`Assignment ${assignmentId} not found`);
    }
    return assignment;
  },

  // ==========================================================================
  // DEBUG HELPERS (console commands)
  // ==========================================================================

  async getDebugInfo() {
    const data = await this._load();
    console.log('🔍 PrototypeAPI Debug Info:', data);
    return data;
  },

  clearAllData() {
    sessionStorage.removeItem(STORAGE_KEY);
    console.log('🗑️ Prototype data cleared. Reload the page to re-seed demo data.');
  },
};

window.PrototypeAPI = PrototypeAPI;
