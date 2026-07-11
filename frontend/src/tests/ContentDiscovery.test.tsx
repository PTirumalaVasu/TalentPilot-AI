import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { AuthProvider } from '@/lib/auth/AuthContext';
import { ContentDiscovery } from '@/pages/employee/ContentDiscovery';
import type { MyAssignmentsResponse } from '@/types/assignments';

const navigateMock = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return { ...actual, useNavigate: () => navigateMock };
});

vi.mock('@/lib/api/authApi', () => ({
  logout: vi.fn().mockResolvedValue(undefined),
}));

vi.mock('@/lib/api/assignmentsApi', () => ({
  listMyAssignments: vi.fn(),
}));

import { logout } from '@/lib/api/authApi';
import { listMyAssignments } from '@/lib/api/assignmentsApi';

function renderPage() {
  return render(
    <MemoryRouter>
      <AuthProvider>
        <ContentDiscovery />
      </AuthProvider>
    </MemoryRouter>
  );
}

const mixedResponse: MyAssignmentsResponse = {
  total: 2,
  in_progress_count: 1,
  to_start_count: 1,
  assignments: [
    {
      assignment_id: 'a1',
      skill_id: 's1',
      skill_name: 'Data Visualization',
      content: {
        id: 'c1',
        skill_id: 's1',
        title: 'Excel Charting Tutorial',
        description: 'Learn to build charts',
        type: 'VIDEO',
        url: 'https://www.youtube.com/watch?v=abc123',
        source: 'YOUTUBE',
        ingested_at: '2026-07-01T00:00:00Z',
        metadata: { duration: 'PT10M0S' },
      },
      watch_position: 300,
      status: 'IN_PROGRESS',
      group: 'IN_PROGRESS',
    },
    {
      assignment_id: 'a2',
      skill_id: 's2',
      skill_name: 'Python Programming',
      content: null,
      watch_position: 0,
      status: 'NOT_STARTED',
      group: 'TO_START',
    },
  ],
};

