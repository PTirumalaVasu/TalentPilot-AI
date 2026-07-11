import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AssignmentModal } from '@/features/assignments/AssignmentModal';

vi.mock('@/lib/api/assignmentsApi', () => ({
  listEmployees: vi.fn(),
  listSkills: vi.fn(),
  matchContentForSkill: vi.fn(),
  checkDuplicateAssignment: vi.fn(),
  createAssignment: vi.fn(),
}));

import {
  listEmployees,
  listSkills,
  matchContentForSkill,
  checkDuplicateAssignment,
  createAssignment,
} from '@/lib/api/assignmentsApi';

const EMPLOYEE = { id: 'emp-1', name: 'Casey Employee', email: 'casey@sails.example.com', role: 'EMPLOYEE' };
const EMPLOYEE2 = { id: 'emp-2', name: 'Morgan Employee', email: 'morgan@sails.example.com', role: 'EMPLOYEE' };
const SKILL = { id: 'skill-1', name: 'Data Visualization', description: 'Charts and dashboards' };
const CONTENT = {
  id: 'content-1',
  skill_id: 'skill-1',
  title: 'Intro to Data Viz',
  description: 'Learn the basics of charting.',
  type: 'VIDEO' as const,
  url: 'https://youtube.com/watch?v=abc',
  source: 'YOUTUBE' as const,
  ingested_at: '2026-01-01T00:00:00Z',
  // Matches the real backend's wire key (ContentResponse's Pydantic alias),
  // not the frontend's old, incorrect `metadata` key (code review round 2).
  content_metadata: { video_id: 'abc', duration: 300 },
};

async function goToStep2(user: ReturnType<typeof userEvent.setup>) {
  await user.click(screen.getByRole('combobox', { name: /select employee or search/i }));
  await user.click(await screen.findByText(EMPLOYEE.name));
  await user.click(screen.getByRole('button', { name: /continue to skill selection/i }));
}

async function selectSkill(user: ReturnType<typeof userEvent.setup>) {
  await user.click(screen.getByRole('combobox', { name: /search for a skill/i }));
  await user.click(await screen.findByText(SKILL.name));
}

async function goToStep3(user: ReturnType<typeof userEvent.setup>) {
  await goToStep2(user);
  await selectSkill(user);
  await user.click(screen.getByRole('button', { name: /review content/i }));
}

