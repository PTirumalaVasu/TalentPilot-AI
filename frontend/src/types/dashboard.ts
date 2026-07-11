/**
 * Dashboard types for the HR Admin dashboard grid (Story 5-1).
 */

export type StatusType = "Not Started" | "In Progress" | "Completed";
export type ProvenanceType =
  | "Verified"
  | "Self-reported"
  | "Needs Attention"
  | "HR Override";

export interface AssignmentRow {
  assignment_id: string; // UUID
  employee_id: string; // UUID
  employee_name: string;
  skill_id: string; // UUID
  skill_name: string;
  status: StatusType;
  status_percentage: number | null; // e.g., 45 for "In Progress (45%)"
  provenance: ProvenanceType;
  last_updated: string; // ISO-8601 datetime
  assignment_created_at: string; // ISO-8601 datetime
}

export interface DashboardResponse {
  assignments: AssignmentRow[];
  total_count: number;
  page: number;
  page_size: number;
}
