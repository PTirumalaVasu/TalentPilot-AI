import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { createRef } from 'react';
import { AssignmentsList, type AssignmentsListHandle } from '@/features/dashboard/AssignmentsList';

vi.mock('@/lib/api/dashboardApi', () => ({
  getDashboardAssignments: vi.fn(),
}));

import { getDashboardAssignments } from '@/lib/api/dashboardApi';

const ROW = {
  id: 'assignment-1',
  employee_id: 'emp-1',
  employee_name: 'Casey the Continuer',
  skill_id: 'skill-1',
  skill_name: 'Data Visualization',
  assigned_at: '2026-07-11T00:00:00Z',
  status: 'NOT_STARTED' as const,
  progress_percent: 0,
  provenance: 'Assigned · Awaiting first watch',
};

const IN_PROGRESS_ROW = {
  ...ROW,
  id: 'assignment-2',
  employee_name: 'Morgan the Motivated',
  status: 'IN_PROGRESS' as const,
  progress_percent: 40,
  provenance: 'Verified · 40% watched',
};

const COMPLETED_ROW = {
  ...ROW,
  id: 'assignment-3',
  employee_name: 'Sam the Stellar',
  status: 'COMPLETED' as const,
  progress_percent: 100,
  provenance: 'Verified · 100% watched',
};

