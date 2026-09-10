import { apiClient } from '@/lib/api/client';

export interface ManualContentCandidate {
  title: string;
  source: 'MANUAL';
  url: string;
  duration_hours: number | null;
}

/**
 * Story 6.7 (FR-17a): "Paste a link" alternative to Story 6.6's search.
 * POST /api/admin/skills/{skillId}/content-manual -- validates the link and
 * echoes it back as a review candidate, same shape as a searched result
 * minus thumbnail_url. No content_catalog row is written by this call.
 */
export async function reviewManualContent(
  skillId: string,
  body: { url: string; title: string; duration_hours: number | null }
): Promise<ManualContentCandidate> {
  const response = await apiClient.post<ManualContentCandidate>(
    `/api/admin/skills/${skillId}/content-manual`,
    body
  );
  return response.data;
}

export interface ContentResponse {
  id: string;
  skill_id: string;
  title: string;
  description: string | null;
  type: string;
  url: string;
  source: 'YOUTUBE' | 'UDEMY' | 'MANUAL';
  ingested_at: string;
  metadata: Record<string, unknown> | null;
}

/**
 * Story 6.8 (FR-18): approves a reviewed candidate (searched or manual) as
 * Content for a Skill. POST /api/admin/content/attach -- writes a
 * content_catalog row, unlike Story 6.6/6.7's search-only endpoints.
 */
export async function attachContent(body: {
  skill_id: string;
  title: string;
  source: 'YOUTUBE' | 'UDEMY' | 'MANUAL';
  url: string;
  duration_hours: number | null;
}): Promise<ContentResponse> {
  const response = await apiClient.post<ContentResponse>('/api/admin/content/attach', body);
  return response.data;
}

/**
 * Story 6.9 (FR-23): rejects (hard-deletes) a previously-approved Content
 * row. DELETE /api/admin/content/{contentId}/reject -- 204/no body on
 * success, independent of approving a replacement.
 */
export async function rejectContent(contentId: string): Promise<void> {
  await apiClient.delete(`/api/admin/content/${contentId}/reject`);
}
