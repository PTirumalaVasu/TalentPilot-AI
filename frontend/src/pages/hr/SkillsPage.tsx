/** Skills tab (Story 6.10): Card Grid, Content Lookup, API Keys, Watch Modal.
 * Left-pane nav shell: Story 7.7.
 * Search + 15/page pagination (Story 10.5, FR-37): client-side over the same
 * fetched list, no new API/query params -- mirrors EmployeesPage.tsx's
 * existing FR-25 search/pagination shape (Story 7.3). Table/Card view toggle
 * is a separate, later story (10.13) and is not built here. */
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { HrAppShell } from '@/components/layout/HrAppShell';
import { Toast } from '@/components/ui/toast';
import { SkillCard, type SkillCardViewContent } from '@/features/admin/SkillCard';
import { NewSkillModal } from '@/features/admin/NewSkillModal';
import { DeleteSkillModal } from '@/features/admin/DeleteSkillModal';
import { ContentLookupPanel } from '@/features/admin/ContentLookupPanel';
import { ApiKeysModal } from '@/features/admin/ApiKeysModal';
import { ContentPreviewModal } from '@/features/admin/ContentPreviewModal';
import { listSkillsWithContent, type SkillWithContent } from '@/lib/api/skillsApi';

const PAGE_SIZE = 15;

function extractErrorMessage(err: unknown, fallback: string): string {
  if (err && typeof err === 'object' && 'response' in err) {
    const response = (err as { response?: { data?: { message?: string } } }).response;
    if (response?.data?.message) return response.data.message;
  }
  return fallback;
}

interface LookupTarget {
  skill: SkillWithContent;
  initialSearchTerm?: string;
}

