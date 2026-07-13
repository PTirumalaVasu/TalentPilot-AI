/**
 * Dashboard types for the HR Admin dashboard grid (Story 5-1).
 */

export type StatusType = "Not Started" | "In Progress" | "Completed";
export type ProvenanceType =
  | "Not Started"
  | "Verified"
  | "Self-reported"
  | "Needs Attention"
  | "HR Override";

export interface AssignmentRow {
  assignment_id: string; // UUID
  employee_id: string; // UUID
  employee_name: string;
  employee_group: string | null;
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

/** Response for GET /api/assignments/{id}/progress/drill-down (Story 5-2). */
export interface DrillDownResponse {
  assignment_id: string; // UUID
  employee_name: string;
  skill_name: string;
  status: "NOT_STARTED" | "IN_PROGRESS" | "COMPLETED";
  status_percentage: number | null;
  provenance: ProvenanceType;
  last_updated: string; // ISO-8601 datetime

  // HR Override case only (provenance === "HR Override")
  override_set_by_name: string | null;
  override_reason: string | null;
  override_set_at: string | null; // ISO-8601 datetime

  // Populated only alongside an active HR Override -- the non-override
  // signal that would otherwise apply (never erased by the override).
  underlying_provenance: Exclude<ProvenanceType, "HR Override"> | null;
  underlying_status: "NOT_STARTED" | "IN_PROGRESS" | "COMPLETED" | null;
  underlying_status_percentage: number | null;
}
