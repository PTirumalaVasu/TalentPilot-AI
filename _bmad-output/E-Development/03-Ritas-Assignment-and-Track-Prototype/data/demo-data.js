/**
 * Demo data for TalentPilot-AI Scenario 03: Rita's Assignment & Track prototype.
 * Loaded as a plain script (not fetched) so it works over file:// with no
 * server needed — see Scenario 01's fetch()/file:// bug write-up.
 *
 * Starting assignments match Scenario 01's dashboard exactly (Casey/Morgan/
 * Jordan/Sam) so this prototype continues the same story. Completing the
 * Skill Assignment Flow (03.1) adds a 5th row (Casey + Python Basics,
 * "Assigned · Awaiting first watch") matching the 03.2 spec's own example.
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
    { id: "emp-sam", firstName: "Sam", lastName: "", role: "Individual Contributor", email: "sam@sailssoftware.com" }
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
    { id: "assign-005", employeeId: "emp-casey", skillId: "skill-python-basics", contentId: "content-python-basics-01", status: "Assigned", provenance: "Assigned", watchPercent: 0, lastUpdate: "Awaiting first watch", assignedDate: "2026-06-25" },
    { id: "assign-006", employeeId: "emp-casey", skillId: "skill-advanced-sql", contentId: "content-advanced-sql-01", status: "Assigned", provenance: "Assigned", watchPercent: 0, lastUpdate: "Awaiting first watch", assignedDate: "2026-06-26" }
  ]
};
