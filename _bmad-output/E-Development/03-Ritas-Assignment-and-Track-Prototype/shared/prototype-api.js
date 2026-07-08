/**
 * PrototypeAPI — simulates the real FastAPI backend using sessionStorage.
 * Seeded from window.DEMO_DATA (data/demo-data.js), not fetch() — see
 * Scenario 01's write-up: ../01-Ritas-Trust-Call-Prototype/stories/01.1.4-*.md
 */

const STORAGE_KEY = 'talentpilot_prototype_data_scenario03';

const PrototypeAPI = {
  async _load() {
    let raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw) {
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

  async getContentForSkill(skillId) {
    const data = await this._load();
    return data.content_catalog.find((c) => c.skillId === skillId && c.approved) || null;
  },

  async createAssignment({ employeeId, skillId, contentId }) {
    const data = await this._load();
    const newAssignment = {
      id: `assign-${Date.now()}`,
      employeeId,
      skillId,
      contentId,
      status: "Assigned",
      provenance: "Assigned",
      watchPercent: 0,
      lastUpdate: "Awaiting first watch",
      assignedDate: new Date().toISOString().slice(0, 10),
    };
    data.assignments.push(newAssignment);
    await this._save(data);

    const employee = data.employees.find((e) => e.id === employeeId);
    const skill = data.skills.find((s) => s.id === skillId);
    return { ...newAssignment, employee, skill };
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
