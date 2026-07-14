import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, act, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { AuthProvider } from '@/lib/auth/AuthContext';
import { DashboardStub } from '@/pages/hr/DashboardStub';

const navigateMock = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return { ...actual, useNavigate: () => navigateMock };
});

vi.mock('@/lib/api/authApi', () => ({
  logout: vi.fn().mockResolvedValue(undefined),
  getCurrentUser: vi.fn().mockRejectedValue({ isAxiosError: true, response: { status: 401 } }),
}));

vi.mock('@/lib/api/dashboardApi', () => ({
  getDashboardAssignments: vi.fn().mockResolvedValue([]),
}));

// AssignmentModal's own 3-step flow is covered by AssignmentModal.test.tsx —
// here we only need to trigger its onAssigned callback to test DashboardStub's
// own wiring (toast/highlight/refresh-error), so it's replaced with a stub
// exposing a button that invokes onAssigned with fixed test data.
vi.mock('@/features/assignments/AssignmentModal', () => ({
  AssignmentModal: ({
    onAssigned,
  }: {
    onAssigned?: (assignment: { id: string }, employeeName: string, skillName: string) => void;
  }) => (
    <>
      <button
        onClick={() =>
          onAssigned?.({ id: 'assignment-1' }, 'Casey the Continuer', 'Data Visualization')
        }
      >
        Simulate Assign
      </button>
      <button
        onClick={() =>
          onAssigned?.({ id: 'assignment-2' }, 'Morgan the Motivated', 'SQL & Databases')
        }
      >
        Simulate Assign 2
      </button>
    </>
  ),
}));

import { logout } from '@/lib/api/authApi';
import { getDashboardAssignments } from '@/lib/api/dashboardApi';

describe('DashboardStub sign out', () => {
  beforeEach(() => {
    vi.mocked(logout).mockClear();
    vi.mocked(getDashboardAssignments).mockReset().mockResolvedValue([]);
    navigateMock.mockReset();
  });

  it('calls the real logout endpoint and redirects to /login', async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <AuthProvider>
          <DashboardStub />
        </AuthProvider>
      </MemoryRouter>
    );

    await user.click(screen.getByRole('button', { name: /sign out/i }));

    expect(logout).toHaveBeenCalledTimes(1);
    expect(navigateMock).toHaveBeenCalledWith('/login', { replace: true });
  });

  it('still clears state and redirects to /login when the logout request fails', async () => {
    vi.mocked(logout).mockRejectedValueOnce(new Error('network error'));
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <AuthProvider>
          <DashboardStub />
        </AuthProvider>
      </MemoryRouter>
    );

    await user.click(screen.getByRole('button', { name: /sign out/i }));

    expect(navigateMock).toHaveBeenCalledWith('/login', { replace: true });
  });
});