export function SkillsPage() {
  const [skills, setSkills] = useState<SkillWithContent[] | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const requestIdRef = useRef(0);

  const [newSkillModalOpen, setNewSkillModalOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<SkillWithContent | null>(null);
  const [lookupTarget, setLookupTarget] = useState<LookupTarget | null>(null);
  const [apiKeysModalOpen, setApiKeysModalOpen] = useState(false);
  const [watchModalContent, setWatchModalContent] = useState<SkillCardViewContent | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // Story 10.5 (FR-37): search matches Skill name only -- SkillWithContent
  // does carry a `description` field, but it's never rendered anywhere on
  // SkillCard (unlike EmployeesPage's displayed Project/Location/
  // Technologies columns), so there's no visible content a name-only search
  // box could plausibly be expected to also match against. 15/page
  // pagination -- both purely additive over the already-fetched `skills`
  // array (Scope Note 1: no backend change).
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);

  const refetch = useCallback(async () => {
    const requestId = ++requestIdRef.current;
    setLoadError(null);
    try {
      const result = await listSkillsWithContent();
      if (requestIdRef.current !== requestId) return;
      setSkills(result);
    } catch (err) {
      if (requestIdRef.current !== requestId) return;
      setLoadError(extractErrorMessage(err, "Couldn't load skills. Try again."));
    }
  }, []);

  useEffect(() => {
    void refetch();
  }, [refetch]);

  function findSkill(skillId: string): SkillWithContent | undefined {
    return skills?.find((s) => s.id === skillId);
  }

  // `skills-tab-summary-count` keeps counting the full fetched list, not the
  // filtered/paginated subset -- matches EmployeesPage.tsx's equivalent
  // summary-count convention.
  const approvedCount = skills?.filter((s) => s.approved_content).length ?? 0;

  const filtered = useMemo(() => {
    if (!skills) return [];
    const q = search.trim().toLowerCase();
    if (!q) return skills;
    return skills.filter((s) => s.name.toLowerCase().includes(q));
  }, [skills, search]);

  // AC2: a new search term resets pagination to page 1.
  useEffect(() => {
    setPage(1);
  }, [search]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const currentPage = Math.min(page, totalPages);
  const pageItems = filtered.slice((currentPage - 1) * PAGE_SIZE, (currentPage - 1) * PAGE_SIZE + PAGE_SIZE);

  return (
    <HrAppShell>
      <main className="px-6 pb-12">
        <div className="flex items-center justify-between py-3">
          <div>
            <h1 className="text-2xl font-black text-gray-900 dark:text-gray-100" data-testid="skills-tab-heading-title">
              Skills
            </h1>
            <span className="text-sm text-gray-500 dark:text-gray-400" data-testid="skills-tab-summary-count">
              {skills ? `${skills.length} skills · ${approvedCount} with approved content` : ''}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <input
              type="text"
              placeholder="Search skills…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-40 rounded-lg border border-gray-300 px-3 py-2 text-sm sm:w-48 dark:border-gray-600 dark:bg-gray-900 dark:text-gray-100"
              data-testid="skills-tab-search-input"
            />
            <button
              type="button"
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-blue-700 dark:bg-blue-700 dark:hover:bg-blue-600"
              onClick={() => setNewSkillModalOpen(true)}
              data-testid="skills-tab-btn-new-skill"
            >
              + New Skill
            </button>
            <button
              type="button"
              className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-semibold text-gray-700 transition-colors hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-900 dark:text-gray-300 dark:hover:bg-gray-800"
              onClick={() => setApiKeysModalOpen(true)}
              data-testid="skills-tab-btn-manage-keys"
            >
              Manage API Keys
            </button>
          </div>
        </div>

        {skills === null && !loadError && <p className="text-sm text-gray-500 dark:text-gray-400">Loading…</p>}

        {loadError && (
          <div className="space-y-2">
            <p className="text-sm text-red-600 dark:text-red-400">{loadError}</p>
            <button type="button" className="text-sm font-medium text-blue-600 hover:underline dark:text-blue-400" onClick={() => void refetch()}>
              Retry
            </button>
          </div>
        )}

        {skills !== null && !loadError && skills.length === 0 && (
          <p className="text-sm text-gray-500 dark:text-gray-400">No skills yet.</p>
        )}

        {skills !== null && !loadError && skills.length > 0 && filtered.length === 0 && (
          <p className="text-sm text-gray-500 dark:text-gray-400">No skills match your search.</p>
        )}

        {skills !== null && !loadError && filtered.length > 0 && (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3" data-testid="skills-tab-grid-skills">
            {pageItems.map((skill) => (
              <SkillCard
                key={skill.id}
                skill={skill}
                onEdit={(s) => setLookupTarget({ skill: s })}
                onDelete={(s) => setDeleteTarget(s)}
                onView={(content) => setWatchModalContent(content)}
              />
            ))}
          </div>
        )}

        {filtered.length > PAGE_SIZE && (
          <div
            className="mt-4 flex items-center justify-center gap-3 text-sm text-gray-600 dark:text-gray-400"
            data-testid="skills-tab-pagination"
          >
            <button
              type="button"
              onClick={() => setPage(currentPage - 1)}
              disabled={currentPage === 1}
              className="disabled:opacity-30"
              aria-label="Previous page"
            >
              ‹
            </button>
            {Array.from({ length: totalPages }, (_, i) => i + 1).map((p) => (
              <button
                key={p}
                type="button"
                onClick={() => setPage(p)}
                className={p === currentPage ? 'font-bold text-blue-600 dark:text-blue-400' : ''}
                aria-label={`Page ${p}`}
                aria-current={p === currentPage ? 'page' : undefined}
              >
                {p}
              </button>
            ))}
            <button
              type="button"
              onClick={() => setPage(currentPage + 1)}
              disabled={currentPage === totalPages}
              className="disabled:opacity-30"
              aria-label="Next page"
            >
              ›
            </button>
          </div>
        )}
      </main>

      <NewSkillModal
        open={newSkillModalOpen}
        onClose={() => setNewSkillModalOpen(false)}
        onCreated={(skill, searchTerm) => {
          setNewSkillModalOpen(false);
          void refetch();
          setLookupTarget({
            skill: { ...skill, approved_content: null },
            initialSearchTerm: searchTerm,
          });
        }}
        onUseExisting={(existingSkillId, existingName, enteredName) => {
          setNewSkillModalOpen(false);
          const existing = findSkill(existingSkillId);
          // A locked (ever_assigned) Skill has no entry point into the
          // Content Lookup panel anywhere on this page (AC10/UX-DR33) --
          // this hand-off must honor that too, not just SkillCard's own
          // Edit icon. When the conflicting Skill isn't in the local cache
          // at all (stale/incomplete fetch), its real ever_assigned/
          // approved_content are unknown, so don't fabricate them as
          // unlocked/empty -- decline the hand-off the same way (code
          // review, 2026-09-10).
          if (!existing || existing.ever_assigned) {
            setToastMessage(
              existing
                ? `'${existingName}' is already assigned to an Employee and can't be edited.`
                : `Couldn't find '${existingName}' — refresh and try again.`
            );
            return;
          }
          setLookupTarget({ skill: existing, initialSearchTerm: enteredName });
        }}
      />

      <DeleteSkillModal
        skill={deleteTarget ? { id: deleteTarget.id, name: deleteTarget.name } : null}
        open={deleteTarget !== null}
        onClose={() => setDeleteTarget(null)}
        onDeleted={(_skillId) => {
          const name = deleteTarget?.name;
          setDeleteTarget(null);
          void refetch();
          setToastMessage(`✓ '${name}' deleted.`);
        }}
      />

      {lookupTarget && (
        <ContentLookupPanel
          skill={lookupTarget.skill}
          initialSearchTerm={lookupTarget.initialSearchTerm}
          open
          onClose={() => setLookupTarget(null)}
          onSkillUpdated={(updated) => {
            // Merge the renamed fields into the panel's own copy immediately
            // (its header reads skill.name) instead of waiting on the grid
            // refetch below to land.
            setLookupTarget((prev) =>
              prev
                ? {
                    ...prev,
                    skill: { ...prev.skill, name: updated.name, description: updated.description },
                  }
                : prev
            );
            void refetch();
          }}
          onContentChanged={() => {
            void refetch();
          }}
          onApproved={(skillName) => {
            void refetch();
            setToastMessage(`✓ Content approved for ${skillName}`);
          }}
          onOpenApiKeys={() => setApiKeysModalOpen(true)}
        />
      )}

      <ApiKeysModal open={apiKeysModalOpen} onClose={() => setApiKeysModalOpen(false)} />

      <ContentPreviewModal
        open={watchModalContent !== null}
        onClose={() => setWatchModalContent(null)}
        title={watchModalContent?.title ?? ''}
        source={watchModalContent?.source ?? ''}
        url={watchModalContent?.url ?? ''}
        durationHours={watchModalContent?.durationHours ?? null}
      />

      <Toast message={toastMessage} onDismiss={() => setToastMessage(null)} />
    </HrAppShell>
  );
}
