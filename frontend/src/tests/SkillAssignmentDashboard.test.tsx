import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { AuthProvider } from '@/lib/auth/AuthContext';
import { ThemeProvider } from '@/lib/theme/ThemeContext';
import { SkillAssignmentDashboard } from '@/pages/hr/SkillAssignmentDashboard';

vi.mock('@/lib/api/authApi', () => ({
  logout: vi.fn().mockResolvedValue(undefined),
  getMe: vi.fn().mockResolvedValue({
    user_id: 'rita-1',
    role: 'HR_ADMIN',
    name: 'Rita the Recruiter',
    email: 'rita@sails.example.com',
  }),
}));

vi.mock('@/lib/api/dashboardApi', () => ({
  dashboardApi: {
    getDashboardStats: vi.fn(),
    getEmployeeSegmentation: vi.fn(),
  },
}));

import { dashboardApi } from '@/lib/api/dashboardApi';
import type { DashboardStatsResponse, EmployeeSegmentationResponse } from '@/types/dashboard';

function makeStats(overrides: Partial<DashboardStatsResponse> = {}): DashboardStatsResponse {
  return {
    total_employees: 5,
    total_skills_assigned: 6,
    total_completed: 2,
    completed_count: 2,
    in_progress_count: 3,
    not_started_count: 1,
    overall_percent: 33,
    ...overrides,
  };
}

function makeSegmentation(
  overrides: Partial<EmployeeSegmentationResponse> = {}
): EmployeeSegmentationResponse {
  return {
    on_track_count: 2,
    in_progress_count: 2,
    needs_attention_count: 1,
    needs_attention: [
      {
        employee_id: 'emp-1',
        employee_name: 'Casey Employee',
        assignment_id: 'assign-1',
        skill_id: 'skill-1',
        skill_name: 'Data Visualization',
      },
    ],
    ...overrides,
  };
}

function renderPage() {
  return render(
    <MemoryRouter>
      <ThemeProvider>
        <AuthProvider>
          <SkillAssignmentDashboard />
        </AuthProvider>
      </ThemeProvider>
    </MemoryRouter>
  );
}

