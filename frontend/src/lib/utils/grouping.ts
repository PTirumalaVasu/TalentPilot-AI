import { AssignmentRow } from "../../types/dashboard";

export interface GroupedEmployeeData {
  employeeName: string;
  assignments: AssignmentRow[];
}

/**
 * Group assignments by employee name and sort alphabetically.
 * Used for the admin dashboard to display employees with their skill assignments.
 */
export function groupAssignmentsByEmployee(
  assignments: AssignmentRow[]
): GroupedEmployeeData[] {
  const grouped = new Map<string, AssignmentRow[]>();

  for (const assignment of assignments) {
    const existing = grouped.get(assignment.employee_name) || [];
    grouped.set(assignment.employee_name, [...existing, assignment]);
  }

  // Convert to array and sort by employee name
  return Array.from(grouped.entries())
    .map(([employeeName, assignmentList]) => ({
      employeeName,
      assignments: assignmentList.sort((a, b) =>
        a.skill_name.localeCompare(b.skill_name)
      ),
    }))
    .sort((a, b) => a.employeeName.localeCompare(b.employeeName));
}