describe('AssignmentsList', () => {
  beforeEach(() => {
    vi.mocked(getDashboardAssignments).mockReset();
  });

  it('renders rows returned by the dashboard API with real Status/Progress', async () => {
    vi.mocked(getDashboardAssignments).mockResolvedValue([ROW, IN_PROGRESS_ROW, COMPLETED_ROW]);
    render(<AssignmentsList />);

    expect(await screen.findByText('Casey the Continuer')).toBeInTheDocument();
    expect(screen.getAllByText('Data Visualization').length).toBe(3);
    expect(screen.getByText('Not Started')).toBeInTheDocument();
    expect(screen.getByText('In Progress')).toBeInTheDocument();
    expect(screen.getByText('Completed')).toBeInTheDocument();
  });

  it('shows a color-coded status badge and a progress bar reflecting progress_percent', async () => {
    vi.mocked(getDashboardAssignments).mockResolvedValue([IN_PROGRESS_ROW]);
    render(<AssignmentsList />);

    const badge = await screen.findByText('In Progress');
    expect(badge.className).toContain('bg-yellow-100');

    const bar = screen.getByRole('progressbar');
    expect(bar).toHaveAttribute('aria-valuenow', '40');
  });

  it('shows the total assignment count', async () => {
    vi.mocked(getDashboardAssignments).mockResolvedValue([ROW, IN_PROGRESS_ROW]);
    render(<AssignmentsList />);

    expect(await screen.findByText('Total: 2 assignments')).toBeInTheDocument();
  });

  it('shows an empty state when there are no assignments', async () => {
    vi.mocked(getDashboardAssignments).mockResolvedValue([]);
    render(<AssignmentsList />);

    expect(await screen.findByText(/no assignments yet/i)).toBeInTheDocument();
    expect(screen.getByText('Total: 0 assignments')).toBeInTheDocument();
  });

  it('shows a load-error state with a working Retry when the initial fetch fails', async () => {
    vi.mocked(getDashboardAssignments).mockRejectedValueOnce(new Error('network error'));
    vi.mocked(getDashboardAssignments).mockResolvedValueOnce([ROW]);
    const user = userEvent.setup();
    render(<AssignmentsList />);

    expect(await screen.findByText("Couldn't load assignments.")).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: /retry/i }));

    expect(await screen.findByText('Casey the Continuer')).toBeInTheDocument();
  });

  it('gives every column header an explicit scope="col"', async () => {
    vi.mocked(getDashboardAssignments).mockResolvedValue([ROW]);
    render(<AssignmentsList />);

    const headers = await screen.findAllByRole('columnheader');
    expect(headers.length).toBeGreaterThan(0);
    headers.forEach((header) => expect(header).toHaveAttribute('scope', 'col'));
  });

  it('highlights the row matching highlightedId', async () => {
    vi.mocked(getDashboardAssignments).mockResolvedValue([ROW]);
    render(<AssignmentsList highlightedId="assignment-1" />);

    const row = await screen.findByTestId('assignment-row-assignment-1');
    expect(row.className).toContain('bg-amber-50');
  });

  it('paginates beyond the first page and Previous/Next work', async () => {
    const manyRows = Array.from({ length: 15 }, (_, i) => ({
      ...ROW,
      id: `assignment-${i}`,
      employee_name: `Employee ${i}`,
    }));
    vi.mocked(getDashboardAssignments).mockResolvedValue(manyRows);
    const user = userEvent.setup();
    render(<AssignmentsList />);

    expect(await screen.findByText('Employee 0')).toBeInTheDocument();
    expect(screen.queryByText('Employee 10')).not.toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: /^next$/i }));
    expect(await screen.findByText('Employee 10')).toBeInTheDocument();
    expect(screen.queryByText('Employee 0')).not.toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: /^previous$/i }));
    expect(await screen.findByText('Employee 0')).toBeInTheDocument();
  });

  it('exposes an imperative refetch() that re-fetches and reports success/failure', async () => {
    vi.mocked(getDashboardAssignments).mockResolvedValueOnce([]);
    const ref = createRef<AssignmentsListHandle>();
    render(<AssignmentsList ref={ref} />);
    await waitFor(() => expect(getDashboardAssignments).toHaveBeenCalledTimes(1));

    vi.mocked(getDashboardAssignments).mockResolvedValueOnce([ROW]);
    let ok = false;
    await act(async () => {
      ok = await ref.current!.refetch();
    });

    expect(ok).toBe(true);
    expect(await screen.findByText('Casey the Continuer')).toBeInTheDocument();

    vi.mocked(getDashboardAssignments).mockRejectedValueOnce(new Error('network error'));
    let failed = true;
    await act(async () => {
      failed = await ref.current!.refetch();
    });
    expect(failed).toBe(false);
  });

  it('does not let a stale (slower, superseded) refetch response overwrite fresher data', async () => {
    // Realistic trigger: two overlapping refetch() calls after the initial
    // mount has already settled (e.g. a double-clicked Retry) — the first
    // is slow, the second is fast, and the first must not clobber the
    // second's result when it finally resolves.
    vi.mocked(getDashboardAssignments).mockResolvedValueOnce([ROW]);
    const ref = createRef<AssignmentsListHandle>();
    render(<AssignmentsList ref={ref} />);
    await screen.findByText('Casey the Continuer');

    let resolveSlow: (rows: (typeof ROW)[]) => void = () => {};
    const slowCall = new Promise<(typeof ROW)[]>((resolve) => {
      resolveSlow = resolve;
    });
    vi.mocked(getDashboardAssignments).mockReturnValueOnce(slowCall);
    const NEWER_ROW = { ...ROW, id: 'assignment-2', employee_name: 'Morgan the Motivated' };
    vi.mocked(getDashboardAssignments).mockResolvedValueOnce([NEWER_ROW]);

    let slowResult: Promise<boolean>;
    await act(async () => {
      slowResult = ref.current!.refetch(); // starts the slow call, doesn't await it
      await Promise.resolve();
      await ref.current!.refetch(); // starts and resolves the fast call first
    });
    expect(await screen.findByText('Morgan the Motivated')).toBeInTheDocument();

    // The slow call finally resolves — its (now stale) data must not
    // overwrite the newer refetch's result.
    await act(async () => {
      resolveSlow([ROW]);
      await slowResult;
    });
    expect(screen.getByText('Morgan the Motivated')).toBeInTheDocument();
    expect(screen.queryByText('Casey the Continuer')).not.toBeInTheDocument();
  });

  it('disables its own Retry button while a retry is in flight', async () => {
    vi.mocked(getDashboardAssignments).mockRejectedValueOnce(new Error('network error'));
    const user = userEvent.setup();
    render(<AssignmentsList />);
    await screen.findByText("Couldn't load assignments.");

    let resolveRetry: (rows: (typeof ROW)[]) => void = () => {};
    vi.mocked(getDashboardAssignments).mockReturnValueOnce(
      new Promise((resolve) => {
        resolveRetry = resolve;
      })
    );

    await user.click(screen.getByRole('button', { name: /^retry$/i }));
    expect(screen.getByRole('button', { name: /retrying/i })).toBeDisabled();

    resolveRetry([ROW]);
    await waitFor(() => expect(screen.queryByRole('button', { name: /retrying/i })).not.toBeInTheDocument());
  });
});
