import { useEffect, useId, useState } from 'react';
import { Dialog } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { FormErrorText } from '@/components/ui/form-error-text';
import { Card, CardContent } from '@/components/ui/card';
import { CurrentlyApprovedContent } from '@/features/admin/CurrentlyApprovedContent';
import { ManualContentEntryForm } from '@/features/admin/ManualContentEntryForm';
import { ContentPreviewModal } from '@/features/admin/ContentPreviewModal';
import {
  attachContent,
  searchContentForSkill,
  type ContentLookupCandidate,
  type ContentLookupResponse,
} from '@/lib/api/adminContentApi';
import { getApiKeysStatus, type ApiKeysStatus } from '@/lib/api/adminApiKeysApi';
import { updateSkill, type SkillResponse, type SkillWithContent } from '@/lib/api/skillsApi';
import { estimateDaysToComplete } from '@/lib/utils/duration';

export interface ContentLookupPanelProps {
  skill: SkillWithContent;
  /** Pre-filled search term for the create/use-existing hand-off (UX-DR31). Defaults to the skill's own name. */
  initialSearchTerm?: string;
  open: boolean;
  onClose: () => void;
  onSkillUpdated: (skill: SkillResponse) => void;
  /** Called after a successful Reject (Story 6.9) so the parent can refetch. */
  onContentChanged: () => void;
  /** Called with the Skill's name right after any successful Approve, after onClose (UX-DR29). */
  onApproved: (skillName: string) => void;
  onOpenApiKeys: () => void;
}

interface ApiErrorLike {
  response?: { status?: number; data?: { message?: string } };
}

function extractErrorMessage(err: unknown, fallback: string): string {
  const apiErr = err as ApiErrorLike;
  return apiErr?.response?.data?.message ?? fallback;
}

type Tab = 'search' | 'manual';
type ViewingContent = { title: string; source: string; url: string; durationHours: number | null };

/**
 * The Content Lookup Panel (Story 6.10 AC3-AC7): edit-name/description
 * fields, the Currently Approved section (reuses CurrentlyApprovedContent
 * as-is, Story 6.9), Search/Paste-a-link tabs. Approving from ANY tab
 * closes the panel immediately (UX-DR29) via the shared handleApproved().
 */
