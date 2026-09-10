import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { AuthProvider } from '@/lib/auth/AuthContext';
import { SkillsPage } from '@/pages/hr/SkillsPage';

const navigateMock = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return { ...actual, useNavigate: () => navigateMock };
});

vi.mock('@/lib/api/authApi', () => ({
  logout: vi.fn().mockResolvedValue(undefined),
  getMe: vi.fn().mockResolvedValue({
    user_id: 'rita-1',
    role: 'HR_ADMIN',
    name: 'Rita the Recruiter',
    email: 'rita@sails.example.com',
  }),
}));

vi.mock('@/lib/api/skillsApi', () => ({
  listSkillsWithContent: vi.fn(),
  createSkill: vi.fn(),
  updateSkill: vi.fn(),
  deleteSkill: vi.fn(),
}));

vi.mock('@/lib/api/adminContentApi', () => ({
  attachContent: vi.fn(),
  searchContentForSkill: vi.fn(),
  rejectContent: vi.fn(),
  reviewManualContent: vi.fn(),
}));

vi.mock('@/lib/api/adminApiKeysApi', () => ({
  getApiKeysStatus: vi.fn().mockResolvedValue({
    youtube: { configured: true },
    udemy: { configured: true, configured_by: 'Rita', configured_at: '2026-09-08T00:00:00Z' },
  }),
  saveYoutubeKey: vi.fn(),
  removeYoutubeKey: vi.fn(),
  saveUdemyCredential: vi.fn(),
  removeUdemyCredential: vi.fn(),
}));

import { listSkillsWithContent, createSkill, deleteSkill } from '@/lib/api/skillsApi';

function makeSkill(overrides: Partial<Awaited<ReturnType<typeof listSkillsWithContent>>[number]> = {}) {
  return {
    id: 'skill-1',
    name: 'Data Visualization',
    description: null,
    ever_assigned: false,
    approved_content: null,
    ...overrides,
  };
}

function renderPage() {
  return render(
    <MemoryRouter>
      <AuthProvider>
        <SkillsPage />
      </AuthProvider>
    </MemoryRouter>
  );
}

