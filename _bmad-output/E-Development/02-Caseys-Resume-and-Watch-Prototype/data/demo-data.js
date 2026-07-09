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

  // Employees - Synchronized with Scenario 01 and 03
  employees: [
    { id: "emp-casey", firstName: "Casey", lastName: "the Continuer", role: "Individual Contributor", email: "casey@sailssoftware.com" },
    { id: "emp-morgan", firstName: "Morgan", lastName: "", role: "Individual Contributor", email: "morgan@sailssoftware.com" },
    { id: "emp-jordan", firstName: "Jordan", lastName: "", role: "Individual Contributor", email: "jordan@sailssoftware.com" },
    { id: "emp-sam", firstName: "Sam", lastName: "", role: "Individual Contributor", email: "sam@sailssoftware.com" }
  ],

  // Synchronized with Scenario 03 (Rita's Assignment & Track)
  skills: [
    { id: "skill-data-viz", name: "Data Visualization Fundamentals" },
    { id: "skill-python-basics", name: "Python Basics" },
    { id: "skill-advanced-sql", name: "Advanced SQL" },
    { id: "skill-excel-advanced", name: "Advanced Excel Techniques" }
  ],

  // Employee-specific assignments
  employeeAssignments: {
    "emp-casey": {
      assignedVideos: [
        {
          id: "video-1",
          employeeId: "emp-casey",
          skillId: "skill-data-viz",
          skillName: "Data Visualization Fundamentals",
          status: "In Progress · 92% watched",
          content: {
            title: "Data Visualization Fundamentals",
            source: "YouTube",
            durationMinutes: 28,
            approved: true,
            description: "Core principles of clear, honest data visualization."
          },
          watchProgress: 92
        },
        {
          id: "video-2",
          employeeId: "emp-casey",
          skillId: "skill-python-basics",
          skillName: "Python Basics",
          status: "Assigned · Awaiting first watch",
          content: {
            title: "Python Basics for Beginners",
            source: "YouTube",
            durationMinutes: 45,
            approved: true,
            description: "Learn Python fundamentals with practical examples and exercises."
          },
          watchProgress: 0
        },
        {
          id: "video-3",
          employeeId: "emp-casey",
          skillId: "skill-advanced-sql",
          skillName: "Advanced SQL",
          status: "Assigned · Awaiting first watch",
          content: {
            title: "Advanced SQL Query Optimization",
            source: "Pluralsight",
            durationMinutes: 52,
            approved: true,
            description: "Master advanced SQL techniques for query optimization and performance tuning."
          },
          watchProgress: 0
        }
      ]
    },
    "emp-sam": {
      assignedVideos: [
        {
          id: "video-4",
          employeeId: "emp-sam",
          skillId: "skill-python-basics",
          skillName: "Python Basics",
          status: "Needs Attention · 40% watched",
          content: {
            title: "Python Basics for Beginners",
            source: "YouTube",
            durationMinutes: 45,
            approved: true,
            description: "Learn Python fundamentals with practical examples and exercises."
          },
          watchProgress: 40
        },
        {
          id: "video-5",
          employeeId: "emp-sam",
          skillId: "skill-data-viz",
          skillName: "Data Visualization Fundamentals",
          status: "Assigned · Awaiting first watch",
          content: {
            title: "Data Visualization Fundamentals",
            source: "YouTube",
            durationMinutes: 28,
            approved: true,
            description: "Core principles of clear, honest data visualization."
          },
          watchProgress: 0
        },
        {
          id: "video-6",
          employeeId: "emp-sam",
          skillId: "skill-advanced-sql",
          skillName: "Advanced SQL",
          status: "Assigned · Awaiting first watch",
          content: {
            title: "Advanced SQL Query Optimization",
            source: "Pluralsight",
            durationMinutes: 52,
            approved: true,
            description: "Master advanced SQL techniques for query optimization and performance tuning."
          },
          watchProgress: 0
        }
      ]
    },
    "emp-morgan": {
      assignedVideos: [
        {
          id: "video-7",
          employeeId: "emp-morgan",
          skillId: "skill-python-basics",
          skillName: "Python Basics",
          status: "Completed · 100% watched",
          content: {
            title: "Python Basics for Beginners",
            source: "YouTube",
            durationMinutes: 45,
            approved: true,
            description: "Learn Python fundamentals with practical examples and exercises."
          },
          watchProgress: 100
        }
      ]
    },
    "emp-jordan": {
      assignedVideos: [
        {
          id: "video-8",
          employeeId: "emp-jordan",
          skillId: "skill-data-viz",
          skillName: "Data Visualization Fundamentals",
          status: "In Progress · 40% watched",
          content: {
            title: "Data Visualization Fundamentals",
            source: "YouTube",
            durationMinutes: 28,
            approved: true,
            description: "Core principles of clear, honest data visualization."
          },
          watchProgress: 40
        }
      ]
    }
  },

  // Legacy format for backward compatibility
  contentDiscovery: {
    assignedVideos: [
      {
        id: "video-1",
        employeeId: "emp-casey",
        skillId: "skill-data-viz",
        skillName: "Data Visualization Fundamentals",
        status: "In Progress · 92% watched",
        content: {
          title: "Data Visualization Fundamentals",
          source: "YouTube",
          durationMinutes: 28,
          approved: true,
          description: "Core principles of clear, honest data visualization."
        },
        watchProgress: 92
      },
      {
        id: "video-2",
        employeeId: "emp-casey",
        skillId: "skill-python-basics",
        skillName: "Python Basics",
        status: "Assigned · Awaiting first watch",
        content: {
          title: "Python Basics for Beginners",
          source: "YouTube",
          durationMinutes: 45,
          approved: true,
          description: "Learn Python fundamentals with practical examples and exercises."
        },
        watchProgress: 0
      },
      {
        id: "video-3",
        employeeId: "emp-casey",
        skillId: "skill-advanced-sql",
        skillName: "Advanced SQL",
        status: "Assigned · Awaiting first watch",
        content: {
          title: "Advanced SQL Query Optimization",
          source: "Pluralsight",
          durationMinutes: 52,
          approved: true,
          description: "Master advanced SQL techniques for query optimization and performance tuning."
        },
        watchProgress: 0
      }
    ]
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
