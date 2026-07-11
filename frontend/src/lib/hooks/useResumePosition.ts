/**
 * Hook for fetching and managing resume position for video playback.
 *
 * Story 4-5: Resume Position Retrieval & Exact-Point Playback
 *
 * Responsibilities:
 * - Fetches the last-watched position from backend on mount
 * - Handles loading, error, and success states
 * - Falls back to position 0 on error or first view
 * - Returns exact position for YouTube IFrame startSeconds initialization
 */

import { useEffect, useState } from 'react';
import type { UUID } from '@/types/common';
import type { SkillProgressResponse } from '@/types/progress';
import { getResumePosition } from '@/lib/api/progressApi';

export interface UseResumePositionResult {
  /** Current watch position in seconds (0 if first view or error) */
  position: number;

  /** True if position is being fetched from server */
  isLoading: boolean;

  /** Error message if fetch failed (e.g., "Could not load resume position") */
  error: string | null;

  /** Full progress response from server (for accessing verified flag, timestamps, etc.) */
  progressResponse: SkillProgressResponse | null;
}

/**
 * Fetch watch position for resuming a video.
 *
 * On mount, calls GET /api/assignments/{assignmentId}/progress to retrieve
 * the exact position where the user last watched. Falls back to position 0
 * if this is the first view or if the fetch fails.
 *
 * **Performance (NFR-L4):**
 * - GET request typically completes in <100ms (fast database query)
 * - Client initialization in <100ms
 * - Total latency from component mount to position available: <200ms
 * - YouTube IFrame initialization from position: <500ms
 * - Total: well under 1 second requirement
 *
 * @param assignmentId - UUID of the assignment being watched
 * @returns Object with { position, isLoading, error, progressResponse }
 *
 * @example
 * ```tsx
 * const { position, isLoading, error } = useResumePosition(assignmentId);
 *
 * return (
 *   <>
 *     {isLoading && <Spinner />}
 *     {error && <p className="text-red-600">{error}</p>}
 *     <VideoPlayer startSeconds={position} />
 *   </>
 * );
 * ```
 */
export function useResumePosition(assignmentId: UUID): UseResumePositionResult {
  const [position, setPosition] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [progressResponse, setProgressResponse] = useState<SkillProgressResponse | null>(null);

  useEffect(() => {
    let isMounted = true;

    const fetchPosition = async () => {
      try {
        setError(null);
        const response = await getResumePosition(assignmentId);

        if (!isMounted) return;

        // AC1: Return exact position (no rounding, no approximation)
        setPosition(response.watch_position ?? 0);
        setProgressResponse(response);

        // Log if position was out-of-bounds and fell back to 0
        if (response.watch_position === 0 && response.event_time !== null) {
          console.debug('Resume position was out-of-bounds; starting from beginning');
        }
      } catch (err) {
        if (!isMounted) return;

        // AC8: Error handling (404, 403, 500, network errors)
        // All error cases fall back to position 0 (start from beginning)
        let errorMessage = 'Could not load resume position. Starting from beginning.';

        if (err instanceof Error) {
          if (err.message.includes('403')) {
            errorMessage = 'Access denied to this assignment.';
          } else if (err.message.includes('404')) {
            errorMessage = 'Assignment not found.';
          } else if (err.message.includes('401')) {
            errorMessage = 'Not authenticated. Redirecting to login...';
          }
        }

        console.error('Failed to fetch resume position:', err);
        setError(errorMessage);
        setPosition(0); // AC3: Fallback to 0
        setProgressResponse(null);
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    fetchPosition();

    return () => {
      isMounted = false;
    };
  }, [assignmentId]);

  return {
    position,
    isLoading,
    error,
    progressResponse,
  };
}