describe('DashboardStub assignment-creation feedback (Story 3.5)', () => {
  beforeEach(() => {
    vi.mocked(getDashboardAssignments).mockReset().mockResolvedValue([]);
    navigateMock.mockReset();
  });

  it('re-fetches the list, shows the exact toast copy, and highlights the new row on a successful assign', async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <AuthProvider>
          <DashboardStub />
        </AuthProvider>
      </MemoryRouter>
    );
    await screen.findByText(/no assignments yet/i);

    vi.mocked(getDashboardAssignments).mockResolvedValueOnce([
      {
        id: 'assignment-1',
        employee_id: 'emp-1',
        employee_name: 'Casey the Continuer',
        skill_id: 'skill-1',
        skill_name: 'Data Visualization',
        assigned_at: '2026-07-11T00:00:00Z',
        status: 'NOT_STARTED',
        progress_percent: 0,
        provenance: 'Assigned · Awaiting first watch',
      },
    ]);

    await user.click(screen.getByRole('button', { name: /^simulate assign$/i }));

    expect(await screen.findByRole('status')).toHaveTextContent(
      '✓ Skill assigned to Casey — Data Visualization'
    );
    const row = await screen.findByTestId('assignment-row-assignment-1');
    expect(row.className).toContain('bg-amber-50');
    expect(getDashboardAssignments).toHaveBeenCalledTimes(2); // initial mount + post-assign refetch
  });

  it('shows the refresh-error state (not a lost-assignment message) when the post-assign refetch fails', async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <AuthProvider>
          <DashboardStub />
        </AuthProvider>
      </MemoryRouter>
    );
    await screen.findByText(/no assignments yet/i);

    vi.mocked(getDashboardAssignments).mockRejectedValueOnce(new Error('network error'));

    await user.click(screen.getByRole('button', { name: /^simulate assign$/i }));

    expect(await screen.findByText("Assignment saved, but dashboard didn't update.")).toBeInTheDocument();

    vi.mocked(getDashboardAssignments).mockResolvedValueOnce([]);
    await user.click(screen.getByRole('button', { name: /^retry$/i }));

    await waitFor(() =>
      expect(
        screen.queryByText("Assignment saved, but dashboard didn't update.")
      ).not.toBeInTheDocument()
    );
  });

  it('shows the success toast even when the post-assign refetch fails (code review: toast is not gated on refresh success)', async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <AuthProvider>
          <DashboardStub />
        </AuthProvider>
      </MemoryRouter>
    );
    await screen.findByText(/no assignments yet/i);

    vi.mocked(getDashboardAssignments).mockRejectedValueOnce(new Error('network error'));

    await user.click(screen.getByRole('button', { name: /^simulate assign$/i }));

    // Both the toast (the Assignment really was saved) and the distinct
    // refresh-error banner render together, rather than the refresh
    // failure suppressing the success toast entirely.
    expect(await screen.findByRole('status')).toHaveTextContent(
      '✓ Skill assigned to Casey — Data Visualization'
    );
    expect(screen.getByText("Assignment saved, but dashboard didn't update.")).toBeInTheDocument();
  });

  it('disables the refresh-error Retry button while a retry is in flight', async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <AuthProvider>
          <DashboardStub />
        </AuthProvider>
      </MemoryRouter>
    );
    await screen.findByText(/no assignments yet/i);

    vi.mocked(getDashboardAssignments).mockRejectedValueOnce(new Error('network error'));
    await user.click(screen.getByRole('button', { name: /^simulate assign$/i }));
    await screen.findByText("Assignment saved, but dashboard didn't update.");

    let resolveRetry: (value: never[]) => void = () => {};
    vi.mocked(getDashboardAssignments).mockReturnValueOnce(
      new Promise((resolve) => {
        resolveRetry = resolve;
      })
    );

    const retryButton = screen.getByRole('button', { name: /^retry$/i });
    await user.click(retryButton);

    expect(screen.getByRole('button', { name: /retrying/i })).toBeDisabled();

    resolveRetry([]);
    await waitFor(() => expect(screen.queryByRole('button', { name: /retrying/i })).not.toBeInTheDocument());
  });

  it('does not let an earlier highlight timer clear a newer row highlighted within the same window', async () => {
    vi.useFakeTimers();
    try {
      render(
        <MemoryRouter>
          <AuthProvider>
            <DashboardStub />
          </AuthProvider>
        </MemoryRouter>
      );
      await act(async () => {
        await Promise.resolve();
      });

      vi.mocked(getDashboardAssignments).mockResolvedValueOnce([
        {
          id: 'assignment-1',
          employee_id: 'e1',
          employee_name: 'Casey the Continuer',
          skill_id: 's1',
          skill_name: 'Data Visualization',
          assigned_at: '2026-07-11T00:00:00Z',
          status: 'NOT_STARTED',
        progress_percent: 0,
          provenance: 'Assigned · Awaiting first watch',
        },
      ]);
      await act(async () => {
        fireEvent.click(screen.getByRole('button', { name: /^simulate assign$/i }));
        await Promise.resolve();
        await Promise.resolve();
      });
      expect(screen.getByTestId('assignment-row-assignment-1').className).toContain('bg-amber-50');

      // Halfway through assignment-1's 4s highlight window.
      await act(async () => {
        vi.advanceTimersByTime(2000);
      });

      vi.mocked(getDashboardAssignments).mockResolvedValueOnce([
        {
          id: 'assignment-1',
          employee_id: 'e1',
          employee_name: 'Casey the Continuer',
          skill_id: 's1',
          skill_name: 'Data Visualization',
          assigned_at: '2026-07-11T00:00:00Z',
          status: 'NOT_STARTED',
        progress_percent: 0,
          provenance: 'Assigned · Awaiting first watch',
        },
        {
          id: 'assignment-2',
          employee_id: 'e2',
          employee_name: 'Morgan the Motivated',
          skill_id: 's2',
          skill_name: 'SQL & Databases',
          assigned_at: '2026-07-11T00:01:00Z',
          status: 'NOT_STARTED',
        progress_percent: 0,
          provenance: 'Assigned · Awaiting first watch',
        },
      ]);
      await act(async () => {
        fireEvent.click(screen.getByRole('button', { name: /simulate assign 2/i }));
        await Promise.resolve();
        await Promise.resolve();
      });
      expect(screen.getByTestId('assignment-row-assignment-2').className).toContain('bg-amber-50');

      // 2s further — this is when assignment-1's *original* timer would have
      // fired (4s after it was created). It must not clear assignment-2's
      // highlight, which only just started its own 4s window.
      await act(async () => {
        vi.advanceTimersByTime(2000);
      });
      expect(screen.getByTestId('assignment-row-assignment-2').className).toContain('bg-amber-50');

      // The remainder of assignment-2's own 4s window.
      await act(async () => {
        vi.advanceTimersByTime(2000);
      });
      expect(screen.getByTestId('assignment-row-assignment-2').className).not.toContain('bg-amber-50');
    } finally {
      vi.useRealTimers();
    }
  });
});
