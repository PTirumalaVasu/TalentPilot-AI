import { apiClient } from '@/lib/api/client';
import type { AssignmentStatus } from '@/lib/api/assignmentsApi';
import {
  DashboardResponse,
  DrillDownResponse,
  DashboardStatsResponse,
  EmployeeSegmentationResponse,
  ExperienceDistributionResponse,
} from "../../types/dashboard";

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

/**
 * `search` (Story 10.6, FR-38) matches Employee name or Skill name,
 * server-side (see backend/app/dashboard/router.py) -- an empty/omitted
 * value is dropped from the request entirely (axios omits `undefined`
 * params), not sent as an empty-string filter.
 */
async function getDashboard(
  page: number = 1,
  pageSize: number = 15,
  search?: string
): Promise<DashboardResponse> {
  const response = await apiClient.get<DashboardResponse>("/api/dashboard", {
    params: { page, page_size: pageSize, search: search || undefined },
  });
  return response.data;
}

/**
 * Org-wide stats + Assignment Progress breakdown for the Skill Assignment
 * Dashboard landing page (Story 9.3, consuming Story 9.1's endpoint).
 */
async function getDashboardStats(): Promise<DashboardStatsResponse> {
  const response = await apiClient.get<DashboardStatsResponse>('/api/dashboard/stats');
  return response.data;
}

/**
 * Employee Segmentation (On Track / In Progress / Needs Attention) for the
 * Skill Assignment Dashboard's pie chart (Story 9.3, consuming Story 9.2's
 * endpoint).
 */
async function getEmployeeSegmentation(): Promise<EmployeeSegmentationResponse> {
  const response = await apiClient.get<EmployeeSegmentationResponse>('/api/dashboard/segmentation');
  return response.data;
}

/**
 * Headcount broken down by years of experience for the Employees page's
 * Experience Distribution panel (Story 10.4, consuming that story's
 * dashboard/-owned endpoint, FR-36).
 */
async function getExperienceDistribution(): Promise<ExperienceDistributionResponse> {
  const response = await apiClient.get<ExperienceDistributionResponse>(
    '/api/dashboard/experience-distribution'
  );
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
  getDashboardStats,
  getEmployeeSegmentation,
  getExperienceDistribution,
  getDrillDown,
  setOverride,
  deleteAssignment,
};
