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
  /** Story 7.5 (FR-27): whether this employee has ever had an Assignment
   * created for them (active or soft-deleted) -- drives the Delete/Archive
   * confirmation dialog's copy (UX-DR38), mirroring
   * skillsApi.ts::SkillResponse's ever_assigned shape. */
  has_assignment_history: boolean;
}

/** GET /api/admin/employees (Story 7.3, FR-25) -- the full roster, active
 * and archived alike. Search/filter/pagination/"show archived" are all
 * applied client-side over this one fetched list, mirroring
 * skillsApi.ts::listSkillsWithContent. */
export async function listEmployees(): Promise<EmployeeResponse[]> {
  const response = await apiClient.get<EmployeeResponse[]>('/api/admin/employees');
  return response.data;
}

export interface UpdateEmployeeRequest {
  name: string;
  email: string;
  phone: string | null;
  experience: string | null;
  technologies: string | null;
  position: string | null;
  project: string | null;
  manager_name: string | null;
  location: string | null;
  department: string | null;
}

/** PATCH /api/admin/employees/{id} (Story 7.4, FR-26) -- a full replace of
 * every editable field. employee_code is immutable and deliberately absent
 * from this type/request. */
export async function updateEmployee(id: string, payload: UpdateEmployeeRequest): Promise<EmployeeResponse> {
  const response = await apiClient.patch<EmployeeResponse>(`/api/admin/employees/${id}`, payload);
  return response.data;
}

export interface DeleteOrArchiveEmployeeResponse {
  action: 'deleted' | 'archived';
}

/** DELETE /api/admin/employees/{id} (Story 7.5, FR-27) -- hard-deletes if
 * the employee has zero Assignment history, archives instead if they have
 * any; the server decides atomically at confirm time, independently of
 * whatever the confirmation dialog predicted from has_assignment_history.
 * Deliberately typed (not skillsApi.ts::deleteSkill's Promise<void>) since
 * the caller's success-toast copy depends on which action actually
 * occurred. */
export async function deleteOrArchiveEmployee(id: string): Promise<DeleteOrArchiveEmployeeResponse> {
  const response = await apiClient.delete<DeleteOrArchiveEmployeeResponse>(`/api/admin/employees/${id}`);
  return response.data;
}

export interface RegeneratePasswordResponse extends EmployeeResponse {
  /** Story 7.6 (FR-28): the new plaintext password, returned exactly once --
   * same one-time-reveal contract as EmployeeCreatedResponse.generated_password
   * (Story 7.2). Never persisted, never retrievable via any other endpoint. */
  generated_password: string;
}

/** POST /api/admin/employees/{id}/regenerate-password (Story 7.6, FR-28) --
 * invalidates the previous password immediately and returns the new
 * plaintext exactly once. No request body. */
export async function regeneratePassword(id: string): Promise<RegeneratePasswordResponse> {
  const response = await apiClient.post<RegeneratePasswordResponse>(`/api/admin/employees/${id}/regenerate-password`);
  return response.data;
}
