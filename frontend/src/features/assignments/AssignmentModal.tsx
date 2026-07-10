import * as React from 'react';
import { Dialog } from '@/components/ui/dialog';
import { Combobox, type ComboboxOption } from '@/components/ui/combobox';
import { Button } from '@/components/ui/button';
import { FormErrorText } from '@/components/ui/form-error-text';
import {
  listEmployees,
  listSkills,
  matchContentForSkill,
  checkDuplicateAssignment,
  createAssignment,
  type Employee,
  type Skill,
  type ContentMatch,
} from '@/lib/api/assignmentsApi';

const TITLE_ID = 'assignment-modal-title';
const TOTAL_STEPS = 3;

type Step = 1 | 2 | 3;

interface ContentMetadata {
  video_id?: string;
  duration?: number;
}

function formatRole(role: string): string {
  return role === 'HR_ADMIN' ? 'HR Admin' : 'Employee';
}

function formatSource(source: string): string {
  return source === 'YOUTUBE' ? 'YouTube' : source === 'MANUAL' ? 'Manual' : source;
}

export interface AssignmentModalProps {
  open: boolean;
  onClose: () => void;
  /** Called after a successful assignment creation, so the caller can refresh any list. */
  onAssigned?: () => void;
}

/**
 * Multi-step "Assign a New Skill" modal (Story 3.4). Step 1: employee,
 * Step 2: skill (+ duplicate check before advancing — a distinct
 * View/Assign-Again interstitial when a duplicate is found, per AC5), Step
 * 3: matched content review + Assignment Summary + Assign/Cancel. Copy
 * strings are taken from the WDS prototype for reference (epics.md AC text
 * wins where they differ) but this component is a from-scratch React
 * implementation.
 */
