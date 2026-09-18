import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { AuthProvider } from '@/lib/auth/AuthContext';
import { ThemeProvider } from '@/lib/theme/ThemeContext';
import { SkillsPage } from '@/pages/hr/SkillsPage';

// Story 8.1: SkillsPage renders through HrAppShell, which now renders
// <ThemeToggle> (calls useTheme()) -- the shared window.matchMedia stub
// (frontend/src/tests/setup.ts) covers jsdom's lack of a real implementation
// (code review: previously duplicated here instead of centralized).

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
      <ThemeProvider>
        <AuthProvider>
          <SkillsPage />
        </AuthProvider>
      </ThemeProvider>
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

  // Story 10.5 (FR-37): search + pagination, mirroring EmployeesPage.tsx (Story 7.3).
  describe('search and pagination (Story 10.5)', () => {
    function makeManySkills(count: number) {
      return Array.from({ length: count }, (_, i) => makeSkill({ id: `skill-${i + 1}`, name: `Skill ${String(i + 1).padStart(2, '0')}` }));
    }

    it('search filters the grid by Skill name (case-insensitive); clearing restores the full list', async () => {
      vi.mocked(listSkillsWithContent).mockResolvedValue([
        makeSkill({ id: 'skill-1', name: 'Data Visualization' }),
        makeSkill({ id: 'skill-2', name: 'Docker Fundamentals' }),
      ]);
      const user = userEvent.setup();
      renderPage();
      await screen.findByText('Data Visualization');

      await user.type(screen.getByTestId('skills-tab-search-input'), 'docker');

      expect(screen.queryByText('Data Visualization')).not.toBeInTheDocument();
      expect(screen.getByText('Docker Fundamentals')).toBeInTheDocument();

      await user.clear(screen.getByTestId('skills-tab-search-input'));

      expect(await screen.findByText('Data Visualization')).toBeInTheDocument();
      expect(screen.getByText('Docker Fundamentals')).toBeInTheDocument();
    });

    it('shows "No skills match your search." when the search term matches nothing', async () => {
      vi.mocked(listSkillsWithContent).mockResolvedValue([makeSkill({ id: 'skill-1', name: 'Data Visualization' })]);
      const user = userEvent.setup();
      renderPage();
      await screen.findByText('Data Visualization');

      await user.type(screen.getByTestId('skills-tab-search-input'), 'nonexistent-skill-xyz');

      expect(await screen.findByText('No skills match your search.')).toBeInTheDocument();
      expect(screen.queryByText('No skills yet.')).not.toBeInTheDocument();
    });

    it('does not render pagination controls when there are 15 or fewer matching skills', async () => {
      vi.mocked(listSkillsWithContent).mockResolvedValue(makeManySkills(15));
      renderPage();

      await screen.findByText('Skill 01');
      expect(screen.getByText('Skill 15')).toBeInTheDocument();
      expect(screen.queryByTestId('skills-tab-pagination')).not.toBeInTheDocument();
    });

    it('paginates at 15 per page and Next/page-number/Prev controls page correctly', async () => {
      vi.mocked(listSkillsWithContent).mockResolvedValue(makeManySkills(20));
      const user = userEvent.setup();
      renderPage();

      await screen.findByText('Skill 01');
      expect(screen.getByText('Skill 15')).toBeInTheDocument();
      expect(screen.queryByText('Skill 16')).not.toBeInTheDocument();
      // Review finding: Prev/Next disabled state must be asserted directly,
      // not just inferred from which skill names are visible.
      expect(screen.getByLabelText('Previous page')).toBeDisabled();
      expect(screen.getByLabelText('Next page')).toBeEnabled();

      await user.click(screen.getByLabelText('Next page'));

      expect(await screen.findByText('Skill 16')).toBeInTheDocument();
      expect(screen.getByText('Skill 20')).toBeInTheDocument();
      expect(screen.queryByText('Skill 01')).not.toBeInTheDocument();
      expect(screen.getByLabelText('Previous page')).toBeEnabled();
      expect(screen.getByLabelText('Next page')).toBeDisabled();

      await user.click(screen.getByLabelText('Previous page'));

      expect(await screen.findByText('Skill 01')).toBeInTheDocument();
      expect(screen.queryByText('Skill 16')).not.toBeInTheDocument();

      await user.click(screen.getByLabelText('Page 2'));

      expect(await screen.findByText('Skill 16')).toBeInTheDocument();
    });

    it('keeps skills-tab-summary-count on the full unfiltered/unpaginated total while a search term and page 2 are active', async () => {
      const skills = makeManySkills(20);
      vi.mocked(listSkillsWithContent).mockResolvedValue(skills);
      const user = userEvent.setup();
      renderPage();

      await screen.findByText('Skill 01');
      expect(screen.getByTestId('skills-tab-summary-count')).toHaveTextContent('20 skills · 0 with approved content');

      await user.click(screen.getByLabelText('Page 2'));
      expect(screen.getByTestId('skills-tab-summary-count')).toHaveTextContent('20 skills · 0 with approved content');

      await user.type(screen.getByTestId('skills-tab-search-input'), 'Skill 0');
      await screen.findByText('Skill 01');
      expect(screen.getByTestId('skills-tab-summary-count')).toHaveTextContent('20 skills · 0 with approved content');
    });

    it('a new search term resets pagination to page 1', async () => {
      const skills = makeManySkills(20);
      // Give one page-2-only skill a distinct, searchable name.
      skills[19] = makeSkill({ id: 'skill-20', name: 'Special Topic' });
      vi.mocked(listSkillsWithContent).mockResolvedValue(skills);
      const user = userEvent.setup();
      renderPage();

      await screen.findByText('Skill 01');
      await user.click(screen.getByLabelText('Page 2'));
      expect(await screen.findByText('Special Topic')).toBeInTheDocument();

      await user.type(screen.getByTestId('skills-tab-search-input'), 'Skill 01');

      expect(await screen.findByText('Skill 01')).toBeInTheDocument();
      expect(screen.queryByText('Special Topic')).not.toBeInTheDocument();
    });
  });
});
