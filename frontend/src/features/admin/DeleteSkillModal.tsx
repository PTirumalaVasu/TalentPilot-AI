import { useEffect, useId, useRef, useState } from 'react';
import { Dialog } from '@/components/ui/dialog';
import { deleteSkill } from '@/lib/api/skillsApi';

export interface DeleteSkillModalProps {
  skill: { id: string; name: string } | null;
  open: boolean;
  onClose: () => void;
  onDeleted: (skillId: string) => void;
}

function extractErrorMessage(err: unknown, fallback: string): string {
  if (err && typeof err === 'object' && 'response' in err) {
    const response = (err as { response?: { data?: { message?: string } } }).response;
    if (response?.data?.message) return response.data.message;
  }
  return fallback;
}

/**
 * Delete-confirmation modal for an unassigned Skill (Story 6.3, FR-22;
 * UX-DR32's Delete side). Built on the existing `Dialog` primitive exactly
 * as `DeleteAssignmentModal.tsx` does -- same requestIdRef guard against a
 * slow response racing a modal reused for a different skill.
 */
export function DeleteSkillModal({ skill, open, onClose, onDeleted }: DeleteSkillModalProps) {
  const titleId = useId();
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const requestIdRef = useRef(0);

  useEffect(() => {
    requestIdRef.current += 1;
    setSubmitting(false);
    setSubmitError(null);
  }, [skill?.id, open]);

  function handleCancel() {
    requestIdRef.current += 1;
    setSubmitError(null);
    onClose();
  }

  async function handleConfirm() {
    if (!skill) return;
    const requestIdAtSubmit = ++requestIdRef.current;
    setSubmitting(true);
    setSubmitError(null);
    try {
      await deleteSkill(skill.id);
      if (requestIdRef.current !== requestIdAtSubmit) return;
      onDeleted(skill.id);
      onClose();
    } catch (err) {
      if (requestIdRef.current !== requestIdAtSubmit) return;
      setSubmitError(extractErrorMessage(err, "Couldn't delete this skill — Try again"));
    } finally {
      if (requestIdRef.current === requestIdAtSubmit) setSubmitting(false);
    }
  }

  if (!open || !skill) return null;

  return (
    <Dialog open={open} onClose={handleCancel} titleId={titleId} className="max-w-md">
      <div className="space-y-4">
        <h2 id={titleId} className="text-lg font-bold text-gray-900" data-testid="delete-skill-heading">
          Delete this skill?
        </h2>
        <p className="text-sm text-gray-700" data-testid="delete-skill-summary">
          &apos;{skill.name}&apos; has no Assignments yet — this will permanently remove it and its approved
          content link, if any.
        </p>

        {submitError && <p className="text-sm text-red-600">{submitError}</p>}

        <div className="flex items-center justify-end gap-2 border-t border-gray-100 pt-2">
          <button
            type="button"
            disabled={submitting}
            onClick={handleCancel}
            className="text-sm font-medium text-gray-600 hover:underline disabled:opacity-50"
            data-testid="delete-skill-btn-cancel"
          >
            Cancel
          </button>
          <button
            type="button"
            disabled={submitting}
            onClick={handleConfirm}
            className="rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-red-700 disabled:opacity-50"
            data-testid="delete-skill-btn-confirm"
          >
            {submitting ? 'Deleting…' : 'Delete Skill'}
          </button>
        </div>
      </div>
    </Dialog>
  );
}
