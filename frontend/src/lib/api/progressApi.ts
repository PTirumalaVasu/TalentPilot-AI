/**
 * API client for watch progress endpoints.
 *
 * Story 4-2: POST endpoint for recording watch progress
 * Story 4-5: GET endpoint for retrieving resume position
 */

import { apiClient } from '@/lib/api/client';
import type { SkillProgressResponse } from '@/types/progress';
import type { UUID } from '@/types/common';

/**
 * Get resume position for an assignment.
 *
 * **Story 4-5: Resume Position Retrieval & Exact-Point Playback**
 *
 * This endpoint:
 * - Returns the exact last-watched position (in seconds) if recorded
 * - Returns position: 0 if this is the first view
 * - Returns position: 0 if stored position is out-of-bounds (corrupted data)
 * - Is hard-scoped to the authenticated session's identity (403 Forbidden if not the assignment owner)
 *
 * @param assignmentId - UUID of the assignment
 * @returns Promise with watch position and metadata for resume initialization
 * @throws AxiosError with status 403 if user is not the assignment owner
 * @throws AxiosError with status 401 if not authenticated
 * @throws AxiosError with status 404 if assignment doesn't exist
 */
export async function getResumePosition(assignmentId: UUID): Promise<SkillProgressResponse> {
  const response = await apiClient.get<SkillProgressResponse>(
    `/api/assignments/${assignmentId}/progress`
  );
  return response.data;
}
