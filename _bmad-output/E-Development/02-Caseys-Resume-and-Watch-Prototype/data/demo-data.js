/**
 * Demo data for TalentPilot-AI Scenario 02: Casey's Resume & Watch prototype.
 * Loaded as a plain script (not fetched) so it works over file:// with no
 * server needed — see Scenario 01's fetch()/file:// bug writeup
 * (../01-Ritas-Trust-Call-Prototype/stories/01.1.4-*.md) for why.
 *
 * Content Discovery and Continue Watching are independent full pages (each
 * has its own URL route per spec), so each gets its own demo state rather
 * than sharing one timeline: Content Discovery shows the fresh/0% moment,
 * Continue Watching shows the mid-progress/51% moment from the 02.2 spec's
 * own worked example (14:32 of 28:00).
 */
window.DEMO_DATA = {
  currentUser: {
    id: "user-casey",
    firstName: "Casey",
    lastName: "the Continuer",
    role: "Individual Contributor",
    email: "casey@sailssoftware.com"
  },

  contentDiscovery: {
    skillName: "Data Visualization Fundamentals",
    assignedBy: "Rita",
    status: "Assigned · Awaiting first watch",
    content: {
      title: "Data Visualization Fundamentals",
      source: "YouTube",
      durationMinutes: 28,
      approved: true,
      description: "Core principles of clear, honest data visualization."
    }
  },

  continueWatching: {
    skillName: "Data Visualization Fundamentals",
    status: "In Progress · 51% watched",
    lastUpdate: "Updated 3 days ago",
    watchedMinutes: 14,
    totalMinutes: 28,
    resumeTimestamp: "14:32",
    watchPercent: 51,
    content: {
      title: "Data Visualization Fundamentals",
      source: "YouTube",
      durationMinutes: 28
    }
  }
};
