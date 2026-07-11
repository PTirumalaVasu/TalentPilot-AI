/**
 * Continue Watching Card Component — Story 4-6
 *
 * Displays video resume progress with state machine:
 * - Empty: No video watched yet ("Start watching")
 * - Loaded: Position saved with progress bar, time labels, play button
 * - Loading: Fetching progress data (skeleton/spinner)
 * - Error: Cannot fetch progress ("Couldn't load your progress. [Try again]")
 *
 * Fetches progress via GET /api/assignments/{assignment_id}/progress (Story 4-5).
 * Passes startSeconds to parent player component for exact resume.
 *
 * Architecture Compliance:
 * - AD-2: Coaching-only boundary (reads progress, no HR access)
 * - AD-9: YouTube adapter initialization deferred to parent
 * - AD-5: Uses event-time-ordered position from Story 4-5
 *
 * Accessibility:
 * - WCAG 2.1 AA: Progress bar labeled with percentage + time (not color-only)
 * - Keyboard navigable: [Play] button reachable via Tab, activatable via Enter/Space
 * - Screen reader: Progress bar announced with ARIA label
 *
 * Responsive:
 * - Desktop (1024px+): Full layout
 * - Tablet (768px+): Compact layout
 * - Mobile (375px+): Tight layout with full-width elements
 */

import React, { useEffect, useRef, useState } from 'react';
import axios from 'axios';
import { UUID } from '../types/common';
import { SkillProgressResponse, SkillProgressResponseResume } from '../types/progress';
import { Card } from './ui/card';
import { Button } from './ui/button';

export interface ContinueWatchingCardProps {
  assignmentId: UUID;
  videoDuration: number; // in seconds (needed for remaining time calculation)
  onPlayClick: (startSeconds: number) => void; // Parent player component
}

type CardState = 'empty' | 'loading' | 'loaded' | 'error';

/**
 * Format seconds to mm:ss or hh:mm:ss human-readable format
 * Examples: 645 seconds → "10:45", 3661 seconds → "1:01:01"
 * Clamps negative values to "0:00" and handles NaN safely
 */
function formatTime(seconds: number): string {
  // Guard against negative, NaN, or non-numeric values
  const safeSeconds = Math.max(0, isNaN(seconds) ? 0 : Math.floor(seconds));

  const hours = Math.floor(safeSeconds / 3600);
  const minutes = Math.floor((safeSeconds % 3600) / 60);
  const secs = safeSeconds % 60;

  // Use hh:mm:ss if hours > 0, otherwise mm:ss
  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }
  return `${minutes}:${secs.toString().padStart(2, '0')}`;
}

/**
 * Calculate percentage of video watched (0-100)
 */
function calculatePercentage(watchPosition: number, duration: number): number {
  if (duration <= 0) return 0;
  return Math.min(100, Math.round((watchPosition / duration) * 100));
}

