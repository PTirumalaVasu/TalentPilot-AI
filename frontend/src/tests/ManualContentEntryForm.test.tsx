import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ManualContentEntryForm } from '@/features/admin/ManualContentEntryForm';

vi.mock('@/lib/api/adminContentApi', () => ({
  reviewManualContent: vi.fn(),
  attachContent: vi.fn(),
}));

import { reviewManualContent, attachContent } from '@/lib/api/adminContentApi';

describe('ManualContentEntryForm', () => {
  beforeEach(() => {
    vi.mocked(reviewManualContent).mockReset();
    vi.mocked(attachContent).mockReset();
  });

  async function fillAndSubmit(
    user: ReturnType<typeof userEvent.setup>,
    { url, title, duration }: { url: string; title: string; duration?: string }
  ) {
    await user.type(screen.getByPlaceholderText('Paste a content link…'), url);
    await user.type(screen.getByPlaceholderText('Title'), title);
    if (duration) {
      await user.type(screen.getByPlaceholderText('Duration (optional, e.g. 2h 30m)'), duration);
    }
    await user.click(screen.getByRole('button', { name: 'Review link' }));
  }

  it('renders the candidate card with title/source/days-to-complete on success', async () => {
    vi.mocked(reviewManualContent).mockResolvedValue({
      title: 'A Manual Course',
      source: 'MANUAL',
      url: 'https://example.com/a-course',
      duration_hours: 5,
    });
    const user = userEvent.setup();
    render(<ManualContentEntryForm skillId="skill-1" />);

    await fillAndSubmit(user, { url: 'https://example.com/a-course', title: 'A Manual Course', duration: '5h' });

    await waitFor(() =>
      expect(reviewManualContent).toHaveBeenCalledWith('skill-1', {
        url: 'https://example.com/a-course',
        title: 'A Manual Course',
        duration_hours: 5,
      })
    );
    expect(await screen.findByText('A Manual Course')).toBeInTheDocument();
    expect(screen.getByText(/≈ 1 day to complete/)).toBeInTheDocument();
  });

  it('omits the days-to-complete estimate when no duration is supplied', async () => {
    vi.mocked(reviewManualContent).mockResolvedValue({
      title: 'A Manual Course',
      source: 'MANUAL',
      url: 'https://example.com/a-course',
      duration_hours: null,
    });
    const user = userEvent.setup();
    render(<ManualContentEntryForm skillId="skill-1" />);

    await fillAndSubmit(user, { url: 'https://example.com/a-course', title: 'A Manual Course' });

    expect(await screen.findByText('A Manual Course')).toBeInTheDocument();
    expect(screen.queryByText(/days to complete/)).not.toBeInTheDocument();
  });

  it('shows an inline error and no candidate card when the review call fails', async () => {
    vi.mocked(reviewManualContent).mockRejectedValue(new Error('boom'));
    const user = userEvent.setup();
    render(<ManualContentEntryForm skillId="skill-1" />);

    await fillAndSubmit(user, { url: 'not-a-url', title: 'A Manual Course' });

    expect(await screen.findByText(/Couldn't review this link/)).toBeInTheDocument();
    expect(screen.queryByText('A Manual Course')).not.toBeInTheDocument();
  });

  it('Approve calls attachContent with the expected body, shows the Toast, and disables the button on success', async () => {
    vi.mocked(reviewManualContent).mockResolvedValue({
      title: 'A Manual Course',
      source: 'MANUAL',
      url: 'https://example.com/a-course',
      duration_hours: 5,
    });
    vi.mocked(attachContent).mockResolvedValue({
      id: 'content-1',
      skill_id: 'skill-1',
      title: 'A Manual Course',
      description: null,
      type: 'VIDEO',
      url: 'https://example.com/a-course',
      source: 'MANUAL',
      ingested_at: '2026-09-10T00:00:00Z',
      metadata: { duration_hours: 5 },
    });
    const user = userEvent.setup();
    render(<ManualContentEntryForm skillId="skill-1" skillName="Data Visualization" />);

    await fillAndSubmit(user, { url: 'https://example.com/a-course', title: 'A Manual Course', duration: '5h' });
    await screen.findByText('A Manual Course');

    await user.click(screen.getByRole('button', { name: 'Approve' }));

    await waitFor(() =>
      expect(attachContent).toHaveBeenCalledWith({
        skill_id: 'skill-1',
        title: 'A Manual Course',
        source: 'MANUAL',
        url: 'https://example.com/a-course',
        duration_hours: 5,
      })
    );
    expect(await screen.findByText('✓ Content approved for Data Visualization')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Approve/ })).toBeDisabled();
  });

  it('falls back to a generic Toast message when no skillName is supplied', async () => {
    vi.mocked(reviewManualContent).mockResolvedValue({
      title: 'A Manual Course',
      source: 'MANUAL',
      url: 'https://example.com/a-course',
      duration_hours: null,
    });
    vi.mocked(attachContent).mockResolvedValue({
      id: 'content-1',
      skill_id: 'skill-1',
      title: 'A Manual Course',
      description: null,
      type: 'VIDEO',
      url: 'https://example.com/a-course',
      source: 'MANUAL',
      ingested_at: '2026-09-10T00:00:00Z',
      metadata: null,
    });
    const user = userEvent.setup();
    render(<ManualContentEntryForm skillId="skill-1" />);

    await fillAndSubmit(user, { url: 'https://example.com/a-course', title: 'A Manual Course' });
    await screen.findByText('A Manual Course');
    await user.click(screen.getByRole('button', { name: 'Approve' }));

    expect(await screen.findByText('✓ Content approved for this skill')).toBeInTheDocument();
  });

  it('shows an inline error and leaves Approve clickable when the attach call fails', async () => {
    vi.mocked(reviewManualContent).mockResolvedValue({
      title: 'A Manual Course',
      source: 'MANUAL',
      url: 'https://example.com/a-course',
      duration_hours: null,
    });
    vi.mocked(attachContent).mockRejectedValue(new Error('boom'));
    const user = userEvent.setup();
    render(<ManualContentEntryForm skillId="skill-1" />);

    await fillAndSubmit(user, { url: 'https://example.com/a-course', title: 'A Manual Course' });
    await screen.findByText('A Manual Course');
    await user.click(screen.getByRole('button', { name: 'Approve' }));

    expect(await screen.findByText(/Couldn't approve this/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Approve' })).not.toBeDisabled();
  });

  it('clears a stale approval Toast when a new review starts (review patch, 2026-09-10)', async () => {
    vi.mocked(reviewManualContent).mockResolvedValue({
      title: 'A Manual Course',
      source: 'MANUAL',
      url: 'https://example.com/a-course',
      duration_hours: null,
    });
    vi.mocked(attachContent).mockResolvedValue({
      id: 'content-1',
      skill_id: 'skill-1',
      title: 'A Manual Course',
      description: null,
      type: 'VIDEO',
      url: 'https://example.com/a-course',
      source: 'MANUAL',
      ingested_at: '2026-09-10T00:00:00Z',
      metadata: null,
    });
    const user = userEvent.setup();
    render(<ManualContentEntryForm skillId="skill-1" />);

    await fillAndSubmit(user, { url: 'https://example.com/a-course', title: 'A Manual Course' });
    await screen.findByText('A Manual Course');
    await user.click(screen.getByRole('button', { name: 'Approve' }));
    expect(await screen.findByText('✓ Content approved for this skill')).toBeInTheDocument();

    await fillAndSubmit(user, { url: 'https://example.com/another-course', title: 'Another Course' });

    expect(screen.queryByText('✓ Content approved for this skill')).not.toBeInTheDocument();
  });

  it('opens the preview modal from the View button', async () => {
    vi.mocked(reviewManualContent).mockResolvedValue({
      title: 'A Manual Course',
      source: 'MANUAL',
      url: 'https://example.com/a-course',
      duration_hours: null,
    });
    const user = userEvent.setup();
    render(<ManualContentEntryForm skillId="skill-1" />);

    await fillAndSubmit(user, { url: 'https://example.com/a-course', title: 'A Manual Course' });
    await screen.findByText('A Manual Course');

    await user.click(screen.getByRole('button', { name: 'View' }));

    expect(await screen.findByTestId('watch-modal-title')).toHaveTextContent('A Manual Course');
  });
});
