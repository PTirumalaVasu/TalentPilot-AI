import { apiClient } from '@/lib/api/client';
import type { AssignmentStatus } from '@/lib/api/assignmentsApi';
import { DashboardResponse } from "../../types/dashboard";

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

export const dashboardApi = {
  getDashboardAssignments,
  getDashboard,
};
