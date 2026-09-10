import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { SkillCard } from '@/features/admin/SkillCard';
import type { SkillWithContent } from '@/lib/api/skillsApi';

function makeSkill(overrides: Partial<SkillWithContent> = {}): SkillWithContent {
  return {
    id: 'skill-1',
    name: 'Data Visualization',
    description: null,
    ever_assigned: false,
    approved_content: null,
    ...overrides,
  };
}

describe('SkillCard', () => {
  it('renders the Approved badge, link row, and days-estimate when approved_content is present', () => {
    const skill = makeSkill({
      approved_content: {
        id: 'content-1',
        skill_id: 'skill-1',
        title: 'A Great Course',
        description: null,
        type: 'VIDEO',
        url: 'https://example.com/a-course',
        source: 'YOUTUBE',
        ingested_at: '2026-09-10T00:00:00Z',
        metadata: { duration_hours: 5 },
      },
    });

    render(<SkillCard skill={skill} onEdit={vi.fn()} onDelete={vi.fn()} onView={vi.fn()} />);

    expect(screen.getByText('✓ Approved')).toBeInTheDocument();
    expect(screen.getByTestId('skills-tab-skill-card-link')).toHaveTextContent('A Great Course');
    expect(screen.getByText('≈1d')).toBeInTheDocument();
  });

  it('renders the None-yet badge and empty-state text when there is no approved content', () => {
    render(<SkillCard skill={makeSkill()} onEdit={vi.fn()} onDelete={vi.fn()} onView={vi.fn()} />);

    expect(screen.getByText('⚠ None yet')).toBeInTheDocument();
    expect(screen.getByText('No approved content yet for this skill.')).toBeInTheDocument();
  });

  it('renders Edit/Delete for an unassigned skill and calls the callbacks with the skill', async () => {
    const onEdit = vi.fn();
    const onDelete = vi.fn();
    const skill = makeSkill();
    const user = userEvent.setup();
    render(<SkillCard skill={skill} onEdit={onEdit} onDelete={onDelete} onView={vi.fn()} />);

    await user.click(screen.getByTestId('skills-tab-btn-edit-skill'));
    await user.click(screen.getByTestId('skills-tab-btn-delete-skill'));

    expect(onEdit).toHaveBeenCalledWith(skill);
    expect(onDelete).toHaveBeenCalledWith(skill);
  });

  it('renders only the lock text for an assigned skill, with no Edit/Delete controls', () => {
    render(<SkillCard skill={makeSkill({ ever_assigned: true })} onEdit={vi.fn()} onDelete={vi.fn()} onView={vi.fn()} />);

    expect(screen.getByTestId('skills-tab-skill-card-lock')).toHaveTextContent(
      'Locked — assigned to an Employee'
    );
    expect(screen.queryByTestId('skills-tab-btn-edit-skill')).not.toBeInTheDocument();
    expect(screen.queryByTestId('skills-tab-btn-delete-skill')).not.toBeInTheDocument();
  });

  it("clicking the approved link's title calls onView with the right fields", async () => {
    const onView = vi.fn();
    const skill = makeSkill({
      approved_content: {
        id: 'content-1',
        skill_id: 'skill-1',
        title: 'A Great Course',
        description: null,
        type: 'VIDEO',
        url: 'https://example.com/a-course',
        source: 'YOUTUBE',
        ingested_at: '2026-09-10T00:00:00Z',
        metadata: { duration_hours: 5 },
      },
    });
    const user = userEvent.setup();
    render(<SkillCard skill={skill} onEdit={vi.fn()} onDelete={vi.fn()} onView={onView} />);

    await user.click(screen.getByTestId('skills-tab-skill-card-link'));

    expect(onView).toHaveBeenCalledWith({
      title: 'A Great Course',
      source: 'YOUTUBE',
      url: 'https://example.com/a-course',
      durationHours: 5,
    });
  });
});
