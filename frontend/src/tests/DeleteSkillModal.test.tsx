import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { DeleteSkillModal } from '@/features/admin/DeleteSkillModal';

vi.mock('@/lib/api/skillsApi', () => ({
  deleteSkill: vi.fn(),
}));

import { deleteSkill } from '@/lib/api/skillsApi';

const SKILL = { id: 'skill-1', name: 'Docker Fundamentals' };

describe('DeleteSkillModal', () => {
  beforeEach(() => {
    vi.mocked(deleteSkill).mockReset();
  });

  it('confirm calls deleteSkill and onDeleted', async () => {
    vi.mocked(deleteSkill).mockResolvedValue(undefined);
    const onDeleted = vi.fn();
    const onClose = vi.fn();
    const user = userEvent.setup();
    render(<DeleteSkillModal skill={SKILL} open onClose={onClose} onDeleted={onDeleted} />);

    await user.click(screen.getByTestId('delete-skill-btn-confirm'));

    await vi.waitFor(() => expect(deleteSkill).toHaveBeenCalledWith('skill-1'));
    expect(onDeleted).toHaveBeenCalledWith('skill-1');
    expect(onClose).toHaveBeenCalled();
  });

  it('cancel calls onClose without deleting', async () => {
    const onClose = vi.fn();
    const user = userEvent.setup();
    render(<DeleteSkillModal skill={SKILL} open onClose={onClose} onDeleted={vi.fn()} />);

    await user.click(screen.getByTestId('delete-skill-btn-cancel'));

    expect(onClose).toHaveBeenCalled();
    expect(deleteSkill).not.toHaveBeenCalled();
  });

  it('shows an inline error and stays open when delete fails', async () => {
    vi.mocked(deleteSkill).mockRejectedValue(new Error('boom'));
    const onClose = vi.fn();
    const user = userEvent.setup();
    render(<DeleteSkillModal skill={SKILL} open onClose={onClose} onDeleted={vi.fn()} />);

    await user.click(screen.getByTestId('delete-skill-btn-confirm'));

    expect(await screen.findByText(/Couldn't delete this skill/)).toBeInTheDocument();
    expect(onClose).not.toHaveBeenCalled();
  });
});
