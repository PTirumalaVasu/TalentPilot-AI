/**
 * Demo data for TalentPilot-AI Scenario 05: Rita's Roster Management prototype.
 * Loaded as a plain script (not fetched) so it works over file:// with no
 * server needed — same pattern as Scenario 01/02/03's demo-data.js.
 *
 * Employee roster matches the canon 5-account demo roster already
 * established in shared/auth.js (Rita + Casey/Morgan/Jordan/Sam) — deliberately
 * NOT reinvented with new names, so this prototype's roster looks like the
 * same org as every other scenario. "Taylor Brooks" is the one deliberately
 * new hire — not in auth.js's DEMO_ACCOUNTS — since this scenario's whole
 * story is Rita creating them fresh.
 */
window.DEMO_DATA = {
  currentUser: {
    id: "user-rita",
    firstName: "Rita",
    lastName: "the Referee",
    role: "HR",
    email: "rita@sailssoftware.com"
  },
  employees: [
    {
      employeeCode: "EMP-1001", id: "emp-casey", firstName: "Casey", lastName: "the Continuer",
      email: "casey@sailssoftware.com", phone: "", experience: "2 years", technologies: "React, TypeScript",
      position: "Software Engineer", project: "Skills Dashboard", managerName: "Rita the Referee",
      location: "Remote", department: "Engineering", status: "Active", hasAssignments: true,
      createdAt: "2026-07-08", updatedAt: "2026-07-08"
    },
    {
      employeeCode: "EMP-1002", id: "emp-morgan", firstName: "Morgan", lastName: "",
      email: "morgan@sailssoftware.com", phone: "", experience: "4 years", technologies: "SQL, Python",
      position: "Data Analyst", project: "Skills Dashboard", managerName: "Rita the Referee",
      location: "Remote", department: "Analytics", status: "Active", hasAssignments: true,
      createdAt: "2026-07-08", updatedAt: "2026-07-08"
    },
    {
      employeeCode: "EMP-1003", id: "emp-jordan", firstName: "Jordan", lastName: "",
      email: "jordan@sailssoftware.com", phone: "", experience: "1 year", technologies: "Selenium, Playwright",
      position: "QA Engineer", project: "Skills Dashboard", managerName: "Rita the Referee",
      location: "Remote", department: "Engineering", status: "Active", hasAssignments: false,
      createdAt: "2026-07-08", updatedAt: "2026-07-08"
    },
    {
      employeeCode: "EMP-1004", id: "emp-sam", firstName: "Sam", lastName: "",
      email: "sam@sailssoftware.com", phone: "", experience: "6 years", technologies: "Figma, Design Systems",
      position: "Product Designer", project: "Skills Dashboard", managerName: "Rita the Referee",
      location: "Remote", department: "Design", status: "Active", hasAssignments: false,
      createdAt: "2026-07-08", updatedAt: "2026-07-08"
    }
  ],
  // Scenario 05's protagonist action creates this employee during 05.2/05.3 —
  // intentionally NOT pre-seeded here so the "before" state (05.1 without
  // Taylor) matches the scenario's own entry context.
  newHireTemplate: {
    employeeCode: "EMP-1005",
    firstName: "Taylor",
    lastName: "Brooks",
    email: "taylor.brooks@sailssoftware.com",
    position: "Software Engineer",
    department: "Engineering",
    managerName: "Rita the Referee",
    location: "Remote"
  }
};
