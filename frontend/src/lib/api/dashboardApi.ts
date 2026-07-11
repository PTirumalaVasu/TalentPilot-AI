import { apiClient } from '@/lib/api/client';
import type { AssignmentStatus } from '@/lib/api/assignmentsApi';
/**
 * API client for the dashboard module (Story 5-1).
 */
import { DashboardResponse } from "../../types/dashboard";
import { client } from "./client";

export const dashboardApi = {
/**
 * A single Assignment row for the HR dashboard list (Story 3.5, expanded at
 * user request to derive real per-row Status/Progress rather than the
 * original placeholder). Matches the backend's `DashboardAssignmentRow` —
 * `status`/`progress_percent`/`provenance` are computed server-side from
 * real `skill_progress` data (AD-3: `progress/` is the sole derivation
 * authority), not hardcoded. Still not the final Epic 5 grid: no
 * Provenance drill-down (Story 5.2), no Needs-Attention staleness
 * threshold (Story 5.3), no live 10-15s auto-polling (Story 5.4).
   * Fetch HR Admin's dashboard with all assignments and their statuses.
   *
   * Implements AD-6 access control:
   * - Returns 200 OK for HR_ADMIN role
   * - Returns 403 Forbidden for EMPLOYEE role
   * - Returns 401 Unauthorized for unauthenticated requests
   *
   * @param page - Page number (1-indexed), default 1
   * @param pageSize - Rows per page, default 50
   * @returns DashboardResponse with paginated assignments
 */
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

export async function getDashboardAssignments(): Promise<DashboardAssignmentRow[]> {
  const response = await apiClient.get<DashboardAssignmentRow[]>('/api/dashboard/assignments');
  async getDashboard(page: number = 1, pageSize: number = 50): Promise<DashboardResponse> {
    const response = await client.get("/dashboard", {
      params: { page, page_size: pageSize },
    });
  return response.data;
}
