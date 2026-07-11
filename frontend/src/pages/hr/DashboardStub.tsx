import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { FormErrorText } from '@/components/ui/form-error-text';
import { Toast } from '@/components/ui/toast';
import { useAuth } from '@/lib/auth/AuthContext';
import { logout } from '@/lib/api/authApi';
import { AssignmentModal } from '@/features/assignments/AssignmentModal';
import { AssignmentsList, type AssignmentsListHandle } from '@/features/dashboard/AssignmentsList';
import type { Assignment } from '@/lib/api/assignmentsApi';

// Matches AC4's 3-5s highlight window (epics.md) — same value used for the
// toast's own default auto-dismiss (components/ui/toast.tsx).
const HIGHLIGHT_DURATION_MS = 4000;

export function DashboardStub() {
  const { signOut } = useAuth();
  const navigate = useNavigate();
  const [assignmentModalOpen, setAssignmentModalOpen] = useState(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [highlightedId, setHighlightedId] = useState<string | null>(null);
  const [refreshError, setRefreshError] = useState(false);
  const [retrying, setRetrying] = useState(false);
  const listRef = useRef<AssignmentsListHandle>(null);
  // Tracks the pending row-highlight-clear timeout so a second assignment
  // created within the same 4s window doesn't have its highlight cleared
  // early by the first timer, and so the timer can be cancelled on unmount
  // (code review finding: navigating away mid-window otherwise calls
  // setHighlightedId on an unmounted component).
  const highlightTimerRef = useRef<number | null>(null);

  useEffect(() => {
    return () => {
      if (highlightTimerRef.current !== null) window.clearTimeout(highlightTimerRef.current);
    };
  }, []);

  async function handleAssigned(assignment: Assignment, employeeName: string, skillName: string) {
    // The Assignment was already created successfully (POST already
    // returned 201) — the toast fires unconditionally on that success,
    // independent of whether the immediate dashboard refresh below
    // succeeds (code review decision: previously gated behind refetch
    // success, which suppressed the toast entirely on a refresh failure).
    const firstName = employeeName.split(' ')[0];
    setToastMessage(`✓ Skill assigned to ${firstName} — ${skillName}`);

    // AC1: the row must appear within ~1s of the POST succeeding — an
    // immediate one-shot re-fetch here, not a wait on any future background
    // polling loop (Story 5.4's poll interval is 10-15s, far too slow).
    const ok = await listRef.current?.refetch();
    if (ok) {
      setRefreshError(false);
      setHighlightedId(assignment.id);
      if (highlightTimerRef.current !== null) window.clearTimeout(highlightTimerRef.current);
      highlightTimerRef.current = window.setTimeout(() => {
        setHighlightedId(null);
        highlightTimerRef.current = null;
      }, HIGHLIGHT_DURATION_MS);
    } else {
      // AC5: refetch failing must never imply the Assignment itself was
      // lost — the refresh-error banner can render alongside the toast.
      setRefreshError(true);
    }
  }

  async function handleRetryRefresh() {
    setRetrying(true);
    try {
      const ok = await listRef.current?.refetch();
      if (ok) setRefreshError(false);
    } finally {
      setRetrying(false);
    }
  }

  async function handleSignOut() {
    try {
      await logout();
    } catch {
      // Best-effort server-side revocation: if the request fails (network
      // error, 5xx), the user's intent to sign out is still honored
      // client-side below, matching AC6's guarantee.
    } finally {
      signOut();
      navigate('/login', { replace: true });
    }
  }

  return (
    <div className="mx-auto max-w-2xl p-8">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold">HR Dashboard</h1>
        <div className="flex gap-2">
          <Button onClick={() => setAssignmentModalOpen(true)}>+ New Assignment</Button>
          <Button variant="outline" onClick={handleSignOut}>
            Sign Out
          </Button>
        </div>
      </div>

      {refreshError && (
        <div className="mb-4 rounded-lg border border-dashed border-red-300 p-3 text-sm">
          <FormErrorText>Assignment saved, but dashboard didn&apos;t update.</FormErrorText>
          <div className="mt-2">
            <Button variant="outline" disabled={retrying} onClick={handleRetryRefresh}>
              {retrying ? 'Retrying…' : 'Retry'}
            </Button>
          </div>
        </div>
      )}

      <AssignmentsList ref={listRef} highlightedId={highlightedId} />

      <AssignmentModal
        open={assignmentModalOpen}
        onClose={() => setAssignmentModalOpen(false)}
        onAssigned={handleAssigned}
      />
      <Toast message={toastMessage} onDismiss={() => setToastMessage(null)} />
    </div>
  );
}
