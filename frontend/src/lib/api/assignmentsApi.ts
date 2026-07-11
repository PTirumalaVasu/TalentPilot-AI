import { apiClient } from '@/lib/api/client';
import type { MyAssignmentsResponse } from '@/types/assignments';

export interface Employee {
  id: string;
  name: string;
  email: string;
  role: string;
}

export interface Skill {
  id: string;
  name: string;
  description: string | null;
}

export type AssignmentStatus = 'NOT_STARTED' | 'IN_PROGRESS' | 'COMPLETED';

export interface Assignment {
  id: string;
  employee_id: string;
  skill_id: string;
  content_id: string | null;
  assigned_at: string;
  assigned_by: string;
  status: AssignmentStatus;
  provenance: string;
}

export interface ContentMatch {
  id: string;
  skill_id: string;
  title: string;
  description: string | null;
  type: 'VIDEO' | 'DOCUMENT' | 'WEBSITE';
  url: string;
  source: 'YOUTUBE' | 'MANUAL';
  ingested_at: string;
  // Matches the backend's actual wire key: ContentResponse's Pydantic field
  // is `metadata: ... = Field(alias="content_metadata")`, and FastAPI
  // serializes by alias -- confirmed via a live HTTP call, since a plain
  // `metadata` key here would silently read as `undefined` against the
  // real API (code review round 2 finding).
  content_metadata: Record<string, unknown> | null;
}

export async function listEmployees(search?: string): Promise<Employee[]> {
  const response = await apiClient.get<Employee[]>('/api/assignments/employees', {
    params: search ? { search } : undefined,
  });
  return response.data;
}

export async function listSkills(search?: string): Promise<Skill[]> {
  const response = await apiClient.get<Skill[]>('/api/assignments/skills', {
    params: search ? { search } : undefined,
  });
  return response.data;
}

export async function matchContentForSkill(skillId: string): Promise<ContentMatch | null> {
  const response = await apiClient.get<ContentMatch | null>('/api/content/match', {
    params: { skill_id: skillId },
  });
  return response.data;
}

export async function checkDuplicateAssignment(employeeId: string, skillId: string): Promise<Assignment[]> {
  const response = await apiClient.get<Assignment[]>('/api/assignments/duplicate-check', {
    params: { employee_id: employeeId, skill_id: skillId },
  });
  return response.data;
}

export async function createAssignment(
  employeeId: string,
  skillId: string,
  contentId: string | null
): Promise<Assignment> {
  const response = await apiClient.post<Assignment>('/api/assignments', {
    employee_id: employeeId,
    skill_id: skillId,
    content_id: contentId,
  });
  return response.data;
}

/**
 * GET /api/assignments/employee-assignments -- EMPLOYEE-only
 * (backend/app/assignments/service.py::list_my_assignments).
 *
 * Merge note (main -> Story2.6): main's history shows this route was
 * originally `GET /api/assignments` (Story 2.5), then renamed to
 * `/employee-assignments` while chasing a suspected FastAPI routing issue.
 * A second, fully redundant router (`backend/app/progress/my_assignments.py`,
 * mounted at `/api/my-assignments`) was added later as a further workaround
 * -- both call the identical `list_my_assignments` service function, so the
 * "routing issue" was never actually in that function. This resolution
 * keeps the `/employee-assignments` route (consistent with every other
 * function in this file living under the `/api/assignments/*` resource,
 * unlike the ad hoc top-level `/api/my-assignments`) and drops the
 * try/catch-to-empty-array fallback: silently returning "0 assignments" on
 * any failure (auth error, 500, network drop) is indistinguishable from a
 * genuine empty state and directly contradicts this project's established
 * error-handling convention (Story 2.5/2.6 both require a real, visible
 * "Couldn't load your assignments. Try again" state on failure -- see
 * ContentDiscovery.tsx). Duplicate `/api/my-assignments` route is left in
 * place (out of scope for a merge-conflict resolution) but is now unused by
 * this client.
 */
export async function listMyAssignments(): Promise<MyAssignmentsResponse> {
  const response = await apiClient.get<MyAssignmentsResponse>('/api/assignments/employee-assignments');
  return response.data;
}
