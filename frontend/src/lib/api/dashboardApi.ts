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

export const dashboardApi = {
  getDashboardAssignments,
  getDashboard,
  getDrillDown,
};
