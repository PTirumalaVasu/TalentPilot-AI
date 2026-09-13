/**
 * Demo data for TalentPilot-AI Scenario 01: Rita's Trust Call prototype.
 * Loaded as a plain script (not fetched) so it works over file:// with no
 * server needed. Edit values here to change what Rita sees on the dashboard.
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
    { id: "emp-casey", firstName: "Casey", lastName: "the Continuer", role: "Individual Contributor", email: "casey@sailssoftware.com" },
    { id: "emp-morgan", firstName: "Morgan", lastName: "", role: "Individual Contributor", email: "morgan@sailssoftware.com" },
    { id: "emp-jordan", firstName: "Jordan", lastName: "", role: "Individual Contributor", email: "jordan@sailssoftware.com" },
    { id: "emp-sam", firstName: "Sam", lastName: "", role: "Individual Contributor", email: "sam@sailssoftware.com" },
    // Added 2026-09-13 for Scenario 06 (Skill Assignment Dashboard) — additive only,
    // the 4 employees above and all 6 original assignments below are untouched so
    // Scenario 01/04/05's already-approved behavior can't regress.
    { id: "emp-alex", firstName: "Alex", lastName: "Kim", role: "Individual Contributor", email: "alex@sailssoftware.com" },
    { id: "emp-taylor", firstName: "Taylor", lastName: "Singh", role: "Individual Contributor", email: "taylor@sailssoftware.com" },
    { id: "emp-riley", firstName: "Riley", lastName: "Brooks", role: "Individual Contributor", email: "riley@sailssoftware.com" }
  ],
  skills: [
    { id: "skill-python-basics", name: "Python Basics" },
    { id: "skill-data-viz", name: "Data Visualization Fundamentals" },
    { id: "skill-advanced-sql", name: "Advanced SQL" }
  ],
  content_catalog: [
    { id: "content-python-basics-01", skillId: "skill-python-basics", title: "Python Basics for Beginners", source: "YouTube", durationMinutes: 45, approved: true, description: "Learn Python fundamentals with practical examples and exercises." },
    { id: "content-data-viz-01", skillId: "skill-data-viz", title: "Data Visualization Fundamentals", source: "YouTube", durationMinutes: 28, approved: true, description: "Core principles of clear, honest data visualization." },
    { id: "content-advanced-sql-01", skillId: "skill-advanced-sql", title: "Advanced SQL Query Optimization", source: "Pluralsight", durationMinutes: 52, approved: true, description: "Master advanced SQL techniques for query optimization and performance tuning." }
  ],
  assignments: [
    { id: "assign-001", employeeId: "emp-casey", skillId: "skill-data-viz", contentId: "content-data-viz-01", status: "In Progress", provenance: "Verified", watchPercent: 92, lastUpdate: "2 hours ago", assignedDate: "2026-06-20" },
    { id: "assign-002", employeeId: "emp-morgan", skillId: "skill-python-basics", contentId: "content-python-basics-01", status: "Completed", provenance: "Verified", watchPercent: 100, lastUpdate: "yesterday", assignedDate: "2026-06-15" },
    { id: "assign-003", employeeId: "emp-jordan", skillId: "skill-data-viz", contentId: "content-data-viz-01", status: "In Progress", provenance: "Self-reported", watchPercent: 40, lastUpdate: "Not updated in 21 days", assignedDate: "2026-06-17",
      lastSelfReport: { value: "In progress — 40% estimated", enteredOn: "2026-06-17T15:42:00" }, watchActivity: "None recorded" },
    { id: "assign-004", employeeId: "emp-sam", skillId: "skill-python-basics", contentId: "content-python-basics-01", status: "Needs Attention", provenance: "Self-reported", watchPercent: 40, lastUpdate: "18 days old", assignedDate: "2026-06-20" },
    { id: "assign-005", employeeId: "emp-sam", skillId: "skill-data-viz", contentId: "content-data-viz-01", status: "Assigned", provenance: "Assigned", watchPercent: 0, lastUpdate: "Awaiting first watch", assignedDate: "2026-06-25" },
    { id: "assign-006", employeeId: "emp-sam", skillId: "skill-advanced-sql", contentId: "content-advanced-sql-01", status: "Assigned", provenance: "Assigned", watchPercent: 0, lastUpdate: "Awaiting first watch", assignedDate: "2026-06-26" },
    // Added 2026-09-13 for Scenario 06 (Skill Assignment Dashboard, page 06.1).
    // Alex: both Completed/Verified -> On Track. Taylor: in-progress, no flag -> In Progress bucket.
    // Riley: provenance is genuinely "Needs Attention" (correctly modeled, not conflated with Status
    // the way assign-004 above is — see 06.1 work file's known_pre_existing_bug_not_fixed_here note) -> the one Needs Attention example in this demo dataset.
    { id: "assign-007", employeeId: "emp-alex", skillId: "skill-python-basics", contentId: "content-python-basics-01", status: "Completed", provenance: "Verified", watchPercent: 100, lastUpdate: "3 days ago", assignedDate: "2026-08-01" },
    { id: "assign-008", employeeId: "emp-alex", skillId: "skill-data-viz", contentId: "content-data-viz-01", status: "Completed", provenance: "Verified", watchPercent: 100, lastUpdate: "1 day ago", assignedDate: "2026-08-05" },
    { id: "assign-009", employeeId: "emp-taylor", skillId: "skill-python-basics", contentId: "content-python-basics-01", status: "In Progress", provenance: "Verified", watchPercent: 55, lastUpdate: "6 hours ago", assignedDate: "2026-08-10" },
    { id: "assign-010", employeeId: "emp-taylor", skillId: "skill-advanced-sql", contentId: "content-advanced-sql-01", status: "In Progress", provenance: "Self-reported", watchPercent: 70, lastUpdate: "2 days ago", assignedDate: "2026-08-12" },
    { id: "assign-011", employeeId: "emp-riley", skillId: "skill-advanced-sql", contentId: "content-advanced-sql-01", status: "In Progress", provenance: "Needs Attention", watchPercent: 35, lastUpdate: "Not updated in 15 days", assignedDate: "2026-07-20" }
  ]
};