export const ContinueWatchingCard: React.FC<ContinueWatchingCardProps> = ({
  assignmentId,
  videoDuration,
  onPlayClick,
}) => {
  const [state, setState] = useState<CardState>('loading');
  const [progress, setProgress] = useState<SkillProgressResponseResume | null>(null);
  const [retryCount, setRetryCount] = useState(0);
  const maxRetries = 3;
  const abortControllerRef = useRef<AbortController | null>(null);

  // Fetch progress position from backend (Story 4-5)
  const fetchProgress = async () => {
    try {
      // Cancel previous request if still in-flight
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }

      abortControllerRef.current = new AbortController();
      setState('loading');

      // Validate API response has required fields
      const response = await axios.get<SkillProgressResponseResume>(
        `/api/assignments/${assignmentId}/progress`,
        {
          withCredentials: true,
          signal: abortControllerRef.current.signal,
        }
      );

      // Runtime type guard: validate watch_position is a valid number (not null/undefined/NaN)
      if (response.data.watch_position === null || response.data.watch_position === undefined || typeof response.data.watch_position !== 'number' || isNaN(response.data.watch_position)) {
        throw new Error('Invalid watch_position from API: expected number, got ' + typeof response.data.watch_position);
      }

      setProgress(response.data);

      // Determine state based on response: use id === null to detect first view (more reliable than position check)
      if (response.data.id === null) {
        // First view: no progress recorded yet (AC1)
        setState('empty');
      } else {
        // Position saved (AC2)
        setState('loaded');
      }
      setRetryCount(0);
    } catch (error) {
      // Check if error is due to AbortController signal (component unmounted or new request)
      if (error instanceof Error && error.name === 'AbortError') {
        return;
      }
      console.error('Failed to fetch progress:', error);
      setProgress(null);
      setState('error');
    }
  };

  // Fetch on mount and when assignmentId changes
  useEffect(() => {
    setRetryCount(0);
    fetchProgress();

    // Cleanup: abort request on unmount or assignmentId change
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [assignmentId]);

  // Timeout: if loading state persists for 3+ seconds, show error (AC3 timeout behavior)
  useEffect(() => {
    if (state !== 'loading') return;

    const timeoutId = setTimeout(() => {
      setState('error');
    }, 3000);

    return () => clearTimeout(timeoutId);
  }, [state]);

  const handlePlayClick = () => {
    if (progress) {
      // Clamp position to valid range before passing to parent
      const safePosition = Math.max(0, Math.min(progress.watch_position, videoDuration));
      onPlayClick(safePosition);
    } else {
      // Fallback: start from beginning (AC1)
      onPlayClick(0);
    }
  };

  const handleRetry = () => {
    if (retryCount < maxRetries) {
      setRetryCount(retryCount + 1);
      fetchProgress();
    }
  };

  // AC1: Empty State — No video watched yet
  if (state === 'empty') {
    return (
      <Card className="p-6 mb-6 bg-neutral-50 border border-neutral-200 rounded-lg">
        <div className="flex flex-col items-center gap-4 py-8">
          <h3 className="text-lg font-semibold text-neutral-900">Start watching</h3>
          <p className="text-sm text-neutral-600 text-center max-w-md">
            Ready to learn? Start the video from the beginning.
          </p>
          <Button
            onClick={handlePlayClick}
            className="mt-4"
            aria-label="Play video from beginning"
          >
            ▶ Play
          </Button>
        </div>
      </Card>
    );
  }

  // AC3: Loading State — Fetching progress data
  if (state === 'loading') {
    return (
      <Card className="p-6 mb-6 bg-neutral-50 border border-neutral-200 rounded-lg">
        <div className="flex flex-col items-center gap-4 py-8">
          {/* Skeleton loader */}
          <div className="w-full h-8 bg-neutral-300 rounded animate-pulse" />
          <p className="text-sm text-neutral-500">Loading...</p>
        </div>
      </Card>
    );
  }

  // AC4: Error State — Cannot fetch progress
  if (state === 'error') {
    return (
      <Card className="p-6 mb-6 bg-neutral-50 border border-neutral-200 rounded-lg">
        <div className="flex flex-col items-center gap-4 py-6">
          <div className="flex items-center gap-2 text-neutral-700">
            <span className="text-lg">⚠️</span>
            <span className="text-sm font-medium">Couldn't load your progress.</span>
          </div>
          {retryCount < maxRetries ? (
            <Button
              onClick={handleRetry}
              variant="outline"
              aria-label="Retry loading progress"
            >
              Try again
            </Button>
          ) : (
            <>
              <p className="text-xs text-neutral-500 text-center">
                Unable to load progress after {maxRetries} attempts.
              </p>
              <Button
                onClick={handlePlayClick}
                aria-label="Play video from beginning"
              >
                Play from beginning
              </Button>
            </>
          )}
        </div>
      </Card>
    );
  }

  // AC2: Loaded State — Video position saved
  if (state === 'loaded' && progress) {
    // Clamp watch_position to valid range [0, videoDuration] to prevent invalid resume positions
    const safeWatchPosition = Math.max(0, Math.min(progress.watch_position, videoDuration));
    const percentage = calculatePercentage(safeWatchPosition, videoDuration);
    const currentTime = formatTime(safeWatchPosition);
    const remainingSeconds = Math.max(0, videoDuration - safeWatchPosition);
    const remainingTime = formatTime(remainingSeconds);

    return (
      <Card className="p-6 mb-6 bg-white border border-neutral-200 rounded-lg">
        <div className="flex flex-col gap-4">
          {/* Progress Bar */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label htmlFor="progress-bar" className="text-sm font-medium text-neutral-900">
                Progress: {percentage}%
              </label>
            </div>
            <div className="w-full h-2 bg-neutral-300 rounded-full overflow-hidden">
              <div
                id="progress-bar"
                className="h-full bg-blue-500 rounded-full transition-all duration-300"
                style={{ width: `${percentage}%` }}
                role="progressbar"
                aria-valuenow={percentage}
                aria-valuemin={0}
                aria-valuemax={100}
                aria-label={`Video progress: ${percentage}%`}
              />
            </div>
          </div>

          {/* Time Labels */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 text-sm">
            <span className="text-neutral-700 font-medium">
              Resume at {currentTime}
            </span>
            <span className="text-neutral-600">
              {remainingTime} remaining
            </span>
          </div>

          {/* Play Button */}
          <div className="flex justify-center mt-2">
            <Button
              onClick={handlePlayClick}
              className="w-full sm:w-auto"
              aria-label={`Play video, resume at ${currentTime}`}
            >
              ▶ Play
            </Button>
          </div>
        </div>
      </Card>
    );
  }

  // Fallback (should not reach here, but provide safe default)
  return null;
};
