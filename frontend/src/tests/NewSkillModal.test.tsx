import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { NewSkillModal } from '@/features/admin/NewSkillModal';

vi.mock('@/lib/api/skillsApi', () => ({
  createSkill: vi.fn(),
}));

import { createSkill } from '@/lib/api/skillsApi';

describe('NewSkillModal', () => {
  beforeEach(() => {
    vi.mocked(createSkill).mockReset();
  });

  it('calls onCreated with the created skill and the entered name on success', async () => {
    vi.mocked(createSkill).mockResolvedValue({
      id: 'skill-1',
      name: 'Docker Fundamentals',
      description: null,
      ever_assigned: false,
    });
    const onCreated = vi.fn();
    const user = userEvent.setup();
    render(<NewSkillModal open onClose={vi.fn()} onCreated={onCreated} onUseExisting={vi.fn()} />);

    await user.type(screen.getByTestId('new-skill-name-input'), 'Docker Fundamentals');
    await user.click(screen.getByTestId('new-skill-btn-create'));

    await vi.waitFor(() =>
      expect(onCreated).toHaveBeenCalledWith(
        { id: 'skill-1', name: 'Docker Fundamentals', description: null, ever_assigned: false },
        'Docker Fundamentals'
      )
    );
  });

  it('shows the duplicate notice with a working "Use existing skill" link on a 409', async () => {
    vi.mocked(createSkill).mockRejectedValue({
      response: {
        status: 409,
        data: { message: "A skill named 'Docker' already exists", extra: { existing_skill: { id: 'existing-1', name: 'Docker' } } },
      },
    });
    const onUseExisting = vi.fn();
    const user = userEvent.setup();
    render(<NewSkillModal open onClose={vi.fn()} onCreated={vi.fn()} onUseExisting={onUseExisting} />);

    await user.type(screen.getByTestId('new-skill-name-input'), 'Docker');
    await user.click(screen.getByTestId('new-skill-btn-create'));

    expect(await screen.findByTestId('new-skill-duplicate-notice')).toBeInTheDocument();
    await user.click(screen.getByText('Use existing skill'));
    expect(onUseExisting).toHaveBeenCalledWith('existing-1', 'Docker', 'Docker');
  });

  it('disables Create while the name is blank', () => {
    render(<NewSkillModal open onClose={vi.fn()} onCreated={vi.fn()} onUseExisting={vi.fn()} />);

    expect(screen.getByTestId('new-skill-btn-create')).toBeDisabled();
  });

  it('resets fields between opens', () => {
    const { rerender } = render(
      <NewSkillModal open={false} onClose={vi.fn()} onCreated={vi.fn()} onUseExisting={vi.fn()} />
    );
    rerender(<NewSkillModal open onClose={vi.fn()} onCreated={vi.fn()} onUseExisting={vi.fn()} />);

    expect(screen.getByTestId('new-skill-name-input')).toHaveValue('');
    expect(screen.queryByTestId('new-skill-duplicate-notice')).not.toBeInTheDocument();
  });

  it('clears the stale duplicate notice when the name is edited afterward (code review, 2026-09-10)', async () => {
    vi.mocked(createSkill).mockRejectedValue({
      response: {
        status: 409,
        data: { message: "A skill named 'Docker' already exists", extra: { existing_skill: { id: 'existing-1', name: 'Docker' } } },
      },
    });
    const user = userEvent.setup();
    render(<NewSkillModal open onClose={vi.fn()} onCreated={vi.fn()} onUseExisting={vi.fn()} />);

    await user.type(screen.getByTestId('new-skill-name-input'), 'Docker');
    await user.click(screen.getByTestId('new-skill-btn-create'));
    expect(await screen.findByTestId('new-skill-duplicate-notice')).toBeInTheDocument();

    await user.type(screen.getByTestId('new-skill-name-input'), ' Advanced');

    expect(screen.queryByTestId('new-skill-duplicate-notice')).not.toBeInTheDocument();
  });

  it('does not call onCreated if the modal is closed while the create request is still pending (code review, 2026-09-10)', async () => {
    let resolveCreate: (value: { id: string; name: string; description: string | null; ever_assigned: boolean }) => void;
    vi.mocked(createSkill).mockReturnValue(
      new Promise((resolve) => {
        resolveCreate = resolve;
      })
    );
    const onCreated = vi.fn();
    const user = userEvent.setup();
    const { rerender } = render(
      <NewSkillModal open onClose={vi.fn()} onCreated={onCreated} onUseExisting={vi.fn()} />
    );

    await user.type(screen.getByTestId('new-skill-name-input'), 'Docker Fundamentals');
    await user.click(screen.getByTestId('new-skill-btn-create'));

    // Admin closes the modal before the request resolves.
    rerender(<NewSkillModal open={false} onClose={vi.fn()} onCreated={onCreated} onUseExisting={vi.fn()} />);

    resolveCreate!({ id: 'skill-1', name: 'Docker Fundamentals', description: null, ever_assigned: false });
    await new Promise((r) => setTimeout(r, 0));

    expect(onCreated).not.toHaveBeenCalled();
  });
});