describe('SkillsPage', () => {
  beforeEach(() => {
    vi.mocked(listSkillsWithContent).mockReset();
    vi.mocked(createSkill).mockReset();
    vi.mocked(deleteSkill).mockReset();
  });

  it('renders one card per fetched skill', async () => {
    vi.mocked(listSkillsWithContent).mockResolvedValue([
      makeSkill({ id: 'skill-1', name: 'Data Visualization' }),
      makeSkill({ id: 'skill-2', name: 'Docker Fundamentals' }),
    ]);
    renderPage();

    expect(await screen.findByText('Data Visualization')).toBeInTheDocument();
    expect(screen.getByText('Docker Fundamentals')).toBeInTheDocument();
    expect(screen.getByTestId('skills-tab-summary-count')).toHaveTextContent('2 skills · 0 with approved content');
  });

  it('shows the empty state when there are no skills', async () => {
    vi.mocked(listSkillsWithContent).mockResolvedValue([]);
    renderPage();

    expect(await screen.findByText('No skills yet.')).toBeInTheDocument();
  });

  it('shows a retryable error banner when the fetch fails', async () => {
    vi.mocked(listSkillsWithContent).mockRejectedValueOnce(new Error('boom')).mockResolvedValueOnce([]);
    const user = userEvent.setup();
    renderPage();

    expect(await screen.findByText(/Couldn't load skills/)).toBeInTheDocument();
    await user.click(screen.getByText('Retry'));

    expect(await screen.findByText('No skills yet.')).toBeInTheDocument();
  });

  it('New Skill -> create -> opens the Content Lookup panel with the entered name as the search term', async () => {
    vi.mocked(listSkillsWithContent).mockResolvedValue([]);
    vi.mocked(createSkill).mockResolvedValue({
      id: 'skill-new',
      name: 'Kubernetes',
      description: null,
      ever_assigned: false,
    });
    const user = userEvent.setup();
    renderPage();
    await screen.findByText('No skills yet.');

    await user.click(screen.getByTestId('skills-tab-btn-new-skill'));
    await user.type(screen.getByTestId('new-skill-name-input'), 'Kubernetes');
    await user.click(screen.getByTestId('new-skill-btn-create'));

    expect(await screen.findByTestId('content-lookup-header-title')).toHaveTextContent('Find content for Kubernetes');
    expect(screen.getByTestId('content-lookup-search-term-input')).toHaveValue('Kubernetes');
  });

  it('Edit opens the panel in edit mode for that skill', async () => {
    vi.mocked(listSkillsWithContent).mockResolvedValue([makeSkill()]);
    const user = userEvent.setup();
    renderPage();
    await screen.findByText('Data Visualization');

    await user.click(screen.getByTestId('skills-tab-btn-edit-skill'));

    expect(await screen.findByTestId('content-lookup-edit-name-input')).toHaveValue('Data Visualization');
  });

  it('Delete -> confirm -> removes the card and shows a toast', async () => {
    vi.mocked(listSkillsWithContent)
      .mockResolvedValueOnce([makeSkill()])
      .mockResolvedValueOnce([]);
    vi.mocked(deleteSkill).mockResolvedValue(undefined);
    const user = userEvent.setup();
    renderPage();
    await screen.findByText('Data Visualization');

    await user.click(screen.getByTestId('skills-tab-btn-delete-skill'));
    await user.click(screen.getByTestId('delete-skill-btn-confirm'));

    await waitFor(() => expect(deleteSkill).toHaveBeenCalledWith('skill-1'));
    expect(await screen.findByText("✓ 'Data Visualization' deleted.")).toBeInTheDocument();
  });

  it('Use existing skill (unlocked, cached) opens the panel with the entered name as search term', async () => {
    vi.mocked(listSkillsWithContent).mockResolvedValue([makeSkill({ id: 'existing-1', name: 'Docker' })]);
    vi.mocked(createSkill).mockRejectedValue({
      response: {
        status: 409,
        data: { message: "A skill named 'Docker' already exists", extra: { existing_skill: { id: 'existing-1', name: 'Docker' } } },
      },
    });
    const user = userEvent.setup();
    renderPage();
    await screen.findByText('Docker');

    await user.click(screen.getByTestId('skills-tab-btn-new-skill'));
    await user.type(screen.getByTestId('new-skill-name-input'), 'docker');
    await user.click(screen.getByTestId('new-skill-btn-create'));
    await user.click(await screen.findByText('Use existing skill'));

    expect(await screen.findByTestId('content-lookup-header-title')).toHaveTextContent('Find content for Docker');
    expect(screen.getByTestId('content-lookup-search-term-input')).toHaveValue('docker');
  });

  it('Use existing skill on a locked skill shows a toast instead of opening the panel (code review, 2026-09-10)', async () => {
    vi.mocked(listSkillsWithContent).mockResolvedValue([
      makeSkill({ id: 'existing-1', name: 'Docker', ever_assigned: true }),
    ]);
    vi.mocked(createSkill).mockRejectedValue({
      response: {
        status: 409,
        data: { message: "A skill named 'Docker' already exists", extra: { existing_skill: { id: 'existing-1', name: 'Docker' } } },
      },
    });
    const user = userEvent.setup();
    renderPage();
    await screen.findByText('Docker');

    await user.click(screen.getByTestId('skills-tab-btn-new-skill'));
    await user.type(screen.getByTestId('new-skill-name-input'), 'docker');
    await user.click(screen.getByTestId('new-skill-btn-create'));
    await user.click(await screen.findByText('Use existing skill'));

    expect(await screen.findByText("'Docker' is already assigned to an Employee and can't be edited.")).toBeInTheDocument();
    expect(screen.queryByTestId('content-lookup-header-title')).not.toBeInTheDocument();
  });

  it('Use existing skill for a skill not in the local cache shows a toast instead of fabricating its state (code review, 2026-09-10)', async () => {
    vi.mocked(listSkillsWithContent).mockResolvedValue([]);
    vi.mocked(createSkill).mockRejectedValue({
      response: {
        status: 409,
        data: { message: "A skill named 'Docker' already exists", extra: { existing_skill: { id: 'not-cached-1', name: 'Docker' } } },
      },
    });
    const user = userEvent.setup();
    renderPage();
    await screen.findByText('No skills yet.');

    await user.click(screen.getByTestId('skills-tab-btn-new-skill'));
    await user.type(screen.getByTestId('new-skill-name-input'), 'docker');
    await user.click(screen.getByTestId('new-skill-btn-create'));
    await user.click(await screen.findByText('Use existing skill'));

    expect(await screen.findByText("Couldn't find 'Docker' — refresh and try again.")).toBeInTheDocument();
    expect(screen.queryByTestId('content-lookup-header-title')).not.toBeInTheDocument();
  });

  it('Manage API Keys button opens the ApiKeysModal', async () => {
    vi.mocked(listSkillsWithContent).mockResolvedValue([]);
    const user = userEvent.setup();
    renderPage();
    await screen.findByText('No skills yet.');

    await user.click(screen.getByTestId('skills-tab-btn-manage-keys'));

    expect(await screen.findByTestId('api-keys-modal-header-title')).toBeInTheDocument();
  });
});