export function ContentLookupPanel({
  skill,
  initialSearchTerm,
  open,
  onClose,
  onSkillUpdated,
  onContentChanged,
  onApproved,
  onOpenApiKeys,
}: ContentLookupPanelProps) {
  const titleId = useId();

  const [name, setName] = useState(skill.name);
  const [description, setDescription] = useState(skill.description ?? '');
  const [savingName, setSavingName] = useState(false);
  const [saveNameError, setSaveNameError] = useState<string | null>(null);
  const [saveNameDuplicate, setSaveNameDuplicate] = useState(false);

  const [contentRejected, setContentRejected] = useState(false);

  const [tab, setTab] = useState<Tab>('search');
  const [apiKeysStatus, setApiKeysStatus] = useState<ApiKeysStatus | null>(null);
  const [youtubeChecked, setYoutubeChecked] = useState(true);
  const [udemyChecked, setUdemyChecked] = useState(true);
  const [searchTerm, setSearchTerm] = useState(initialSearchTerm ?? skill.name);
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [searchResult, setSearchResult] = useState<ContentLookupResponse | null>(null);
  const [approvingUrl, setApprovingUrl] = useState<string | null>(null);
  const [approveError, setApproveError] = useState<string | null>(null);
  const [viewing, setViewing] = useState<ViewingContent | null>(null);

  useEffect(() => {
    if (!open) return;
    setName(skill.name);
    setDescription(skill.description ?? '');
    setSaveNameError(null);
    setSaveNameDuplicate(false);
    setContentRejected(false);
    setTab('search');
    setSearchTerm(initialSearchTerm ?? skill.name);
    setSearchResult(null);
    setSearchError(null);
    setApproveError(null);
    setApprovingUrl(null);
    setViewing(null);

    let cancelled = false;
    void (async () => {
      try {
        const status = await getApiKeysStatus();
        if (cancelled) return;
        setApiKeysStatus(status);
        setYoutubeChecked(status.youtube.configured);
        setUdemyChecked(status.udemy.configured);
      } catch {
        if (cancelled) return;
        setApiKeysStatus(null);
      }
    })();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, skill.id]);

  async function handleSaveName() {
    const trimmedName = name.trim();
    if (!trimmedName) return;
    setSavingName(true);
    setSaveNameError(null);
    setSaveNameDuplicate(false);
    try {
      const updated = await updateSkill(skill.id, { name: trimmedName, description: description.trim() || null });
      onSkillUpdated(updated);
    } catch (err) {
      if ((err as ApiErrorLike)?.response?.status === 409) {
        setSaveNameDuplicate(true);
      } else {
        setSaveNameError(extractErrorMessage(err, "Couldn't save this skill — Try again"));
      }
    } finally {
      setSavingName(false);
    }
  }

  async function handleSearch() {
    const query = searchTerm.trim() || skill.name;
    setSearching(true);
    setSearchError(null);
    setSearchResult(null);
    try {
      const result = await searchContentForSkill(skill.id, query);
      setSearchResult(result);
    } catch (err) {
      setSearchError(extractErrorMessage(err, "Couldn't search right now — Try again"));
    } finally {
      setSearching(false);
    }
  }

  function handleApproved() {
    onClose();
    onApproved(skill.name);
  }

  async function handleApproveCandidate(candidate: ContentLookupCandidate) {
    setApprovingUrl(candidate.url);
    setApproveError(null);
    try {
      await attachContent({
        skill_id: skill.id,
        title: candidate.title,
        source: candidate.source,
        url: candidate.url,
        duration_hours: candidate.duration_hours,
      });
      handleApproved();
    } catch (err) {
      setApproveError(extractErrorMessage(err, "Couldn't approve this — Try again"));
      setApprovingUrl(null);
    }
  }

  if (!open) return null;

  const youtubeConfigured = apiKeysStatus?.youtube.configured ?? false;
  const udemyConfigured = apiKeysStatus?.udemy.configured ?? false;
  const youtubeResults = searchResult?.results.filter((r) => r.source === 'YOUTUBE') ?? [];
  const udemyResults = searchResult?.results.filter((r) => r.source === 'UDEMY') ?? [];
  const youtubeSourceError = searchResult?.errors.find((e) => e.source === 'YOUTUBE');
  const udemySourceError = searchResult?.errors.find((e) => e.source === 'UDEMY');

  return (
    <>
      <Dialog open={open} onClose={onClose} titleId={titleId} className="max-h-[85vh] max-w-2xl overflow-y-auto">
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 id={titleId} className="text-lg font-bold text-gray-900" data-testid="content-lookup-header-title">
              Find content for {skill.name}
            </h2>
            <button
              type="button"
              aria-label="Close"
              onClick={onClose}
              className="text-xl leading-none text-gray-400 hover:text-gray-600"
              data-testid="content-lookup-btn-close"
            >
              ✕
            </button>
          </div>

          <div className="space-y-2 border-b border-gray-100 pb-4" data-testid="content-lookup-edit-fields">
            <div>
              <Label htmlFor="content-lookup-edit-name-input">Skill name</Label>
              <Input
                id="content-lookup-edit-name-input"
                value={name}
                onChange={(e) => setName(e.target.value)}
                disabled={savingName}
                data-testid="content-lookup-edit-name-input"
              />
            </div>
            <div>
              <Label htmlFor="content-lookup-edit-description-input">Description (optional)</Label>
              <textarea
                id="content-lookup-edit-description-input"
                rows={2}
                className="w-full rounded-lg border border-gray-300 px-3 py-1.5 text-sm"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                disabled={savingName}
                data-testid="content-lookup-edit-description-input"
              />
            </div>
            {saveNameDuplicate && (
              <p className="text-sm text-amber-800" data-testid="content-lookup-edit-duplicate-notice">
                A skill named &apos;{name.trim()}&apos; already exists.
              </p>
            )}
            {saveNameError && <FormErrorText>{saveNameError}</FormErrorText>}
            <Button
              variant="outline"
              size="sm"
              onClick={handleSaveName}
              disabled={savingName || !name.trim()}
              data-testid="content-lookup-btn-save-name"
            >
              {savingName ? 'Saving…' : 'Save name'}
            </Button>
          </div>

          {skill.approved_content && !contentRejected && (
            <div data-testid="content-lookup-current-approved-section">
              <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">Currently Approved</h3>
              <CurrentlyApprovedContent
                contentId={skill.approved_content.id}
                title={skill.approved_content.title}
                source={skill.approved_content.source}
                url={skill.approved_content.url}
                durationHours={(skill.approved_content.metadata?.duration_hours as number | undefined) ?? null}
                skillName={skill.name}
                onRejected={() => {
                  setContentRejected(true);
                  onContentChanged();
                }}
              />
            </div>
          )}

          <div className="flex gap-1 border-b border-gray-200">
            <button
              type="button"
              className={
                tab === 'search'
                  ? 'border-b-2 border-blue-600 px-3 py-2 text-sm font-medium text-blue-600'
                  : 'border-b-2 border-transparent px-3 py-2 text-sm font-medium text-gray-500 hover:text-gray-700'
              }
              onClick={() => setTab('search')}
              data-testid="content-lookup-tab-search"
            >
              Search
            </button>
            <button
              type="button"
              className={
                tab === 'manual'
                  ? 'border-b-2 border-blue-600 px-3 py-2 text-sm font-medium text-blue-600'
                  : 'border-b-2 border-transparent px-3 py-2 text-sm font-medium text-gray-500 hover:text-gray-700'
              }
              onClick={() => setTab('manual')}
              data-testid="content-lookup-tab-manual"
            >
              Paste a link
            </button>
          </div>

          {tab === 'search' && (
            <div className="space-y-4" data-testid="content-lookup-search-view">
              <p className="text-xs text-gray-400">Search Results — unreviewed candidates, not yet approved</p>
              <div className="flex flex-wrap items-center gap-4">
                <label className="flex items-center gap-1.5 text-sm">
                  <input
                    type="checkbox"
                    checked={youtubeChecked && youtubeConfigured}
                    disabled={!youtubeConfigured}
                    onChange={(e) => setYoutubeChecked(e.target.checked)}
                    data-testid="content-lookup-source-toggle-youtube"
                  />
                  YouTube
                </label>
                {!youtubeConfigured && (
                  <span className="text-xs text-gray-500">
                    Add a YouTube key to search this source.{' '}
                    <button type="button" className="underline" onClick={onOpenApiKeys}>
                      Manage API Keys
                    </button>
                  </span>
                )}
                <label className="flex items-center gap-1.5 text-sm">
                  <input
                    type="checkbox"
                    checked={udemyChecked && udemyConfigured}
                    disabled={!udemyConfigured}
                    onChange={(e) => setUdemyChecked(e.target.checked)}
                    data-testid="content-lookup-source-toggle-udemy"
                  />
                  Udemy
                </label>
                {!udemyConfigured && (
                  <span className="text-xs text-gray-500">
                    Add the Udemy credential to search this source.{' '}
                    <button type="button" className="underline" onClick={onOpenApiKeys}>
                      Manage API Keys
                    </button>
                  </span>
                )}
              </div>
              <div className="flex gap-2">
                <Input
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="Search term (defaults to skill name)"
                  data-testid="content-lookup-search-term-input"
                />
                <Button onClick={handleSearch} disabled={searching} data-testid="content-lookup-search-btn">
                  {searching ? 'Searching…' : 'Search'}
                </Button>
              </div>
              {searchError && <FormErrorText>{searchError}</FormErrorText>}
              {approveError && <FormErrorText>{approveError}</FormErrorText>}

              {searchResult && youtubeChecked && (
                <div data-testid="content-lookup-results-youtube">
                  <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">YouTube</h3>
                  {youtubeSourceError && (
                    <p className="text-xs text-gray-500">Couldn&apos;t search YouTube right now. Try again</p>
                  )}
                  {!youtubeSourceError && youtubeResults.length === 0 && (
                    <p className="text-xs text-gray-500">No results from YouTube for this skill.</p>
                  )}
                  <div className="space-y-2">
                    {youtubeResults.map((candidate) => (
                      <ResultCard
                        key={candidate.url}
                        candidate={candidate}
                        approving={approvingUrl === candidate.url}
                        disabled={approvingUrl !== null}
                        onView={() =>
                          setViewing({
                            title: candidate.title,
                            source: candidate.source,
                            url: candidate.url,
                            durationHours: candidate.duration_hours,
                          })
                        }
                        onApprove={() => handleApproveCandidate(candidate)}
                      />
                    ))}
                  </div>
                </div>
              )}

              {searchResult && udemyChecked && (
                <div data-testid="content-lookup-results-udemy">
                  <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">Udemy</h3>
                  {udemySourceError && (
                    <p className="text-xs text-gray-500">Couldn&apos;t search Udemy right now. Try again</p>
                  )}
                  {!udemySourceError && udemyResults.length === 0 && (
                    <p className="text-xs text-gray-500">No results from Udemy for this skill.</p>
                  )}
                  <div className="space-y-2">
                    {udemyResults.map((candidate) => (
                      <ResultCard
                        key={candidate.url}
                        candidate={candidate}
                        approving={approvingUrl === candidate.url}
                        disabled={approvingUrl !== null}
                        onView={() =>
                          setViewing({
                            title: candidate.title,
                            source: candidate.source,
                            url: candidate.url,
                            durationHours: candidate.duration_hours,
                          })
                        }
                        onApprove={() => handleApproveCandidate(candidate)}
                      />
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {tab === 'manual' && (
            <div data-testid="content-lookup-manual-view">
              <ManualContentEntryForm skillId={skill.id} skillName={skill.name} onApproved={handleApproved} />
            </div>
          )}
        </div>
      </Dialog>

      {viewing && (
        <ContentPreviewModal
          open
          onClose={() => setViewing(null)}
          title={viewing.title}
          source={viewing.source}
          url={viewing.url}
          durationHours={viewing.durationHours}
        />
      )}
    </>
  );
}

function ResultCard({
  candidate,
  approving,
  disabled,
  onView,
  onApprove,
}: {
  candidate: ContentLookupCandidate;
  /** True only for the specific candidate whose attach call is in flight -- drives the "Approving…" label. */
  approving: boolean;
  /**
   * True whenever ANY candidate in this panel is being approved, not just
   * this one -- without this, every other card's [Approve] button stayed
   * clickable during another candidate's in-flight attach, letting two
   * concurrent approves both succeed and write two content_catalog rows
   * for the same Skill before either's handleApproved() could close the
   * panel (code review, 2026-09-10).
   */
  disabled: boolean;
  onView: () => void;
  onApprove: () => void;
}) {
  const days = estimateDaysToComplete(candidate.duration_hours);
  return (
    <Card data-testid="content-lookup-result-card">
      <CardContent className="flex items-center justify-between gap-3 space-y-0 p-4">
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium text-gray-900">{candidate.title}</p>
          {days != null && (
            <p className="text-xs text-gray-500" data-testid="content-lookup-result-days-estimate">
              ≈ {days} day{days === 1 ? '' : 's'} to complete (at 5 hrs/day)
            </p>
          )}
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <Button variant="outline" size="sm" onClick={onView} data-testid="content-lookup-btn-view">
            View
          </Button>
          <Button size="sm" onClick={onApprove} disabled={disabled} data-testid="content-lookup-btn-approve">
            {approving ? 'Approving…' : 'Approve'}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
