import { apiClient } from '@/lib/api/client';
import type { ContentResponse } from '@/lib/api/adminContentApi';

export interface SkillResponse {
  id: string;
  name: string;
  description: string | null;
  ever_assigned: boolean;
}

export interface SkillWithContent extends SkillResponse {
  approved_content: ContentResponse | null;
}

/** GET /api/admin/skills (Story 6.10 AC1) -- every Skill plus its currently-approved Content, if any. */
export async function listSkillsWithContent(): Promise<SkillWithContent[]> {
  const response = await apiClient.get<SkillWithContent[]>('/api/admin/skills');
  return response.data;
}

/** POST /api/admin/skills (Story 6.2, FR-20). */
export async function createSkill(body: { name: string; description: string | null }): Promise<SkillResponse> {
  const response = await apiClient.post<SkillResponse>('/api/admin/skills', body);
  return response.data;
}

/** PATCH /api/admin/skills/{id} (Story 6.3, FR-21). Omitted fields are left unchanged. */
export async function updateSkill(
  skillId: string,
  body: { name?: string; description?: string | null }
): Promise<SkillResponse> {
  const response = await apiClient.patch<SkillResponse>(`/api/admin/skills/${skillId}`, body);
  return response.data;
}

/** DELETE /api/admin/skills/{id} (Story 6.3, FR-22). */
export async function deleteSkill(skillId: string): Promise<void> {
  await apiClient.delete(`/api/admin/skills/${skillId}`);
}