describe('ContentDiscovery', () => {
  beforeEach(() => {
    vi.mocked(logout).mockClear();
    navigateMock.mockReset();
    vi.mocked(listMyAssignments).mockReset();
  });

  it('shows a loading state before data arrives', () => {
    vi.mocked(listMyAssignments).mockReturnValue(new Promise(() => {}));
    renderPage();

    expect(screen.getByTestId('content-discovery-loading')).toBeInTheDocument();
  });

  it('renders the grid with mixed groups, stats, and per-card details once loaded', async () => {
    vi.mocked(listMyAssignments).mockResolvedValue(mixedResponse);
    renderPage();

    await waitFor(() => expect(screen.getByText('Data Visualization')).toBeInTheDocument());

    expect(screen.getByText('Python Programming')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /in progress/i })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /to start/i })).toBeInTheDocument();
    // Status badge is icon + text, never color-only (AC10/NFR-A2).
    expect(screen.getByText('⟳')).toBeInTheDocument();
  });

  it('renders the Completed badge for a COMPLETED assignment, still grouped under In Progress', async () => {
    const completedResponse: MyAssignmentsResponse = {
      total: 1,
      in_progress_count: 1,
      to_start_count: 0,
      assignments: [
        {
          assignment_id: 'a3',
          skill_id: 's3',
          skill_name: 'SQL Fundamentals',
          content: {
            id: 'c3',
            skill_id: 's3',
            title: 'SQL Joins Explained',
            description: 'Master SQL joins',
            type: 'VIDEO',
            url: 'https://www.youtube.com/watch?v=xyz789',
            source: 'YOUTUBE',
            ingested_at: '2026-07-01T00:00:00Z',
            metadata: { duration: 'PT10M0S' },
          },
          watch_position: 600,
          status: 'COMPLETED',
          group: 'IN_PROGRESS',
        },
      ],
    };
    vi.mocked(listMyAssignments).mockResolvedValue(completedResponse);
    renderPage();

    await waitFor(() => expect(screen.getByText('SQL Fundamentals')).toBeInTheDocument());

    // COMPLETED status folds into the In Progress section (Dev Notes' deliberate decision).
    expect(screen.getByRole('heading', { name: /in progress/i })).toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: /to start/i })).not.toBeInTheDocument();
    expect(screen.getByText('✓')).toBeInTheDocument();
    expect(screen.getByText('Completed')).toBeInTheDocument();
    expect(screen.getByText('100% watched')).toBeInTheDocument();
  });

  it('does not suppress the nested "Contact Rita" link\'s own keyboard activation on a no-content card', async () => {
    vi.mocked(listMyAssignments).mockResolvedValue(mixedResponse);
    renderPage();

    await waitFor(() => expect(screen.getByText('Python Programming')).toBeInTheDocument());

    const link = screen.getByRole('link', { name: /contact rita/i });
    // jsdom doesn't perform the browser's default mailto-navigation on Enter,
    // but it does dispatch a real keydown that bubbles -- this proves the
    // ancestor Card's onKeyDown no longer calls preventDefault() on it
    // (previously it did, for every Enter/Space keydown regardless of target).
    const keydownEvent = new KeyboardEvent('keydown', { key: 'Enter', bubbles: true, cancelable: true });
    const wasPrevented = !link.dispatchEvent(keydownEvent);

    expect(wasPrevented).toBe(false);
    // The card's own activation must not fire either -- this keydown targeted the link, not the card.
    expect(navigateMock).not.toHaveBeenCalled();
  });

  it('renders a page-level empty state when there are zero assignments', async () => {
    vi.mocked(listMyAssignments).mockResolvedValue({
      total: 0,
      in_progress_count: 0,
      to_start_count: 0,
      assignments: [],
    });
    renderPage();

    await waitFor(() => expect(screen.getByText(/nothing in progress right now/i)).toBeInTheDocument());
  });

  it('renders a per-card empty state for an assignment with no matched content', async () => {
    vi.mocked(listMyAssignments).mockResolvedValue(mixedResponse);
    renderPage();

    await waitFor(() =>
      expect(screen.getByText(/no recommended content yet for this skill/i)).toBeInTheDocument()
    );
    // The card with matched content must not also show the empty-state copy.
    expect(screen.getByText('Excel Charting Tutorial')).toBeInTheDocument();
  });

  it('renders a page-level error state and supports retry on API failure', async () => {
    vi.mocked(listMyAssignments).mockRejectedValueOnce(new Error('network error'));
    renderPage();

    await waitFor(() => expect(screen.getByText(/couldn't load your assignments/i)).toBeInTheDocument());

    vi.mocked(listMyAssignments).mockResolvedValueOnce(mixedResponse);
    const user = userEvent.setup();
    await user.click(screen.getByRole('button', { name: /try again/i }));

    await waitFor(() => expect(screen.getByText('Data Visualization')).toBeInTheDocument());
  });

  it('navigates to the watch route with videoUrl/startSeconds when a card with content is activated', async () => {
    vi.mocked(listMyAssignments).mockResolvedValue(mixedResponse);
    renderPage();

    await waitFor(() => expect(screen.getByText('Data Visualization')).toBeInTheDocument());

    const user = userEvent.setup();
    const card = screen.getByRole('button', { name: /data visualization/i });
    await user.click(card);

    expect(navigateMock).toHaveBeenCalledWith('/assignments/a1/watch', {
      state: { videoUrl: 'https://www.youtube.com/watch?v=abc123', startSeconds: 300 },
    });
  });

  it('does not navigate when a card with no matched content is activated', async () => {
    vi.mocked(listMyAssignments).mockResolvedValue(mixedResponse);
    renderPage();

    await waitFor(() => expect(screen.getByText('Python Programming')).toBeInTheDocument());

    const user = userEvent.setup();
    const card = screen.getByRole('button', { name: /python programming/i });
    await user.click(card);

    expect(navigateMock).not.toHaveBeenCalled();
  });

  it('supports keyboard activation of a card via Enter', async () => {
    vi.mocked(listMyAssignments).mockResolvedValue(mixedResponse);
    renderPage();

    await waitFor(() => expect(screen.getByText('Data Visualization')).toBeInTheDocument());

    const card = screen.getByRole('button', { name: /data visualization/i });
    card.focus();
    await userEvent.keyboard('{Enter}');

    expect(navigateMock).toHaveBeenCalledWith('/assignments/a1/watch', {
      state: { videoUrl: 'https://www.youtube.com/watch?v=abc123', startSeconds: 300 },
    });
  });

  it('calls the real logout endpoint and redirects to /login', async () => {
    vi.mocked(listMyAssignments).mockResolvedValue(mixedResponse);
    const user = userEvent.setup();
    renderPage();

    await user.click(screen.getByRole('button', { name: /sign out/i }));

    expect(logout).toHaveBeenCalledTimes(1);
    expect(navigateMock).toHaveBeenCalledWith('/login', { replace: true });
  });

  it('still clears state and redirects to /login when the logout request fails', async () => {
    vi.mocked(listMyAssignments).mockResolvedValue(mixedResponse);
    vi.mocked(logout).mockRejectedValueOnce(new Error('network error'));
    const user = userEvent.setup();
    renderPage();

    await user.click(screen.getByRole('button', { name: /sign out/i }));

    expect(navigateMock).toHaveBeenCalledWith('/login', { replace: true });
  });
});
