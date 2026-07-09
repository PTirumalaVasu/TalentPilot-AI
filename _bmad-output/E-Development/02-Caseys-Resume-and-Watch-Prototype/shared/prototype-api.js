/**
 * PrototypeAPI — simulates the real FastAPI backend using sessionStorage.
 * Seeded from window.DEMO_DATA (data/demo-data.js), not fetch() — fetch() of
 * a local file is blocked by browsers under file://, which breaks the
 * "just double-click, no server" prototype promise. See Scenario 01's
 * write-up: ../01-Ritas-Trust-Call-Prototype/stories/01.1.4-*.md
 */

const STORAGE_KEY = 'talentpilot_prototype_data_scenario02';

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

  async getUser() {
    const data = await this._load();
    return data.currentUser;
  },

  async getContentDiscovery() {
    const data = await this._load();
    return data.contentDiscovery;
  },

  async getContinueWatching() {
    const data = await this._load();
    return data.continueWatching;
  },

  async getAssignedVideos() {
    const data = await this._load();
    return data.contentDiscovery.assignedVideos || [];
  },

  async selectVideo(videoId) {
    const data = await this._load();
    const video = data.contentDiscovery.assignedVideos.find(v => v.id === videoId);
    if (video) {
      sessionStorage.setItem('selected_video', JSON.stringify(video));
      return video;
    }
    throw new Error(`Video with id ${videoId} not found`);
  },

  async getSelectedVideo() {
    const stored = sessionStorage.getItem('selected_video');
    if (stored) {
      return JSON.parse(stored);
    }
    return null;
  },

  async getSkills() {
    const data = await this._load();
    return data.skills || [];
  },

  async getEmployeeAssignments(employeeId) {
    const data = await this._load();
    return data.contentDiscovery.assignedVideos || [];
  },

  async getSelectedSkillDetails() {
    const selected = await this.getSelectedVideo();
    if (selected && selected.skillId) {
      const skills = await this.getSkills();
      return skills.find(s => s.id === selected.skillId);
    }
    return null;
  },

  async getEmployees() {
    const data = await this._load();
    return data.employees || [];
  },

  async getEmployeeVideos(employeeId) {
    const data = await this._load();
    if (data.employeeAssignments && data.employeeAssignments[employeeId]) {
      return data.employeeAssignments[employeeId].assignedVideos;
    }
    // Fallback to contentDiscovery if no employee-specific data
    return data.contentDiscovery.assignedVideos || [];
  },

  async setSelectedEmployee(employeeId) {
    sessionStorage.setItem('selected_employee_id', employeeId);
  },

  async getSelectedEmployeeId() {
    return sessionStorage.getItem('selected_employee_id') || 'emp-casey';
  },

  async getSelectedEmployee() {
    const employeeId = await this.getSelectedEmployeeId();
    const employees = await this.getEmployees();
    return employees.find(e => e.id === employeeId);
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
