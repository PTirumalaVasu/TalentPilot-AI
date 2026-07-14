import { useEffect, useId, useRef, useState } from "react";
import { Dialog } from "@/components/ui/dialog";
import { dashboardApi } from "@/lib/api/dashboardApi";

export interface DeleteAssignmentModalProps {
  assignmentId: string | null;
  employeeName: string;
  skillName: string;
  /** Row status !== "Not Started" -- see story Dev Notes for why this is
   * the correct escalation-trigger proxy without an extra API call. */
  hasRecordedProgress: boolean;
  /** Null when hasRecordedProgress is true but the row is Completed (the
   * dashboard grid nulls status_percentage unless status === "In Progress"). */
  progressPercent: number | null;
  open: boolean;
  onClose: () => void;
  onDeleted: (assignmentId: string) => void;
}

/**
 * Delete-confirmation modal (Story 5.7). Built on the existing `Dialog`
 * primitive exactly as `ProvenanceDrillDownModal.tsx` does -- focus trap,
 * Escape, backdrop-click all already handled there.
 */
export function DeleteAssignmentModal({
  assignmentId,
  employeeName,
  skillName,
  hasRecordedProgress,
  progressPercent,
  open,
  onClose,
  onDeleted,
}: DeleteAssignmentModalProps) {
  const titleId = useId();
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  // Guards a slow delete response against a modal reused for a different
  // assignment before it resolves -- mirrors ProvenanceDrillDownModal.tsx's
  // requestIdRef pattern (code review finding, Story 5.2).
  const requestIdRef = useRef(0);

  // Code review patch: this modal is an always-mounted single instance
  // (DashboardPage.tsx only toggles `open`, never remounts it per row), so
  // without this reset a delete cancelled mid-flight (Escape, backdrop, or
  // [Cancel]) left `submitting`/`submitError` stuck from the abandoned
  // request -- disabling Cancel/Confirm on every future delete, for any
  // row, until a full page reload. Bumping requestIdRef here also
  // invalidates any in-flight request's finally-block guard. Mirrors
  // ProvenanceDrillDownModal.tsx's fetchDetail(), which resets its
  // equivalent state on every assignmentId/open change the same way.
  useEffect(() => {
    requestIdRef.current += 1;
    setSubmitting(false);
    setSubmitError(null);
  }, [assignmentId, open]);

  function handleCancel() {
    requestIdRef.current += 1;
    setSubmitError(null);
    onClose();
  }

  async function handleConfirm() {
    if (!assignmentId) return;
    const requestIdAtSubmit = ++requestIdRef.current;
    setSubmitting(true);
    setSubmitError(null);
    try {
      await dashboardApi.deleteAssignment(assignmentId);
      if (requestIdRef.current !== requestIdAtSubmit) return;
      onDeleted(assignmentId);
      onClose();
    } catch (err) {
      if (requestIdRef.current !== requestIdAtSubmit) return;
      const message = err instanceof Error ? err.message : "Couldn't remove assignment. Try again.";
      setSubmitError(message);
    } finally {
      if (requestIdRef.current === requestIdAtSubmit) {
        setSubmitting(false);
      }
    }
  }

  if (!open) return null;

  return (
    <Dialog open={open} onClose={handleCancel} titleId={titleId}>
      <div className="space-y-4">
        <h2 id={titleId} className="text-lg font-bold text-gray-900">
          Remove this assignment?
        </h2>
        <p className="text-sm text-gray-700">
          {employeeName} — {skillName}
        </p>
        {hasRecordedProgress && (
          <p className="text-sm text-gray-700">
            This assignment has recorded progress (
            {progressPercent !== null ? `${progressPercent}% watched` : "Completed"}). Removing it
            will take it off the dashboard; the history is retained for audit.
          </p>
        )}

        {submitError && (
          <p role="alert" className="text-red-600 text-sm">
            {submitError}
          </p>
        )}

        <div className="flex items-center justify-end gap-2 pt-2 border-t border-gray-100">
          <button
            disabled={submitting}
            onClick={handleCancel}
            className="text-sm font-medium text-gray-600 hover:underline disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            disabled={submitting}
            onClick={handleConfirm}
            className="bg-red-600 text-white text-sm font-semibold px-4 py-2 rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50"
          >
            Remove Assignment
          </button>
        </div>
      </div>
    </Dialog>
  );
}