describe('SkillAssignmentDashboard', () => {
  beforeEach(() => {
    vi.mocked(dashboardApi.getDashboardStats).mockReset();
    vi.mocked(dashboardApi.getEmployeeSegmentation).mockReset();
  });

  it('shows the loading state before data resolves', async () => {
    let resolveStats!: (value: DashboardStatsResponse) => void;
    vi.mocked(dashboardApi.getDashboardStats).mockReturnValue(
      new Promise((resolve) => {
        resolveStats = resolve;
      })
    );
    vi.mocked(dashboardApi.getEmployeeSegmentation).mockReturnValue(new Promise(() => {}));

    renderPage();

    expect(screen.getByTestId('dashboard-state-loading')).toBeInTheDocument();

    // Resolve to avoid an unhandled-promise warning after the test ends.
    resolveStats(makeStats());
  });

  it('renders stats, progress ring, and segmentation once both requests resolve (AC1, AC4)', async () => {
    vi.mocked(dashboardApi.getDashboardStats).mockResolvedValue(makeStats());
    vi.mocked(dashboardApi.getEmployeeSegmentation).mockResolvedValue(makeSegmentation());

    renderPage();

    expect(await screen.findByTestId('dashboard-state-loaded')).toBeInTheDocument();

    expect(screen.getByTestId('dashboard-stat-employees')).toHaveTextContent('Total Employees');
    expect(screen.getByTestId('dashboard-stat-employees')).toHaveTextContent('5');
    expect(screen.getByTestId('dashboard-stat-skills-assigned')).toHaveTextContent('6');
    expect(screen.getByTestId('dashboard-stat-completed')).toHaveTextContent('2');

    // Progress ring: percent label + 3 labeled legend rows (never color-only).
    expect(screen.getByTestId('dashboard-progress-ring')).toHaveTextContent('33%');
    expect(screen.getByTestId('dashboard-progress-legend-completed')).toHaveTextContent('Completed — 2');
    expect(screen.getByTestId('dashboard-progress-legend-inprogress')).toHaveTextContent('In Progress — 3');
    expect(screen.getByTestId('dashboard-progress-legend-notstarted')).toHaveTextContent('Not Started — 1');

    // Segmentation: 3 labeled legend rows.
    expect(screen.getByTestId('dashboard-segmentation-legend-ontrack')).toHaveTextContent('On Track — 2');
    expect(screen.getByTestId('dashboard-segmentation-legend-inprogress')).toHaveTextContent('In Progress — 2');
    expect(screen.getByTestId('dashboard-segmentation-legend-needsattention')).toHaveTextContent(
      'Needs Attention — 1'
    );
  });

  it('renders Needs Attention as plain, non-interactive text when the count is exactly zero (AC2, UX-DR46)', async () => {
    vi.mocked(dashboardApi.getDashboardStats).mockResolvedValue(makeStats());
    vi.mocked(dashboardApi.getEmployeeSegmentation).mockResolvedValue(
      makeSegmentation({ needs_attention_count: 0, needs_attention: [] })
    );

    renderPage();
    await screen.findByTestId('dashboard-state-loaded');

    const row = screen.getByTestId('dashboard-segmentation-legend-needsattention');
    expect(row.tagName).not.toBe('BUTTON');
    expect(row.querySelector('button')).toBeNull();
    expect(row).not.toHaveAttribute('role', 'button');
    expect(screen.queryByText('Click to see who')).not.toBeInTheDocument();
    expect(screen.queryByTestId('dashboard-segmentation-hint')).not.toBeInTheDocument();
    expect(screen.queryByTestId('dashboard-needs-attention-popover')).not.toBeInTheDocument();
  });

  it('on-click, On Track / In Progress segments remain inert regardless of count (AC3, deliberate asymmetry)', async () => {
    const user = userEvent.setup();
    vi.mocked(dashboardApi.getDashboardStats).mockResolvedValue(makeStats());
    vi.mocked(dashboardApi.getEmployeeSegmentation).mockResolvedValue(makeSegmentation());

    renderPage();
    await screen.findByTestId('dashboard-state-loaded');

    await user.click(screen.getByTestId('dashboard-segmentation-legend-ontrack'));
    await user.click(screen.getByTestId('dashboard-segmentation-legend-inprogress'));

    expect(screen.getByTestId('dashboard-segmentation-legend-ontrack').tagName).not.toBe('BUTTON');
    expect(screen.getByTestId('dashboard-segmentation-legend-inprogress').tagName).not.toBe('BUTTON');
    expect(screen.queryByTestId('dashboard-needs-attention-popover')).not.toBeInTheDocument();
  });

  describe('Needs Attention popover (count > 0, AC1/AC4, Story 9.4)', () => {
    function makeTwoFlaggedAssignmentsForSameEmployee(): EmployeeSegmentationResponse {
      return makeSegmentation({
        needs_attention_count: 1,
        needs_attention: [
          {
            employee_id: 'emp-1',
            employee_name: 'Casey Employee',
            assignment_id: 'assign-1',
            skill_id: 'skill-1',
            skill_name: 'Data Visualization',
          },
          {
            employee_id: 'emp-1',
            employee_name: 'Casey Employee',
            assignment_id: 'assign-2',
            skill_id: 'skill-2',
            skill_name: 'SQL Fundamentals',
          },
        ],
      });
    }

    it('renders a real button with the exact aria-label and hint text, popover closed by default', async () => {
      vi.mocked(dashboardApi.getDashboardStats).mockResolvedValue(makeStats());
      vi.mocked(dashboardApi.getEmployeeSegmentation).mockResolvedValue(makeSegmentation());

      renderPage();
      await screen.findByTestId('dashboard-state-loaded');

      const button = screen.getByTestId('dashboard-segmentation-legend-needsattention');
      expect(button.tagName).toBe('BUTTON');
      expect(button).toHaveAttribute('aria-haspopup', 'true');
      expect(button).toHaveAttribute('aria-expanded', 'false');
      expect(button).toHaveAttribute('aria-label', 'Needs Attention, 1 employees, click to see who');
      expect(screen.getByTestId('dashboard-segmentation-hint')).toHaveTextContent('Click to see who');
      expect(screen.queryByTestId('dashboard-needs-attention-popover')).not.toBeInTheDocument();
    });

    it('opens on click, listing one row per flagged Assignment -- not deduplicated per Employee', async () => {
      const user = userEvent.setup();
      vi.mocked(dashboardApi.getDashboardStats).mockResolvedValue(makeStats());
      vi.mocked(dashboardApi.getEmployeeSegmentation).mockResolvedValue(
        makeTwoFlaggedAssignmentsForSameEmployee()
      );

      renderPage();
      await screen.findByTestId('dashboard-state-loaded');

      await user.click(screen.getByTestId('dashboard-segmentation-legend-needsattention'));

      expect(screen.getByTestId('dashboard-needs-attention-popover')).toBeInTheDocument();
      const items = screen.getAllByTestId('dashboard-needs-attention-popover-item');
      expect(items).toHaveLength(2);
      expect(items[0]).toHaveTextContent('Casey Employee — Data Visualization');
      expect(items[0]).toHaveAttribute('href', '/hr/dashboard?assignmentId=assign-1');
      expect(items[1]).toHaveTextContent('Casey Employee — SQL Fundamentals');
      expect(items[1]).toHaveAttribute('href', '/hr/dashboard?assignmentId=assign-2');
    });

    it('Escape closes the popover and returns focus to the trigger button (AC4)', async () => {
      const user = userEvent.setup();
      vi.mocked(dashboardApi.getDashboardStats).mockResolvedValue(makeStats());
      vi.mocked(dashboardApi.getEmployeeSegmentation).mockResolvedValue(makeSegmentation());

      renderPage();
      await screen.findByTestId('dashboard-state-loaded');

      const button = screen.getByTestId('dashboard-segmentation-legend-needsattention');
      await user.click(button);
      expect(screen.getByTestId('dashboard-needs-attention-popover')).toBeInTheDocument();

      await user.keyboard('{Escape}');

      expect(screen.queryByTestId('dashboard-needs-attention-popover')).not.toBeInTheDocument();
      expect(button).toHaveFocus();
    });

    it('clicking outside the popover closes it (AC4)', async () => {
      const user = userEvent.setup();
      vi.mocked(dashboardApi.getDashboardStats).mockResolvedValue(makeStats());
      vi.mocked(dashboardApi.getEmployeeSegmentation).mockResolvedValue(makeSegmentation());

      renderPage();
      await screen.findByTestId('dashboard-state-loaded');

      await user.click(screen.getByTestId('dashboard-segmentation-legend-needsattention'));
      expect(screen.getByTestId('dashboard-needs-attention-popover')).toBeInTheDocument();

      await user.click(document.body);

      expect(screen.queryByTestId('dashboard-needs-attention-popover')).not.toBeInTheDocument();
    });

    it('clicking a popover employee link closes the popover and links into the drill-down (AC1, AC4)', async () => {
      const user = userEvent.setup();
      vi.mocked(dashboardApi.getDashboardStats).mockResolvedValue(makeStats());
      vi.mocked(dashboardApi.getEmployeeSegmentation).mockResolvedValue(makeSegmentation());

      renderPage();
      await screen.findByTestId('dashboard-state-loaded');

      await user.click(screen.getByTestId('dashboard-segmentation-legend-needsattention'));
      const item = screen.getByTestId('dashboard-needs-attention-popover-item');
      expect(item).toHaveAttribute('href', '/hr/dashboard?assignmentId=assign-1');

      await user.click(item);

      expect(screen.queryByTestId('dashboard-needs-attention-popover')).not.toBeInTheDocument();
    });
  });

  it('applies a visibly larger heading token to the Segmentation card than the Progress Ring card (AC2, UX-DR44)', async () => {
    vi.mocked(dashboardApi.getDashboardStats).mockResolvedValue(makeStats());
    vi.mocked(dashboardApi.getEmployeeSegmentation).mockResolvedValue(makeSegmentation());

    renderPage();
    await screen.findByTestId('dashboard-state-loaded');

    const progressHeading = screen.getByTestId('dashboard-progress-heading');
    const segmentationHeading = screen.getByTestId('dashboard-segmentation-heading');
    expect(progressHeading).toHaveClass('text-xl');
    expect(segmentationHeading).toHaveClass('text-2xl');
    expect(progressHeading).not.toHaveClass('text-2xl');
  });

  it('shows the Empty state when there are zero active Employees, while still showing the stats row with zeros (AC3, UX spec Page States)', async () => {
    vi.mocked(dashboardApi.getDashboardStats).mockResolvedValue(makeStats({ total_employees: 0 }));
    vi.mocked(dashboardApi.getEmployeeSegmentation).mockResolvedValue(
      makeSegmentation({ on_track_count: 0, in_progress_count: 0, needs_attention_count: 0, needs_attention: [] })
    );

    renderPage();

    expect(await screen.findByTestId('dashboard-state-empty')).toHaveTextContent(
      'Nothing to show yet — assign a Skill to get started.'
    );
    expect(screen.getByRole('link', { name: '+ New Assignment' })).toBeInTheDocument();
    // UX spec's Page States table: "Stats show zeros" in the Empty state --
    // only the ring/pie region is replaced, not the whole content area.
    expect(screen.getByTestId('dashboard-stat-employees')).toHaveTextContent('0');
    expect(screen.queryByTestId('dashboard-progress-card')).not.toBeInTheDocument();
    expect(screen.queryByTestId('dashboard-segmentation-card')).not.toBeInTheDocument();
  });

  it('shows the Empty state when there are zero active Assignments (AC3)', async () => {
    vi.mocked(dashboardApi.getDashboardStats).mockResolvedValue(makeStats({ total_skills_assigned: 0 }));
    vi.mocked(dashboardApi.getEmployeeSegmentation).mockResolvedValue(
      makeSegmentation({ on_track_count: 0, in_progress_count: 0, needs_attention_count: 0, needs_attention: [] })
    );

    renderPage();

    expect(await screen.findByTestId('dashboard-state-empty')).toBeInTheDocument();
  });

  it('shows the backend\'s real error message when the rejection carries one (matches this app\'s centralized error envelope)', async () => {
    // Mirrors this codebase's real error envelope shape (backend/app/core/errors.py's
    // http_exception_handler: {"message": "...", ...}), the same shape a
    // real 403 from require_hr_admin returns -- not just the generic
    // Error()-with-no-.response fallback path the other error test covers.
    vi.mocked(dashboardApi.getDashboardStats).mockRejectedValueOnce({
      response: { data: { message: 'This action requires an HR Admin session' } },
    });
    vi.mocked(dashboardApi.getEmployeeSegmentation).mockResolvedValue(makeSegmentation());

    renderPage();

    expect(await screen.findByTestId('dashboard-state-error')).toHaveTextContent(
      'This action requires an HR Admin session'
    );
  });

  it('shows the Error state with Retry when a request fails, and Retry re-fetches (AC3)', async () => {
    const user = userEvent.setup();
    vi.mocked(dashboardApi.getDashboardStats).mockRejectedValueOnce(new Error('network down'));
    vi.mocked(dashboardApi.getEmployeeSegmentation).mockResolvedValue(makeSegmentation());

    renderPage();

    expect(await screen.findByTestId('dashboard-state-error')).toHaveTextContent(
      "Couldn't load dashboard data."
    );

    vi.mocked(dashboardApi.getDashboardStats).mockResolvedValueOnce(makeStats());
    await user.click(screen.getByRole('button', { name: 'Retry' }));

    expect(await screen.findByTestId('dashboard-state-loaded')).toBeInTheDocument();
    expect(dashboardApi.getDashboardStats).toHaveBeenCalledTimes(2);
    expect(dashboardApi.getEmployeeSegmentation).toHaveBeenCalledTimes(2);
  });
});
