import { useEffect, useId, useRef, useState } from 'react';
import { Dialog } from '@/components/ui/dialog';
import { FormErrorText } from '@/components/ui/form-error-text';
import { deleteOrArchiveEmployee } from '@/lib/api/employeesApi';

export interface DeleteArchiveEmployeeModalProps {
  employee: { id: string; name: string; has_assignment_history: boolean } | null;
  open: boolean;
  onClose: () => void;
  onCompleted: (action: 'deleted' | 'archived') => void;
}

function extractErrorMessage(err: unknown, fallback: string): string {
  if (err && typeof err === 'object' && 'response' in err) {
    const response = (err as { response?: { data?: { message?: string } } }).response;
    if (response?.data?.message) return response.data.message;
  }
  return fallback;
}

/**
 * Delete/Archive confirmation modal for an Employee (Story 7.5, FR-27;
 * UX-DR38). Mirrors DeleteSkillModal.tsx's Dialog/requestIdRef/
 * extractErrorMessage() shape, but unlike that modal's always-static copy
 * (Skills gate deletability by hiding the button entirely), this one always
 * renders and must show one of two messages depending on
 * employee.has_assignment_history -- decided server-side (the field comes
 * from the already-fetched roster list, not a fresh per-click check) and
 * independently re-decided atomically by the DELETE endpoint itself at
 * confirm time, whose response's `action` (not this dialog's prediction)
 * drives the caller's success toast.
 */
export function DeleteArchiveEmployeeModal({ employee, open, onClose, onCompleted }: DeleteArchiveEmployeeModalProps) {
  const titleId = useId();
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const requestIdRef = useRef(0);

  useEffect(() => {
    requestIdRef.current += 1;
    setSubmitting(false);
    setSubmitError(null);
  }, [employee?.id, open]);

  function handleCancel() {
    requestIdRef.current += 1;
    setSubmitError(null);
    onClose();
  }

  async function handleConfirm() {
    if (!employee) return;
    const requestIdAtSubmit = ++requestIdRef.current;
    setSubmitting(true);
    setSubmitError(null);
    try {
      const result = await deleteOrArchiveEmployee(employee.id);
      if (requestIdRef.current !== requestIdAtSubmit) return;
      onCompleted(result.action);
      onClose();
    } catch (err) {
      if (requestIdRef.current !== requestIdAtSubmit) return;
      setSubmitError(extractErrorMessage(err, "Couldn't complete this — Try again"));
    } finally {
      if (requestIdRef.current === requestIdAtSubmit) setSubmitting(false);
    }
  }

  if (!open || !employee) return null;

  const hasHistory = employee.has_assignment_history;

  return (
    <Dialog open={open} onClose={handleCancel} titleId={titleId} className="max-w-md">
      <div className="space-y-4">
        <h2 id={titleId} className="text-lg font-bold text-gray-900" data-testid="delete-employee-heading">
          Remove {employee.name}?
        </h2>
        {hasHistory ? (
          <p className="text-sm text-gray-700" data-testid="delete-employee-summary-archive">
            &apos;{employee.name}&apos; has assignment history — they&apos;ll be archived, not deleted. Their
            records are kept, but they&apos;ll drop off the active roster and every assignment picker.
          </p>
        ) : (
          <p className="text-sm text-gray-700" data-testid="delete-employee-summary-hard">
            &apos;{employee.name}&apos; has no assignments yet — this will permanently remove them.
          </p>
        )}

        {submitError && <FormErrorText>{submitError}</FormErrorText>}

        <div className="flex items-center justify-end gap-2 border-t border-gray-100 pt-2">
          <button
            type="button"
            disabled={submitting}
            onClick={handleCancel}
            className="text-sm font-medium text-gray-600 hover:underline disabled:opacity-50"
            data-testid="delete-employee-btn-cancel"
          >
            Cancel
          </button>
          <button
            type="button"
            disabled={submitting}
            onClick={handleConfirm}
            className="rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-red-700 disabled:opacity-50"
            data-testid="delete-employee-btn-confirm"
          >
            {submitting ? 'Working…' : hasHistory ? 'Archive Employee' : 'Remove Employee'}
          </button>
        </div>
      </div>
    </Dialog>
  );
}