export function AssignmentModal({ open, onClose, onAssigned }: AssignmentModalProps) {
  const [step, setStep] = React.useState<Step>(1);

  const [employeeSearch, setEmployeeSearch] = React.useState('');
  const [employees, setEmployees] = React.useState<Employee[]>([]);
  const [employeeId, setEmployeeId] = React.useState<string | null>(null);
  const [employeesLoading, setEmployeesLoading] = React.useState(false);

  const [skillSearch, setSkillSearch] = React.useState('');
  const [skills, setSkills] = React.useState<Skill[]>([]);
  const [skillId, setSkillId] = React.useState<string | null>(null);
  const [skillsLoading, setSkillsLoading] = React.useState(false);

  const [duplicateChecking, setDuplicateChecking] = React.useState(false);
  const [duplicateFound, setDuplicateFound] = React.useState(false);
  const [advanceError, setAdvanceError] = React.useState<string | null>(null);

  const [content, setContent] = React.useState<ContentMatch | null | undefined>(undefined);
  const [contentLoading, setContentLoading] = React.useState(false);
  const [contentError, setContentError] = React.useState<string | null>(null);

  const [submitting, setSubmitting] = React.useState(false);
  const [submitError, setSubmitError] = React.useState<string | null>(null);

  // Bumped on every new content-fetch/duplicate-check call so a superseded
  // (slow, out-of-order) response can recognize it's stale and skip applying
  // its result — mirrors the `cancelled` flag the two list-fetch effects
  // below already use, extended to these two imperative async flows. Kept as
  // two separate counters (not one shared one) because handleContinueFromStep2
  // calls fetchContent internally — a shared counter would make fetchContent's
  // own bump look like it superseded the still-running outer call, permanently
  // skipping its finally-block cleanup (a real bug caught while re-testing this
  // fix: `duplicateChecking` got stuck `true` after every successful advance).
  const duplicateCheckTokenRef = React.useRef(0);
  const contentFetchTokenRef = React.useRef(0);

  const resetToSkillSelection = React.useCallback(() => {
    setDuplicateFound(false);
    setAdvanceError(null);
    setContent(undefined);
    setContentError(null);
    setSubmitError(null);
  }, []);

  const resetState = React.useCallback(() => {
    // Same rationale as handleBackFromStep3: invalidate any in-flight
    // fetchContent()/duplicate-check so a late response can't write into a
    // closed-and-reset (but still-mounted) modal instance.
    contentFetchTokenRef.current += 1;
    duplicateCheckTokenRef.current += 1;
    setStep(1);
    setEmployeeSearch('');
    setEmployees([]);
    setEmployeeId(null);
    setSkillSearch('');
    setSkills([]);
    setSkillId(null);
    setDuplicateFound(false);
    setDuplicateChecking(false);
    setAdvanceError(null);
    setContent(undefined);
    setContentLoading(false);
    setContentError(null);
    setSubmitting(false);
    setSubmitError(null);
  }, []);

  function handleClose() {
    // Guard against closing mid-flight: an in-progress duplicate-check can
    // still resolve and jump `step` forward, and an in-progress Assign POST
    // can't be un-sent once it's left the client — closing (and visually
    // resetting) while either is in flight would let a stale callback fire
    // against a modal the user believes is gone. Cancel/Back/the close
    // button are also `disabled` during these states so this is a silent
    // no-op only for Escape/backdrop-click, not a dead-looking button.
    if (submitting || duplicateChecking) return;
    resetState();
    onClose();
  }

  React.useEffect(() => {
    if (!open || step !== 1) return;
    let cancelled = false;
    setEmployeesLoading(true);
    listEmployees(employeeSearch || undefined)
      .then((result) => {
        if (!cancelled) setEmployees(result);
      })
      .finally(() => {
        if (!cancelled) setEmployeesLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [open, step, employeeSearch]);

  React.useEffect(() => {
    if (!open || step !== 2) return;
    let cancelled = false;
    setSkillsLoading(true);
    listSkills(skillSearch || undefined)
      .then((result) => {
        if (!cancelled) setSkills(result);
      })
      .finally(() => {
        if (!cancelled) setSkillsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [open, step, skillSearch]);

  async function fetchContent() {
    const token = ++contentFetchTokenRef.current;
    setContentLoading(true);
    setContentError(null);
    try {
      const match = await matchContentForSkill(skillId as string);
      if (contentFetchTokenRef.current !== token) return;
      setContent(match);
    } catch {
      if (contentFetchTokenRef.current !== token) return;
      setContentError("Couldn't load content recommendation.");
    } finally {
      if (contentFetchTokenRef.current === token) setContentLoading(false);
    }
  }

  async function handleContinueFromStep2() {
    if (!employeeId || !skillId) return;
    const token = ++duplicateCheckTokenRef.current;
    setAdvanceError(null);
    setDuplicateChecking(true);
    try {
      const existing = await checkDuplicateAssignment(employeeId, skillId);
      if (duplicateCheckTokenRef.current !== token) return;
      if (existing.length > 0) {
        setDuplicateFound(true);
        return;
      }
      setDuplicateFound(false);
      setStep(3);
      await fetchContent();
    } catch {
      if (duplicateCheckTokenRef.current !== token) return;
      setAdvanceError("Couldn't check for an existing assignment. Please try again.");
    } finally {
      if (duplicateCheckTokenRef.current === token) setDuplicateChecking(false);
    }
  }

  async function handleAssignAgain() {
    // Clears the interstitial's `duplicateFound` flag before advancing —
    // otherwise neither this path nor Step 3's [Back] could ever return the
    // user to the normal skill Combobox once a duplicate had been found once.
    setDuplicateFound(false);
    setStep(3);
    await fetchContent();
  }

  function handleBackFromStep3() {
    // Invalidate any in-flight fetchContent() (from Assign Again or Retry) so
    // a late-resolving response can't write into state after the user has
    // already navigated away — the modal stays mounted (DashboardStub only
    // toggles `open`), so a stale write would otherwise silently land here.
    contentFetchTokenRef.current += 1;
    resetToSkillSelection();
    setStep(2);
  }

  async function handleAssign() {
    if (!employeeId || !skillId) return;
    setSubmitting(true);
    setSubmitError(null);
    try {
      await createAssignment(employeeId, skillId, content?.id ?? null);
      onAssigned?.();
      handleClose();
    } catch {
      setSubmitError("Couldn't create the assignment. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  const employeeOptions: ComboboxOption[] = employees.map((employee) => ({
    id: employee.id,
    label: employee.name,
    sublabel: formatRole(employee.role),
  }));
  const skillOptions: ComboboxOption[] = skills.map((skill) => ({
    id: skill.id,
    label: skill.name,
  }));

  const selectedEmployee = employees.find((employee) => employee.id === employeeId);
  const selectedSkill = skills.find((skill) => skill.id === skillId);

  const metadata = (content?.content_metadata ?? null) as ContentMetadata | null;
  const durationMinutes = typeof metadata?.duration === 'number' ? Math.round(metadata.duration / 60) : null;
  const thumbnailUrl =
    content?.source === 'YOUTUBE' && metadata?.video_id
      ? `https://img.youtube.com/vi/${metadata.video_id}/hqdefault.jpg`
      : null;

  return (
    <Dialog open={open} onClose={handleClose} titleId={TITLE_ID}>
      <div className="mb-4 flex items-start justify-between">
        <div>
          <h2 id={TITLE_ID} className="text-xl font-semibold">
            Assign a New Skill
          </h2>
          <p aria-live="polite" className="mt-1 text-sm text-gray-500">
            Step {step} of {TOTAL_STEPS}
          </p>
        </div>
        <button
          type="button"
          onClick={handleClose}
          disabled={submitting || duplicateChecking}
          aria-label="Close"
          className="rounded-lg p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-talentpilot-500 disabled:cursor-not-allowed disabled:opacity-50"
        >
          ×
        </button>
      </div>

      {step === 1 && (
        <div>
          <label htmlFor="assignment-employee" className="mb-1 block text-sm font-medium text-gray-700">
            Who should learn this?
          </label>
          <Combobox
            id="assignment-employee"
            aria-label="Select employee or search"
            placeholder="Select employee or search..."
            options={employeeOptions}
            value={employeeId}
            onSelect={(id) => {
              setEmployeeId(id);
              // Clear a previously-chosen Skill from an earlier Step 2 visit
              // (reached via Back) — otherwise it stays silently pre-selected
              // for this new Employee, letting [Review Content] enable
              // without an explicit reaffirmation for the new pairing.
              setSkillId(null);
              setSkillSearch('');
              setSkills([]);
              resetToSkillSelection();
            }}
            searchValue={employeeSearch}
            onSearchChange={(value) => {
              setEmployeeSearch(value);
              setEmployeeId(null);
            }}
            loading={employeesLoading}
          />
          <div className="mt-6 flex justify-end gap-2">
            <Button variant="outline" onClick={handleClose}>
              Cancel
            </Button>
            <Button disabled={!employeeId} onClick={() => setStep(2)}>
              Continue to Skill Selection
            </Button>
          </div>
        </div>
      )}

      {step === 2 && duplicateFound && (
        <div>
          <p role="alert" className="mb-4 rounded-lg bg-amber-50 p-3 text-sm text-amber-800">
            This skill is already assigned to {selectedEmployee?.name ?? 'this employee'}.
          </p>
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={handleClose}>
              View
            </Button>
            <Button onClick={handleAssignAgain}>Assign Again</Button>
          </div>
        </div>
      )}

      {step === 2 && !duplicateFound && (
        <div>
          <label htmlFor="assignment-skill" className="mb-1 block text-sm font-medium text-gray-700">
            What skill?
          </label>
          <Combobox
            id="assignment-skill"
            aria-label="Search for a skill or select from recommended"
            placeholder="Search for a skill or select from recommended..."
            options={skillOptions}
            value={skillId}
            onSelect={(id) => {
              setSkillId(id);
              resetToSkillSelection();
            }}
            searchValue={skillSearch}
            onSearchChange={(value) => {
              setSkillSearch(value);
              setSkillId(null);
            }}
            loading={skillsLoading}
          />
          {advanceError && <FormErrorText className="mt-2">{advanceError}</FormErrorText>}
          <div className="mt-6 flex justify-end gap-2">
            <Button variant="outline" disabled={duplicateChecking} onClick={handleClose}>
              Cancel
            </Button>
            <Button variant="outline" disabled={duplicateChecking} onClick={() => setStep(1)}>
              Back
            </Button>
            <Button disabled={!skillId || duplicateChecking} onClick={handleContinueFromStep2}>
              {duplicateChecking ? 'Checking…' : 'Review Content'}
            </Button>
          </div>
        </div>
      )}

      {step === 3 && (
        <div>
          <p className="mb-2 text-sm font-medium text-gray-700">
            We&apos;ve found the best match for this skill:
          </p>

          {contentLoading ? (
            <div className="animate-pulse rounded-lg border border-gray-200 p-4">
              <div className="h-4 w-1/2 rounded bg-gray-200" />
              <div className="mt-2 h-3 w-1/3 rounded bg-gray-200" />
            </div>
          ) : contentError ? (
            <div className="rounded-lg border border-dashed border-red-300 p-4 text-sm">
              <FormErrorText>{contentError}</FormErrorText>
              <div className="mt-2">
                <Button variant="outline" onClick={fetchContent}>
                  Retry
                </Button>
              </div>
            </div>
          ) : content ? (
            <div className="rounded-lg border border-gray-200 p-4">
              {thumbnailUrl && (
                <img src={thumbnailUrl} alt="" className="mb-3 h-32 w-full rounded object-cover" />
              )}
              <div className="flex items-start justify-between">
                <div>
                  <p className="font-medium">{content.title}</p>
                  <p className="text-sm text-gray-500">
                    {formatSource(content.source)}
                    {durationMinutes !== null ? ` · ${durationMinutes} minutes` : ''}
                  </p>
                </div>
                <span className="rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700">
                  ✓ Approved
                </span>
              </div>
              {content.description && <p className="mt-2 text-sm text-gray-600">{content.description}</p>}
              <div className="mt-3 flex gap-4 text-sm">
                <a
                  href={content.url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-talentpilot-600 hover:underline"
                >
                  View on YouTube
                </a>
                <span aria-disabled="true" className="cursor-not-allowed text-gray-300">
                  Choose Different Content
                </span>
              </div>
            </div>
          ) : (
            <div className="rounded-lg border border-dashed border-gray-300 p-4 text-sm text-gray-500">
              No approved content found yet for this skill.
              <div className="mt-2">
                <span aria-disabled="true" className="cursor-not-allowed text-gray-300">
                  Choose Different Content
                </span>{' '}
                or assign without content.
              </div>
            </div>
          )}

          <div className="mt-4 rounded-lg bg-gray-50 p-3 text-sm text-gray-600">
            <p>Employee: {selectedEmployee?.name ?? '—'}</p>
            <p>Skill: {selectedSkill?.name ?? '—'}</p>
            <p>Content: {content ? `${content.title} (Approved)` : 'None'}</p>
            <p>Assignment Date: Today</p>
            <p>Status: Will be &quot;Assigned · Awaiting first watch&quot;</p>
          </div>

          {submitError && <FormErrorText className="mt-3">{submitError}</FormErrorText>}

          <div className="mt-6 flex justify-end gap-2">
            <Button variant="outline" disabled={submitting} onClick={handleClose}>
              Cancel
            </Button>
            <Button variant="outline" disabled={submitting} onClick={handleBackFromStep3}>
              Back
            </Button>
            <Button disabled={submitting || contentLoading || !!contentError} onClick={handleAssign}>
              {submitting ? 'Assigning…' : content === null ? 'Assign without content' : 'Assign'}
            </Button>
          </div>
        </div>
      )}
    </Dialog>
  );
}
