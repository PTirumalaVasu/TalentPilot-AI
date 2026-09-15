/**
 * PrototypeAPI — simulates the real FastAPI backend using sessionStorage.
 * Mirrors the data shape from DD-001-poc-hypothesis-flows.yaml (assignments,
 * skill_progress) so migration notes stay meaningful. See PROTOTYPE-ROADMAP.md
 * "Production Migration Note" — this is throwaway, not the real backend.
 */

const STORAGE_KEY = 'talentpilot_prototype_data';

const PrototypeAPI = {
  async _load() {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    const cached = raw ? JSON.parse(raw) : null;

    // [ADDED 2026-09-15] Reseed whenever data/demo-data.js's own _version is
    // newer than what's cached — otherwise an already-open tab from before a
    // demo-data.js edit keeps serving the stale shape indefinitely, since
    // sessionStorage previously only ever seeded when completely empty. This
    // is why Story 10.11's new experienceYears fields didn't show up without
    // a manual cache clear the first time.
    const isStale = !cached || (window.DEMO_DATA && cached._version !== window.DEMO_DATA._version);

    if (isStale) {
      // Seeded from window.DEMO_DATA (data/demo-data.js), not fetch() —
      // fetch() of a local file is blocked by browsers under file://,
      // which breaks the "just double-click, no server" prototype promise.
      if (!window.DEMO_DATA) {
        throw new Error('window.DEMO_DATA not found — is data/demo-data.js included before this script?');
      }
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(window.DEMO_DATA));
    }
    // Always return a fresh deep clone from storage, not a live reference to
    // window.DEMO_DATA — preserves the original behavior that downstream
    // mutations (e.g. deleteAssignment) never leak back into the source data.
    return JSON.parse(sessionStorage.getItem(STORAGE_KEY));
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

  // Mirrors DELETE /api/assignments/{id} (Story 3.7/5.7) -- soft-delete in
  // the real backend, but the prototype's sessionStorage store has no
  // audit trail to preserve, so this just removes the row.
  async deleteAssignment(assignmentId) {
    const data = await this._load();
    const before = data.assignments.length;
    data.assignments = data.assignments.filter((a) => a.id !== assignmentId);
    if (data.assignments.length === before) {
      throw new Error(`Assignment ${assignmentId} not found`);
    }
    await this._save(data);
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
