/**
 * TalentPilotAuth — mock login/session gate for the prototype layer.
 * Sessions live in sessionStorage only, matching PrototypeAPI (no backend,
 * no real credential store). Same account list and logic duplicated in
 * every prototype folder's shared/auth.js — see
 * evolution/specs/authentication-login-gate.md for why duplication over a
 * true shared file was chosen (each folder is opened standalone via file://).
 */

const DEMO_ACCOUNTS = [
  { email: 'rita@sailssoftware.com', password: 'demo123', role: 'HR', firstName: 'Rita', lastName: 'the Referee' },
  { email: 'casey@sailssoftware.com', password: 'demo123', role: 'Employee', employeeId: 'emp-casey', firstName: 'Casey', lastName: 'the Continuer' },
  { email: 'morgan@sailssoftware.com', password: 'demo123', role: 'Employee', employeeId: 'emp-morgan', firstName: 'Morgan', lastName: '' },
  { email: 'jordan@sailssoftware.com', password: 'demo123', role: 'Employee', employeeId: 'emp-jordan', firstName: 'Jordan', lastName: '' },
  { email: 'sam@sailssoftware.com', password: 'demo123', role: 'Employee', employeeId: 'emp-sam', firstName: 'Sam', lastName: '' },
];

const TalentPilotAuth = {
  SESSION_KEY: 'talentpilot_auth_session',

  login(email, password) {
    const account = DEMO_ACCOUNTS.find(
      (a) => a.email.toLowerCase() === String(email).trim().toLowerCase() && a.password === password
    );
    if (!account) return null;

    const session = {
      email: account.email,
      role: account.role,
      firstName: account.firstName,
      lastName: account.lastName,
      employeeId: account.employeeId || null,
    };
    sessionStorage.setItem(this.SESSION_KEY, JSON.stringify(session));

    if (session.employeeId) {
      // Written directly (not via PrototypeAPI.setSelectedEmployee) because
      // login.html doesn't load shared/prototype-api.js — PrototypeAPI reads
      // this exact sessionStorage key, so this stays in sync without it.
      sessionStorage.setItem('selected_employee_id', session.employeeId);
    }
    return session;
  },

  getSession() {
    const raw = sessionStorage.getItem(this.SESSION_KEY);
    return raw ? JSON.parse(raw) : null;
  },

  logout() {
    sessionStorage.removeItem(this.SESSION_KEY);
    window.location.href = 'login.html';
  },

  requireRole(role) {
    const session = this.getSession();
    if (!session || session.role !== role) {
      window.location.replace('login.html');
      return null;
    }
    return session;
  },
};

window.TalentPilotAuth = TalentPilotAuth;
window.DEMO_ACCOUNTS = DEMO_ACCOUNTS;