describe('AssignmentModal', () => {
  beforeEach(() => {
    vi.mocked(listEmployees).mockReset().mockResolvedValue([EMPLOYEE]);
    vi.mocked(listSkills).mockReset().mockResolvedValue([SKILL]);
    vi.mocked(matchContentForSkill).mockReset().mockResolvedValue(CONTENT);
    vi.mocked(checkDuplicateAssignment).mockReset().mockResolvedValue([]);
    vi.mocked(createAssignment).mockReset().mockResolvedValue({
      id: 'assignment-1',
      employee_id: EMPLOYEE.id,
      skill_id: SKILL.id,
      content_id: CONTENT.id,
      assigned_at: '2026-01-01T00:00:00Z',
      assigned_by: 'hr-1',
      status: 'NOT_STARTED',
      provenance: 'Assigned · Awaiting first watch',
    });
  });

  it('renders nothing when closed', () => {
    render(<AssignmentModal open={false} onClose={vi.fn()} />);
    expect(screen.queryByText('Assign a New Skill')).not.toBeInTheDocument();
  });

  it('loads employees on Step 1, shows role (not email) in results, and requires a selection before continuing', async () => {
    const user = userEvent.setup();
    render(<AssignmentModal open onClose={vi.fn()} />);

    expect(screen.getByText('Step 1 of 3')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /continue to skill selection/i })).toBeDisabled();

    await user.click(screen.getByRole('combobox', { name: /select employee or search/i }));
    expect(await screen.findByText(/· Employee/)).toBeInTheDocument();
    expect(screen.queryByText(EMPLOYEE.email)).not.toBeInTheDocument();
    await user.click(screen.getByText(EMPLOYEE.name));
    expect(screen.getByRole('button', { name: /continue to skill selection/i })).toBeEnabled();
  });

  it('advances to Step 2 and loads skills', async () => {
    const user = userEvent.setup();
    render(<AssignmentModal open onClose={vi.fn()} />);

    await goToStep2(user);

    expect(screen.getByText('Step 2 of 3')).toBeInTheDocument();
    await user.click(screen.getByRole('combobox', { name: /search for a skill/i }));
    await screen.findByText(SKILL.name);
  });

  it('has a Cancel button on Step 2 that closes without side effects', async () => {
    const onClose = vi.fn();
    const user = userEvent.setup();
    render(<AssignmentModal open onClose={onClose} />);

    await goToStep2(user);
    await user.click(screen.getByRole('button', { name: /^cancel$/i }));

    expect(onClose).toHaveBeenCalledTimes(1);
    expect(checkDuplicateAssignment).not.toHaveBeenCalled();
  });

  it('checks for a duplicate assignment and loads content (with thumbnail/duration/description) when advancing to Step 3', async () => {
    const user = userEvent.setup();
    render(<AssignmentModal open onClose={vi.fn()} />);

    await goToStep3(user);

    expect(checkDuplicateAssignment).toHaveBeenCalledWith(EMPLOYEE.id, SKILL.id);
    expect(matchContentForSkill).toHaveBeenCalledWith(SKILL.id);
    expect(screen.getByText('Step 3 of 3')).toBeInTheDocument();
    expect(screen.getByText(CONTENT.title)).toBeInTheDocument();
    expect(screen.getByText(/5 minutes/)).toBeInTheDocument();
    expect(screen.getByText(CONTENT.description)).toBeInTheDocument();
    expect(screen.getByRole('img', { hidden: true })).toHaveAttribute('src', expect.stringContaining('abc'));
    // Displays formatted "YouTube", not the raw backend enum value "YOUTUBE".
    expect(screen.getByText(/YouTube · 5 minutes/)).toBeInTheDocument();
    expect(screen.queryByText('YOUTUBE')).not.toBeInTheDocument();
  });

  it('shows the read-only Assignment Summary on Step 3', async () => {
    const user = userEvent.setup();
    render(<AssignmentModal open onClose={vi.fn()} />);

    await goToStep3(user);

    expect(screen.getByText(`Employee: ${EMPLOYEE.name}`)).toBeInTheDocument();
    expect(screen.getByText(`Skill: ${SKILL.name}`)).toBeInTheDocument();
    expect(screen.getByText(`Content: ${CONTENT.title} (Approved)`)).toBeInTheDocument();
    expect(screen.getByText('Assignment Date: Today')).toBeInTheDocument();
    expect(screen.getByText(/Will be "Assigned · Awaiting first watch"/)).toBeInTheDocument();
  });

  it('shows a duplicate-pair interstitial with View/Assign Again instead of advancing straight to Step 3', async () => {
    vi.mocked(checkDuplicateAssignment).mockResolvedValue([
      {
        id: 'existing-1',
        employee_id: EMPLOYEE.id,
        skill_id: SKILL.id,
        content_id: null,
        assigned_at: '2026-01-01T00:00:00Z',
        assigned_by: 'hr-1',
        status: 'NOT_STARTED',
        provenance: 'Assigned · Awaiting first watch',
      },
    ]);
    const user = userEvent.setup();
    render(<AssignmentModal open onClose={vi.fn()} />);

    await goToStep2(user);
    await selectSkill(user);
    await user.click(screen.getByRole('button', { name: /review content/i }));

    expect(await screen.findByRole('alert')).toHaveTextContent(/already assigned to/i);
    expect(screen.queryByText('Step 3 of 3')).not.toBeInTheDocument();
    expect(matchContentForSkill).not.toHaveBeenCalled();
    expect(screen.getByRole('button', { name: /^view$/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /assign again/i })).toBeInTheDocument();
  });

  it('advances to Step 3 and fetches content when Assign Again is clicked from the duplicate interstitial', async () => {
    vi.mocked(checkDuplicateAssignment).mockResolvedValue([
      {
        id: 'existing-1',
        employee_id: EMPLOYEE.id,
        skill_id: SKILL.id,
        content_id: null,
        assigned_at: '2026-01-01T00:00:00Z',
        assigned_by: 'hr-1',
        status: 'NOT_STARTED',
        provenance: 'Assigned · Awaiting first watch',
      },
    ]);
    const user = userEvent.setup();
    render(<AssignmentModal open onClose={vi.fn()} />);

    await goToStep2(user);
    await selectSkill(user);
    await user.click(screen.getByRole('button', { name: /review content/i }));
    await user.click(await screen.findByRole('button', { name: /assign again/i }));

    expect(matchContentForSkill).toHaveBeenCalledWith(SKILL.id);
    expect(await screen.findByText('Step 3 of 3')).toBeInTheDocument();
  });

  it('returns to the normal skill picker (not the interstitial again) after Assign Again then Back', async () => {
    vi.mocked(checkDuplicateAssignment).mockResolvedValueOnce([
      {
        id: 'existing-1',
        employee_id: EMPLOYEE.id,
        skill_id: SKILL.id,
        content_id: null,
        assigned_at: '2026-01-01T00:00:00Z',
        assigned_by: 'hr-1',
        status: 'NOT_STARTED',
        provenance: 'Assigned · Awaiting first watch',
      },
    ]);
    const user = userEvent.setup();
    render(<AssignmentModal open onClose={vi.fn()} />);

    await goToStep2(user);
    await selectSkill(user);
    await user.click(screen.getByRole('button', { name: /review content/i }));
    await user.click(await screen.findByRole('button', { name: /assign again/i }));
    await screen.findByText('Step 3 of 3');

    await user.click(screen.getByRole('button', { name: /^back$/i }));

    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    expect(screen.getByRole('combobox', { name: /search for a skill/i })).toBeInTheDocument();
  });

  it('closes without side effects when View is clicked from the duplicate interstitial', async () => {
    vi.mocked(checkDuplicateAssignment).mockResolvedValue([
      {
        id: 'existing-1',
        employee_id: EMPLOYEE.id,
        skill_id: SKILL.id,
        content_id: null,
        assigned_at: '2026-01-01T00:00:00Z',
        assigned_by: 'hr-1',
        status: 'NOT_STARTED',
        provenance: 'Assigned · Awaiting first watch',
      },
    ]);
    const onClose = vi.fn();
    const user = userEvent.setup();
    render(<AssignmentModal open onClose={onClose} />);

    await goToStep2(user);
    await selectSkill(user);
    await user.click(screen.getByRole('button', { name: /review content/i }));
    await user.click(await screen.findByRole('button', { name: /^view$/i }));

    expect(onClose).toHaveBeenCalledTimes(1);
    expect(createAssignment).not.toHaveBeenCalled();
  });

  it('shows the empty-content state and an "Assign without content" label when no content matches the skill', async () => {
    vi.mocked(matchContentForSkill).mockResolvedValue(null);
    const user = userEvent.setup();
    render(<AssignmentModal open onClose={vi.fn()} />);

    await goToStep3(user);

    expect(screen.getByText(/no approved content found yet for this skill/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /assign without content/i })).toBeInTheDocument();
  });

  it('shows an inline error with a Retry button on Step 3 when the content match request fails, and Retry re-fetches', async () => {
    vi.mocked(matchContentForSkill).mockRejectedValueOnce(new Error('network error'));
    const user = userEvent.setup();
    render(<AssignmentModal open onClose={vi.fn()} />);

    await goToStep3(user);

    expect(screen.getByText('Step 3 of 3')).toBeInTheDocument();
    expect(await screen.findByRole('alert')).toHaveTextContent(/couldn't load content recommendation/i);
    expect(checkDuplicateAssignment).toHaveBeenCalledTimes(1);

    await userEvent.setup().click(screen.getByRole('button', { name: /retry/i }));

    await waitFor(() => expect(matchContentForSkill).toHaveBeenCalledTimes(2));
    // Retry only re-runs the content match, not the duplicate check.
    expect(checkDuplicateAssignment).toHaveBeenCalledTimes(1);
    expect(await screen.findByText(CONTENT.title)).toBeInTheDocument();
  });

  it('submits the assignment and closes the modal on Assign', async () => {
    const onClose = vi.fn();
    const onAssigned = vi.fn();
    const user = userEvent.setup();
    render(<AssignmentModal open onClose={onClose} onAssigned={onAssigned} />);

    await goToStep3(user);
    await user.click(screen.getByRole('button', { name: /^assign$/i }));

    await waitFor(() => expect(createAssignment).toHaveBeenCalledWith(EMPLOYEE.id, SKILL.id, CONTENT.id));
    // Story 3.5: onAssigned must receive the created Assignment plus the
    // already-resolved Employee/Skill display names, not just fire as a
    // no-op signal — the dashboard's toast copy is built from these.
    expect(onAssigned).toHaveBeenCalledTimes(1);
    expect(onAssigned).toHaveBeenCalledWith(
      expect.objectContaining({ id: 'assignment-1', employee_id: EMPLOYEE.id, skill_id: SKILL.id }),
      EMPLOYEE.name,
      SKILL.name
    );
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('shows an inline error and does not close when assignment creation fails', async () => {
    vi.mocked(createAssignment).mockRejectedValueOnce(new Error('network error'));
    const onClose = vi.fn();
    const user = userEvent.setup();
    render(<AssignmentModal open onClose={onClose} />);

    await goToStep3(user);
    await user.click(screen.getByRole('button', { name: /^assign$/i }));

    expect(await screen.findByText(/couldn't create the assignment/i)).toBeInTheDocument();
    expect(onClose).not.toHaveBeenCalled();
  });

  it('closes without side effects when Cancel is clicked on Step 1', async () => {
    const onClose = vi.fn();
    const user = userEvent.setup();
    render(<AssignmentModal open onClose={onClose} />);

    await user.click(screen.getByRole('button', { name: /cancel/i }));

    expect(onClose).toHaveBeenCalledTimes(1);
    expect(checkDuplicateAssignment).not.toHaveBeenCalled();
    expect(createAssignment).not.toHaveBeenCalled();
  });

  it('closes without side effects when the close (×) button is clicked', async () => {
    const onClose = vi.fn();
    const user = userEvent.setup();
    render(<AssignmentModal open onClose={onClose} />);

    await user.click(screen.getByRole('button', { name: /close/i }));

    expect(onClose).toHaveBeenCalledTimes(1);
    expect(createAssignment).not.toHaveBeenCalled();
  });

  it('closes without side effects when Cancel is clicked on Step 3', async () => {
    const onClose = vi.fn();
    const user = userEvent.setup();
    render(<AssignmentModal open onClose={onClose} />);

    await goToStep3(user);
    await user.click(screen.getByRole('button', { name: /^cancel$/i }));

    expect(onClose).toHaveBeenCalledTimes(1);
    expect(createAssignment).not.toHaveBeenCalled();
  });

  it('disables Cancel/Back/Close while an Assign request is in flight', async () => {
    type CreatedAssignment = Awaited<ReturnType<typeof createAssignment>>;
    let resolveCreate!: (value: CreatedAssignment) => void;
    vi.mocked(createAssignment).mockReturnValue(
      new Promise<CreatedAssignment>((resolve) => {
        resolveCreate = resolve;
      })
    );
    const user = userEvent.setup();
    render(<AssignmentModal open onClose={vi.fn()} />);

    await goToStep3(user);
    await user.click(screen.getByRole('button', { name: /^assign$/i }));

    expect(screen.getByRole('button', { name: /^cancel$/i })).toBeDisabled();
    expect(screen.getByRole('button', { name: /^back$/i })).toBeDisabled();
    expect(screen.getByRole('button', { name: /close/i })).toBeDisabled();

    resolveCreate({
      id: 'assignment-1',
      employee_id: EMPLOYEE.id,
      skill_id: SKILL.id,
      content_id: CONTENT.id,
      assigned_at: '2026-01-01T00:00:00Z',
      assigned_by: 'hr-1',
      status: 'NOT_STARTED',
      provenance: 'Assigned · Awaiting first watch',
    });
    await waitFor(() => expect(createAssignment).toHaveBeenCalledTimes(1));
  });

  it('clears a previously-chosen Skill when the Employee is changed after a Back round-trip', async () => {
    vi.mocked(listEmployees).mockResolvedValue([EMPLOYEE, EMPLOYEE2]);
    const user = userEvent.setup();
    render(<AssignmentModal open onClose={vi.fn()} />);

    await goToStep2(user);
    await selectSkill(user);
    await user.click(screen.getByRole('button', { name: /^back$/i }));

    await user.click(screen.getByRole('combobox', { name: /select employee or search/i }));
    await user.click(await screen.findByText(EMPLOYEE2.name));
    await user.click(screen.getByRole('button', { name: /continue to skill selection/i }));

    expect(screen.getByRole('combobox', { name: /search for a skill/i })).toHaveValue('');
    expect(screen.getByRole('button', { name: /review content/i })).toBeDisabled();
  });

  it('does not apply a stale content-fetch result after navigating Back from Step 3', async () => {
    let resolveFirstFetch!: (value: typeof CONTENT | null) => void;
    vi.mocked(matchContentForSkill).mockReturnValueOnce(
      new Promise((resolve) => {
        resolveFirstFetch = resolve;
      })
    );
    const user = userEvent.setup();
    render(<AssignmentModal open onClose={vi.fn()} />);

    await goToStep3(user);
    await user.click(screen.getByRole('button', { name: /^back$/i }));

    // The abandoned first fetch resolves only after the user has already
    // navigated away — its result must not land in the (now Step 2) view.
    resolveFirstFetch(CONTENT);
    await waitFor(() => expect(matchContentForSkill).toHaveBeenCalledTimes(1));

    expect(screen.getByText('Step 2 of 3')).toBeInTheDocument();
    expect(screen.queryByText(CONTENT.title)).not.toBeInTheDocument();
  });
});
