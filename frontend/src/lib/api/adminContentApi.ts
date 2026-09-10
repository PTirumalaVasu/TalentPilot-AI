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
