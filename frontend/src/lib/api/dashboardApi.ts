import { apiClient } from '@/lib/api/client';
import type { AssignmentStatus } from '@/lib/api/assignmentsApi';

/**
 * A single Assignment row for the HR dashboard list (Story 3.5, expanded at
 * user request to derive real per-row Status/Progress rather than the
 * original placeholder). Matches the backend's `DashboardAssignmentRow` —
 * `status`/`progress_percent`/`provenance` are computed server-side from
 * real `skill_progress` data (AD-3: `progress/` is the sole derivation
 * authority), not hardcoded. Still not the final Epic 5 grid: no
 * Provenance drill-down (Story 5.2), no Needs-Attention staleness
 * threshold (Story 5.3), no live 10-15s auto-polling (Story 5.4).
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
  return response.data;
}
