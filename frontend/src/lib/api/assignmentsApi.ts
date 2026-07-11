import { apiClient } from '@/lib/api/client';
import type { MyAssignmentsResponse } from '@/types/assignments';

/** GET /api/assignments -- EMPLOYEE-only (backend/app/assignments/service.py::list_my_assignments). */
export async function listMyAssignments(): Promise<MyAssignmentsResponse> {
  const response = await apiClient.get<MyAssignmentsResponse>('/api/assignments');
  return response.data;
}
