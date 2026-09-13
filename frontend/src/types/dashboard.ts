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

/**
 * Response for GET /api/dashboard/stats (Story 9.1, FR-31/FR-32) -- org-wide
 * stats and Assignment Progress breakdown for the Skill Assignment Dashboard
 * landing page (Story 9.3). `total_completed` and `completed_count` are
 * always numerically identical -- intentional, not a duplication (see the
 * backend schema's own docstring, backend/app/dashboard/schemas.py).
 */
export interface DashboardStatsResponse {
  total_employees: number;
  total_skills_assigned: number;
  total_completed: number;
  completed_count: number;
  in_progress_count: number;
  not_started_count: number;
  overall_percent: number;
}

/**
 * One flagged Assignment backing the Needs Attention segment (Story 9.2,
 * FR-32/UX-DR45). One row per flagged Assignment, not per Employee.
 */
export interface NeedsAttentionEntry {
  employee_id: string; // UUID
  employee_name: string;
  assignment_id: string; // UUID
  skill_id: string; // UUID
  skill_name: string;
}

/**
 * Response for GET /api/dashboard/segmentation (Story 9.2, FR-32/AR-27/AR-28).
 * `needs_attention_count` is the number of distinct flagged Employees
 * (matches the pie chart's segment count) -- it is NOT the length of
 * `needs_attention`, which is one row per flagged Assignment and can exceed
 * `needs_attention_count` when an Employee has more than one flagged
 * Assignment. Do not conflate the two.
 */
export interface EmployeeSegmentationResponse {
  on_track_count: number;
  in_progress_count: number;
  needs_attention_count: number;
  needs_attention: NeedsAttentionEntry[];
}
