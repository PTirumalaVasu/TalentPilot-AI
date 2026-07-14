import { apiClient } from '@/lib/api/client';
import type { AssignmentStatus } from '@/lib/api/assignmentsApi';
import { DashboardResponse, DrillDownResponse } from "../../types/dashboard";

export interface DashboardAssignmentRow {
  id: string;
  employee_id: string;
  employee_name: string;
  skill_id: string;
  skill_name: string;
  assigned_at: string;
  status: AssignmentStatus;
  progress_percent: number;
  provenance: string;
}

async function getDashboardAssignments(): Promise<DashboardAssignmentRow[]> {
  const response = await apiClient.get<DashboardAssignmentRow[]>('/api/dashboard/assignments');
  return response.data;
}

async function getDashboard(page: number = 1, pageSize: number = 50): Promise<DashboardResponse> {
  const response = await apiClient.get<DashboardResponse>("/api/dashboard", {
    params: { page, page_size: pageSize },
  });
  return response.data;
}

async function getDrillDown(assignmentId: string): Promise<DrillDownResponse> {
  const response = await apiClient.get<DrillDownResponse>(
    `/api/assignments/${assignmentId}/progress/drill-down`
  );
  return response.data;
}

/**
 * Create or reverse an HR Override (Story 5.5/5.5b). Returns the same
 * DrillDownResponse shape as getDrillDown so callers can replace their
 * detail state directly from the response, no extra round-trip needed.
 */
async function setOverride(
  assignmentId: string,
  action: "set" | "unset",
  reason?: string
): Promise<DrillDownResponse> {
  const response = await apiClient.post<DrillDownResponse>(
    `/api/assignments/${assignmentId}/override`,
    { action, reason }
  );
  return response.data;
}

/**
 * Soft-deletes an Assignment (Story 5.7, backend already done in Story 3.7).
 * Backend returns 204 No Content -- nothing to parse.
 */
async function deleteAssignment(assignmentId: string): Promise<void> {
  await apiClient.delete(`/api/assignments/${assignmentId}`);
}

export const dashboardApi = {
  getDashboardAssignments,
  getDashboard,
  getDrillDown,
  setOverride,
  deleteAssignment,
};
