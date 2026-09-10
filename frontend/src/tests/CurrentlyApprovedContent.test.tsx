import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { CurrentlyApprovedContent } from '@/features/admin/CurrentlyApprovedContent';

vi.mock('@/lib/api/adminContentApi', () => ({
  rejectContent: vi.fn(),
}));

import { rejectContent } from '@/lib/api/adminContentApi';

const baseProps = {
  contentId: 'content-1',
  title: 'A Great Course',
  source: 'MANUAL' as const,
  url: 'https://example.com/a-course',
  durationHours: 5,
};

describe('CurrentlyApprovedContent', () => {
  beforeEach(() => {
    vi.mocked(rejectContent).mockReset();
  });

  it('renders source/title and the days-to-complete estimate when duration is known', () => {
    render(<CurrentlyApprovedContent {...baseProps} />);

    expect(screen.getByText('A Great Course')).toBeInTheDocument();
    expect(screen.getByText('MANUAL')).toBeInTheDocument();
    expect(screen.getByText(/≈ 1 day to complete/)).toBeInTheDocument();
    expect(screen.getByText('Approving a new link below will also replace this.')).toBeInTheDocument();
  });

  it('omits the days-to-complete estimate when duration is null', () => {
    render(<CurrentlyApprovedContent {...baseProps} durationHours={null} />);

    expect(screen.queryByText(/days to complete/)).not.toBeInTheDocument();
  });

  it('opens the preview modal from the View button', async () => {
    const user = userEvent.setup();
    render(<CurrentlyApprovedContent {...baseProps} />);

    await user.click(screen.getByRole('button', { name: 'View' }));

    expect(await screen.findByTestId('watch-modal-title')).toHaveTextContent('A Great Course');
  });

  it('Reject calls rejectContent with the contentId, shows the Toast, and removes the card on success', async () => {
    vi.mocked(rejectContent).mockResolvedValue(undefined);
    const onRejected = vi.fn();
    const user = userEvent.setup();
    render(<CurrentlyApprovedContent {...baseProps} skillName="Data Visualization" onRejected={onRejected} />);

    await user.click(screen.getByRole('button', { name: 'Reject' }));

    expect(rejectContent).toHaveBeenCalledWith('content-1');
    expect(await screen.findByText('✓ Rejected the approved link for Data Visualization')).toBeInTheDocument();
    expect(screen.queryByTestId('content-lookup-current-approved')).not.toBeInTheDocument();
    expect(onRejected).toHaveBeenCalled();
  });

  it('falls back to a generic Toast message when no skillName is supplied', async () => {
    vi.mocked(rejectContent).mockResolvedValue(undefined);
    const user = userEvent.setup();
    render(<CurrentlyApprovedContent {...baseProps} />);

    await user.click(screen.getByRole('button', { name: 'Reject' }));

    expect(await screen.findByText('✓ Rejected the approved link for this skill')).toBeInTheDocument();
  });

  it('falls back to a generic Toast message when skillName is an empty string (review patch, 2026-09-10)', async () => {
    vi.mocked(rejectContent).mockResolvedValue(undefined);
    const user = userEvent.setup();
    render(<CurrentlyApprovedContent {...baseProps} skillName="" />);

    await user.click(screen.getByRole('button', { name: 'Reject' }));

    expect(await screen.findByText('✓ Rejected the approved link for this skill')).toBeInTheDocument();
  });

  it('shows an inline error and leaves Reject clickable when the call fails', async () => {
    vi.mocked(rejectContent).mockRejectedValue(new Error('boom'));
    const user = userEvent.setup();
    render(<CurrentlyApprovedContent {...baseProps} />);

    await user.click(screen.getByRole('button', { name: 'Reject' }));

    expect(await screen.findByText(/Couldn't reject this/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Reject' })).not.toBeDisabled();
    expect(screen.getByTestId('content-lookup-current-approved')).toBeInTheDocument();
  });
});
