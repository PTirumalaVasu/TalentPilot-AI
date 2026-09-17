import { apiClient } from '@/lib/api/client';

export interface EmployeeResponse {
  id: string;
  employee_code: string;
  /** Auto-derived server-side as `${first_name} ${last_name}` (Story 10.2)
   * -- kept for other features that display a natural "First Last" name;
   * the roster grid itself formats first_name/last_name as "Last, First". */
  name: string;
  first_name: string;
  last_name: string;
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
  /** Story 10.2 (FR-34/FR-35): whole days since created_at, computed
   * server-side on every read -- never stored. */
  days_in_talent_pool: number;
}

/** GET /api/admin/employees (Story 7.3, FR-25) -- the full roster, active
 * and archived alike. Search/filter/pagination/"show archived" are all
 * applied client-side over this one fetched list, mirroring
 * skillsApi.ts::listSkillsWithContent. */
export async function listEmployees(): Promise<EmployeeResponse[]> {
  const response = await apiClient.get<EmployeeResponse[]>('/api/admin/employees');
  return response.data;
}

export interface CreateEmployeeRequest {
  employee_code: string;
  first_name: string;
  last_name: string;
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

export interface EmployeeCreatedResponse extends EmployeeResponse {
  /** Story 7.2 (FR-24): the generated plaintext password, returned exactly
   * once -- same one-time-reveal contract as RegeneratePasswordResponse.
   * generated_password (Story 7.6). Never persisted, never retrievable via
   * any other endpoint. */
  generated_password: string;
}

/** POST /api/admin/employees (Story 7.2, FR-24) -- creates the Employee
 * plus its paired login Account in one transaction; the server generates
 * the password. 409 on a collision with an existing employee_code (exact
 * match) or email (case-insensitive), active or archived. */
export async function createEmployee(payload: CreateEmployeeRequest): Promise<EmployeeCreatedResponse> {
  const response = await apiClient.post<EmployeeCreatedResponse>('/api/admin/employees', payload);
  return response.data;
}

export interface UpdateEmployeeRequest {
  first_name: string;
  last_name: string;
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
