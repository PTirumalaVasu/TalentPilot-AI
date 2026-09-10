import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ContentLookupPanel } from '@/features/admin/ContentLookupPanel';
import type { SkillWithContent } from '@/lib/api/skillsApi';

vi.mock('@/lib/api/adminContentApi', () => ({
  attachContent: vi.fn(),
  searchContentForSkill: vi.fn(),
  rejectContent: vi.fn(),
  reviewManualContent: vi.fn(),
}));
vi.mock('@/lib/api/adminApiKeysApi', () => ({
  getApiKeysStatus: vi.fn(),
}));
vi.mock('@/lib/api/skillsApi', () => ({
  updateSkill: vi.fn(),
}));

import { attachContent, searchContentForSkill, rejectContent } from '@/lib/api/adminContentApi';
import { getApiKeysStatus } from '@/lib/api/adminApiKeysApi';
import { updateSkill } from '@/lib/api/skillsApi';

const BOTH_CONFIGURED = {
  youtube: { configured: true },
  udemy: { configured: true, configured_by: 'Rita', configured_at: '2026-09-08T00:00:00Z' },
};

function makeSkill(overrides: Partial<SkillWithContent> = {}): SkillWithContent {
  return {
    id: 'skill-1',
    name: 'Data Visualization',
    description: 'Charts and graphs',
    ever_assigned: false,
    approved_content: null,
    ...overrides,
  };
}

