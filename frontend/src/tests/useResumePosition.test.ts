/**
 * Tests for useResumePosition hook.
 *
 * Story 4-5: Resume Position Retrieval & Exact-Point Playback
 *
 * Tests cover:
 * - Fetching position on mount
 * - Loading state management
 * - Error handling (404, 403, 401, 500)
 * - First view (position 0, null event_time)
 * - Out-of-bounds fallback (position 0 with warning)
 * - Idempotent reads (no side effects)
 */

import { renderHook, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { useResumePosition } from '@/lib/hooks/useResumePosition';
import * as progressApi from '@/lib/api/progressApi';

// Mock the API
vi.mock('@/lib/api/progressApi');

describe('useResumePosition', () => {
  const assignmentId = '550e8400-e29b-41d4-a716-446655440001';
  const now = new Date().toISOString();

  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(console, 'debug').mockImplementation(() => {});
    vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('should start with loading state', () => {
    vi.mocked(progressApi.getResumePosition).mockResolvedValueOnce({
      id: '550e8400-e29b-41d4-a716-446655440099',
      assignment_id: assignmentId,
      watch_position: 300,
      event_time: now,
      verified: true,
      updated_at: now,
    });

    const { result } = renderHook(() => useResumePosition(assignmentId));

    // Initial state
    expect(result.current.isLoading).toBe(true);
    expect(result.current.position).toBe(0);
    expect(result.current.error).toBe(null);
  });

  it('should fetch position on mount and return exact value', async () => {
    const mockResponse = {
      id: '550e8400-e29b-41d4-a716-446655440099',
      assignment_id: assignmentId,
      watch_position: 872, // 14:32 - exact, not rounded
      event_time: now,
      verified: true,
      updated_at: now,
    };

    vi.mocked(progressApi.getResumePosition).mockResolvedValueOnce(mockResponse);

    const { result } = renderHook(() => useResumePosition(assignmentId));

    // Should call API
    expect(progressApi.getResumePosition).toHaveBeenCalledWith(assignmentId);

    // Wait for state update
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Verify exact position (AC2)
    expect(result.current.position).toBe(872); // Exact, no rounding
    expect(result.current.error).toBe(null);
    expect(result.current.progressResponse).toEqual(mockResponse);
  });

  it('should handle first view (position 0, null event_time)', async () => {
    const mockResponse = {
      id: null,
      assignment_id: assignmentId,
      watch_position: 0, // First view
      event_time: null, // No event_time
      verified: false,
      updated_at: null,
    };

    vi.mocked(progressApi.getResumePosition).mockResolvedValueOnce(mockResponse);

    const { result } = renderHook(() => useResumePosition(assignmentId));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // AC8: First view handling
    expect(result.current.position).toBe(0);
    expect(result.current.progressResponse?.event_time).toBeNull();
    expect(result.current.progressResponse?.verified).toBe(false);
  });

  it('should handle out-of-bounds fallback (position 0)', async () => {
    const mockResponse = {
      id: '550e8400-e29b-41d4-a716-446655440099',
      assignment_id: assignmentId,
      watch_position: 0, // Fell back to 0 (was out-of-bounds)
      event_time: now, // But event_time is preserved
      verified: false,
      updated_at: now,
    };

    vi.mocked(progressApi.getResumePosition).mockResolvedValueOnce(mockResponse);

    const { result } = renderHook(() => useResumePosition(assignmentId));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // AC3: Out-of-bounds fallback
    expect(result.current.position).toBe(0);
    expect(result.current.progressResponse?.event_time).not.toBeNull();
    // Should log diagnostic
    expect(console.debug).toHaveBeenCalled();
  });

  it('should handle 404 error (assignment not found)', async () => {
    const error = new Error('404');
    vi.mocked(progressApi.getResumePosition).mockRejectedValueOnce(error);

    const { result } = renderHook(() => useResumePosition(assignmentId));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // AC3: Fallback to 0 on error
    expect(result.current.position).toBe(0);
    expect(result.current.error).not.toBeNull();
    expect(result.current.progressResponse).toBeNull();
    expect(console.error).toHaveBeenCalled();
  });

  it('should handle 403 error (access denied)', async () => {
    const error = new Error('403');
    vi.mocked(progressApi.getResumePosition).mockRejectedValueOnce(error);

    const { result } = renderHook(() => useResumePosition(assignmentId));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // AC3: Fallback to 0 on error
    expect(result.current.position).toBe(0);
    expect(result.current.error).toContain('Access denied');
  });

  it('should handle 401 error (not authenticated)', async () => {
    const error = new Error('401');
    vi.mocked(progressApi.getResumePosition).mockRejectedValueOnce(error);

    const { result } = renderHook(() => useResumePosition(assignmentId));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // AC3: Fallback to 0 on error
    expect(result.current.position).toBe(0);
    expect(result.current.error).toContain('Not authenticated');
  });

  it('should handle 500 error (server error)', async () => {
    const error = new Error('500 Internal Server Error');
    vi.mocked(progressApi.getResumePosition).mockRejectedValueOnce(error);

    const { result } = renderHook(() => useResumePosition(assignmentId));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // AC3: Fallback to 0 on error
    expect(result.current.position).toBe(0);
    expect(result.current.error).toContain('Could not load resume position');
  });

  it('should call API only once (not multiple times on re-render)', async () => {
    const mockResponse = {
      id: '550e8400-e29b-41d4-a716-446655440099',
      assignment_id: assignmentId,
      watch_position: 300,
      event_time: now,
      verified: true,
      updated_at: now,
    };

    vi.mocked(progressApi.getResumePosition).mockResolvedValueOnce(mockResponse);

    const { rerender } = renderHook(() => useResumePosition(assignmentId));

    await waitFor(() => {
      expect(progressApi.getResumePosition).toHaveBeenCalledTimes(1);
    });

    // Re-render (same assignmentId)
    rerender();

    // API should not be called again (same dependency)
    expect(progressApi.getResumePosition).toHaveBeenCalledTimes(1);
  });

  it('should fetch new position when assignmentId changes', async () => {
    const mockResponse1 = {
      id: null,
      assignment_id: assignmentId,
      watch_position: 300,
      event_time: now,
      verified: true,
      updated_at: now,
    };

    const newAssignmentId = '550e8400-e29b-41d4-a716-446655440002';
    const mockResponse2 = {
      id: null,
      assignment_id: newAssignmentId,
      watch_position: 500,
      event_time: now,
      verified: true,
      updated_at: now,
    };

    vi.mocked(progressApi.getResumePosition)
      .mockResolvedValueOnce(mockResponse1)
      .mockResolvedValueOnce(mockResponse2);

    const { rerender, result } = renderHook(
      ({ id }) => useResumePosition(id),
      { initialProps: { id: assignmentId } }
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.position).toBe(300);
    expect(progressApi.getResumePosition).toHaveBeenCalledWith(assignmentId);

    // Change assignmentId
    rerender({ id: newAssignmentId });

    await waitFor(() => {
      expect(result.current.position).toBe(500);
    });

    // API should be called for new ID
    expect(progressApi.getResumePosition).toHaveBeenCalledWith(newAssignmentId);
    expect(progressApi.getResumePosition).toHaveBeenCalledTimes(2);
  });

  it('should be idempotent (no side effects on read)', async () => {
    const mockResponse = {
      id: '550e8400-e29b-41d4-a716-446655440099',
      assignment_id: assignmentId,
      watch_position: 300,
      event_time: now,
      verified: true,
      updated_at: now,
    };

    vi.mocked(progressApi.getResumePosition).mockResolvedValueOnce(mockResponse);

    const { result } = renderHook(() => useResumePosition(assignmentId));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    const position1 = result.current.position;

    // "Re-use" the result (no new fetch)
    const position2 = result.current.position;

    // Positions are identical (idempotent)
    expect(position1).toBe(position2);
    // API called only once
    expect(progressApi.getResumePosition).toHaveBeenCalledTimes(1);
  });
});
