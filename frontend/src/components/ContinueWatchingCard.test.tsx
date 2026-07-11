/**
 * Unit Tests for ContinueWatchingCard Component — Story 4-6
 * Essential test coverage for AC1-AC10
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';

const { mockGet } = vi.hoisted(() => ({ mockGet: vi.fn() }));

vi.mock('axios', () => ({
  default: {
    get: mockGet,
  },
}));

import { ContinueWatchingCard } from './ContinueWatchingCard';

const mockAssignmentId = '550e8400-e29b-41d4-a716-446655440001' as any;
const mockVideoDuration = 600; // 10 minutes

describe('ContinueWatchingCard', () => {
  beforeEach(() => {
    mockGet.mockClear();
  });

  // AC1: Empty State
  it('AC1: renders empty state when no watch history', async () => {
    const progressData: any = {
      id: null,
      assignment_id: mockAssignmentId,
      watch_position: 0,
      event_time: null,
      verified: false,
      updated_at: null,
    };

    mockGet.mockResolvedValue({ data: progressData });
    const mockOnPlay = vi.fn();

    render(
      <ContinueWatchingCard
        assignmentId={mockAssignmentId}
        videoDuration={mockVideoDuration}
        onPlayClick={mockOnPlay}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Start watching')).toBeInTheDocument();
    });

    expect(screen.getByText(/Ready to learn/)).toBeInTheDocument();
    expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
  });

  // AC1: Empty state play button
  it('AC1: clicking [Play] on empty state calls onPlayClick(0)', async () => {
    const progressData: any = {
      id: null,
      assignment_id: mockAssignmentId,
      watch_position: 0,
      event_time: null,
      verified: false,
      updated_at: null,
    };

    mockGet.mockResolvedValue({ data: progressData });
    const mockOnPlay = vi.fn();

    render(
      <ContinueWatchingCard
        assignmentId={mockAssignmentId}
        videoDuration={mockVideoDuration}
        onPlayClick={mockOnPlay}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Start watching')).toBeInTheDocument();
    });

    const playButton = screen.getByRole('button', { name: /Play/ });
    fireEvent.click(playButton);

    expect(mockOnPlay).toHaveBeenCalledWith(0);
  });

  // AC2: Loaded State
  it('AC2: renders loaded state with saved position and progress bar', async () => {
    const progressData: any = {
      id: '550e8400-e29b-41d4-a716-446655440099',
      assignment_id: mockAssignmentId,
      watch_position: 323, // 5:23
      event_time: '2026-07-11T14:32:00Z',
      verified: true,
      updated_at: '2026-07-11T14:32:05Z',
    };

    mockGet.mockResolvedValue({ data: progressData });
    const mockOnPlay = vi.fn();

    render(
      <ContinueWatchingCard
        assignmentId={mockAssignmentId}
        videoDuration={mockVideoDuration}
        onPlayClick={mockOnPlay}
      />
    );

    await waitFor(() => {
      expect(screen.getByText(/Resume at 5:23/)).toBeInTheDocument();
    });

    const progressBar = screen.getByRole('progressbar');
    expect(progressBar).toBeInTheDocument();
    // 323/600 = 0.538333... rounds to 54%
    expect(progressBar).toHaveAttribute('aria-valuenow', '54');
    expect(screen.getByText(/4:37 remaining/)).toBeInTheDocument();
  });

  // AC2: Loaded state play button
  it('AC2: clicking [Play] on loaded state calls onPlayClick(watch_position)', async () => {
    const progressData: any = {
      id: '550e8400-e29b-41d4-a716-446655440099',
      assignment_id: mockAssignmentId,
      watch_position: 380, // 6:20 (within 10-minute video duration)
      event_time: '2026-07-11T14:32:00Z',
      verified: true,
      updated_at: '2026-07-11T14:32:05Z',
    };

    mockGet.mockResolvedValue({ data: progressData });
    const mockOnPlay = vi.fn();

    render(
      <ContinueWatchingCard
        assignmentId={mockAssignmentId}
        videoDuration={mockVideoDuration}
        onPlayClick={mockOnPlay}
      />
    );

    await waitFor(() => {
      expect(screen.getByText(/Resume at 6:20/)).toBeInTheDocument();
    });

    const playButton = screen.getByRole('button', { name: /Play video, resume at 6:20/ });
    fireEvent.click(playButton);

    expect(mockOnPlay).toHaveBeenCalledWith(380);
  });

  // AC3: Loading State
  it('AC3: renders loading state while fetching progress', async () => {
    mockGet.mockImplementation(
      () =>
        new Promise(() => {
          // Never resolves
        })
    );
    const mockOnPlay = vi.fn();

    render(
      <ContinueWatchingCard
        assignmentId={mockAssignmentId}
        videoDuration={mockVideoDuration}
        onPlayClick={mockOnPlay}
      />
    );

    expect(screen.getByText(/Loading.../)).toBeInTheDocument();
  });

  // AC4: Error State
  it('AC4: renders error state on fetch failure', async () => {
    mockGet.mockRejectedValue(new Error('Network error'));
    const mockOnPlay = vi.fn();

    render(
      <ContinueWatchingCard
        assignmentId={mockAssignmentId}
        videoDuration={mockVideoDuration}
        onPlayClick={mockOnPlay}
      />
    );

    await waitFor(() => {
      expect(screen.getByText(/Couldn't load your progress/)).toBeInTheDocument();
    });

    expect(screen.getByRole('button', { name: /Retry loading progress/ })).toBeInTheDocument();
  });

  // AC4: Error state retry
  it('AC4: [Try again] retries the fetch', async () => {
    mockGet
      .mockRejectedValueOnce(new Error('Network error'))
      .mockResolvedValueOnce({
        data: {
          id: null,
          assignment_id: mockAssignmentId,
          watch_position: 0,
          event_time: null,
          verified: false,
          updated_at: null,
        },
      });

    const mockOnPlay = vi.fn();

    render(
      <ContinueWatchingCard
        assignmentId={mockAssignmentId}
        videoDuration={mockVideoDuration}
        onPlayClick={mockOnPlay}
      />
    );

    await waitFor(() => {
      expect(screen.getByText(/Couldn't load your progress/)).toBeInTheDocument();
    });

    const retryButton = screen.getByRole('button', { name: /Retry loading progress/ });
    fireEvent.click(retryButton);

    await waitFor(() => {
      expect(screen.getByText('Start watching')).toBeInTheDocument();
    });

    expect(mockGet).toHaveBeenCalledTimes(2);
  });

  // AC5: Integration with Story 4-5
  it('AC5: fetches from GET /api/assignments/{assignment_id}/progress', async () => {
    const progressData: any = {
      id: '550e8400-e29b-41d4-a716-446655440099',
      assignment_id: mockAssignmentId,
      watch_position: 323,
      event_time: '2026-07-11T14:32:00Z',
      verified: true,
      updated_at: '2026-07-11T14:32:05Z',
    };

    mockGet.mockResolvedValue({ data: progressData });
    const mockOnPlay = vi.fn();

    render(
      <ContinueWatchingCard
        assignmentId={mockAssignmentId}
        videoDuration={mockVideoDuration}
        onPlayClick={mockOnPlay}
      />
    );

    await waitFor(() => {
      expect(mockGet).toHaveBeenCalledWith(
        `/api/assignments/${mockAssignmentId}/progress`,
        expect.objectContaining({
          withCredentials: true,
          signal: expect.any(AbortSignal),
        })
      );
    });
  });

  // AC8: Accessibility - keyboard focus
  it('AC8: [Play] button is keyboard accessible', async () => {
    const progressData: any = {
      id: null,
      assignment_id: mockAssignmentId,
      watch_position: 0,
      event_time: null,
      verified: false,
      updated_at: null,
    };

    mockGet.mockResolvedValue({ data: progressData });
    const mockOnPlay = vi.fn();

    render(
      <ContinueWatchingCard
        assignmentId={mockAssignmentId}
        videoDuration={mockVideoDuration}
        onPlayClick={mockOnPlay}
      />
    );

    await waitFor(() => {
      const playButton = screen.getByRole('button', { name: /Play/ });
      playButton.focus();
      expect(playButton).toHaveFocus();
    });
  });

  // AC8: ARIA labels for screen reader
  it('AC8: progress bar has ARIA labels for screen readers', async () => {
    const progressData: any = {
      id: '550e8400-e29b-41d4-a716-446655440099',
      assignment_id: mockAssignmentId,
      watch_position: 300,
      event_time: '2026-07-11T14:32:00Z',
      verified: true,
      updated_at: '2026-07-11T14:32:05Z',
    };

    mockGet.mockResolvedValue({ data: progressData });
    const mockOnPlay = vi.fn();

    render(
      <ContinueWatchingCard
        assignmentId={mockAssignmentId}
        videoDuration={mockVideoDuration}
        onPlayClick={mockOnPlay}
      />
    );

    await waitFor(() => {
      const progressBar = screen.getByRole('progressbar');
      expect(progressBar).toHaveAttribute('aria-valuenow');
      expect(progressBar).toHaveAttribute('aria-valuemin', '0');
      expect(progressBar).toHaveAttribute('aria-valuemax', '100');
    });
  });

  // AC9: Null-safe handling
  it('AC9: handles null event_time gracefully', async () => {
    const progressData: any = {
      id: null,
      assignment_id: mockAssignmentId,
      watch_position: 0,
      event_time: null,
      verified: false,
      updated_at: null,
    };

    mockGet.mockResolvedValue({ data: progressData });
    const mockOnPlay = vi.fn();

    render(
      <ContinueWatchingCard
        assignmentId={mockAssignmentId}
        videoDuration={mockVideoDuration}
        onPlayClick={mockOnPlay}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Start watching')).toBeInTheDocument();
    });

    expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
  });

  // AC10: State transitions - no simultaneous rendering
  it('AC10: does not render loading and content simultaneously', async () => {
    const progressData: any = {
      id: null,
      assignment_id: mockAssignmentId,
      watch_position: 0,
      event_time: null,
      verified: false,
      updated_at: null,
    };

    mockGet.mockResolvedValue({ data: progressData });
    const mockOnPlay = vi.fn();

    render(
      <ContinueWatchingCard
        assignmentId={mockAssignmentId}
        videoDuration={mockVideoDuration}
        onPlayClick={mockOnPlay}
      />
    );

    await waitFor(() => {
      const loadingText = screen.queryByText(/Loading.../);
      const startWatchingText = screen.queryByText('Start watching');

      // Only one of these should be visible at any time
      const bothVisible = loadingText && startWatchingText;
      expect(bothVisible).toBeFalsy();
    });
  });
});