describe('ContentLookupPanel', () => {
  beforeEach(() => {
    vi.mocked(attachContent).mockReset();
    vi.mocked(searchContentForSkill).mockReset();
    vi.mocked(rejectContent).mockReset();
    vi.mocked(updateSkill).mockReset();
    vi.mocked(getApiKeysStatus).mockReset().mockResolvedValue(BOTH_CONFIGURED);
  });

  const defaultProps = {
    open: true,
    onClose: vi.fn(),
    onSkillUpdated: vi.fn(),
    onContentChanged: vi.fn(),
    onApproved: vi.fn(),
    onOpenApiKeys: vi.fn(),
  };

  it('renders CurrentlyApprovedContent when approved_content is present', async () => {
    const skill = makeSkill({
      approved_content: {
        id: 'content-1',
        skill_id: 'skill-1',
        title: 'Existing Course',
        description: null,
        type: 'VIDEO',
        url: 'https://example.com/existing',
        source: 'MANUAL',
        ingested_at: '2026-09-10T00:00:00Z',
        metadata: null,
      },
    });
    render(<ContentLookupPanel {...defaultProps} skill={skill} />);

    expect(await screen.findByTestId('content-lookup-current-approved')).toBeInTheDocument();
    expect(screen.getByText('Existing Course')).toBeInTheDocument();
  });

  it('omits the Currently Approved section when there is no approved content', async () => {
    render(<ContentLookupPanel {...defaultProps} skill={makeSkill()} />);

    await waitFor(() => expect(getApiKeysStatus).toHaveBeenCalled());
    expect(screen.queryByTestId('content-lookup-current-approved')).not.toBeInTheDocument();
  });

  it('edit-name save success calls onSkillUpdated and the panel stays open', async () => {
    vi.mocked(updateSkill).mockResolvedValue({
      id: 'skill-1',
      name: 'Data Viz Renamed',
      description: 'Charts and graphs',
      ever_assigned: false,
    });
    const onSkillUpdated = vi.fn();
    const user = userEvent.setup();
    render(<ContentLookupPanel {...defaultProps} skill={makeSkill()} onSkillUpdated={onSkillUpdated} />);

    const nameInput = screen.getByTestId('content-lookup-edit-name-input');
    await user.clear(nameInput);
    await user.type(nameInput, 'Data Viz Renamed');
    await user.click(screen.getByTestId('content-lookup-btn-save-name'));

    await waitFor(() =>
      expect(onSkillUpdated).toHaveBeenCalledWith({
        id: 'skill-1',
        name: 'Data Viz Renamed',
        description: 'Charts and graphs',
        ever_assigned: false,
      })
    );
    expect(screen.getByTestId('content-lookup-header-title')).toBeInTheDocument();
  });

  it('edit-name 409 shows the no-redirect duplicate notice', async () => {
    vi.mocked(updateSkill).mockRejectedValue({ response: { status: 409, data: { message: 'conflict' } } });
    const user = userEvent.setup();
    render(<ContentLookupPanel {...defaultProps} skill={makeSkill()} />);

    await user.click(screen.getByTestId('content-lookup-btn-save-name'));

    const notice = await screen.findByTestId('content-lookup-edit-duplicate-notice');
    expect(notice).toHaveTextContent('already exists');
    expect(screen.queryByText('Use existing skill')).not.toBeInTheDocument();
  });

  it('search renders grouped result cards and respects the source checkbox filter', async () => {
    vi.mocked(searchContentForSkill).mockResolvedValue({
      results: [
        { title: 'YT Result', source: 'YOUTUBE', url: 'https://youtube.com/watch?v=1', thumbnail_url: null, duration_hours: 5 },
        { title: 'Udemy Result', source: 'UDEMY', url: 'https://udemy.com/course/1', thumbnail_url: null, duration_hours: null },
      ],
      errors: [],
    });
    const user = userEvent.setup();
    render(<ContentLookupPanel {...defaultProps} skill={makeSkill()} />);
    await waitFor(() => expect(getApiKeysStatus).toHaveBeenCalled());

    await user.click(screen.getByTestId('content-lookup-search-btn'));

    expect(await screen.findByText('YT Result')).toBeInTheDocument();
    expect(screen.getByText('Udemy Result')).toBeInTheDocument();

    await user.click(screen.getByTestId('content-lookup-source-toggle-udemy'));

    expect(screen.queryByText('Udemy Result')).not.toBeInTheDocument();
    expect(screen.getByText('YT Result')).toBeInTheDocument();
  });

  it('disables an unconfigured source checkbox and shows the "Add a key" prompt', async () => {
    vi.mocked(getApiKeysStatus).mockResolvedValue({
      youtube: { configured: false },
      udemy: { configured: true, configured_by: 'Rita', configured_at: '2026-09-08T00:00:00Z' },
    });
    render(<ContentLookupPanel {...defaultProps} skill={makeSkill()} />);

    expect(await screen.findByText(/Add a YouTube key/)).toBeInTheDocument();
    expect(screen.getByTestId('content-lookup-source-toggle-youtube')).toBeDisabled();
    expect(screen.getByTestId('content-lookup-source-toggle-udemy')).not.toBeDisabled();
  });

  it('a Search-tab Approve click calls onClose then onApproved with the skill name', async () => {
    vi.mocked(searchContentForSkill).mockResolvedValue({
      results: [
        { title: 'YT Result', source: 'YOUTUBE', url: 'https://youtube.com/watch?v=1', thumbnail_url: null, duration_hours: 5 },
      ],
      errors: [],
    });
    vi.mocked(attachContent).mockResolvedValue({
      id: 'content-2',
      skill_id: 'skill-1',
      title: 'YT Result',
      description: null,
      type: 'VIDEO',
      url: 'https://youtube.com/watch?v=1',
      source: 'YOUTUBE',
      ingested_at: '2026-09-10T00:00:00Z',
      metadata: null,
    });
    const onClose = vi.fn();
    const onApproved = vi.fn();
    const user = userEvent.setup();
    render(
      <ContentLookupPanel {...defaultProps} skill={makeSkill()} onClose={onClose} onApproved={onApproved} />
    );
    await user.click(screen.getByTestId('content-lookup-search-btn'));
    await screen.findByText('YT Result');

    await user.click(screen.getByTestId('content-lookup-btn-approve'));

    await waitFor(() => expect(attachContent).toHaveBeenCalledWith({
      skill_id: 'skill-1',
      title: 'YT Result',
      source: 'YOUTUBE',
      url: 'https://youtube.com/watch?v=1',
      duration_hours: 5,
    }));
    expect(onClose).toHaveBeenCalled();
    expect(onApproved).toHaveBeenCalledWith('Data Visualization');
  });

  it('disables every result card\'s Approve button while any one approve is in flight (code review, 2026-09-10)', async () => {
    vi.mocked(searchContentForSkill).mockResolvedValue({
      results: [
        { title: 'YT Result A', source: 'YOUTUBE', url: 'https://youtube.com/watch?v=a', thumbnail_url: null, duration_hours: 5 },
        { title: 'YT Result B', source: 'YOUTUBE', url: 'https://youtube.com/watch?v=b', thumbnail_url: null, duration_hours: 3 },
      ],
      errors: [],
    });
    let resolveAttach!: (value: Awaited<ReturnType<typeof attachContent>>) => void;
    vi.mocked(attachContent).mockReturnValue(
      new Promise((resolve) => {
        resolveAttach = resolve;
      })
    );
    const user = userEvent.setup();
    render(<ContentLookupPanel {...defaultProps} skill={makeSkill()} onClose={vi.fn()} onApproved={vi.fn()} />);
    await user.click(screen.getByTestId('content-lookup-search-btn'));
    await screen.findByText('YT Result A');

    const approveButtons = screen.getAllByTestId('content-lookup-btn-approve');
    expect(approveButtons).toHaveLength(2);
    await user.click(approveButtons[0]);

    expect(approveButtons[0]).toBeDisabled();
    expect(approveButtons[1]).toBeDisabled();

    resolveAttach!({
      id: 'content-2',
      skill_id: 'skill-1',
      title: 'YT Result A',
      description: null,
      type: 'VIDEO',
      url: 'https://youtube.com/watch?v=a',
      source: 'YOUTUBE',
      ingested_at: '2026-09-10T00:00:00Z',
      metadata: null,
    });
  });

  it("the Paste-a-link tab's approve also closes the panel and calls onApproved", async () => {
    const { reviewManualContent } = await import('@/lib/api/adminContentApi');
    vi.mocked(reviewManualContent).mockResolvedValue({
      title: 'Manual Course',
      source: 'MANUAL',
      url: 'https://example.com/manual',
      duration_hours: null,
    });
    vi.mocked(attachContent).mockResolvedValue({
      id: 'content-3',
      skill_id: 'skill-1',
      title: 'Manual Course',
      description: null,
      type: 'VIDEO',
      url: 'https://example.com/manual',
      source: 'MANUAL',
      ingested_at: '2026-09-10T00:00:00Z',
      metadata: null,
    });
    const onClose = vi.fn();
    const onApproved = vi.fn();
    const user = userEvent.setup();
    render(
      <ContentLookupPanel {...defaultProps} skill={makeSkill()} onClose={onClose} onApproved={onApproved} />
    );

    await user.click(screen.getByTestId('content-lookup-tab-manual'));
    await user.type(screen.getByTestId('content-lookup-manual-url-input'), 'https://example.com/manual');
    await user.type(screen.getByTestId('content-lookup-manual-title-input'), 'Manual Course');
    await user.click(screen.getByTestId('content-lookup-manual-btn-review'));
    await screen.findByText('Manual Course');
    await user.click(screen.getByTestId('content-lookup-btn-approve'));

    await waitFor(() => expect(onClose).toHaveBeenCalled());
    expect(onApproved).toHaveBeenCalledWith('Data Visualization');
  });

  it('View on a search result card opens ContentPreviewModal with the right fields', async () => {
    vi.mocked(searchContentForSkill).mockResolvedValue({
      results: [
        { title: 'YT Result', source: 'YOUTUBE', url: 'https://youtube.com/watch?v=abc123', thumbnail_url: null, duration_hours: 2 },
      ],
      errors: [],
    });
    const user = userEvent.setup();
    render(<ContentLookupPanel {...defaultProps} skill={makeSkill()} />);
    await user.click(screen.getByTestId('content-lookup-search-btn'));
    await screen.findByText('YT Result');

    await user.click(screen.getByTestId('content-lookup-btn-view'));

    expect(await screen.findByTestId('watch-modal-title')).toHaveTextContent('YT Result');
  });
});
