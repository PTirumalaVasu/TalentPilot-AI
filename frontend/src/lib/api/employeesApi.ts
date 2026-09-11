import { apiClient } from '@/lib/api/client';

export interface EmployeeResponse {
  id: string;
  employee_code: string;
  name: string;
  email: string;
  role: string;
  phone: string | null;
  experience: string | null;
  technologies: string | null;
  position: string | null;
  project: string | null;
  manager_name: string | null;
  location: string | null;
  department: string | null;
  created_at: string;
  updated_at: string;
  archived_at: string | null;
}

/** GET /api/admin/employees (Story 7.3, FR-25) -- the full roster, active
 * and archived alike. Search/filter/pagination/"show archived" are all
 * applied client-side over this one fetched list, mirroring
 * skillsApi.ts::listSkillsWithContent. */
export async function listEmployees(): Promise<EmployeeResponse[]> {
  const response = await apiClient.get<EmployeeResponse[]>('/api/admin/employees');
  return response.data;
}
